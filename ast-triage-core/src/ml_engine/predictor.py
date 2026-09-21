"""
src/ml_engine/predictor.py - Fast inference runtime for pre-trained models.

Loads cached model weights and SHAP explainer from disk via a thread-safe singleton,
provides single-sample prediction with calibrated probability output, risk tier stratification,
and exports the top-3 risk-increasing features formatted as human-readable strings.
"""
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np

from config.settings import get_settings
from src.feature_pipeline.vector_builder import FEATURE_NAMES
from src.ml_engine.explainer import TreeSHAPExplainer


class RiskPredictor:
    """
    Thread-safe inference engine for pull request risk scoring.

    Loads the calibrated XGBoost classifier and TreeSHAP explainer,
    evaluates single samples with sub-30ms latency, maps probabilities
    to risk tiers (LOW/MEDIUM/HIGH), and formats top risk drivers.
    """

    def __init__(self, model_dir: Union[str, Path] = "models"):
        self.model_dir = Path(model_dir)
        self.settings = get_settings()
        self.low_threshold = float(self.settings.LOW_RISK_THRESHOLD)
        self.high_threshold = float(self.settings.HIGH_RISK_THRESHOLD)

        self.model: Optional[Any] = None
        self.explainer: Optional[Any] = None
        self.explainer_wrapper: Optional[TreeSHAPExplainer] = None
        self.feature_names: List[str] = list(FEATURE_NAMES)
        self._load_lock = threading.Lock()

        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Loads serialized model and explainer checkpoints from disk."""
        with self._load_lock:
            model_path = self.model_dir / "calibrated_triage_xgb.joblib"
            explainer_path = self.model_dir / "shap_explainer.joblib"
            meta_path = self.model_dir / "feature_meta.joblib"

            if not model_path.exists() or not explainer_path.exists():
                raise FileNotFoundError(
                    f"Model artifacts not found in {self.model_dir}. "
                    "Run trainer.train_calibrated_triage_model() first."
                )

            self.model = joblib.load(model_path)
            self.explainer = joblib.load(explainer_path)

            if meta_path.exists():
                try:
                    meta = joblib.load(meta_path)
                    if "feature_names" in meta:
                        self.feature_names = meta["feature_names"]
                except Exception:
                    pass

            self.explainer_wrapper = TreeSHAPExplainer(
                explainer=self.explainer,
                feature_names=self.feature_names,
            )

    def predict(
        self,
        feature_vector: np.ndarray,
        check_hard_overrides: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes single-sample calibrated risk prediction with SHAP attribution.

        Args:
            feature_vector: Array of shape (1, 28) or (28,).
            check_hard_overrides: If True, applies safety override rules.

        Returns:
            Dictionary containing:
                calibrated_risk_score: float in [0.0, 1.0]
                raw_risk_score: uncalibrated logit/score
                risk_tier: 'LOW', 'MEDIUM', or 'HIGH'
                top_shap_features: List of formatted strings (e.g. "assertions_deleted = 3 (+0.32 SHAP)")
                shap_attributions: Structured attribution records
                override_applied: Optional description of triggered override
                inference_latency_ms: Milliseconds elapsed
        """
        start_time = time.perf_counter()

        if self.model is None or self.explainer_wrapper is None:
            raise RuntimeError("Model or explainer is not loaded.")

        X_arr = np.array(feature_vector, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        if X_arr.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got {X_arr.shape[1]}."
            )

        # 1. Calibrated probability prediction P(defect | X)
        probs = self.model.predict_proba(X_arr)[0]
        calibrated_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

        # 2. Raw uncalibrated score (logit)
        # Logit = ln(p / (1 - p)) clipped for stability
        p_safe = max(1e-6, min(1.0 - 1e-6, calibrated_prob))
        raw_score = float(np.log(p_safe / (1.0 - p_safe)))

        # 3. Top-3 risk-increasing SHAP feature explanations
        top_shap_strings = self.explainer_wrapper.format_risk_driver_strings(X_arr, top_k=3)
        top_shap_attributions = self.explainer_wrapper.get_top_risk_drivers(X_arr, top_k=3)

        # 4. Stratification & Hard Override Rules
        risk_tier = "LOW"
        override_reason: Optional[str] = None

        if check_hard_overrides:
            # Rule 1: Semantic drift override (F17 = 1)
            semantic_drift_val = X_arr[0, 16] if X_arr.shape[1] > 16 else 0
            if semantic_drift_val == 1.0:
                risk_tier = "HIGH"
                override_reason = "Semantic drift override: PR intent deviates from prompt (F17=1)"

            # Rule 2: Assertion suppression anomaly (F21 > 5 and F20 == 0)
            assertions_deleted = X_arr[0, 20] if X_arr.shape[1] > 20 else 0
            test_nodes_added = X_arr[0, 19] if X_arr.shape[1] > 19 else 0
            if assertions_deleted > 5 and test_nodes_added == 0:
                risk_tier = "HIGH"
                override_reason = "Assertion deletion anomaly: Deleted > 5 tests with 0 tests added"

            # Rule 3: High disturbance with failing CI (F10 > 0.85 and F27 == 0)
            disturbance = X_arr[0, 9] if X_arr.shape[1] > 9 else 0
            ci_pass = X_arr[0, 26] if X_arr.shape[1] > 26 else 1
            if disturbance > 0.85 and ci_pass == 0:
                risk_tier = "HIGH"
                override_reason = "Critical disturbance: High AST disturbance (>0.85) with failing CI"

        if override_reason is None:
            if calibrated_prob < self.low_threshold:
                risk_tier = "LOW"
            elif calibrated_prob < self.high_threshold:
                risk_tier = "MEDIUM"
            else:
                risk_tier = "HIGH"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "calibrated_risk_score": round(calibrated_prob, 4),
            "raw_risk_score": round(raw_score, 4),
            "risk_tier": risk_tier,
            "top_shap_features": top_shap_strings,
            "shap_attributions": top_shap_attributions,
            "override_applied": override_reason,
            "inference_latency_ms": round(latency_ms, 2),
        }


# Module-level thread-safe singleton
_predictor_instance: Optional[RiskPredictor] = None
_singleton_lock = threading.Lock()


def get_predictor(
    model_dir: Union[str, Path] = "models",
    reload: bool = False,
) -> RiskPredictor:
    """
    Returns a cached singleton instance of RiskPredictor protected by a thread lock.

    Args:
        model_dir: Checkpoint directory.
        reload: If True, re-instantiates and reloads artifacts from disk.

    Returns:
        Singleton RiskPredictor instance.
    """
    global _predictor_instance
    with _singleton_lock:
        if _predictor_instance is None or reload:
            _predictor_instance = RiskPredictor(model_dir=model_dir)
        return _predictor_instance


def predict_risk(
    feature_vector: np.ndarray,
    model_dir: Union[str, Path] = "models",
) -> Dict[str, Any]:
    """
    Convenience functional API for single-sample PR risk prediction.

    Args:
        feature_vector: Array of shape (1, 28) or (28,).
        model_dir: Model checkpoint directory.

    Returns:
        Prediction result dictionary.
    """
    predictor = get_predictor(model_dir=model_dir)
    return predictor.predict(feature_vector)
