# ML Classifier & Calibration Pipeline

> Implementation: [src/ml_engine/trainer.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/trainer.py), [src/ml_engine/predictor.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/predictor.py)  
> Architecture: XGBoost Classifier + Platt Scaling (`CalibratedClassifierCV`)  
> Verification Gate: `python -m pytest tests/test_feature_pipeline.py` (19/19 passing)

---

## 1. Model Selection Rationale

Software engineering defect prediction relies on tabular metrics with non-linear threshold effects. For example, cyclomatic complexity exceeding 10 creates an exponential jump in defect rates.

- **Why XGBoost over Deep Learning**: Gradient-boosted decision trees naturally handle mixed discrete and continuous tabular data, require zero heavy GPU infrastructure during inference, and provide sub-15 millisecond evaluation latency.
- **Why Platt Scaling**: Raw boosting margins ($z \in \mathbb{R}$) or raw tree leaf probabilities often exhibit overconfidence towards 0 and 1. Platt scaling fits a logistic sigmoid mapping:
  $$P(y=1 \mid z) = \frac{1}{1 + \exp(A z + B)}$$
  using 5-fold cross-validation, ensuring the resulting score is a true probability matching empirical defect frequencies.

---

## 2. Handling Class Imbalance

In software repositories, defective pull requests are a minority (around 20% defective vs 80% accepted/clean, creating a 4:1 imbalance).

- **Weighting Strategy**: Set XGBoost `scale_pos_weight = (len(y) - sum(y)) / sum(y)` during initial tree construction.
- **Stratified Folds**: Training splits use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` to maintain label distributions across folds.
- **Evaluation Metrics**: Models are evaluated using:
  - **Brier Score**: Measures probability calibration quality (lower is better, goal < 0.12).
  - **AUC-ROC**: Measures ranking discrimination across thresholds (goal > 0.85).
  - **Precision-Recall AUC (PR-AUC)**: Measures precision across the minority defective class.
  - **F1 Score**: Harmonic mean of precision and recall at 0.5 decision threshold.

---

## 3. Training and Serialization Lifecycle

```
28-D Feature Matrix ──> 5-Fold Stratified Split ──> Base XGBoost Training
                                                          │
                                                          ▼
Serialized Checkpoint (.joblib) <── Platt Calibration <── CalibratedClassifierCV
```

- **Saved Checkpoints**: Saved in [ast-triage-core/models/](file:///e:/study/ASTRA/ast-triage-core/models/) as serialized `joblib` artifacts:
  - `calibrated_triage_xgb.joblib`: 5-fold Platt-calibrated wrapper.
  - `shap_explainer.joblib`: Fitted `shap.TreeExplainer` on base XGBoost booster.
  - `feature_meta.joblib`: Feature name list, count, and training metrics.

---

## 4. Standalone CLI Execution

The pipeline can be executed and evaluated via the standalone CLI runner:

```powershell
python scripts/train_model.py --n-samples 500 --demo-predict
```
