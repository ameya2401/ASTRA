# Risk Stratification Policy

> The decision logic mapping continuous calibrated defect probabilities into actionable triage bands.

ASTRA maps the calibrated defect probability $P(\text{Defect} \mid X) \in [0.0, 1.0]$ into three operational risk tiers.

---

## 1. Risk Bands and Policies

```
0.0                                0.35                             0.70                 1.0
 ├───────────────────────────────────┼────────────────────────────────┼───────────────────┤
 │               GREEN               │             YELLOW             │        RED        │
 │            (Low Risk)             │         (Medium Risk)          │    (High Risk)    │
 └───────────────────────────────────┴────────────────────────────────┴───────────────────┘
```

| Risk Tier | Calibrated Score Range | Automated Triage Action | Reviewer Guidance |
|---|---|---|---|
| **GREEN** | $[0.00, 0.35)$ | Fast-track approval / auto-merge eligible | Minimal review required. Verify test coverage and merge. |
| **YELLOW**| $[0.35, 0.70)$ | Standard human review queue | Focus human inspection on the top 3 SHAP highlighted risk factors. |
| **RED**   | $[0.70, 1.00]$ | Block PR merge & request agent revision | Auto-reject or request major revision. Point agent to drift or structural issues. |

---

## 2. Hard Override Rules

Certain features represent critical failures that immediately elevate a PR to the **RED** tier regardless of the XGBoost baseline score:

1. **Semantic Drift Override**:
   If `f17_semantic_drift_flag == 1` (i.e. `f13_intent_diff_cosine_sim < 0.45`), the PR is forced to **RED**. An agent that solved the wrong issue must not be merged.
2. **Assertion Deletion Anomaly**:
   If `f21_test_assertions_deleted > 5` and `f20_test_ast_nodes_added == 0`, the PR is flagged for suspicious assertion suppression.
3. **Severe Disturbance with Failing CI**:
   If `f10_ast_disturbance_index > 0.85` and `f27_ci_pass_flag == 0`, the PR is classified as high-risk breaking code.

---

## 3. Feedback Loop to Agent Developers

When a PR receives a RED or YELLOW status, the triage reporter outputs structured feedback:
- Primary risk driver (e.g. "Branching complexity increased by +12 without accompanying test coverage").
- Concrete diff locations where disturbance spiked.
- Suggested agent revision prompts to remedy the flagged issues.
