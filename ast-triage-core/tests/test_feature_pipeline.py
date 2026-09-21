"""
tests/test_feature_pipeline.py - Complete test suite for Phase 4 ML Engine and Feature Pipeline.

Validates:
    - 28-D feature vector assembly and dtype
    - Strict feature ordering matching training columns (F01-F28)
    - Alias resolution and default fallback behavior
    - Dispersion entropy edge cases and skewness
    - Test-to-code churn and process provenance extractors
    - Feature normalizer imputation, bounds clipping, and fit-transform
    - Synthetic dataset generation distributions
    - Model evaluation metrics calculation (ROC-AUC, PR-AUC, F1, Brier Score)
    - Calibrated XGBoost classifier training with 5-fold Platt scaling
    - SHAP TreeExplainer integration and local attribution calculation
    - Fast inference runtime with RiskPredictor singleton
    - Top-3 human-readable SHAP formatting (e.g., 'assertions_deleted = 3 (+0.32 SHAP)')
    - Risk tier mapping and safety override rules
    - Robust error handling on malformed input dimensions
"""
import math
from pathlib import Path
import tempfile
import numpy as np
import pytest

from src.feature_pipeline import (
    FEATURE_BOUNDS,
    FEATURE_NAMES,
    FeatureNormalizer,
    build_feature_vector,
    calculate_dispersion_entropy,
    clip_feature_bounds,
    extract_process_metrics,
    extract_test_metrics,
    impute_missing_values,
)
from src.ml_engine import (
    RiskPredictor,
    TreeSHAPExplainer,
    evaluate_model,
    generate_synthetic_pr_dataset,
    train_calibrated_triage_model,
)


# =====================================================================
# 1. Dispersion Entropy Tests (F26)
# =====================================================================

def test_dispersion_entropy_empty_and_zero():
    assert calculate_dispersion_entropy([]) == 0.0
    assert calculate_dispersion_entropy([0]) == 0.0
    assert calculate_dispersion_entropy([0, 0, 0]) == 0.0


def test_dispersion_entropy_single_file():
    assert calculate_dispersion_entropy([100]) == 0.0
    assert calculate_dispersion_entropy([1]) == 0.0


def test_dispersion_entropy_uniform_distribution():
    # 2 files with equal 50/50 churn -> H = -(0.5*log2(0.5) + 0.5*log2(0.5)) = 1.0
    assert calculate_dispersion_entropy([50, 50]) == 1.0
    # 4 files with equal churn -> H = log2(4) = 2.0
    assert calculate_dispersion_entropy([25, 25, 25, 25]) == 2.0


def test_dispersion_entropy_skewed_distribution():
    h_uniform = calculate_dispersion_entropy([50, 50])
    h_skewed = calculate_dispersion_entropy([95, 5])
    assert 0.0 < h_skewed < h_uniform


# =====================================================================
# 2. Feature Vector Builder Tests (F01 - F28)
# =====================================================================

def test_build_feature_vector_shape_and_dtype():
    vec = build_feature_vector({}, {}, {}, {})
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (1, 28)
    assert vec.dtype == np.float32


