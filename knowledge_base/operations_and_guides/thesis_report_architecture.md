# Thesis Report Architecture and Dissertation Audit

> Master structural map and audit ledger connecting the academic dissertation in [thesis/](file:///e:/study/ASTRA/thesis) with the core engineering implementation in [ast-triage-core/](file:///e:/study/ASTRA/ast-triage-core).

---

## 1. Dissertation Overview

The academic dissertation report titled **"ASTRA: Automated Risk Stratification and Abstract Syntax Tree Triage for AI-Agent-Authored Pull Requests"** documents the research, mathematical formulation, static analysis implementation, machine learning calibration, and empirical verification of ASTRA for the Master of Computer Applications (MCA) degree at the University of Mumbai (BVIMIT, Navi Mumbai).

The report is compiled from modular LaTeX sources centered in [thesis/main.tex](file:///e:/study/ASTRA/thesis/main.tex).

---

## 2. Chapter Structure and Codebase Cross-Reference

| Chapter | Document Title | Target File | Core Codebase Mapping | Primary Deliverables and Visuals |
| :--- | :--- | :--- | :--- | :--- |
| **Frontmatter** | Cover, Certificate, Declaration, Acknowledgement, Abstract, Nomenclature | `cover.tex`<br>`cert.tex`<br>`declaration.tex`<br>`ack.tex`<br>`abst.tex`<br>`nomenclature.tex` | Repository root | Institutional details, keywords, nomenclature definitions (F01-F28, SBERT, CC, SHAP). |
| **Chapter 1** | Introduction | [chap1.tex](file:///e:/study/ASTRA/thesis/chap1.tex) | `ast-triage-core/` | Deceptive Green CI problem, domain background (ML4SE, Tree-sitter, SBERT, XGBoost), sub-350ms CPU latency goal. |
| **Chapter 2** | Existing Solutions and Analysis | [chap2.tex](file:///e:/study/ASTRA/thesis/chap2.tex) | SWE-bench, GumTree, SBERT | Literature review, Comparative Analysis Matrix (linters vs line diffs vs LLMs vs ASTRA), Research Questions RQ1-RQ4. |
| **Chapter 3** | System Analysis | [chap3.tex](file:///e:/study/ASTRA/thesis/chap3.tex) | `config/`, `static/` | Gantt chart, DFD Level 0, DFD Level 1, UML Use Case, System Architecture diagram, hardware/software/UI requirements. |
| **Chapter 4** | System Design | [chap4.tex](file:///e:/study/ASTRA/thesis/chap4.tex) | `database/models.py`<br>`src/feature_pipeline/` | ER diagram, SQLAlchemy 2.0 schema, Class/Component diagram, Sequence diagram (Mermaid), 28-D Feature Taxonomy, Input/Output design. |
| **Chapter 5** | Coding | [chap5.tex](file:///e:/study/ASTRA/thesis/chap5.tex) | `src/ast_engine/`<br>`src/semantic_engine/`<br>`src/ml_engine/`<br>`src/api/` | Nine core production routines: Tree-sitter cyclomatic walker, MiniLM embedder, SQLAlchemy sessionmaker, Platt calibration, AST hotspot locator, safety overrides, rich reporter, aggregate analytics. |
| **Chapter 6** | System Implementation | [chap6.tex](file:///e:/study/ASTRA/thesis/chap6.tex) | `scripts/`<br>`static/`<br>Render / GitHub | AST verification (m1), Semantic verification (m2), Training & Platt calibration (m3), API demo (m4), Live GitHub triage (PR #8 and PR #9), SWE-bench dataset mining (600 PRs), 4-way feature ablation study, Web simulator, and GitHub Actions CI gate. |
| **Chapter 7** | System Testing | [chap7.tex](file:///e:/study/ASTRA/thesis/chap7.tex) | `tests/` | Pytest 103-test verification, 5-fold cross-validation ablation metrics, 21 comprehensive test cases (TC01-TC21), and 77.7ms CPU latency benchmarks. |
| **Chapter 8** | Limitation and Future Enhancement | [chap8.tex](file:///e:/study/ASTRA/thesis/chap8.tex) | Future Work | Operational boundaries (static vs dynamic, sparse prompts, monorepo diffs) and post-dissertation frontiers (polyglot Tree-sitter, WebAssembly sandboxing, call graph blast radius). |
| **Chapter 9** | Conclusions | [chap9.tex](file:///e:/study/ASTRA/thesis/chap9.tex) | Repository root | Phase review, architectural achievements, final dissertation deliverables (103 tests, Brier 0.0004, live cloud hosting, automated gate), and final remarks. |
| **Appendix A** | Mathematical Formulations | [APPENDIX.tex](file:///e:/study/ASTRA/thesis/APPENDIX.tex) | Formulas | McCabe cyclomatic complexity ($\Delta CC$), nesting depth delta ($\Delta D$), AST disturbance index ($D_{AST}$), SBERT cosine ($S_{align}$), Jaccard drift ($J_{drift}$), Platt scaling sigmoid, Brier score. |
| **Appendix B** | Automated CI/CD Risk Gate | [APPENDIX.tex](file:///e:/study/ASTRA/thesis/APPENDIX.tex) | `.github/workflows/astra-gate.yml` | Full turnkey GitHub Actions YAML workflow specification. |
| **Appendix C** | REST API Specifications | [APPENDIX.tex](file:///e:/study/ASTRA/thesis/APPENDIX.tex) | `src/api/main.py` | OpenAPI schemas and sample JSON payloads for triage, webhook, and analytics endpoints. |

---

## 3. Key Empirical Benchmarks Documented in Thesis

* **Unit Test Pass Rate:** 103/103 passing tests across AST, semantic, feature, and integration suites.
* **SWE-bench Dataset Size:** 600 standardized real-world pull requests mined across Django, Scikit-learn, Pytest, SymPy, and Flask.
* **Feature Modality Ablation (5-Fold CV, `n_estimators=100`):**
  * AST-Only (F01-F12): ROC-AUC 1.0000, PR-AUC 1.0000, F1 0.9981, Brier 0.0022
  * Semantic-Only (F13-F18): ROC-AUC 1.0000, PR-AUC 1.0000, F1 0.9981, Brier 0.0021
  * Process-Only (F19-F28): ROC-AUC 1.0000, PR-AUC 1.0000, F1 0.9981, Brier 0.0019
  * Full 28-D ASTRA (5-Fold CV): ROC-AUC 1.0000, PR-AUC 1.0000, F1 0.9981, Brier 0.0022 (Production Checkpoint `n_estimators=200`: F1 1.0000, Brier 0.0004)
* **Local CPU Triage Latency:** 77.7 milliseconds mean execution time (budget: 350.0 ms).
* **Cloud Triage Roundtrip:** 1.8 to 2.2 seconds on Render containerized web service.
