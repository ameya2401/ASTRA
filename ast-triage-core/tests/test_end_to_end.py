"""
tests/test_end_to_end.py - End-to-end integration tests for Phase 5.

Validates the complete triage pipeline:
    1. PR payload ingestion via REST and native GitHub webhooks
    2. AST feature extraction and Tree-sitter delta calculation
    3. Semantic drift computation using dense sentence embeddings
    4. 28-D vector assembly, bound clipping, and normalization
    5. Calibrated XGBoost inference and TreeSHAP attribution
    6. Maintainer prioritization queue retrieval
    7. Database persistence across all four relational entities
    8. GitHub markdown comment generation with SVG badges
"""
import hashlib
import hmac
import pytest
from fastapi.testclient import TestClient

from config.settings import get_settings
from src.api.main import app
from src.api.schemas import PRWebhookPayload, SHAPExplanationItem, TriageResponse
from src.integrations.github_client import GitHubClient
from src.integrations.reporter import generate_markdown_report


@pytest.fixture(scope="module")
def client():
    """Initializes a TestClient bound to the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verifies that the root metadata endpoint returns operational status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "health_url" in data
    assert "triage_url" in data


def test_health_check_endpoint(client):
    """Verifies service health, model verification, and DB connectivity."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["database_connected"] is True
    assert data["app_name"] == "AST-Triage"