def test_build_feature_vector_ordering():
    ast_m = {
        "nodes_added": 11,
        "nodes_deleted": 12,
        "nodes_mutated": 13,
        "delta_cc": 14,
        "nesting_depth_delta": 15,
        "func_signatures_mod": 16,
        "classes_modified": 17,
        "return_types_altered": 18,
        "call_graph_fanout_delta": 19,
        "ast_disturbance_index": 0.20,
        "try_catch_added": 21,
        "control_flow_churn": 0.22,
    }
    sem_m = {
        "intent_diff_cosine": 0.23,
        "title_diff_cosine": 0.24,
        "entity_drift_jaccard": 0.25,
        "docstring_code_ratio": 0.26,
        "semantic_drift_flag": 1,
        "issue_token_length": 28,
    }
    test_m = {
        "test_files_modified": 29,
        "test_ast_nodes_added": 30,
        "assertions_deleted": 31,
        "test_to_logic_ratio": 0.32,
        "mock_patch_count_delta": 33,
    }
    proc_m = {
        "commit_count": 34,
        "files_touched_count": 35,
        "dispersion_entropy": 0.36,
        "ci_pass_flag": 1,
        "is_known_agent_bot": 0,
    }

    vec = build_feature_vector(ast_m, sem_m, test_m, proc_m)

    # Check that indices match canonical order
    assert vec[0, 0] == 11.0  # nodes_added
    assert vec[0, 3] == 14.0  # delta_cc
    assert vec[0, 9] == pytest.approx(0.20, abs=1e-4)  # ast_disturbance_index
    assert vec[0, 11] == pytest.approx(0.22, abs=1e-4) # control_flow_churn
    assert vec[0, 12] == pytest.approx(0.23, abs=1e-4) # intent_diff_cosine
    assert vec[0, 16] == 1.0  # semantic_drift_flag
    assert vec[0, 20] == 31.0 # assertions_deleted
    assert vec[0, 23] == 34.0 # commit_count
    assert vec[0, 27] == 0.0  # is_known_agent_bot


def test_build_feature_vector_alias_resolution():
    # Database column names with 'fNN_' prefix
    db_metrics = {
        "f01_ast_nodes_added": 42,
        "f04_cyclomatic_delta": 7,
        "f10_ast_disturbance_index": 0.65,
        "f13_intent_diff_cosine_sim": 0.81,
        "f17_semantic_drift_flag": 0,
        "f21_test_assertions_deleted": 3,
        "f26_file_dispersion_entropy": 1.45,
        "f28_is_known_agent_bot": 1,
    }
    vec = build_feature_vector(ast_metrics=db_metrics)
    assert vec[0, 0] == 42.0
    assert vec[0, 3] == 7.0
    assert vec[0, 9] == pytest.approx(0.65, abs=1e-4)
    assert vec[0, 12] == pytest.approx(0.81, abs=1e-4)
    assert vec[0, 16] == 0.0
    assert vec[0, 20] == 3.0
    assert vec[0, 25] == pytest.approx(1.45, abs=1e-4)
    assert vec[0, 27] == 1.0


def test_build_feature_vector_defaults_for_missing():
    vec = build_feature_vector()
    assert vec.shape == (1, 28)
    # Default commit_count and files_touched_count should be at least 1.0
    assert vec[0, 23] >= 1.0
    assert vec[0, 24] >= 1.0
    # ci_pass_flag defaults to 1.0
    assert vec[0, 26] == 1.0


# =====================================================================
# 3. Test and Process Metric Extractor Tests
# =====================================================================

def test_extract_test_metrics_from_diff():
    diff = """
diff --git a/src/logic.py b/src/logic.py
--- a/src/logic.py
+++ b/src/logic.py
@@ -1,3 +1,5 @@
+def new_feature():
+    return True
diff --git a/tests/test_logic.py b/tests/test_logic.py
--- a/tests/test_logic.py
+++ b/tests/test_logic.py
@@ -10,4 +10,6 @@ def test_feature():
-    assert old_behavior() == 1
+    from unittest.mock import patch
+    assert new_feature() is True
"""
    metrics = extract_test_metrics(diff)
    assert metrics["test_files_modified"] == 1
    assert metrics["assertions_deleted"] == 1
    assert metrics["mock_patch_count_delta"] == 1
    assert metrics["test_ast_nodes_added"] > 0
    assert metrics["test_to_logic_ratio"] > 0.0


