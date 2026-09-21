"""
src/feature_pipeline/normalizer.py - Feature scaling, clipping, and imputation.

Ensures that all 28-D input vectors are numerically stable, within physiological bounds,
and free of NaNs, Infs, or malformed data before feeding into the ML classifier.
"""
from typing import Dict, Optional, Tuple, Union
import numpy as np

# Physiological / algorithmic bounds for all 28 features (F01 - F28)
FEATURE_BOUNDS: Dict[int, Tuple[Optional[float], Optional[float]]] = {
    0: (0.0, None),       # nodes_added >= 0
    1: (0.0, None),       # nodes_deleted >= 0
    2: (0.0, None),       # nodes_mutated >= 0
    3: (-50.0, 50.0),     # delta_cc
    4: (-20.0, 20.0),     # nesting_depth_delta
    5: (0.0, None),       # func_signatures_mod >= 0
    6: (0.0, None),       # classes_modified >= 0
    7: (0.0, None),       # return_types_altered >= 0
    8: (None, None),      # call_graph_fanout_delta
    9: (0.0, 1.0),        # ast_disturbance_index in [0.0, 1.0]
    10: (0.0, None),      # try_catch_added >= 0
    11: (0.0, 1.0),       # control_flow_churn in [0.0, 1.0]
    12: (-1.0, 1.0),      # intent_diff_cosine in [-1.0, 1.0]
    13: (-1.0, 1.0),      # title_diff_cosine in [-1.0, 1.0]
    14: (0.0, 1.0),       # entity_drift_jaccard in [0.0, 1.0]
    15: (0.0, None),      # docstring_code_ratio >= 0.0
    16: (0.0, 1.0),       # semantic_drift_flag in {0, 1}
    17: (0.0, None),      # issue_token_length >= 0
    18: (0.0, None),      # test_files_modified >= 0
    19: (0.0, None),      # test_ast_nodes_added >= 0
    20: (0.0, None),      # assertions_deleted >= 0
    21: (0.0, None),      # test_to_logic_ratio >= 0.0
    22: (0.0, None),      # mock_patch_count_delta >= 0
    23: (1.0, None),      # commit_count >= 1
    24: (1.0, None),      # files_touched_count >= 1
    25: (0.0, None),      # dispersion_entropy >= 0.0
    26: (0.0, 1.0),       # ci_pass_flag in {0, 1}
    27: (0.0, 1.0),       # is_known_agent_bot in {0, 1}
}


def impute_missing_values(
    X: np.ndarray,
    fill_value: float = 0.0,
) -> np.ndarray:
    """
    Replaces NaN, positive infinity, and negative infinity with clean numerical values.

    Args:
        X: Input array of shape (N, 28) or (28,).
        fill_value: Default replacement value.

    Returns:
        Cleaned NumPy array with same shape and float32 dtype.
    """
    X_clean = np.array(X, dtype=np.float32, copy=True)
    nan_mask = np.isnan(X_clean)
    pos_inf_mask = np.isposinf(X_clean)
    neg_inf_mask = np.isneginf(X_clean)

    X_clean[nan_mask] = fill_value
    X_clean[pos_inf_mask] = 1e5
    X_clean[neg_inf_mask] = -1e5

    return X_clean


def clip_feature_bounds(X: np.ndarray) -> np.ndarray:
    """
    Clips features to their algorithmic and physiological bounds.

    Args:
        X: Input array of shape (N, 28) or (28,).

    Returns:
        Clipped array of the same shape.
    """
    is_1d = X.ndim == 1
    X_out = np.array(X, dtype=np.float32, copy=True)
    if is_1d:
        X_out = X_out.reshape(1, -1)

    n_features = min(X_out.shape[1], 28)
    for col_idx in range(n_features):
        lower, upper = FEATURE_BOUNDS.get(col_idx, (None, None))
        if lower is not None:
            X_out[:, col_idx] = np.maximum(X_out[:, col_idx], lower)
        if upper is not None:
            X_out[:, col_idx] = np.minimum(X_out[:, col_idx], upper)

    if is_1d:
        return X_out.reshape(-1)
    return X_out


class FeatureNormalizer:
    """
    Normalizer pipeline for 28-D feature vectors.
    Handles imputation, clipping, and optional robust scaling.
    """

    def __init__(self, clip_bounds: bool = True, default_fill: float = 0.0):
        self.clip_bounds = clip_bounds
        self.default_fill = default_fill
        self.fitted = False
        self.medians: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "FeatureNormalizer":
        """Computes column-wise medians for robust imputation."""
        X_arr = np.array(X, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        # Compute medians ignoring NaNs
        clean = impute_missing_values(X_arr, fill_value=self.default_fill)
        self.medians = np.median(clean, axis=0)
        self.fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Imputes missing values and applies feature bounds."""
        X_arr = np.array(X, dtype=np.float32)
        orig_shape = X_arr.shape

        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        # Impute missing values
        if self.fitted and self.medians is not None:
            # Replace NaNs with column medians
            nan_mask = np.isnan(X_arr)
            for j in range(X_arr.shape[1]):
                col_nans = nan_mask[:, j]
                if np.any(col_nans):
                    med = self.medians[j] if j < len(self.medians) else self.default_fill
                    X_arr[col_nans, j] = med
            X_arr = impute_missing_values(X_arr, fill_value=self.default_fill)
        else:
            X_arr = impute_missing_values(X_arr, fill_value=self.default_fill)

        # Clip bounds
        if self.clip_bounds:
            X_arr = clip_feature_bounds(X_arr)

        return X_arr.reshape(orig_shape)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fits and transforms in a single call."""
        return self.fit(X).transform(X)
