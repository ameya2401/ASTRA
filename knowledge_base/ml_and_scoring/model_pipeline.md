# ML Classifier & Calibration Pipeline

> Architecture: XGBoost Classifier + Platt Scaling (`CalibratedClassifierCV`)  
> Target Metric: Calibrated Brier Score & AUC-ROC under 4:1 class imbalance

---

## 1. Model Selection Rationale

Software engineering defect prediction relies heavily on tabular metrics with non-linear threshold effects (e.g. cyclomatic complexity exceeding 10 creates an exponential jump in bugs). 

- **Why XGBoost over Deep Learning**: Gradient-boosted decision trees naturally handle mixed discrete/continuous tabular data, require zero heavy GPU infrastructure during inference, and provide nanosecond evaluation latency.
- **Why Platt Scaling**: Raw boosting margins ($z \in \mathbb{R}$) or raw tree leaf probabilities often exhibit extreme overconfidence towards 0 and 1. Platt scaling fits a logistic sigmoid mapping:
  $$P(y=1 \mid z) = \frac{1}{1 + \exp(A z + B)}$$
  using 5-fold cross-validation, ensuring the resulting score is a true probability matching empirical defect frequencies.

---

## 2. Handling Class Imbalance

In real software repositories, defective PRs are a minority (typically ~20% defective vs 80% accepted/clean, creating a 4:1 imbalance).

- **Weighting Strategy**: Set XGBoost `scale_pos_weight = 4.0` during initial tree construction.
- **Stratified Folds**: Training splits use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` to maintain label distributions across folds.
- **Evaluation Metrics**: Models are evaluated using:
  - **Brier Score**: Measures probability calibration quality (lower is better, goal < 0.12).
  - **AUC-ROC**: Measures ranking discrimination across thresholds (goal > 0.85).
  - **Precision-Recall AUC (PR-AUC)**: Measures precision across the minority defective class.

---

## 3. Training and Serialization Lifecycle

```
Processed Parquet Matrix ──> 5-Fold Stratified Split ──> Base XGBoost Training
                                                              │
                                                              ▼
Serialized Checkpoint (.joblib) <── Platt Calibration <── CalibratedClassifierCV
```

- **Model Checkpoints**: Saved in [ast-triage-core/models/](file:///e:/study/ASTRA/ast-triage-core/models/) as serialized `joblib` artifacts containing:
  - Base XGBoost booster.
  - Calibrated pipeline wrapper.
  - Feature name mapping list (guaranteeing exact 28-D index alignment).
  - Normalization scaler parameters.