def test_extract_process_metrics():
    # Bot detection via username
    metrics_bot = extract_process_metrics(
        commit_count=3,
        files_touched=["a.py", "b.py"],
        file_churns=[10, 20],
        ci_passed=True,
        author_login="copilot-sweeper[bot]",
    )
    assert metrics_bot["is_known_agent_bot"] == 1
    assert metrics_bot["ci_pass_flag"] == 1
    assert metrics_bot["files_touched_count"] == 2
    assert metrics_bot["commit_count"] == 3
    assert metrics_bot["dispersion_entropy"] > 0.0

    # Human developer
    metrics_human = extract_process_metrics(
        commit_count=1,
        files_touched=["main.py"],
        file_churns=[50],
        ci_passed=False,
        author_login="octocat",
    )
    assert metrics_human["is_known_agent_bot"] == 0
    assert metrics_human["ci_pass_flag"] == 0


# =====================================================================
# 4. Feature Normalizer and Bounds Tests
# =====================================================================

def test_impute_missing_values():
    arr = np.array([1.0, np.nan, np.inf, -np.inf, 5.0], dtype=np.float32)
    clean = impute_missing_values(arr, fill_value=0.0)
    assert not np.any(np.isnan(clean))
    assert not np.any(np.isinf(clean))
    assert clean[1] == 0.0


def test_clip_feature_bounds():
    # Row with out-of-bound values
    vec = np.zeros(28, dtype=np.float32)
    vec[3] = 100.0   # delta_cc bound [-50, 50]
    vec[9] = 1.85    # ast_disturbance_index bound [0.0, 1.0]
    vec[12] = -2.5   # intent_diff_cosine bound [-1.0, 1.0]
    vec[26] = 5.0    # ci_pass_flag bound [0, 1]

    clipped = clip_feature_bounds(vec)
    assert clipped[3] == 50.0
    assert clipped[9] == 1.0
    assert clipped[12] == -1.0
    assert clipped[26] == 1.0


def test_feature_normalizer_pipeline():
    normalizer = FeatureNormalizer()
    X = np.random.randn(20, 28).astype(np.float32)
    X[0, 0] = np.nan
    X[1, 9] = 2.5

    X_trans = normalizer.fit_transform(X)
    assert not np.any(np.isnan(X_trans))
    assert np.all(X_trans[:, 9] <= 1.0)


# =====================================================================
# 5. Model Training, Calibration & SHAP Tests
# =====================================================================

def test_synthetic_dataset_generation():
    X, y = generate_synthetic_pr_dataset(n_samples=100, defect_ratio=0.25, random_state=42)
    assert X.shape == (100, 28)
    assert y.shape == (100,)
    assert np.sum(y) == 25
    # Defective PRs should exhibit higher mean cyclomatic delta than clean PRs
    clean_cc = np.mean(X[y == 0, 3])
    defect_cc = np.mean(X[y == 1, 3])
    assert defect_cc > clean_cc


def test_evaluate_model():
    y_true = np.array([0, 0, 0, 0, 1, 1])
    y_pred_prob = np.array([0.1, 0.2, 0.15, 0.3, 0.85, 0.9])
    metrics = evaluate_model(y_true, y_pred_prob, print_summary=False)

    assert "roc_auc" in metrics
    assert "pr_auc" in metrics
    assert "f1" in metrics
    assert "brier_score" in metrics
    assert metrics["roc_auc"] == 1.0
    assert metrics["brier_score"] < 0.10


