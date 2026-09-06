# Phase 4: Calibrated Classifier & SHAP Local Attribution

**Goal:** Build the Machine Learning inference engine that takes the extracted features, predicts risk, and explains the prediction.

---

## Instructions for the AI Agent

Act as a Senior Machine Learning Engineer specializing in Tabular Risk Modeling.
Write `src/ml_engine/trainer.py`, `src/ml_engine/predictor.py`, and `src/feature_pipeline/vector_builder.py` in `e:\study\ASTRA\ast-triage-core`.

**Requirements:**

1. **Feature Assembly (`vector_builder.py`):**
   - Create a function to take AST metrics, semantic metrics, test metrics, and process metrics and output a normalized 28-dimensional numpy array.

2. **Model Training (`trainer.py`):**
   - Train an XGBoost classifier on an imbalanced tabular dataset.
   - Wrap the model in `CalibratedClassifierCV(method='sigmoid', cv=5)` to guarantee that the predicted probability accurately represents the true empirical defect rate (minimizing the Brier Score).
   - Integrate `shap.TreeExplainer` to compute local feature attributions for any single incoming inference row.
   - Save model weights and explainer objects with joblib to `models/`.
   - Include a function `evaluate_model(y_true, y_pred_prob)` that prints ROC-AUC, PR-AUC, F1, and Brier Score.

3. **Inference (`predictor.py`):**
   - Create a fast loading method for the pre-trained model and explainer.
   - Export the top 3 risk-increasing features formatted as human-readable strings (e.g. "assertions_deleted = 3 (+0.32 SHAP)") based on a single sample prediction.
