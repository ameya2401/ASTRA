"""
src/ml_engine/explainer.py - SHAP TreeExplainer local feature attribution.

Computes exact per-sample Shapley values using TreeSHAP to identify and isolate
the top risk-increasing and risk-mitigating features for every pull request.
"""
from typing import Any, Dict, List, Optional, Sequence
import numpy as np

from src.feature_pipeline.vector_builder import FEATURE_NAMES


class TreeSHAPExplainer:
    """
    Wrapper around SHAP TreeExplainer for fast local feature attribution.

    Provides polynomial-time Shapley attribution calculation, top-K risk driver
    filtering, and human-readable formatting for developer-facing pull request feedback.
    """

    def __init__(
        self,
        explainer: Any = None,
        feature_names: Optional[Sequence[str]] = None,
    ):
        """
        Initializes the TreeSHAP explainer wrapper.

        Args:
            explainer: Fitted shap.TreeExplainer instance (optional on init).
            feature_names: Ordered list of feature names matching vector columns.
        """
        self.explainer = explainer
        self.feature_names = list(feature_names or FEATURE_NAMES)

    def set_explainer(self, explainer: Any) -> None:
        """Sets or replaces the underlying SHAP TreeExplainer object."""
        self.explainer = explainer

    def compute_attributions(self, X_sample: np.ndarray) -> List[Dict[str, Any]]:
        """
        Computes SHAP values for a single sample row.

        Args:
            X_sample: Array of shape (1, 28) or (28,).

        Returns:
            List of 28 attribution dictionaries, each containing:
            feature_name, feature_value, shap_value, and impact.
        """
        if self.explainer is None:
            raise ValueError("SHAP TreeExplainer has not been initialized or loaded.")

        X_arr = np.array(X_sample, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        # Call TreeExplainer
        raw_shap = self.explainer.shap_values(X_arr)

        # Handle different SHAP output formats across versions
        if isinstance(raw_shap, list):
            # Binary classification list [class_0, class_1]
            shap_row = raw_shap[1][0] if len(raw_shap) > 1 else raw_shap[0][0]
        elif hasattr(raw_shap, "values"):
            # SHAP Explanation object
            vals = raw_shap.values
            if vals.ndim == 3:
                shap_row = vals[0, :, 1]
            elif vals.ndim == 2:
                shap_row = vals[0]
            else:
                shap_row = vals
        elif isinstance(raw_shap, np.ndarray):
            if raw_shap.ndim == 3:
                # Shape (1, n_features, 2)
                shap_row = raw_shap[0, :, 1]
            elif raw_shap.ndim == 2:
                # Shape (1, n_features)
                shap_row = raw_shap[0]
            else:
                shap_row = raw_shap
        else:
            shap_row = np.asarray(raw_shap).flatten()

        attributions: List[Dict[str, Any]] = []
        n_feats = min(len(self.feature_names), len(shap_row), X_arr.shape[1])

        for i in range(n_feats):
            feat_name = self.feature_names[i]
            feat_val = float(X_arr[0, i])
            attribution = float(shap_row[i])
            impact = "INCREASES_RISK" if attribution > 0 else "DECREASES_RISK"

            attributions.append({
                "feature_name": feat_name,
                "feature_value": feat_val,
                "shap_value": round(attribution, 4),
                "impact": impact,
            })

        return attributions

    def get_top_risk_drivers(
        self,
        X_sample: np.ndarray,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Extracts the top K risk-increasing features (sorted descending by positive SHAP).

        Args:
            X_sample: Array of shape (1, 28) or (28,).
            top_k: Number of risk-increasing drivers to isolate.

        Returns:
            List of top K attribution dictionaries.
        """
        all_attrs = self.compute_attributions(X_sample)

        # Filter features that increased risk (positive SHAP attribution)
        positive_drivers = [a for a in all_attrs if a["shap_value"] > 0]
        positive_drivers.sort(key=lambda item: item["shap_value"], reverse=True)

        if len(positive_drivers) >= top_k:
            return positive_drivers[:top_k]

        # If fewer than top_k positive drivers, sort remaining by absolute magnitude
        remaining = [a for a in all_attrs if a["shap_value"] <= 0]
        remaining.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
        combined = positive_drivers + remaining
        return combined[:top_k]

    def format_risk_driver_strings(
        self,
        X_sample: np.ndarray,
        top_k: int = 3,
    ) -> List[str]:
        """
        Formats top K risk drivers into clean human-readable strings.

        Example: "assertions_deleted = 3 (+0.32 SHAP)"

        Args:
            X_sample: Array of shape (1, 28) or (28,).
            top_k: Number of risk drivers to format.

        Returns:
            List of human-readable summary strings.
        """
        top_drivers = self.get_top_risk_drivers(X_sample, top_k=top_k)
        formatted: List[str] = []

        for driver in top_drivers:
            name = driver["feature_name"]
            val = driver["feature_value"]
            shap_val = driver["shap_value"]

            # Display integers cleanly
            if val == int(val):
                val_str = str(int(val))
            else:
                val_str = f"{val:.2f}"

            sign = "+" if shap_val >= 0 else ""
            formatted.append(f"{name} = {val_str} ({sign}{shap_val:.2f} SHAP)")

        return formatted