def test_train_calibrated_triage_model_and_persistence():
    with tempfile.TemporaryDirectory() as tmp_dir:
        X, y = generate_synthetic_pr_dataset(n_samples=120, defect_ratio=0.25, random_state=42)

        model, explainer, metrics = train_calibrated_triage_model(
            X, y,
            save_dir=tmp_dir,
            random_state=42,
            n_estimators=30,
            max_depth=3,
        )

        assert model is not None
        assert explainer is not None
        assert metrics["brier_score"] < 0.25

        # Check saved files
        saved_model = Path(tmp_dir) / "calibrated_triage_xgb.joblib"
        saved_explainer = Path(tmp_dir) / "shap_explainer.joblib"
        saved_meta = Path(tmp_dir) / "feature_meta.joblib"

        assert saved_model.exists()
        assert saved_explainer.exists()
        assert saved_meta.exists()

        # Test TreeSHAPExplainer wrapper
        explainer_wrapper = TreeSHAPExplainer(explainer=explainer, feature_names=FEATURE_NAMES)
        sample = X[:1]
        attributions = explainer_wrapper.compute_attributions(sample)
        assert len(attributions) == 28
        assert "feature_name" in attributions[0]
        assert "shap_value" in attributions[0]

        top_drivers = explainer_wrapper.get_top_risk_drivers(sample, top_k=3)
        assert len(top_drivers) == 3

        formatted_strings = explainer_wrapper.format_risk_driver_strings(sample, top_k=3)
        assert len(formatted_strings) == 3
        assert "SHAP" in formatted_strings[0]


# =====================================================================
# 6. Risk Predictor Runtime Tests
# =====================================================================

def test_risk_predictor_inference():
    with tempfile.TemporaryDirectory() as tmp_dir:
        X, y = generate_synthetic_pr_dataset(n_samples=120, defect_ratio=0.25, random_state=42)
        train_calibrated_triage_model(
            X, y,
            save_dir=tmp_dir,
            random_state=42,
            n_estimators=30,
            max_depth=3,
        )

        predictor = RiskPredictor(model_dir=tmp_dir)

        # Clean PR vector (index 0 is clean)
        clean_sample = X[0]
        result_clean = predictor.predict(clean_sample)

        assert 0.0 <= result_clean["calibrated_risk_score"] <= 1.0
        assert result_clean["risk_tier"] in ["LOW", "MEDIUM", "HIGH"]
        assert len(result_clean["top_shap_features"]) == 3
        assert result_clean["inference_latency_ms"] >= 0.0

        # High-risk PR sample (index -1 is defective)
        defect_sample = X[-1]
        result_defect = predictor.predict(defect_sample)
        assert result_defect["calibrated_risk_score"] > result_clean["calibrated_risk_score"]


def test_risk_predictor_hard_overrides():
    with tempfile.TemporaryDirectory() as tmp_dir:
        X, y = generate_synthetic_pr_dataset(n_samples=120, defect_ratio=0.25, random_state=42)
        train_calibrated_triage_model(
            X, y,
            save_dir=tmp_dir,
            random_state=42,
            n_estimators=30,
            max_depth=3,
        )

        predictor = RiskPredictor(model_dir=tmp_dir)

        # Override 1: Semantic drift flag = 1 (feature index 16)
        test_vec = np.zeros(28, dtype=np.float32)
        test_vec[16] = 1.0
        res = predictor.predict(test_vec, check_hard_overrides=True)
        assert res["risk_tier"] == "HIGH"
        assert "Semantic drift override" in (res["override_applied"] or "")

        # Override 2: Deleted assertions without test additions (F21 > 5, F20 == 0)
        test_vec2 = np.zeros(28, dtype=np.float32)
        test_vec2[20] = 7.0  # assertions_deleted
        test_vec2[19] = 0.0  # test_ast_nodes_added
        res2 = predictor.predict(test_vec2, check_hard_overrides=True)
        assert res2["risk_tier"] == "HIGH"
        assert "Assertion deletion anomaly" in (res2["override_applied"] or "")


def test_risk_predictor_invalid_dimension():
    with tempfile.TemporaryDirectory() as tmp_dir:
        X, y = generate_synthetic_pr_dataset(n_samples=120, defect_ratio=0.25, random_state=42)
        train_calibrated_triage_model(X, y, save_dir=tmp_dir, n_estimators=20, max_depth=2)

        predictor = RiskPredictor(model_dir=tmp_dir)
        invalid_vec = np.zeros((1, 15), dtype=np.float32)
        with pytest.raises(ValueError, match="Expected 28 features"):
            predictor.predict(invalid_vec)
