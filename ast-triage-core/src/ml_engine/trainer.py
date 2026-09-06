"""
src/ml_engine/trainer.py - XGBoost model training with Platt calibration.

Trains an XGBoost classifier on imbalanced tabular PR data,
wraps it in CalibratedClassifierCV for probability calibration,
and fits a SHAP TreeExplainer for local feature attribution.

Implementation: Phase 4
"""
