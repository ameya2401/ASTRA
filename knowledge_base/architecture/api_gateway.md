# FastAPI Ingestion Gateway & REST Architecture

> Architectural specifications and design contracts for the ASTRA FastAPI triage gateway.

---

## 1. Overview

The API gateway layer connects external pull request events to internal static and statistical analysis engines. Operating under a strict 300ms SLA, the gateway receives PR metadata and unified diffs, runs AST extraction and semantic drift evaluation, constructs the 28-D feature vector, queries the calibrated XGBoost runtime, and stores persistent state in SQLAlchemy 2.0 ORM tables.

- Module: `src/api`
- Main Application: `src/api/main.py`
- Endpoints: `src/api/routes.py`
- Schema Contracts: `src/api/schemas.py`
- Runtime Server: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`

---

## 2. Endpoint Contracts

| Method | Route | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root service metadata | None | Service status and endpoint URLs |
| `GET` | `/api/v1/health` | Service health and model verification | None | `HealthResponse` |
| `POST` | `/api/v1/triage/analyze` | Core PR risk evaluation endpoint | `PRWebhookPayload` | `TriageResponse` |
| `GET` | `/api/v1/triage/queue/{repo_name}` | Maintainer review prioritization queue | None | `List[TriageQueueItem]` |
| `POST` | `/api/v1/github/webhook` | GitHub native webhook event receiver | GitHub Webhook JSON | `GitHubWebhookAck` |

---

## 3. Request and Response Schemas

### 3.1 Ingestion Payload (`PRWebhookPayload`)

```python
class PRWebhookPayload(BaseModel):
    repo_name: str
    pr_number: int
    title: str
    issue_description: str
    author_login: str = ""
    author_is_bot: bool = False
    agent_framework: str = "unknown"
    base_sha: str = ""
    head_sha: str = ""
    raw_diff: str = ""
    ci_passed: Optional[bool] = True
    files_touched: Optional[List[str]] = None
    file_churns: Optional[List[int]] = None
    commit_count: Optional[int] = 1
```

### 3.2 Triage Assessment (`TriageResponse`)

```python
class TriageResponse(BaseModel):
    pr_number: int
    repo_name: Optional[str] = None
    risk_probability: float
    raw_risk_score: Optional[float] = None
    risk_tier: str
    recommendation: str
    top_risk_drivers: List[SHAPExplanationItem]
    latency_ms: float
    override_applied: Optional[str] = None
```

---

## 4. Application Lifecycle & Performance Guarantees

### 4.1 Lifespan Pre-warming

Neural embeddings and machine learning models incur a one-time memory loading latency. To prevent cold-start penalties on incoming webhooks, `src/api/main.py` uses an async lifespan context manager:

1. **Database Schema Setup:** Executes `await init_db()` to verify or create SQLite/PostgreSQL tables.
2. **Model Singleton Pre-warming:** Instantiates `RiskPredictor` and `SemanticDriftAnalyzer` prior to listening for requests, loading XGBoost checkpoints, SHAP explainers, and MiniLM transformers into memory.

### 4.2 SLA Performance Breakdown

Under ordinary CPU execution, total processing latency per PR diff adheres to the following budget:

- AST Parsing and Metric Calculation: 10 to 30 ms
- Sentence Embeddings and Cosine Drift: 25 to 50 ms
- Vector Assembly and Normalization: < 2 ms
- Calibrated Inference and TreeSHAP: 10 to 20 ms
- Database Persistence (Async): 5 to 15 ms
- **Total Round-Trip Latency:** 50 to 120 ms (well within the 300 ms SLA threshold)
