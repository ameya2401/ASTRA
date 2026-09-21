# Explainability & SHAP Attribution

> Implementation: [src/ml_engine/explainer.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/explainer.py)  
> Algorithm: TreeSHAP (Lundberg et al.)  
> Runtime Wrapper: `TreeSHAPExplainer`

Predicting a risk score without explanation fails developers. A human reviewer told "Risk: 0.82" cannot take targeted action without knowing what triggered the warning. ASTRA integrates local TreeSHAP explanations to break down the exact risk drivers for each pull request.

---

## 1. Why TreeSHAP?

- **Exact Efficiency**: While KernelSHAP requires thousands of random model perturbations, TreeSHAP evaluates tree paths in polynomial time $O(T L D^2)$, allowing feature attribution calculation in under 15 milliseconds per pull request.
- **Local Additivity**: For any pull request feature vector $x$:
  $$f(x) = \phi_0 + \sum_{i=1}^{28} \phi_i(x)$$
  where $\phi_0$ is the base expected model prediction across the training set, and $\phi_i(x)$ is the exact marginal credit assigned to feature $i$.

---

## 2. Explanation Extraction Workflow

1. **Calculate Attributions**: `TreeSHAPExplainer.compute_attributions(X_sample)` evaluates the 28 features against the trained XGBoost ensemble.
2. **Sort by Contribution**:
   - **Risk Amplifiers ($\phi_i > 0$)**: Features that pushed the probability toward defective. Sorted descending to isolate the top 3 positive contributors via `get_top_risk_drivers(top_k=3)`.
   - **Mitigating Factors ($\phi_i < 0$)**: Features that pulled the probability toward safe (such as high test coverage or clean CI).
3. **Database Storage**: The top 3 positive feature names and their numerical attribution values are persisted in [database/models.py](file:///e:/study/ASTRA/ast-triage-core/database/models.py) (`top_shap_feature_1..3`, `shap_value_1..3`).

---

## 3. Human-Readable Translation

The runtime exports human-readable explanation strings via `format_risk_driver_strings(top_k=3)`:

```python
# Example outputs:
"assertions_deleted = 3 (+0.32 SHAP)"
"delta_cc = 14 (+0.28 SHAP)"
"semantic_drift_flag = 1 (+0.25 SHAP)"
```

| Raw Metric | SHAP Value | Rendered Markdown Report Clause |
|---|---|---|
| `f04_cyclomatic_delta = +8` | $+0.24$ | "Cyclomatic complexity jumped by +8 across 2 functions." |
| `f17_semantic_drift_flag = 1` | $+0.31$ | "Intent-to-diff alignment is low (0.38 < 0.45 threshold); PR drifts from prompt." |
| `f21_test_assertions_deleted = 4` | $+0.19$ | "4 test assertions were deleted in modified test suites." |
| `f22_test_to_logic_ratio = 0.55` | $-0.15$ | "Comprehensive accompanying test suites partially offset complexity risk." |
