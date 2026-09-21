"""
src/ml_engine - Calibrated XGBoost Risk Classifier & SHAP Attribution.

Re-exports:
    - RiskPredictor: Inference runtime with cached weights and TreeSHAP explainer.
    - get_predictor: Thread-safe singleton predictor factory.
    - predict_risk: Functional single-sample risk prediction API.
    - train_calibrated_triage_model: 5-fold Platt calibrated model training pipeline.
    - evaluate_model: ROC-AUC, PR-AUC, F1, and Brier score evaluation.
    - generate_synthetic_pr_dataset: Deterministic synthetic tabular data generator.
    - TreeSHAPExplainer: Local feature attribution engine.
"""
from src.ml_engine.explainer import TreeSHAPExplainer
from src.ml_engine.predictor import RiskPredictor, get_predictor, predict_risk
from src.ml_engine.trainer import (
    evaluate_model,
    generate_synthetic_pr_dataset,
    train_calibrated_triage_model,
)

__all__ = [
    "TreeSHAPExplainer",
    "RiskPredictor",
    "get_predictor",
    "predict_risk",
    "train_calibrated_triage_model",
    "evaluate_model",
    "generate_synthetic_pr_dataset",
]
