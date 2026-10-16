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

    for i in range(n_clean):
        X[i, 0] = rng.randint(20, 500)
        X[i, 1] = rng.exponential(scale=35.0)
        X[i, 2] = rng.exponential(scale=30.0)
        X[i, 3] = rng.choice([-1, 0, 1, 2, 3, 4, 5, 6], p=[0.05, 0.25, 0.25, 0.20, 0.12, 0.08, 0.04, 0.01])
        X[i, 4] = np.clip(X[i, 3] // 2 + rng.choice([0, 1]), 0, 4)
        X[i, 5] = rng.choice([0, 1, 2, 3], p=[0.60, 0.25, 0.10, 0.05])
        X[i, 6] = rng.choice([0, 1, 2], p=[0.70, 0.22, 0.08])
        X[i, 7] = float(rng.choice([0, 1], p=[0.85, 0.15]))
        X[i, 8] = rng.randint(0, 6)
        X[i, 9] = np.clip(0.08 + 0.04 * X[i, 3] + rng.normal(0, 0.06), 0.02, 0.60)
        X[i, 10] = rng.choice([0, 1, 2], p=[0.65, 0.25, 0.10])
        X[i, 11] = np.clip(0.02 + 0.03 * X[i, 3] + rng.normal(0, 0.04), 0.01, 0.50)
        X[i, 12] = np.clip(0.85 - 0.02 * X[i, 3] + rng.normal(0, 0.10), 0.48, 0.98)
        X[i, 13] = np.clip(X[i, 12] + rng.normal(0, 0.06), 0.45, 0.98)
        X[i, 14] = np.clip(0.30 + 0.03 * X[i, 3] + rng.normal(0, 0.10), 0.05, 0.85)
        X[i, 15] = np.clip(rng.exponential(scale=0.30), 0.0, 1.5)
        X[i, 16] = 0.0
        X[i, 17] = rng.randint(10, 200)
        X[i, 18] = rng.choice([0, 1, 2, 3], p=[0.20, 0.50, 0.20, 0.10])
        X[i, 19] = np.where(X[i, 18] > 0, rng.randint(20, 220), 0.0)
        X[i, 20] = float(rng.choice([0, 1], p=[0.92, 0.08]))
        X[i, 21] = np.clip(X[i, 19] / (X[i, 0] + 1e-5), 0.0, 2.5)
        X[i, 22] = float(rng.choice([0, 1], p=[0.8, 0.2]))
        X[i, 23] = rng.poisson(lam=2.0) + 1
        X[i, 24] = rng.poisson(lam=1.8) + 1
        X[i, 25] = np.clip(0.3 * np.log1p(X[i, 24]) + rng.normal(0, 0.2), 0.0, 2.5)
        X[i, 26] = float(rng.rand() > 0.08)
        X[i, 27] = float(rng.choice([0.0, 1.0], p=[0.4, 0.6]))

    for i in range(n_clean, n_samples):
        X[i, 0] = rng.randint(30, 600)
        X[i, 1] = rng.exponential(scale=50.0)
        X[i, 2] = rng.exponential(scale=45.0)
        X[i, 3] = rng.choice([4, 5, 6, 7, 8, 10, 12, 16], p=[0.10, 0.15, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05])
        X[i, 4] = np.clip(X[i, 3] // 2 + rng.choice([1, 2, 3]), 1, 7)
        X[i, 5] = rng.randint(1, 5)
        X[i, 6] = rng.randint(0, 3)
        X[i, 7] = float(rng.choice([0, 1, 2], p=[0.60, 0.30, 0.10]))
        X[i, 8] = rng.randint(2, 10)
        X[i, 9] = np.clip(0.20 + 0.04 * X[i, 3] + rng.normal(0, 0.08), 0.25, 0.95)
        X[i, 10] = rng.randint(0, 4)
        X[i, 11] = np.clip(0.08 + 0.035 * X[i, 3] + rng.normal(0, 0.05), 0.08, 0.85)
        is_drift = rng.rand() < 0.35
        X[i, 16] = 1.0 if is_drift else 0.0
        X[i, 12] = rng.uniform(0.15, 0.42) if is_drift else rng.uniform(0.48, 0.72)
        X[i, 13] = rng.uniform(0.15, 0.42) if is_drift else rng.uniform(0.45, 0.70)
        X[i, 14] = np.clip(0.50 + 0.03 * X[i, 3] + rng.normal(0, 0.10), 0.20, 0.95)
        X[i, 15] = np.clip(rng.exponential(scale=0.15), 0.0, 0.8)
        X[i, 17] = rng.randint(5, 150)
        X[i, 18] = rng.choice([0, 1, 2], p=[0.50, 0.35, 0.15])
        X[i, 19] = np.where(X[i, 18] > 0, rng.randint(0, 30), 0.0)
        X[i, 20] = float(rng.choice([0, 1, 2, 4, 8], p=[0.40, 0.25, 0.15, 0.12, 0.08]))
        X[i, 21] = np.clip(X[i, 19] / (X[i, 0] + 1e-5), 0.0, 0.35)
        X[i, 22] = float(rng.choice([0, 1, 2, 4], p=[0.4, 0.3, 0.2, 0.1]))
        X[i, 23] = rng.poisson(lam=3.5) + 1
        X[i, 24] = rng.poisson(lam=2.5) + 1
        X[i, 25] = np.clip(0.3 * np.log1p(X[i, 24]) + rng.normal(0.2, 0.3), 0.0, 3.2)
        X[i, 26] = float(rng.rand() > 0.40)
        X[i, 27] = float(rng.choice([0.0, 1.0], p=[0.2, 0.8]))

    return X, y


