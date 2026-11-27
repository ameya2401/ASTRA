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
| **Frontmatter** | Cover (14pt title, Roll/Seat No., Month), Certificate, Declaration, Acknowledgement, Abstract (200-300 words), Nomenclature | `cover.tex`<br>`cert.tex`<br>`declaration.tex`<br>`ack.tex`<br>`abst.tex`<br>`nomenclature.tex` | Repository root | Institutional details, keywords, nomenclature definitions (F01-F28, SBERT, CC, SHAP). |
| **Chapter 1** | Introduction (1.1-1.7) | [chap1.tex](file:///e:/study/ASTRA/thesis/chap1.tex) | `ast-triage-core/` | Background, problem statement, objectives, scope, significance, RQ1-RQ4, report organization. |
| **Chapter 2** | Literature Review (2.1-2.4) | [chap2.tex](file:///e:/study/ASTRA/thesis/chap2.tex) | SWE-bench, GumTree, SBERT | Domain overview, related work (Ehsani et al., Qi et al., Tree-sitter), Comparative Matrix, Gap Analysis. |
| **Chapter 3** | Methodology (3.1-3.7) | [chap3.tex](file:///e:/study/ASTRA/thesis/chap3.tex) | `database/models.py`<br>`src/feature_pipeline/` | Gantt, DFDs, UML, ER diagram, Component/Sequence diagrams, Data sources, Tools, 600-row 28-D dataset, XGBoost + Platt + overrides, Architecture/Workflow diagrams, Metrics. |
| **Chapter 4** | Implementation (4.1-4.3) | [chap4.tex](file:///e:/study/ASTRA/thesis/chap4.tex) | `src/`<br>`static/`<br>`.github/workflows/` | Diff pre-processing, testbed/Render/Vercel environment, Tree-sitter cyclomatic walker, MiniLM drift, Platt inference, CI gate. |
| **Chapter 5** | Results and Discussions (5.1-5.4) | [chap5.tex](file:///e:/study/ASTRA/thesis/chap5.tex) | `scripts/`<br>`tests/` | CLI runs (m1-m4), Live GitHub PR #9 and PR #8, 4-way ablation table, 77.7 ms CPU latency, 103/103 Pytest + TC01-TC21, critical discussion. |
| **Chapter 6** | Conclusion and Recommendations (6.1-6.4) | [chap6.tex](file:///e:/study/ASTRA/thesis/chap6.tex) | Repository root | Summary of work done, key findings, limitations, future scope (polyglot Tree-sitter, sandboxing, call graphs, closed-loop feedback). |
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
