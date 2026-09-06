# AST-Triage: Technical Architecture

> **Last Updated:** Phase 1 — Project Scaffolding & Environment Setup  
> **Date:** September 6, 2026

---

## 1. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Web Framework** | FastAPI + Uvicorn | ≥0.111.0 | Async REST API & webhook ingestion |
| **Data Validation** | Pydantic + pydantic-settings | ≥2.7.0 | Request/response schemas, config management |
| **AST Parsing** | tree-sitter + tree-sitter-python | ≥0.22.0 | C-binding syntax tree parser for structural analysis |
| **NLP Embeddings** | sentence-transformers (MiniLM) | ≥3.0.0 | Dense text embeddings for semantic alignment |
| **ML Classifier** | XGBoost | ≥2.0.0 | Gradient-boosted tree classifier for risk prediction |
| **Calibration** | scikit-learn CalibratedClassifierCV | ≥1.5.0 | Platt scaling for probability calibration |
| **Explainability** | SHAP (TreeExplainer) | ≥0.45.0 | Local feature attribution for interpretability |
| **Database** | SQLAlchemy 2.0 (async) + aiosqlite | ≥2.0.30 | Async ORM with SQLite (dev) / PostgreSQL (prod) |
| **Data Processing** | NumPy, Pandas, PyArrow | various | Feature vector assembly, Parquet I/O |
| **Runtime** | Python 3.11+ | 3.11+ | Type hints, async/await, modern syntax |

---

## 2. Directory Layout

```
ast-triage-core/
├── .env                          # Local environment variables (not committed)
├── .env.example                  # Template environment configuration
├── README.md                     # Project overview & quick start
├── requirements.txt              # Python dependencies
├── setup.py                      # Package configuration
├── context.md                    # Project context (this gets updated every phase)
├── architecture.md               # Technical architecture (this file)
│
├── config/
│   ├── __init__.py               # Re-exports Settings, get_settings
│   └── settings.py               # Pydantic BaseSettings — loads from .env
│
├── database/
│   ├── __init__.py               # Re-exports models & connection utils
│   ├── connection.py             # AsyncEngine factory, session generator, init_db()
│   └── models.py                 # ORM: Repository, PullRequest, FeatureRecord, TriagePrediction
│
├── src/
│   ├── __init__.py
│   ├── ast_engine/               # [Phase 2] Tree-sitter AST analysis
│   │   ├── __init__.py
│   │   ├── parser.py             # Tree-sitter Python grammar wrapper
│   │   ├── cyclomatic.py         # McCabe complexity calculator
│   │   └── differ.py             # Structural AST comparison engine
│   ├── semantic_engine/          # [Phase 3] NLP intent alignment
│   │   ├── __init__.py
│   │   ├── embedder.py           # Sentence-transformers singleton
│   │   └── drift_analyzer.py     # Cosine similarity & entity drift
│   ├── feature_pipeline/         # [Phase 4] Feature assembly
│   │   ├── __init__.py
│   │   ├── vector_builder.py     # 28-D feature vector constructor
│   │   └── normalizer.py         # Scaling & imputation
│   ├── ml_engine/                # [Phase 4] ML training & inference
│   │   ├── __init__.py
│   │   ├── trainer.py            # XGBoost + Platt calibration training
│   │   ├── predictor.py          # Fast inference runtime
│   │   └── explainer.py          # SHAP TreeExplainer
│   ├── api/                      # [Phase 5] REST API layer
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app entrypoint
│   │   ├── routes.py             # Endpoint definitions
│   │   └── schemas.py            # Pydantic DTOs
│   └── integrations/             # [Phase 5] External services
│       ├── __init__.py
│       ├── github_client.py      # GitHub API queries
│       └── reporter.py           # PR comment generator
│
├── data/
│   ├── raw/                      # Mined JSONL dumps
│   ├── processed/                # Normalized feature matrices (.parquet)
│   └── fixtures/                 # Mock diffs & issues for testing
│
├── models/                       # Trained model checkpoints (.joblib)
│
├── scripts/
│   ├── mine_swebench.py          # SWE-bench dataset mining
│   ├── mine_github_repos.py      # GitHub PR scraping
│   ├── train_model.py            # Standalone training script
│   └── generate_ablation_table.py# Ablation study generation
│
├── tests/
│   ├── __init__.py
│   ├── test_ast_engine.py        # [Phase 2]
│   ├── test_semantic_engine.py   # [Phase 3]
│   ├── test_feature_pipeline.py  # [Phase 4]
│   └── test_end_to_end.py        # [Phase 5]
│
└── docs/
    ├── prerequisites/
    │   ├── AST_Triage_Technical_Reference.md
    │   ├── AST_Triage_Comprehensive_Research_Guide.md
    │   ├── aiflow.md
    │   └── questions.md
    └── prompts/
        ├── phase_1_scaffolding.md
        ├── phase_2_ast_engine.md
        ├── phase_3_semantic_engine.md
        ├── phase_4_ml_engine.md
        └── phase_5_api_webhook.md
```

