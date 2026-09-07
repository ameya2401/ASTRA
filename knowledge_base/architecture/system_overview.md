# System Overview

> Module: `ast-triage-core`  
> Architecture: Asynchronous Microservice Pipeline  
> Runtime: Python 3.11+

ASTRA intercepts pull requests authored by autonomous AI software engineering agents (such as Devin, Claude Code, GitHub Copilot, and OpenHands) before human code reviewers evaluate them. It operates as an automated triage service that extracts syntax tree metrics, NLP intent-to-diff alignment metrics, and provenance signals to predict PR risk.

---

## 1. Technology Stack

| Layer | Technology | Minimum Version | Purpose |
|---|---|---|---|
| **Web Framework** | FastAPI + Uvicorn | 0.111.0 | Asynchronous REST API and GitHub webhook receiver |
| **Data Validation** | Pydantic + pydantic-settings | 2.7.0 | Strict request/response DTOs and environment settings |
| **AST Analysis** | tree-sitter + tree-sitter-python | 0.22.0 | High-speed C-binding parser for Python AST extraction |
| **NLP Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | 3.0.0 | Generates 384-D dense embeddings for semantic drift |
| **Classifier** | XGBoost | 2.0.0 | Gradient-boosted decision trees for binary defect classification |
| **Calibration** | scikit-learn (`CalibratedClassifierCV`) | 1.5.0 | Platt scaling for well-calibrated risk probabilities |
| **Explainability** | SHAP (`TreeExplainer`) | 0.45.0 | Local Shapley attribution values for triage commentary |
| **Database** | SQLAlchemy 2.0 (async) + aiosqlite | 2.0.30 | Async ORM supporting SQLite (dev) and PostgreSQL (prod) |
| **Data Processing** | NumPy, Pandas, PyArrow | Latest | 28-D vector assembly, normalization, and Parquet caching |

---

## 2. Core Package Structure

All core application code resides in [ast-triage-core](file:///e:/study/ASTRA/ast-triage-core/):

```text
ast-triage-core/
├── config/              # Pydantic Settings loaded from .env
├── database/            # SQLAlchemy 2.0 async engine and ORM tables
├── src/
│   ├── ast_engine/      # Phase 2: Tree-sitter AST & Cyclomatic Complexity (F01-F12)
│   ├── semantic_engine/ # Phase 3: Sentence-Transformers Intent Alignment (F13-F18)
│   ├── feature_pipeline/# Phase 4: 28-D vector builder & normalizer
│   ├── ml_engine/       # Phase 4: XGBoost classifier, Platt scaling, SHAP
│   ├── api/             # Phase 5: FastAPI REST endpoints & webhook handler
│   └── integrations/    # Phase 5: GitHub API client & PR markdown reporter
├── scripts/             # Standalone CLI tools and mining runners
└── tests/               # Pytest test suites matching verification gates
```

---

## 3. Component Boundaries

ASTRA enforces clean isolation across functional layers:

1. **Static Analysis Isolation**: The AST engine ([src/ast_engine/](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/)) operates purely on source text strings. It has no dependency on the database or network.
2. **Model Lifecycle Isolation**: Neural models (SentenceTransformer) and gradient-boosted models (XGBoost) are managed as thread-safe module singletons ([src/semantic_engine/embedder.py:L24-L60](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/embedder.py#L24-L60)). They are loaded once at startup, never inside per-request execution loops.
3. **Database Non-Blocking I/O**: All database transactions use asynchronous context managers (`async with get_async_session() as session:`). Synchronous blocking calls are forbidden in API routes.
4. **Resilience to Malformed Code**: AI-generated code frequently contains incomplete syntax. The AST engine relies on Tree-sitter error-tolerant parsing (`tree.root_node.has_error`), preventing unhandled parser exceptions from halting the service.
