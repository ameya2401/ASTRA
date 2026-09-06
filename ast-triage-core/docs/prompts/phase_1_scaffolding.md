# Phase 1: Project Scaffolding & Environment Setup

**Goal:** Establish the foundational boilerplate for AST-Triage, including dependencies, configuration, and database models.

---

## Instructions for the AI Agent

Act as a Principal Staff Software Architect. We are building AST-Triage, an automated risk-scoring system that intercepts AI-agent-generated GitHub Pull Requests using Tree-sitter AST differencing, sentence-transformers semantic intent alignment, and a Platt-calibrated XGBoost classifier.

**Generate the complete project boilerplate structure following standard Python packaging best practices in `e:\study\ASTRA\ast-triage-core`:**

1. Create a `requirements.txt` file with dependencies for:
   - fastapi
   - uvicorn
   - pydantic
   - pydantic-settings
   - tree-sitter
   - tree-sitter-python
   - xgboost
   - scikit-learn
   - sentence-transformers
   - shap
   - sqlalchemy
   - aiosqlite
   - pyarrow

2. Create `config/settings.py` using Pydantic BaseSettings loading from a `.env` file. Include placeholders for:
   - `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`
   - `DATABASE_URL` (default to sqlite+aiosqlite:///./data/ast_triage.db)
   - `MODEL_CHECKPOINT_DIR`, `EMBEDDING_MODEL_NAME`
   - Risk thresholds: `LOW_RISK_THRESHOLD`, `HIGH_RISK_THRESHOLD`

3. Create `database/models.py` using SQLAlchemy 2.0 async mapped classes for:
   - `PullRequest` (repo_name, pr_number, title, issue_description, author_login, etc.)
   - `FeatureRecord` (capturing all 28 extracted features)
   - `TriagePrediction` (capturing risk score, tier, SHAP values, latency)
   - *Reference the exact schema defined in the technical reference.*

4. Ensure strict type hints, docstrings, and clean separation of concerns. Do not omit any boilerplate.