---

## 3. Database Schema

### 3.1 Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ repositories │ 1───M │  pull_requests   │ 1───1 │ feature_records  │
│──────────────│       │──────────────────│       │──────────────────│
│ id (PK)      │       │ id (PK)          │       │ id (PK)          │
│ repo_name    │       │ repo_id (FK)     │       │ pr_id (FK, UQ)   │
│ default_br.  │       │ pr_number        │       │ f01..f28         │
│ created_at   │       │ title            │       │ computed_at      │
└──────────────┘       │ issue_desc.      │       └──────────────────┘
                       │ author_login     │
                       │ author_is_bot    │       ┌──────────────────────┐
                       │ agent_framework  │ 1───1 │ triage_predictions   │
                       │ base_sha         │       │──────────────────────│
                       │ head_sha         │       │ id (PK)              │
                       │ raw_diff         │       │ pr_id (FK, UQ)       │
                       │ ci_passed        │       │ raw_risk_score       │
                       │ gt_status        │       │ calibrated_risk_score│
                       │ gt_label (0/1)   │       │ risk_tier            │
                       │ created_at       │       │ shap_feature_1..3    │
                       └──────────────────┘       │ shap_value_1..3      │
                                                  │ inference_latency_ms │
                                                  │ created_at           │
                                                  └──────────────────────┘
```

### 3.2 Feature Record Schema (28 Features)

| Feature | Column | Type | Group |
|---------|--------|------|-------|
| F01 | `f01_ast_nodes_added` | INT | AST Structural |
| F02 | `f02_ast_nodes_deleted` | INT | AST Structural |
| F03 | `f03_ast_nodes_mutated` | INT | AST Structural |
| F04 | `f04_cyclomatic_delta` | INT | AST Structural |
| F05 | `f05_max_nesting_depth_delta` | INT | AST Structural |
| F06 | `f06_func_signatures_modified` | INT | AST Structural |
| F07 | `f07_classes_modified` | INT | AST Structural |
| F08 | `f08_return_types_altered` | INT | AST Structural |
| F09 | `f09_call_graph_fan_out_delta` | INT | AST Structural |
| F10 | `f10_ast_disturbance_index` | FLOAT | AST Structural |
| F11 | `f11_try_catch_blocks_added` | INT | AST Structural |
| F12 | `f12_control_flow_churn_ratio` | FLOAT | AST Structural |
| F13 | `f13_intent_diff_cosine_sim` | FLOAT | Semantic NLP |
| F14 | `f14_issue_title_diff_sim` | FLOAT | Semantic NLP |
| F15 | `f15_entity_drift_jaccard` | FLOAT | Semantic NLP |
| F16 | `f16_docstring_to_code_ratio` | FLOAT | Semantic NLP |
| F17 | `f17_semantic_drift_flag` | INT | Semantic NLP |
| F18 | `f18_issue_token_length` | INT | Semantic NLP |
| F19 | `f19_test_files_modified` | INT | Test Churn |
| F20 | `f20_test_ast_nodes_added` | INT | Test Churn |
| F21 | `f21_test_assertions_deleted` | INT | Test Churn |
| F22 | `f22_test_to_logic_ratio` | FLOAT | Test Churn |
| F23 | `f23_mock_patch_count_delta` | INT | Test Churn |
| F24 | `f24_commit_count` | INT | Process |
| F25 | `f25_files_touched_count` | INT | Process |
| F26 | `f26_file_dispersion_entropy` | FLOAT | Process |
| F27 | `f27_ci_pass_flag` | INT | Process |
| F28 | `f28_is_known_agent_bot` | INT | Process |

---

## 4. Configuration Architecture

```
.env (file)  →  Pydantic BaseSettings  →  lru_cache singleton  →  app modules
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_TOKEN` | `""` | GitHub API authentication |
| `GITHUB_WEBHOOK_SECRET` | `""` | Webhook payload verification |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/ast_triage.db` | Database connection string |
| `MODEL_CHECKPOINT_DIR` | `./models` | Trained model artifacts path |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence-transformers model name |
| `LOW_RISK_THRESHOLD` | `0.25` | Below = LOW risk tier |
| `HIGH_RISK_THRESHOLD` | `0.65` | Above = HIGH risk tier |

