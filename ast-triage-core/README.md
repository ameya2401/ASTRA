# AST-Triage Core

**Automated risk-scoring system for AI-agent-generated GitHub Pull Requests.**

AST-Triage intercepts PRs created by AI coding agents (Devin, Claude Code, Copilot, OpenHands, etc.) and produces a calibrated risk score using:

- **Tree-sitter AST Differencing** — Structural code disruption analysis
- **Sentence-Transformers Semantic Alignment** — Intent-to-diff drift detection
- **Platt-Calibrated XGBoost Classifier** — 28-feature risk prediction with SHAP explanations

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your GitHub token and settings

# 3. Initialize the database
python -c "import asyncio; from database.connection import init_db; asyncio.run(init_db())"

# 4. Run the API server (Phase 5)
uvicorn src.api.main:app --reload --port 8000
```

## Project Structure

```
ast-triage-core/
├── config/           # Pydantic BaseSettings configuration
├── database/         # SQLAlchemy 2.0 async ORM models
├── src/
│   ├── ast_engine/       # Tree-sitter parsing & cyclomatic analysis
│   ├── semantic_engine/  # Intent alignment & drift detection
│   ├── feature_pipeline/ # 28-D feature vector assembly
│   ├── ml_engine/        # XGBoost training, inference, SHAP
│   ├── api/              # FastAPI endpoints
│   └── integrations/     # GitHub API client & PR reporter
├── data/             # Raw/processed datasets & fixtures
├── models/           # Trained model checkpoints
├── scripts/          # Data mining & training scripts
└── tests/            # Unit & integration tests
```

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + aiosqlite
- Tree-sitter + tree-sitter-python
- XGBoost + scikit-learn
- sentence-transformers (all-MiniLM-L6-v2)
- SHAP (TreeExplainer)

## License

MIT
