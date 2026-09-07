# Verification Gates & Quality Ledger

> The mandatory verification commands required before marking any milestone or phase complete.

ASTRA enforces strict verification gates. No task, refactor, or phase is considered complete without passing its corresponding gate.

---

## 1. Master Verification Ledger

| Phase / Component | Verification Command | Target Result | What It Proves |
|---|---|---|---|
| **Phase 1: DB Init** | `python -c "import asyncio; from database.connection import init_db; asyncio.run(init_db())"` | Process returns 0 with no exceptions | Database engine creates all 4 tables cleanly |
| **Phase 2: AST Engine** | `python -m pytest tests/test_ast_engine.py` | 38/38 unit tests pass | Tree-sitter parsing, McCabe complexity, and F01-F12 metrics work correctly |
| **Phase 2: AST CLI** | `python scripts/run_ast_diff.py` | Structural delta summary prints successfully | Standalone AST differ CLI computes metrics end-to-end |
| **Phase 3: Semantic Engine** | `python -m pytest tests/test_semantic_engine.py` | 34/34 unit tests pass | MiniLM embeddings, cosine similarity, entity Jaccard, and F13-F18 work |
| **Phase 3: Semantic CLI** | `python scripts/run_semantic_drift.py` | Correctly flags drifted PR scenario (< 0.45 threshold) | Standalone drift CLI distinguishes aligned from drifted PRs |
| **Phase 4: ML & Features** | `python -m pytest tests/test_feature_pipeline.py` | Pipeline & normalizer tests pass | 28-D vector builder, normalization, and XGBoost inference pass |
| **Phase 5: End-to-End** | `python -m pytest tests/test_end_to_end.py` | Complete PR webhook-to-comment test passes | Full ingestion, extraction, inference, and SHAP response cycle passes |

---

## 2. Running Targeted Checks During Development

### Running with Verbose Output
```powershell
python -m pytest tests/test_ast_engine.py -v
```

### Running a Specific Test Method
```powershell
python -m pytest tests/test_semantic_engine.py -k "test_semantic_drift_flag" -v
```

### Checking Test Execution with Print Outputs
```powershell
python -m pytest tests/test_ast_engine.py -s
```

---

## 3. Debugging Failed Gates

1. **Tree-Sitter Syntax Errors**: If an AST test fails due to parser errors, check if the test case triggers `has_error`. Tree-sitter should handle errors gracefully rather than throwing unhandled exceptions.
2. **Transformer Model Download Failures**: If `test_semantic_engine.py` times out, verify internet access or cached HuggingFace models under `~/.cache/huggingface/hub/`.
3. **Database Concurrency Lock**: If SQLite reports `database is locked`, confirm that `check_same_thread=False` is configured in `database/connection.py`.