---

## 5. Data Flow Architecture

```
                     ┌─────────────┐
                     │  GitHub PR  │
                     │   Webhook   │
                     └──────┬──────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  FastAPI Gate  │
                   │  /api/v1/...   │
                   └────────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌───────────┐ ┌──────────┐ ┌──────────┐
        │ AST Engine│ │ Semantic │ │ Process  │
        │ (F01-F12) │ │  Engine  │ │  Metrics │
        │ tree-sitter│ │ (F13-F18)│ │ (F19-F28)│
        └─────┬─────┘ └────┬─────┘ └────┬─────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Feature Vector │
                   │  Builder (28-D)│
                   └────────┬───────┘
                            │
                            ▼
                   ┌────────────────┐
                   │   XGBoost +    │
                   │ Platt Calib.   │
                   └────────┬───────┘
                            │
                     ┌──────┴──────┐
                     │  Risk Score │
                     │ + SHAP Top 3│
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              │                           │
              ▼                           ▼
        ┌───────────┐            ┌────────────┐
        │  SQLite   │            │ GitHub PR  │
        │  Storage  │            │  Comment   │
        └───────────┘            └────────────┘
```

---

## 6. Async Database Architecture

```python
# Engine creation (cached singleton)
AsyncEngine ← create_async_engine(DATABASE_URL)

# Session lifecycle (FastAPI dependency injection)
async with session_factory() as session:
    yield session       # Used in route handlers
    await session.commit()   # Auto-commit on success
    # Auto-rollback on exception
```

**Key design choices:**
- `expire_on_commit=False` — Prevents lazy-loading issues in async context
- `check_same_thread=False` — Required for SQLite with async drivers
- `lru_cache` on engine — Single engine instance per process
- Generator-based session — Compatible with `Depends()` injection

---

## 7. Phase Implementation Roadmap

| Phase | Module | Status | Key Deliverables |
|-------|--------|--------|------------------|
| **1** | Scaffolding | ✅ DONE | requirements.txt, settings, DB models, directory structure |
| **2** | AST Engine | ⬜ TODO | tree-sitter parser, cyclomatic calculator, structural differ |
| **3** | Semantic Engine | ⬜ TODO | MiniLM embedder, cosine drift, entity Jaccard |
| **4** | ML Engine | ⬜ TODO | XGBoost trainer, Platt calibrator, SHAP explainer, vector builder |
| **5** | API & Integration | ⬜ TODO | FastAPI endpoints, webhook handler, GitHub reporter |
