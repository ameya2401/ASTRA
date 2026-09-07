# Database Schema & Models

> Defines the relational database schema implemented in [database/models.py](file:///e:/study/ASTRA/ast-triage-core/database/models.py) using SQLAlchemy 2.0 mapped columns.

---

## 1. Entity-Relationship Diagram

```
┌──────────────────┐         ┌────────────────────────┐         ┌───────────────────────┐
│   repositories   │ 1 ─── M │     pull_requests      │ 1 ─── 1 │    feature_records    │
│──────────────────│         │────────────────────────│         │───────────────────────│
│ id (PK)          │         │ id (PK)                │         │ id (PK)               │
│ repo_name (UQ)   │         │ repo_id (FK)           │         │ pr_id (FK, UQ)        │
│ default_branch   │         │ pr_number              │         │ f01_ast_nodes_added   │
│ created_at       │         │ title                  │         │ ...                   │
└──────────────────┘         │ issue_description      │         │ f28_is_known_agent_bot│
                             │ author_login           │         │ computed_at           │
                             │ author_is_bot          │         └───────────────────────┘
                             │ agent_framework        │
                             │ base_sha               │         ┌───────────────────────┐
                             │ head_sha               │ 1 ─── 1 │  triage_predictions   │
                             │ raw_diff               │         │───────────────────────│
                             │ ci_passed              │         │ id (PK)               │
                             │ ground_truth_status    │         │ pr_id (FK, UQ)        │
                             │ ground_truth_label     │         │ raw_risk_score        │
                             │ created_at             │         │ calibrated_risk_score │
                             └────────────────────────┘         │ risk_tier             │
                                                                │ shap_feature_1..3     │
                                                                │ shap_value_1..3       │
                                                                │ inference_latency_ms  │
                                                                │ created_at            │
                                                                └───────────────────────┘
```

---

## 2. Table Definitions

### 2.1 repositories
Represents a source code repository monitored by ASTRA.

- `id` (`Integer`, PK, Autoincrement)
- `repo_name` (`String(255)`, Unique, Not Null): Fully qualified name, such as `django/django`.
- `default_branch` (`String(64)`, Default: `"main"`): Primary branch name.
- `created_at` (`DateTime(timezone=True)`): Registration timestamp.

### 2.2 pull_requests
Stores metadata, issue description, and raw diff for every evaluated PR.

- `id` (`Integer`, PK, Autoincrement)
- `repo_id` (`Integer`, FK -> `repositories.id`, On Delete CASCADE)
- `pr_number` (`Integer`, Not Null): Repository PR number.
- `title` (`Text`, Not Null): PR title text.
- `issue_description` (`Text`, Not Null): Issue body or user prompt guiding the change.
- `author_login` (`String(255)`, Not Null): GitHub username or bot login.
- `author_is_bot` (`Boolean`, Default: `False`): Bot account indicator flag.
- `agent_framework` (`String(64)`, Default: `"unknown"`): Agent label (`"devin"`, `"claude-code"`, etc.).
- `base_sha` (`String(40)`, Not Null): Target commit SHA.
- `head_sha` (`String(40)`, Not Null): Source PR commit SHA.
- `raw_diff` (`Text`, Not Null): Unified diff text.
- `ci_passed` (`Boolean`, Nullable): Continuous integration result (None if pending).
- `ground_truth_status` (`String(32)`, Not Null): Outcome status (`"MERGED"`, `"REJECTED_CLOSED"`, `"REVERTED"`).
- `ground_truth_label` (`Integer`, Not Null): Binary label where 0 = Accepted/Clean, 1 = Rejected/Defective.
- `created_at` (`DateTime(timezone=True)`): Record creation timestamp.

Constraints:
- Unique constraint on `(repo_id, pr_number)`.
- Index on `(repo_id, pr_number)`.

### 2.3 feature_records
Stores the extracted 28-dimensional feature vector. Each column is named with `f{NN}_` prefix to guarantee unambiguous index ordering.

- `id` (`Integer`, PK, Autoincrement)
- `pr_id` (`Integer`, FK -> `pull_requests.id`, Unique, Not Null)
- `f01_ast_nodes_added` (`Integer`) to `f12_control_flow_churn_ratio` (`Float`): AST structural metrics.
- `f13_intent_diff_cosine_sim` (`Float`) to `f18_issue_token_length` (`Integer`): Semantic NLP metrics.
- `f19_test_files_modified` (`Integer`) to `f23_mock_patch_count_delta` (`Integer`): Test churn metrics.
- `f24_commit_count` (`Integer`) to `f28_is_known_agent_bot` (`Integer`): Process and provenance metrics.
- `computed_at` (`DateTime(timezone=True)`): Calculation timestamp.

Method:
- `to_vector()` returns an ordered list of 28 floats (`list[float]`) ready for model inference.

### 2.4 triage_predictions
Stores risk scores and local SHAP explanations produced by the ML engine.

- `id` (`Integer`, PK, Autoincrement)
- `pr_id` (`Integer`, FK -> `pull_requests.id`, Unique, Not Null)
- `raw_risk_score` (`Float`, Not Null): Raw uncalibrated model output probability.
- `calibrated_risk_score` (`Float`, Not Null): Platt-calibrated defect probability in `[0.0, 1.0]`.
- `risk_tier` (`String(16)`, Not Null): Risk category (`"GREEN"`, `"YELLOW"`, or `"RED"`).
- `shap_feature_1`, `shap_feature_2`, `shap_feature_3` (`String(64)`): Top 3 risk contributors.
- `shap_value_1`, `shap_value_2`, `shap_value_3` (`Float`): Associated SHAP attribution values.
- `inference_latency_ms` (`Float`): Execution time of the inference pass.
- `created_at` (`DateTime(timezone=True)`): Timestamp of prediction.
