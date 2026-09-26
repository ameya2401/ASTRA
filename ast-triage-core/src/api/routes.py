"""
src/api/routes.py - FastAPI endpoint definitions for ASTRA triage.

Defines REST endpoints for:
    - Pull request triage analysis: POST /api/v1/triage/analyze
    - Maintainer prioritization queue: GET /api/v1/triage/queue/{repo_name}
    - GitHub native webhook ingestion: POST /api/v1/github/webhook
    - System health check: GET /api/v1/health
"""
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from database.connection import get_async_session
from database.models import FeatureRecord, PullRequest, Repository, TriagePrediction
from src.api.schemas import (
    GitHubWebhookAck,
    HealthResponse,
    PRWebhookPayload,
    SHAPExplanationItem,
    TriageQueueItem,
    TriageResponse,
)
from src.ast_engine.differ import ASTMetrics, diff_multi_file
from src.feature_pipeline.normalizer import clip_feature_bounds, impute_missing_values
from src.feature_pipeline.vector_builder import (
    build_feature_vector,
    extract_process_metrics,
    extract_test_metrics,
)
from src.integrations.github_client import GitHubClient
from src.integrations.reporter import generate_markdown_report
from src.ml_engine.predictor import get_predictor
from src.semantic_engine.drift_analyzer import SemanticDriftAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["triage"])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency providing an async database session."""
    async with get_async_session() as session:
        yield session


def parse_diff_into_files(raw_diff: str) -> List[Dict[str, str]]:
    """
    Parses a unified diff string into base and head source code pairs per file.

    Args:
        raw_diff: Unified diff string.

    Returns:
        List of dicts with 'base_code' and 'head_code' keys.
    """
    if not raw_diff or not raw_diff.strip():
        return [{"base_code": "", "head_code": ""}]

    # If it is a multi-file unified git diff, split on "diff --git "
    if "diff --git " in raw_diff:
        chunks = raw_diff.split("diff --git ")
        file_diffs: List[Dict[str, str]] = []
        for chunk in chunks:
            if not chunk.strip():
                continue
            base_lines: List[str] = []
            head_lines: List[str] = []
            for line in chunk.splitlines():
                if line.startswith(("--- ", "+++ ", "index ", "@@", "new file", "deleted file")):
                    continue
                if line.startswith("-"):
                    base_lines.append(line[1:])
                elif line.startswith("+"):
                    head_lines.append(line[1:])
                elif line.startswith(" "):
                    base_lines.append(line[1:])
                    head_lines.append(line[1:])
            file_diffs.append({
                "base_code": "\n".join(base_lines),
                "head_code": "\n".join(head_lines),
            })
        if file_diffs:
            return file_diffs

    # Fallback for single unified diff without git headers
    base_lines = []
    head_lines = []
    has_diff_markers = False
    for line in raw_diff.splitlines():
        if line.startswith(("--- ", "+++ ", "@@")):
            has_diff_markers = True
            continue
        if line.startswith("-"):
            base_lines.append(line[1:])
            has_diff_markers = True
        elif line.startswith("+"):
            head_lines.append(line[1:])
            has_diff_markers = True
        elif line.startswith(" "):
            base_lines.append(line[1:])
            head_lines.append(line[1:])
        else:
            base_lines.append(line)
            head_lines.append(line)

    if has_diff_markers:
        return [{
            "base_code": "\n".join(base_lines),
            "head_code": "\n".join(head_lines),
        }]

    # Plain code snippet treated as head code with empty base
    return [{"base_code": "", "head_code": raw_diff}]


async def persist_triage_record(
    session: AsyncSession,
    payload: PRWebhookPayload,
    vector_row: List[float],
    pred_res: Dict[str, Any],
) -> None:
    """
    Persists Repository, PullRequest, FeatureRecord, and TriagePrediction
    to the database within the current session.
    """
    try:
        # 1. Upsert / locate Repository
        stmt_repo = select(Repository).where(Repository.repo_name == payload.repo_name)
        result_repo = await session.execute(stmt_repo)
        repo = result_repo.scalar_one_or_none()
        if not repo:
            repo = Repository(repo_name=payload.repo_name, default_branch="main")
            session.add(repo)
            await session.flush()

        # 2. Upsert PullRequest
        stmt_pr = select(PullRequest).where(
            PullRequest.repo_id == repo.id,
            PullRequest.pr_number == payload.pr_number,
        )
        result_pr = await session.execute(stmt_pr)
        pr_record = result_pr.scalar_one_or_none()

        gt_label = 1 if pred_res["risk_tier"] == "HIGH" else 0
        if not pr_record:
            pr_record = PullRequest(
                repo_id=repo.id,
                pr_number=payload.pr_number,
                title=payload.title,
                issue_description=payload.issue_description,
                author_login=payload.author_login,
                author_is_bot=payload.author_is_bot,
                agent_framework=payload.agent_framework,
                base_sha=payload.base_sha,
                head_sha=payload.head_sha,
                raw_diff=payload.raw_diff,
                ci_passed=payload.ci_passed,
                ground_truth_status="PENDING",
                ground_truth_label=gt_label,
            )
            session.add(pr_record)
            await session.flush()
        else:
            pr_record.title = payload.title
            pr_record.issue_description = payload.issue_description
            pr_record.raw_diff = payload.raw_diff
            pr_record.ci_passed = payload.ci_passed
            pr_record.ground_truth_label = gt_label
            await session.flush()

        # 3. Create or update FeatureRecord
        stmt_feat = select(FeatureRecord).where(FeatureRecord.pr_id == pr_record.id)
        result_feat = await session.execute(stmt_feat)
        feat_record = result_feat.scalar_one_or_none()

        v = vector_row
        feat_kwargs = {
            "f01_ast_nodes_added": int(v[0]),
            "f02_ast_nodes_deleted": int(v[1]),
            "f03_ast_nodes_mutated": int(v[2]),
            "f04_cyclomatic_delta": int(v[3]),
            "f05_max_nesting_depth_delta": int(v[4]),
            "f06_func_signatures_modified": int(v[5]),
            "f07_classes_modified": int(v[6]),
            "f08_return_types_altered": int(v[7]),
            "f09_call_graph_fan_out_delta": int(v[8]),
            "f10_ast_disturbance_index": float(v[9]),
            "f11_try_catch_blocks_added": int(v[10]),
            "f12_control_flow_churn_ratio": float(v[11]),
            "f13_intent_diff_cosine_sim": float(v[12]),
            "f14_issue_title_diff_sim": float(v[13]),
            "f15_entity_drift_jaccard": float(v[14]),
            "f16_docstring_to_code_ratio": float(v[15]),
            "f17_semantic_drift_flag": int(v[16]),
            "f18_issue_token_length": int(v[17]),
            "f19_test_files_modified": int(v[18]),
            "f20_test_ast_nodes_added": int(v[19]),
            "f21_test_assertions_deleted": int(v[20]),
            "f22_test_to_logic_ratio": float(v[21]),
            "f23_mock_patch_count_delta": int(v[22]),
            "f24_commit_count": int(v[23]),
            "f25_files_touched_count": int(v[24]),
            "f26_file_dispersion_entropy": float(v[25]),
            "f27_ci_pass_flag": int(v[26]),
            "f28_is_known_agent_bot": int(v[27]),
        }

        if not feat_record:
            feat_record = FeatureRecord(pr_id=pr_record.id, **feat_kwargs)
            session.add(feat_record)
        else:
            for k, val in feat_kwargs.items():
                setattr(feat_record, k, val)

        # 4. Create or update TriagePrediction
        stmt_pred = select(TriagePrediction).where(TriagePrediction.pr_id == pr_record.id)
        result_pred = await session.execute(stmt_pred)
        pred_record = result_pred.scalar_one_or_none()

        drivers = pred_res.get("shap_attributions", [])
        top1 = drivers[0] if len(drivers) > 0 else {}
        top2 = drivers[1] if len(drivers) > 1 else {}
        top3 = drivers[2] if len(drivers) > 2 else {}

        pred_kwargs = {
            "raw_risk_score": float(pred_res.get("raw_risk_score", 0.0)),
            "calibrated_risk_score": float(pred_res.get("calibrated_risk_score", 0.0)),
            "risk_tier": pred_res.get("risk_tier", "LOW"),
            "top_shap_feature_1": top1.get("feature_name"),
            "shap_value_1": top1.get("shap_value"),
            "top_shap_feature_2": top2.get("feature_name"),
            "shap_value_2": top2.get("shap_value"),
            "top_shap_feature_3": top3.get("feature_name"),
            "shap_value_3": top3.get("shap_value"),
            "inference_latency_ms": float(pred_res.get("inference_latency_ms", 0.0)),
        }

        if not pred_record:
            pred_record = TriagePrediction(pr_id=pr_record.id, **pred_kwargs)
            session.add(pred_record)
        else:
            for k, val in pred_kwargs.items():
                setattr(pred_record, k, val)

        await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist triage record to database: {e}", exc_info=True)
        await session.rollback()


@router.post("/triage/analyze", response_model=TriageResponse)
async def analyze_pull_request(
    payload: PRWebhookPayload,
    session: Optional[AsyncSession] = Depends(get_db),
) -> TriageResponse:
    """
    Analyzes an incoming pull request payload and returns a calibrated risk assessment.

    Asynchronously coordinates:
        1. Tree-sitter AST structural delta extraction (F01-F12)
        2. Intent-to-diff semantic alignment calculation (F13-F18)
        3. Test churn and author provenance metrics (F19-F28)
        4. Feature vector assembly and bounded normalization
        5. Calibrated XGBoost inference and TreeSHAP feature attribution
        6. Optional database persistence
    """
    start_time = time.perf_counter()

    try:
        # 1. Structural AST Features (F01-F12)
        file_diffs = parse_diff_into_files(payload.raw_diff)
        ast_result = diff_multi_file(file_diffs)

        # 2. Semantic Drift Features (F13-F18)
        analyzer = SemanticDriftAnalyzer()
        semantic_result = analyzer.analyze(
            issue_description=payload.issue_description,
            raw_diff=payload.raw_diff,
            issue_title=payload.title,
        )

        # 3. Test Churn & Process Features (F19-F28)
        test_result = extract_test_metrics(
            raw_diff=payload.raw_diff,
            ast_metrics=ast_result,
        )
        process_result = extract_process_metrics(
            commit_count=payload.commit_count or 1,
            files_touched=payload.files_touched,
            file_churns=payload.file_churns,
            ci_passed=payload.ci_passed,
            author_is_bot=payload.author_is_bot,
            author_login=payload.author_login,
        )

        # 4. Feature Vector Assembly & Normalization
        X_sample = build_feature_vector(
            ast_metrics=ast_result,
            semantic_metrics=semantic_result,
            test_metrics=test_result,
            process_metrics=process_result,
        )
        X_sample = impute_missing_values(X_sample)
        X_sample = clip_feature_bounds(X_sample)

        # 5. Inference & SHAP Attribution
        predictor = get_predictor()
        pred_res = predictor.predict(X_sample, check_hard_overrides=True)

        tier = pred_res["risk_tier"]
        prob = pred_res["calibrated_risk_score"]

        # 6. Recommendation formulation
        if tier == "LOW":
            recommendation = "FAST-TRACK: High structural integrity, intent aligned, tests verified."
        elif tier == "MEDIUM":
            recommendation = "STANDARD REVIEW: Verify boundary conditions and cyclomatic changes."
        else:
            recommendation = "DEPRIORITIZE / REJECT: Probable semantic divergence, test cheat, or AST bloat."

        # Map SHAP attributions to response items
        top_risk_drivers: List[SHAPExplanationItem] = []
        for item in pred_res.get("shap_attributions", [])[:3]:
            top_risk_drivers.append(
                SHAPExplanationItem(
                    feature_name=item["feature_name"],
                    shap_value=round(item["shap_value"], 4),
                    description=f"{item['feature_name']} = {item['feature_value']} ({item['impact']})",
                    feature_value=item.get("feature_value"),
                    impact=item.get("impact"),
                )
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # 7. Asynchronous persistence
        if session:
            vector_list = [float(x) for x in X_sample[0]]
            await persist_triage_record(session, payload, vector_list, pred_res)

        return TriageResponse(
            pr_number=payload.pr_number,
            repo_name=payload.repo_name,
            risk_probability=prob,
            raw_risk_score=pred_res.get("raw_risk_score"),
            risk_tier=tier,
            recommendation=recommendation,
            top_risk_drivers=top_risk_drivers,
            latency_ms=elapsed_ms,
            override_applied=pred_res.get("override_applied"),
        )
    except Exception as e:
        logger.error(f"Error analyzing PR #{payload.pr_number}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Triage pipeline failed: {str(e)}",
        )


@router.get("/triage/queue/{repo_name:path}", response_model=List[TriageQueueItem])
async def get_triage_queue(
    repo_name: str,
    sort_by: str = "risk_asc",
    session: AsyncSession = Depends(get_db),
) -> List[TriageQueueItem]:
    """
    Retrieves the maintainer review queue for a repository sorted by triage priority.

    Default sort is 'risk_asc' (lowest risk first) to enable fast-tracking.
    """
    stmt = (
        select(PullRequest, TriagePrediction)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .outerjoin(TriagePrediction, PullRequest.id == TriagePrediction.pr_id)
        .where(Repository.repo_name == repo_name)
    )

    if sort_by == "risk_desc":
        stmt = stmt.order_by(desc(TriagePrediction.calibrated_risk_score))
    else:
        stmt = stmt.order_by(TriagePrediction.calibrated_risk_score.asc().nullslast())

    result = await session.execute(stmt)
    rows = result.all()

    queue_items: List[TriageQueueItem] = []
    for pr, pred in rows:
        risk_prob = float(pred.calibrated_risk_score) if pred else 0.5
        risk_tier = pred.risk_tier if pred else "MEDIUM"
        created_str = pr.created_at.isoformat() if pr.created_at else None

        queue_items.append(
            TriageQueueItem(
                pr_number=pr.pr_number,
                repo_name=repo_name,
                title=pr.title,
                risk_tier=risk_tier,
                risk_probability=round(risk_prob, 4),
                author_login=pr.author_login,
                ci_passed=pr.ci_passed,
                created_at=created_str,
            )
        )

    return queue_items


@router.post("/github/webhook", response_model=GitHubWebhookAck)
async def github_webhook_endpoint(
    request: Request,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    session: AsyncSession = Depends(get_db),
) -> GitHubWebhookAck:
    """
    Ingestion endpoint for native GitHub webhooks.

    Validates HMAC signature and handles pull_request opened, synchronize,
    and reopened events.
    """
    body_bytes = await request.body()

    # Signature verification
    github_client = GitHubClient()
    if not github_client.verify_webhook_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitHub webhook HMAC-SHA256 signature",
        )

    event = x_github_event or "unknown"
    if event == "ping":
        return GitHubWebhookAck(
            status="processed",
            event=event,
            message="Pong: Webhook configuration verified successfully.",
        )

    if event != "pull_request":
        return GitHubWebhookAck(
            status="ignored",
            event=event,
            message=f"Event '{event}' is not monitored for triage.",
        )

    payload = await request.json()
    action = payload.get("action")
    supported_actions = {"opened", "synchronize", "reopened"}

    if action not in supported_actions:
        return GitHubWebhookAck(
            status="ignored",
            event=event,
            action=action,
            message=f"Action '{action}' does not trigger triage re-evaluation.",
        )

    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    repo_name = repo_data.get("full_name") or "unknown/unknown"
    pr_number = pr_data.get("number", 0)

    # Extract or fetch diff
    raw_diff = pr_data.get("diff", "")
    if not raw_diff and github_client.token:
        raw_diff = await github_client.get_pr_diff(repo_name, pr_number)

    author = pr_data.get("user", {})
    author_login = author.get("login", "")
    author_is_bot = author.get("type") == "Bot"

    triage_payload = PRWebhookPayload(
        repo_name=repo_name,
        pr_number=pr_number,
        title=pr_data.get("title", "Untitled PR"),
        issue_description=pr_data.get("body") or "",
        author_login=author_login,
        author_is_bot=author_is_bot,
        agent_framework="github-agent",
        base_sha=pr_data.get("base", {}).get("sha", ""),
        head_sha=pr_data.get("head", {}).get("sha", ""),
        raw_diff=raw_diff,
        ci_passed=True,
    )

    triage_response = await analyze_pull_request(triage_payload, session=session)

    # Post comment back to GitHub if client is configured
    markdown_report = generate_markdown_report(triage_response, repo_name, pr_number)
    posted = await github_client.post_pr_comment(repo_name, pr_number, markdown_report)

    comment_msg = "Triage comment posted to PR." if posted else "Triage evaluated."

    return GitHubWebhookAck(
        status="processed",
        event=event,
        action=action,
        message=f"PR #{pr_number} analyzed ({triage_response.risk_tier} risk). {comment_msg}",
        triage_summary={
            "pr_number": pr_number,
            "risk_tier": triage_response.risk_tier,
            "risk_probability": triage_response.risk_probability,
            "latency_ms": triage_response.latency_ms,
        },
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """
    Verifies service health, database connectivity, and ML model checkpoints.
    """
    settings = get_settings()

    # Test ML model availability
    predictor_loaded = False
    try:
        predictor = get_predictor()
        predictor_loaded = predictor.model is not None
    except Exception as e:
        logger.error(f"Health check failed to inspect model: {e}")

    # Test DB connectivity
    db_connected = False
    try:
        result = await session.execute(select(1))
        db_connected = result.scalar() == 1
    except Exception as e:
        logger.error(f"Health check failed DB query: {e}")

    service_status = "healthy" if predictor_loaded and db_connected else "degraded"

    return HealthResponse(
        status=service_status,
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        model_loaded=predictor_loaded,
        database_connected=db_connected,
    )
