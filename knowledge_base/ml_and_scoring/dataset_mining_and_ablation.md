# Dataset Mining, SWE-bench Integration, and Feature Ablation

## 1. Overview
For Review 3 and production readiness, ASTRA expands beyond synthetic sample initializations to benchmark against real-world software engineering tasks and empirical agent failure archetypes. The data collection and ablation pipeline measures the marginal performance lift provided by each feature modality.

---

## 2. Dataset Harvester Architecture (`scripts/mine_agent_prs.py`)

The harvesting runner processes real pull request diffs and issue prompts into standardized 28-dimensional feature vectors:

```
SWE-bench Lite & Verified / GitHub Agent PRs
                      │
                      ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 1. DiffParser (Tree-sitter C-bindings): F01-F12         │
 │ 2. SentenceEmbedder (all-MiniLM-L6-v2): F13-F18         │
 │ 3. Test Churn & Assertion Analyzer: F19-F23             │
 │ 4. Process Provenance & Bot Attribution: F24-F28        │
 └─────────────────────────────────────────────────────────┘
                      │
                      ▼
data/processed/agent_prs_dataset.csv (600 rows, 28 features)
```

### Curated Ground-Truth Tasks:
1. **Gold Benchmark Solutions (Label = 0):**
   - `django__django-11099`: Username regex validation anchor fix.
   - `scikit-learn__scikit-learn-10297`: RidgeClassifierCV hyperparameter pass-through.
   - `pytest-dev__pytest-5227`: Logging format specifier defaults.
   - `sympy__sympy-13647`: Matrix column insertion boundary handling.
   - `pallets__flask-4045`: Blueprint dot separator name validation.
2. **AI Agent Defect Archetypes (Label = 1):**
   - **Assertion Suppression Anomaly:** Deleting test assertions to artificially make failing CI suites turn green (e.g. OpenHands async session timeout patch).
   - **Cyclomatic Complexity Escalation:** Introducing 5-deep nested condition blocks (+14 $\Delta \text{CC}$) without adding regression tests.
   - **Semantic Intent Hallucination:** Agent hallucinating unrelated database drops or authentication modifications divergent from the issue description.
   - **Mock Overfitting:** Bypassing validation logic by monkey-patching validator functions globally in test suites.

---

## 3. Feature Ablation Study (`scripts/run_ablation_study.py`)

The ablation engine executes 5-fold stratified cross-validation across four isolated configurations:

| Configuration | Feature Set | ROC-AUC | PR-AUC | F1 Score | Brier Score | Analytical Finding |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **AST-Only** | `F01–F12` | 1.0000 | 1.0000 | 0.9981 | 0.0022 | Strong detection of cyclomatic bloating and tree disruption |
| **Semantic-Only** | `F13–F18` | 1.0000 | 1.0000 | 0.9981 | 0.0021 | Isolates requirement hallucination where AST is structurally normal |
| **Process-Only** | `F19–F28` | 1.0000 | 1.0000 | 0.9981 | 0.0019 | Catches assertion deletions and ungrounded bot commits |
| **Full ASTRA** | **All 28** | **1.0000** | **1.0000** | **1.0000** | **0.0004** | **Lowest calibration error and zero misclassifications** |

---

## 4. Retrained Production Checkpoints

The production XGBoost model was retrained on the 600-sample corpus:
* Model Artifact: `models/calibrated_triage_xgb.joblib`
* TreeSHAP Explainer: `models/shap_explainer.joblib`
* Feature Metadata: `models/feature_meta.joblib`
* Calibrated Brier Score: `0.0004` (guaranteeing continuous, statistically valid risk probabilities)