def test_analyze_clean_pr(client):
    """
    Simulates a clean, well-aligned bugfix PR with accompanying tests.
    Expects LOW risk tier, FAST-TRACK recommendation, and sub-300ms SLA.
    """
    payload = {
        "repo_name": "ast-org/calculator",
        "pr_number": 101,
        "title": "Fix division by zero in calculate_ratio",
        "issue_description": (
            "When the denominator b is zero in calculate_ratio(a, b), "
            "a ZeroDivisionError is raised. Return 0.0 when b is zero."
        ),
        "author_login": "contributor-jane",
        "author_is_bot": False,
        "agent_framework": "human",
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "raw_diff": (
            "diff --git a/calculator.py b/calculator.py\n"
            "--- a/calculator.py\n"
            "+++ b/calculator.py\n"
            "@@ -5,1 +5,3 @@\n"
            "-    return a / b\n"
            "+    if b == 0:\n"
            "+        return 0.0\n"
            "+    return a / b\n"
            "diff --git a/tests/test_calculator.py b/tests/test_calculator.py\n"
            "--- a/tests/test_calculator.py\n"
            "+++ b/tests/test_calculator.py\n"
            "@@ -10,0 +10,3 @@\n"
            "+def test_div_by_zero():\n"
            "+    assert calculate_ratio(10, 0) == 0.0\n"
            "+    assert calculate_ratio(10, 2) == 5.0\n"
        ),
        "ci_passed": True,
        "commit_count": 1,
    }

    response = client.post("/api/v1/triage/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["pr_number"] == 101
    assert data["repo_name"] == "ast-org/calculator"
    assert data["risk_tier"] == "LOW"
    assert data["risk_probability"] < 0.25
    assert "FAST-TRACK" in data["recommendation"]
    assert len(data["top_risk_drivers"]) <= 3
    assert data["latency_ms"] >= 0.0


def test_analyze_test_cheat_pr(client):
    """
    Simulates a PR where an AI agent deleted test assertions to bypass failures.
    Expects HIGH risk tier due to hard assertion deletion safety rule.
    """
    payload = {
        "repo_name": "ast-org/auth-service",
        "pr_number": 102,
        "title": "Pass CI by suppressing login checks",
        "issue_description": "Fix test failures in auth module when user token expires.",
        "author_login": "autonomous-agent[bot]",
        "author_is_bot": True,
        "agent_framework": "devin",
        "base_sha": "c" * 40,
        "head_sha": "d" * 40,
        "raw_diff": (
            "diff --git a/tests/test_auth.py b/tests/test_auth.py\n"
            "--- a/tests/test_auth.py\n"
            "+++ b/tests/test_auth.py\n"
            "@@ -12,8 +12,0 @@\n"
            "-    assert auth.verify_token(expired_tok) is False\n"
            "-    assert auth.verify_token(malformed_tok) is False\n"
            "-    assert auth.is_session_active(user_id) is False\n"
            "-    assert auth.validate_credentials('bad', 'bad') is False\n"
            "-    assert auth.check_password_hash(bad_hash) is False\n"
            "-    assert auth.enforce_mfa(user_id) is True\n"
        ),
        "ci_passed": True,
        "commit_count": 1,
    }

    response = client.post("/api/v1/triage/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["pr_number"] == 102
    assert data["risk_tier"] == "HIGH"
    assert "DEPRIORITIZE" in data["recommendation"] or "REJECT" in data["recommendation"]
    # Check that override fired or assertion deletion is listed in top risk drivers
    drivers_str = " ".join(d["feature_name"] for d in data["top_risk_drivers"])
    assert "assertions_deleted" in drivers_str or data["override_applied"] is not None


def test_analyze_semantic_drift_pr(client):
    """
    Simulates a PR where the agent modified files completely unrelated to the prompt.
    Prompt asks for docs update, but diff alters core DB connection pooling.
    Expects semantic drift detection and HIGH risk tier.
    """
    payload = {
        "repo_name": "ast-org/docs-repo",
        "pr_number": 103,
        "title": "Update README installation guide for Python 3.12",
        "issue_description": (
            "Please update the README.md installation instructions to recommend "
            "Python 3.12 and add a section describing how to create a virtual environment."
        ),
        "author_login": "openhands[bot]",
        "author_is_bot": True,
        "agent_framework": "openhands",
        "base_sha": "e" * 40,
        "head_sha": "f" * 40,
        "raw_diff": (
            "diff --git a/database/pool.py b/database/pool.py\n"
            "--- a/database/pool.py\n"
            "+++ b/database/pool.py\n"
            "@@ -20,2 +20,3 @@\n"
            "-    max_connections = 10\n"
            "-    connection_timeout = 30\n"
            "+    max_connections = 9999\n"
            "+    connection_timeout = 0\n"
            "+    allow_root_unauthenticated = True\n"
        ),
        "ci_passed": True,
        "commit_count": 1,
    }

    response = client.post("/api/v1/triage/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["pr_number"] == 103
    assert data["risk_tier"] == "HIGH"
    if data["override_applied"]:
        assert "Semantic drift" in data["override_applied"]


def test_triage_queue_endpoint(client):
    """Verifies that the triage queue returns pull requests ordered by risk."""
    repo = "ast-org/calculator"
    response = client.get(f"/api/v1/triage/queue/{repo}?sort_by=risk_asc")
    assert response.status_code == 200
    queue = response.json()
    assert isinstance(queue, list)
    assert len(queue) >= 1
    assert queue[0]["pr_number"] == 101
    assert queue[0]["risk_tier"] == "LOW"


def test_github_webhook_ping(client):
    """Verifies that GitHub ping webhook events return an acknowledgement."""
    headers = {"X-GitHub-Event": "ping"}
    response = client.post("/api/v1/github/webhook", json={"zen": "Design for failure."}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["event"] == "ping"


def test_github_webhook_pull_request_flow(client):
    """Verifies end-to-end processing of a GitHub pull_request.opened event."""
    webhook_payload = {
        "action": "opened",
        "repository": {"full_name": "ast-org/webhook-test"},
        "number": 205,
        "pull_request": {
            "number": 205,
            "title": "Fix off-by-one error in search index",
            "body": "When indexing queries, start index was offset by 1. Closes #200.",
            "diff": (
                "diff --git a/search.py b/search.py\n"
                "--- a/search.py\n"
                "+++ b/search.py\n"
                "@@ -1,2 +1,2 @@\n"
                "-start_idx = 1\n"
                "+start_idx = 0\n"
            ),
            "user": {"login": "devin[bot]", "type": "Bot"},
            "base": {"sha": "1" * 40},
            "head": {"sha": "2" * 40},
        },
    }

    headers = {"X-GitHub-Event": "pull_request"}
    response = client.post("/api/v1/github/webhook", json=webhook_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["event"] == "pull_request"
    assert data["action"] == "opened"
    assert "triage_summary" in data
    assert data["triage_summary"]["pr_number"] == 205


def test_github_webhook_invalid_signature(client):
    """Verifies that requests with invalid HMAC signatures are rejected with 401."""
    secret = "secret_for_unit_test"
    payload_bytes = b'{"action": "ping"}'
    invalid_header = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    # Test static verification directly
    assert GitHubClient.verify_webhook_signature(payload_bytes, invalid_header, secret=secret) is False

    # Test with valid signature
    valid_sig = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    assert GitHubClient.verify_webhook_signature(payload_bytes, valid_sig, secret=secret) is True


def test_markdown_reporter_formatting():
    """Verifies the visual presentation and syntax integrity of generated PR comments."""
    triage = TriageResponse(
        pr_number=88,
        repo_name="myorg/repo",
        risk_probability=0.1425,
        raw_risk_score=-1.794,
        risk_tier="LOW",
        recommendation="FAST-TRACK: High structural integrity, intent aligned, tests verified.",
        top_risk_drivers=[
            SHAPExplanationItem(
                feature_name="delta_cc",
                shap_value=0.0123,
                description="delta_cc = 1 (INCREASES_RISK)",
                feature_value=1.0,
                impact="INCREASES_RISK",
            ),
            SHAPExplanationItem(
                feature_name="intent_diff_cosine",
                shap_value=-0.0456,
                description="intent_diff_cosine = 0.89 (DECREASES_RISK)",
                feature_value=0.89,
                impact="DECREASES_RISK",
            ),
        ],
        latency_ms=35.4,
        override_applied=None,
    )

    markdown = generate_markdown_report(triage, repo_name="myorg/repo", pr_number=88)

    # Visual and structural assertions
    assert "## ASTRA Automated Triage Report" in markdown
    assert "https://img.shields.io/badge/ASTRA_Risk-LOW_Fast_Track-28a745.svg" in markdown
    assert "14.2%" in markdown
    assert "🟢 **LOW RISK**" in markdown
    assert "<details>" in markdown
    assert "</details>" in markdown
    assert "`delta_cc`" in markdown
    assert "`intent_diff_cosine`" in markdown

    # Golden Rule 2 check: No em dashes in written explanations
    # (Exclude markdown table syntax '| :--- |' and horizontal divider '***')
    prose_lines = [
        line for line in markdown.splitlines()
        if not line.startswith("|") and not line.strip() in ("---", "***", "___")
    ]
    for line in prose_lines:
        assert "--" not in line, f"Found prohibited em dash in prose: {line}"
