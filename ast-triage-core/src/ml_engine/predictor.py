"""
src/ml_engine/predictor.py - Fast inference runtime for pre-trained models.

Loads cached model weights and SHAP explainer from disk, provides
single-sample prediction with calibrated probability output and
top-3 SHAP risk driver explanations.

Implementation: Phase 4
"""
