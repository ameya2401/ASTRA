# Risk Stratification Policy

> Implementation: [src/ml_engine/predictor.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/predictor.py)  
> Configuration: [config/settings.py](file:///e:/study/ASTRA/ast-triage-core/config/settings.py)  
> Mapping: Calibrated defect probabilities mapped to LOW, MEDIUM, and HIGH triage bands.

ASTRA maps the calibrated defect probability $P(\text{Defect} \mid X) \in [0.0, 1.0]$ into three operational risk tiers using configurable thresholds (`LOW_RISK_THRESHOLD = 0.25`, `HIGH_RISK_THRESHOLD = 0.65`).

---

## 1. Risk Bands and Policies

```
0.0                                0.25                             0.65                 1.0
 ├───────────────────────────────────┼────────────────────────────────┼───────────────────┤
 │                LOW                │             MEDIUM             │       HIGH        │
 │              (Green)              │            (Yellow)            │       (Red)       │
 └───────────────────────────────────┴────────────────────────────────┴───────────────────┘
```

| Risk Tier | Calibrated Score Range | Automated Triage Action | Reviewer Guidance |
|---|---|---|---|
| **LOW**   | $[0.00, 0.25)$ | Fast-track approval / auto-merge eligible | Minimal review required. Verify test coverage and merge. |
| **MEDIUM**| $[0.25, 0.65)$ | Standard human review queue | Focus human inspection on the top 3 SHAP highlighted risk factors. |
| **HIGH**  | $[0.65, 1.00]$ | Block PR merge and request agent revision | Auto-reject or request major revision. Point agent to drift or structural issues. |

---

## 2. Hard Override Rules

Certain features represent critical failures that immediately elevate a PR to the **HIGH** tier regardless of the baseline calibrated score:

1. **Semantic Drift Override**:
   If `f17_semantic_drift_flag == 1` (i.e. `f13_intent_diff_cosine < 0.45`), the PR is forced to **HIGH**. An agent that solved the wrong issue must not be merged.
2. **Assertion Deletion Anomaly**:
   If `f21_test_assertions_deleted > 5` and `f20_test_ast_nodes_added == 0`, the PR is flagged for suspicious assertion suppression and forced to **HIGH**.
3. **Severe Disturbance with Failing CI**:
   If `f10_ast_disturbance_index > 0.85` and `f27_ci_pass_flag == 0`, the PR is classified as high-risk breaking code and forced to **HIGH**.

---

## 3. Feedback Loop to Agent Developers

When a PR receives a HIGH or MEDIUM status, the triage reporter outputs structured feedback:
- Primary risk driver (e.g. "Branching complexity increased by +12 without accompanying test coverage").
- Concrete diff locations where disturbance spiked.
- Suggested agent revision prompts to remedy the flagged issues.
