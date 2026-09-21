"""
scripts/train_model.py - Standalone training and verification runner for AST-Triage.

Trains the calibrated XGBoost model using 5-fold Platt scaling, fits the TreeSHAP
explainer, evaluates calibration metrics (ROC-AUC, PR-AUC, F1, Brier Score), persists
serialized checkpoints to disk, and runs demonstration sample predictions.

Usage:
    # Train calibrated model and run sample prediction demo
    python scripts/train_model.py --demo-predict

    # Specify custom sample size and save directory
    python scripts/train_model.py --n-samples 800 --save-dir models/
"""
import argparse
from pathlib import Path
import sys

# Ensure root package is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
from src.feature_pipeline import FEATURE_NAMES, build_feature_vector
from src.ml_engine import (
    RiskPredictor,
    generate_synthetic_pr_dataset,
    get_predictor,
    train_calibrated_triage_model,
)


def run_demo_predictions(predictor: RiskPredictor) -> None:
    """Demonstrates risk scoring and SHAP feature attributions on clean vs high-risk PRs."""
    print("\n" + "=" * 60)
    print("RUNNING DEMONSTRATION INFERENCE SCENARIOS")
    print("=" * 60)

    # Scenario 1: Clean, well-tested PR
    clean_ast = {
        "nodes_added": 18,
        "nodes_deleted": 4,
        "nodes_mutated": 5,
        "delta_cc": 0,
        "nesting_depth_delta": 0,
        "func_signatures_mod": 0,
        "classes_modified": 0,
        "ast_disturbance_index": 0.12,
        "control_flow_churn": 0.05,
    }
    clean_semantic = {
        "intent_diff_cosine": 0.88,
        "title_diff_cosine": 0.85,
        "entity_drift_jaccard": 0.22,
        "docstring_code_ratio": 0.15,
        "semantic_drift_flag": 0,
        "issue_token_length": 110,
    }
    clean_test = {
        "test_files_modified": 2,
        "test_ast_nodes_added": 35,
        "assertions_deleted": 0,
        "test_to_logic_ratio": 1.10,
        "mock_patch_count_delta": 0,
    }
    clean_process = {
        "commit_count": 2,
        "files_touched_count": 2,
        "dispersion_entropy": 0.95,
        "ci_pass_flag": 1,
        "is_known_agent_bot": 0,
    }

    v_clean = build_feature_vector(clean_ast, clean_semantic, clean_test, clean_process)
    res_clean = predictor.predict(v_clean)

    print("\n--- Scenario A: Clean & Well-Tested PR ---")
    print(f"Calibrated Risk Score: {res_clean['calibrated_risk_score']:.4f}")
    print(f"Risk Tier:             {res_clean['risk_tier']}")
    print(f"Inference Latency:     {res_clean['inference_latency_ms']:.2f} ms")
    print("Top Risk Factors:")
    for f in res_clean["top_shap_features"]:
        print(f"  * {f}")

    # Scenario B: High-Risk Agent PR (deleted assertions, semantic drift, high CC)
    risky_ast = {
        "nodes_added": 140,
        "nodes_deleted": 80,
        "nodes_mutated": 55,
        "delta_cc": 14,
        "nesting_depth_delta": 4,
        "func_signatures_mod": 3,
        "classes_modified": 2,
        "ast_disturbance_index": 0.82,
        "control_flow_churn": 0.65,
    }
    risky_semantic = {
        "intent_diff_cosine": 0.31,
        "title_diff_cosine": 0.28,
        "entity_drift_jaccard": 0.78,
        "docstring_code_ratio": 0.0,
        "semantic_drift_flag": 1,
        "issue_token_length": 25,
    }
    risky_test = {
        "test_files_modified": 1,
        "test_ast_nodes_added": 0,
        "assertions_deleted": 6,
        "test_to_logic_ratio": 0.0,
        "mock_patch_count_delta": 5,
    }
    risky_process = {
        "commit_count": 8,
        "files_touched_count": 9,
        "dispersion_entropy": 2.85,
        "ci_pass_flag": 0,
        "is_known_agent_bot": 1,
    }

    v_risky = build_feature_vector(risky_ast, risky_semantic, risky_test, risky_process)
    res_risky = predictor.predict(v_risky)

    print("\n--- Scenario B: High-Risk / Drifted PR ---")
    print(f"Calibrated Risk Score: {res_risky['calibrated_risk_score']:.4f}")
    print(f"Risk Tier:             {res_risky['risk_tier']}")
    if res_risky.get("override_applied"):
        print(f"Override Triggered:    {res_risky['override_applied']}")
    print(f"Inference Latency:     {res_risky['inference_latency_ms']:.2f} ms")
    print("Top Risk Factors (SHAP Local Attribution):")
    for f in res_risky["top_shap_features"]:
        print(f"  * {f}")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="AST-Triage Model Trainer & Evaluator")
    parser.add_argument("--n-samples", type=int, default=500, help="Number of synthetic samples")
    parser.add_argument("--save-dir", type=str, default="models", help="Artifact checkpoint directory")
    parser.add_argument("--demo-predict", action="store_true", help="Run sample prediction demonstration")
    args = parser.parse_args()

    print(f"Generating {args.n_samples} synthetic pull request feature records...")
    X, y = generate_synthetic_pr_dataset(n_samples=args.n_samples, defect_ratio=0.20, random_state=42)
    print(f"Dataset shape: X={X.shape}, y={y.shape} (Defective rate: {np.mean(y):.2%})")

    print(f"Training Platt-calibrated XGBoost classifier (5-fold CV) and fitting TreeSHAP explainer...")
    train_calibrated_triage_model(X, y, save_dir=args.save_dir, random_state=42)
    print(f"Artifacts successfully saved to: {Path(args.save_dir).resolve()}")

    if args.demo_predict:
        predictor = get_predictor(model_dir=args.save_dir, reload=True)
        run_demo_predictions(predictor)


if __name__ == "__main__":
    main()
