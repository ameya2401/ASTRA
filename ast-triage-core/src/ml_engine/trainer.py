"""
src/ml_engine/trainer.py - XGBoost model training with Platt calibration and SHAP.

Trains an XGBoost classifier on imbalanced tabular PR data, applies Platt scaling
via CalibratedClassifierCV(method='sigmoid', cv=5) to guarantee calibrated probabilities,
fits a SHAP TreeExplainer for local feature attributions, and persists serialized checkpoints.
"""
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    auc,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier
import shap

from src.feature_pipeline.vector_builder import FEATURE_NAMES


def evaluate_model(
    y_true: np.ndarray,
    y_pred_prob: np.ndarray,
    print_summary: bool = True,
) -> Dict[str, float]:
    """
    Evaluates calibrated model performance on tabular defect risk predictions.

    Args:
        y_true: Ground truth binary labels (0 = Accepted, 1 = Defective).
        y_pred_prob: Calibrated risk probabilities in [0.0, 1.0].
        print_summary: If True, prints formatted metrics table to stdout.

    Returns:
        Dictionary containing roc_auc, pr_auc, f1, and brier_score.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_pred_prob, dtype=float)

    # ROC-AUC
    if len(np.unique(y_true_arr)) > 1:
        roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
    else:
        roc_auc = 0.5

    # PR-AUC
    precision, recall, _ = precision_recall_curve(y_true_arr, y_prob_arr)
    pr_auc = float(auc(recall, precision))

    # Brier Score (lower is better, goal < 0.12)
    brier = float(brier_score_loss(y_true_arr, y_prob_arr))

    # F1 Score at standard 0.5 decision threshold
    preds_binary = (y_prob_arr >= 0.5).astype(int)
    f1 = float(f1_score(y_true_arr, preds_binary, zero_division=0))

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "f1": round(f1, 4),
        "brier_score": round(brier, 4),
    }

    if print_summary:
        print("\n=== AST-Triage Model Evaluation ===")
        print(f"ROC-AUC:     {metrics['roc_auc']:.4f}")
        print(f"PR-AUC:      {metrics['pr_auc']:.4f}")
        print(f"F1 Score:    {metrics['f1']:.4f}")
        print(f"Brier Score: {metrics['brier_score']:.4f}")
        print("===================================\n")

    return metrics


def train_calibrated_triage_model(
    X: np.ndarray,
    y: np.ndarray,
    save_dir: str = "models",
    random_state: int = 42,
    n_estimators: int = 200,
    max_depth: int = 4,
    learning_rate: float = 0.05,
) -> Tuple[Any, Any, Dict[str, float]]:
    """
    Trains an XGBoost model with 5-fold Platt probability calibration and fits SHAP explainer.

    Args:
        X: Feature matrix of shape (N, 28).
        y: Binary ground truth labels (N,) where 0 = Accepted, 1 = Defective.
        save_dir: Directory to save serialized model checkpoints.
        random_state: Seed for reproducibility.
        n_estimators: Number of trees in XGBoost ensemble.
        max_depth: Maximum tree depth.
        learning_rate: Gradient boosting learning rate.

    Returns:
        Tuple of (calibrated_model, shap_explainer, in_sample_metrics).
    """
    X_arr = np.asarray(X, dtype=np.float32)
    y_arr = np.asarray(y, dtype=int)

    pos_count = int(np.sum(y_arr))
    neg_count = len(y_arr) - pos_count
    scale_pos = float(neg_count) / max(1.0, float(pos_count))

    # Base XGBoost Classifier configured for imbalanced tabular data
    base_xgb = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        random_state=random_state,
        eval_metric="logloss",
    )

    # 5-fold Stratified Platt Calibration via Sigmoid
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    try:
        calibrated_model = CalibratedClassifierCV(
            estimator=base_xgb,
            method="sigmoid",
            cv=cv,
        )
    except TypeError:
        calibrated_model = CalibratedClassifierCV(
            base_estimator=base_xgb,
            method="sigmoid",
            cv=cv,
        )

    calibrated_model.fit(X_arr, y_arr)

    # Fit base XGBoost model on full dataset for SHAP TreeExplainer
    base_xgb.fit(X_arr, y_arr)
    explainer = shap.TreeExplainer(base_xgb)

    # Compute training metrics
    preds_prob = calibrated_model.predict_proba(X_arr)[:, 1]
    metrics = evaluate_model(y_arr, preds_prob, print_summary=True)

    # Persist model artifacts to target directory
    out_dir = Path(save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / "calibrated_triage_xgb.joblib"
    explainer_path = out_dir / "shap_explainer.joblib"
    meta_path = out_dir / "feature_meta.joblib"

    joblib.dump(calibrated_model, model_path)
    joblib.dump(explainer, explainer_path)
    joblib.dump({
        "feature_names": FEATURE_NAMES,
        "n_features": len(FEATURE_NAMES),
        "random_state": random_state,
        "metrics": metrics,
    }, meta_path)

    return calibrated_model, explainer, metrics


def generate_synthetic_pr_dataset(
    n_samples: int = 400,
    defect_ratio: float = 0.20,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a deterministic synthetic 28-D PR dataset for testing and baseline initialization.

    Features reflect realistic distributions:
    - Clean PRs (0): Low cyclomatic delta, high intent alignment (cosine > 0.6), tests present, zero deleted assertions.
    - Defective PRs (1): High cyclomatic delta, low intent alignment (cosine < 0.45), deleted assertions, high disturbance.

    Args:
        n_samples: Total number of synthetic samples.
        defect_ratio: Fraction of defective PRs (default 0.20 matching 4:1 imbalance).
        random_state: Seed for deterministic synthesis.

    Returns:
        Tuple of (X, y) with X shape (n_samples, 28) and y shape (n_samples,).
    """
    rng = np.random.RandomState(random_state)
    n_defects = int(n_samples * defect_ratio)
    n_clean = n_samples - n_defects

    X = np.zeros((n_samples, len(FEATURE_NAMES)), dtype=np.float32)
    y = np.zeros(n_samples, dtype=int)
    y[n_clean:] = 1

    # Populate clean samples (first n_clean rows)
    for i in range(n_clean):
        # AST Structural (F01 - F12)
        X[i, 0] = rng.poisson(lam=25)                # nodes_added
        X[i, 1] = rng.poisson(lam=10)                # nodes_deleted
        X[i, 2] = rng.poisson(lam=8)                 # nodes_mutated
        X[i, 3] = rng.choice([-1, 0, 1, 2])          # delta_cc
        X[i, 4] = rng.choice([0, 1])                 # nesting_depth_delta
        X[i, 5] = rng.binomial(n=2, p=0.2)           # func_signatures_mod
        X[i, 6] = rng.binomial(n=1, p=0.1)           # classes_modified
        X[i, 7] = 0.0                                # return_types_altered
        X[i, 8] = rng.choice([0, 1])                 # call_graph_fanout_delta
        X[i, 9] = rng.uniform(0.05, 0.35)            # ast_disturbance_index
        X[i, 10] = rng.binomial(n=1, p=0.1)          # try_catch_added
        X[i, 11] = rng.uniform(0.02, 0.20)           # control_flow_churn

        # Semantic Drift (F13 - F18)
        X[i, 12] = rng.uniform(0.65, 0.95)           # intent_diff_cosine
        X[i, 13] = rng.uniform(0.60, 0.90)           # title_diff_cosine
        X[i, 14] = rng.uniform(0.10, 0.40)           # entity_drift_jaccard
        X[i, 15] = rng.uniform(0.05, 0.30)           # docstring_code_ratio
        X[i, 16] = 0.0                               # semantic_drift_flag
        X[i, 17] = rng.randint(40, 200)              # issue_token_length

        # Test Churn (F19 - F23)
        X[i, 18] = rng.randint(1, 4)                 # test_files_modified
        X[i, 19] = rng.randint(15, 60)               # test_ast_nodes_added
        X[i, 20] = 0.0                               # assertions_deleted
        X[i, 21] = rng.uniform(0.70, 1.40)           # test_to_logic_ratio
        X[i, 22] = rng.binomial(n=2, p=0.1)          # mock_patch_count_delta

        # Process (F24 - F28)
        X[i, 23] = rng.randint(1, 4)                 # commit_count
        X[i, 24] = rng.randint(1, 3)                 # files_touched_count
        X[i, 25] = rng.uniform(0.0, 1.2)             # dispersion_entropy
        X[i, 26] = 1.0                               # ci_pass_flag
        X[i, 27] = rng.binomial(n=1, p=0.4)          # is_known_agent_bot

    # Populate defective samples (last n_defects rows)
    for i in range(n_clean, n_samples):
        # AST Structural (F01 - F12)
        X[i, 0] = rng.poisson(lam=120)               # nodes_added
        X[i, 1] = rng.poisson(lam=60)                # nodes_deleted
        X[i, 2] = rng.poisson(lam=45)                # nodes_mutated
        X[i, 3] = rng.randint(6, 25)                 # delta_cc
        X[i, 4] = rng.randint(3, 8)                  # nesting_depth_delta
        X[i, 5] = rng.randint(2, 6)                  # func_signatures_mod
        X[i, 6] = rng.randint(1, 4)                  # classes_modified
        X[i, 7] = rng.randint(1, 3)                  # return_types_altered
        X[i, 8] = rng.randint(3, 9)                  # call_graph_fanout_delta
        X[i, 9] = rng.uniform(0.60, 0.95)            # ast_disturbance_index
        X[i, 10] = rng.randint(2, 7)                 # try_catch_added
        X[i, 11] = rng.uniform(0.40, 0.85)           # control_flow_churn

        # Semantic Drift (F13 - F18)
        is_drifted = rng.binomial(n=1, p=0.7)
        if is_drifted:
            X[i, 12] = rng.uniform(0.10, 0.42)       # intent_diff_cosine
            X[i, 13] = rng.uniform(0.10, 0.40)       # title_diff_cosine
            X[i, 16] = 1.0                           # semantic_drift_flag
        else:
            X[i, 12] = rng.uniform(0.48, 0.65)
            X[i, 13] = rng.uniform(0.45, 0.60)
            X[i, 16] = 0.0

        X[i, 14] = rng.uniform(0.55, 0.90)           # entity_drift_jaccard
        X[i, 15] = rng.uniform(0.0, 0.05)            # docstring_code_ratio
        X[i, 17] = rng.randint(10, 50)               # issue_token_length

        # Test Churn (F19 - F23)
        X[i, 18] = rng.choice([0, 1])                # test_files_modified
        X[i, 19] = rng.choice([0, 5])                # test_ast_nodes_added
        X[i, 20] = float(rng.randint(2, 9))          # assertions_deleted
        X[i, 21] = rng.uniform(0.0, 0.15)            # test_to_logic_ratio
        X[i, 22] = float(rng.randint(3, 8))          # mock_patch_count_delta

        # Process (F24 - F28)
        X[i, 23] = rng.randint(5, 15)                # commit_count
        X[i, 24] = rng.randint(6, 18)                # files_touched_count
        X[i, 25] = rng.uniform(2.0, 3.8)             # dispersion_entropy
        X[i, 26] = float(rng.choice([0, 1], p=[0.7, 0.3])) # ci_pass_flag
        X[i, 27] = 1.0                               # is_known_agent_bot

    return X, y
