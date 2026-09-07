# Feature Vector Assembly & Normalization

> Implementation: [src/feature_pipeline/](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/)  
> Key modules: [vector_builder.py](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/vector_builder.py), [normalizer.py](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/normalizer.py)

Before feeding metrics into XGBoost, ASTRA bundles extracted structural deltas, NLP similarities, and git metadata into an aligned, normalized numerical array.

---

## 1. Feature Order and Vector Alignment

The vector ordering strictly matches the 28 columns defined in the [feature_taxonomy.md](file:///e:/study/ASTRA/knowledge_base/features/feature_taxonomy.md).

```
Index:   0    1    2    3    4    5    6    7    8    9   10   11
Feature: F01  F02  F03  F04  F05  F06  F07  F08  F09  F10  F11  F12
Group:   [------------------ AST Structural --------------------]

Index:   12   13   14   15   16   17
Feature: F13  F14  F15  F16  F17  F18
Group:   [-------- Semantic NLP ---------]

Index:   18   19   20   21   22
Feature: F19  F20  F21  F22  F23
Group:   [--------- Test Churn ---------]

Index:   23   24   25   26   27
Feature: F24  F25  F26  F27  F28
Group:   [---- Process & Provenance ----]
```

This strict ordering is implemented in `FeatureRecord.to_vector()` in [database/models.py:L209-L245](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L209-L245).

---

## 2. Missing Value Imputation

Certain features may be unavailable during early triage:

1. **Pending CI Status (`f27_ci_pass_flag`)**:
   When a PR is evaluated before CI runs complete, `ci_passed` is `None`. The normalizer imputes `0.5` (neutral) rather than zero to avoid falsely penalizing pending builds.
2. **Missing Issue Text (`f13_intent_diff_cosine_sim`)**:
   If an agent creates a PR without an issue prompt or description, `f18_issue_token_length` is 0, and `f13_intent_diff_cosine_sim` falls back to title similarity (`f14_issue_title_diff_sim`). If title is also empty, cosine defaults to `0.0` and `f17_semantic_drift_flag` triggers.

---

## 3. Parquet Matrix Storage for Training

For batch offline training and ablation studies:
- Extracted features are compiled into Apache Parquet matrices saved under `data/processed/features_matrix.parquet`.
- Parquet provides high read throughput and preserves schema types across training experiments without CSV serialization precision loss.
