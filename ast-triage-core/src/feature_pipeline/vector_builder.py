"""
src/feature_pipeline/vector_builder.py - 28-dimensional feature vector assembly.

Aggregates AST metrics (F01-F12), semantic metrics (F13-F18), test metrics (F19-F23),
and process provenance metrics (F24-F28) into a structured NumPy vector for XGBoost inference.
"""
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np


# Exact 28 feature names strictly matching model training column order (F01 - F28)
FEATURE_NAMES: List[str] = [
    "nodes_added",
    "nodes_deleted",
    "nodes_mutated",
    "delta_cc",
    "nesting_depth_delta",
    "func_signatures_mod",
    "classes_modified",
    "return_types_altered",
    "call_graph_fanout_delta",
    "ast_disturbance_index",
    "try_catch_added",
    "control_flow_churn",
    "intent_diff_cosine",
    "title_diff_cosine",
    "entity_drift_jaccard",
    "docstring_code_ratio",
    "semantic_drift_flag",
    "issue_token_length",
    "test_files_modified",
    "test_ast_nodes_added",
    "assertions_deleted",
    "test_to_logic_ratio",
    "mock_patch_count_delta",
    "commit_count",
    "files_touched_count",
    "dispersion_entropy",
    "ci_pass_flag",
    "is_known_agent_bot",
]

# Aliases mapping canonical names to database column names and common alternate keys
FEATURE_ALIASES: Dict[str, List[str]] = {
    "nodes_added": ["nodes_added", "f01_ast_nodes_added"],
    "nodes_deleted": ["nodes_deleted", "f02_ast_nodes_deleted"],
    "nodes_mutated": ["nodes_mutated", "f03_ast_nodes_mutated"],
    "delta_cc": ["delta_cc", "cyclomatic_delta", "f04_cyclomatic_delta"],
    "nesting_depth_delta": ["nesting_depth_delta", "f05_max_nesting_depth_delta"],
    "func_signatures_mod": ["func_signatures_mod", "f06_func_signatures_modified"],
    "classes_modified": ["classes_modified", "f07_classes_modified"],
    "return_types_altered": ["return_types_altered", "f08_return_types_altered"],
    "call_graph_fanout_delta": ["call_graph_fanout_delta", "f09_call_graph_fan_out_delta"],
    "ast_disturbance_index": ["ast_disturbance_index", "f10_ast_disturbance_index"],
    "try_catch_added": ["try_catch_added", "f11_try_catch_blocks_added"],
    "control_flow_churn": ["control_flow_churn", "control_flow_churn_ratio", "f12_control_flow_churn_ratio"],
    "intent_diff_cosine": ["intent_diff_cosine", "f13_intent_diff_cosine_sim", "intent_diff_cosine_sim"],
    "title_diff_cosine": ["title_diff_cosine", "f14_issue_title_diff_sim", "issue_title_diff_sim"],
    "entity_drift_jaccard": ["entity_drift_jaccard", "f15_entity_drift_jaccard"],
    "docstring_code_ratio": ["docstring_code_ratio", "f16_docstring_to_code_ratio"],
    "semantic_drift_flag": ["semantic_drift_flag", "f17_semantic_drift_flag"],
    "issue_token_length": ["issue_token_length", "f18_issue_token_length"],
    "test_files_modified": ["test_files_modified", "f19_test_files_modified"],
    "test_ast_nodes_added": ["test_ast_nodes_added", "f20_test_ast_nodes_added"],
    "assertions_deleted": ["assertions_deleted", "test_assertions_deleted", "f21_test_assertions_deleted"],
    "test_to_logic_ratio": ["test_to_logic_ratio", "f22_test_to_logic_ratio"],
    "mock_patch_count_delta": ["mock_patch_count_delta", "f23_mock_patch_count_delta"],
    "commit_count": ["commit_count", "f24_commit_count"],
    "files_touched_count": ["files_touched_count", "f25_files_touched_count"],
    "dispersion_entropy": ["dispersion_entropy", "file_dispersion_entropy", "f26_file_dispersion_entropy"],
    "ci_pass_flag": ["ci_pass_flag", "f27_ci_pass_flag"],
    "is_known_agent_bot": ["is_known_agent_bot", "f28_is_known_agent_bot"],
}

# Known AI bot signatures for provenance detection (F28)
KNOWN_AGENT_BOTS = {
    "devin",
    "claude",
    "copilot",
    "openhands",
    "github-actions[bot]",
    "copilot-sweeper[bot]",
    "agent",
}


def calculate_dispersion_entropy(file_churns: Sequence[int]) -> float:
    """
    Calculates Shannon dispersion entropy across touched files:
    H = -sum(p_i * log2(p_i)) where p_i = Delta LOC_i / sum(Delta LOC).

    Args:
        file_churns: Sequence of line changes (added + deleted) per file.

    Returns:
        Entropy rounded to 4 decimal places. 0.0 if total churn is 0 or 1 file touched.
    """
    valid_churns = [c for c in file_churns if c > 0]
    total_churn = sum(valid_churns)
    if total_churn == 0 or len(valid_churns) <= 1:
        return 0.0

    entropy = 0.0
    for churn in valid_churns:
        p = churn / total_churn
        entropy -= p * math.log2(p)
    return round(float(entropy), 4)


def extract_test_metrics(
    raw_diff: str,
    ast_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extracts test churn and asymmetry metrics (F19-F23) from a unified diff.

    Args:
        raw_diff: Unified diff string across the pull request.
        ast_metrics: Optional pre-extracted AST metrics for node counts.

    Returns:
        Dictionary with test metrics: test_files_modified, test_ast_nodes_added,
        assertions_deleted, test_to_logic_ratio, and mock_patch_count_delta.
    """
    if not raw_diff:
        return {
            "test_files_modified": 0,
            "test_ast_nodes_added": 0,
            "assertions_deleted": 0,
            "test_to_logic_ratio": 0.0,
            "mock_patch_count_delta": 0,
        }

    test_files_modified = 0
    test_added_lines = 0
    prod_added_lines = 0
    assertions_deleted = 0
    mock_patch_count_delta = 0

    is_in_test_file = False
    file_header_pattern = re.compile(r"^diff --git a/(\S+) b/(\S+)")

    for line in raw_diff.splitlines():
        match = file_header_pattern.match(line)
        if match:
            filepath = match.group(2).lower()
            if "test" in filepath or "tests" in filepath:
                test_files_modified += 1
                is_in_test_file = True
            else:
                is_in_test_file = False
            continue

        if line.startswith("+") and not line.startswith("+++"):
            if is_in_test_file:
                test_added_lines += 1
            else:
                prod_added_lines += 1

            line_lower = line.lower()
            if "patch" in line_lower or "mock" in line_lower or "monkeypatch" in line_lower:
                mock_patch_count_delta += 1

        elif line.startswith("-") and not line.startswith("---"):
            if is_in_test_file and "assert " in line:
                assertions_deleted += 1

    # Approximate AST nodes added if AST metrics provided
    if ast_metrics and "nodes_added" in ast_metrics:
        total_nodes_added = ast_metrics.get("nodes_added", 0)
        total_lines = max(1, test_added_lines + prod_added_lines)
        test_fraction = test_added_lines / total_lines
        test_ast_nodes_added = int(total_nodes_added * test_fraction)
    else:
        test_ast_nodes_added = test_added_lines

    # Target test to logic ratio
    denom = (ast_metrics.get("nodes_added", prod_added_lines) if ast_metrics else prod_added_lines) + 1.0
    test_to_logic_ratio = round(test_ast_nodes_added / max(1.0, float(denom)), 4)

    return {
        "test_files_modified": test_files_modified,
        "test_ast_nodes_added": test_ast_nodes_added,
        "assertions_deleted": assertions_deleted,
        "test_to_logic_ratio": test_to_logic_ratio,
        "mock_patch_count_delta": mock_patch_count_delta,
    }


def extract_process_metrics(
    commit_count: int = 1,
    files_touched: Optional[List[str]] = None,
    file_churns: Optional[List[int]] = None,
    ci_passed: Optional[bool] = True,
    author_is_bot: bool = False,
    author_login: str = "",
) -> Dict[str, Any]:
    """
    Extracts process and provenance metrics (F24-F28).

    Args:
        commit_count: Number of commits in the PR.
        files_touched: List of distinct touched file paths.
        file_churns: List of line change counts per file for dispersion entropy.
        ci_passed: True if CI passed, False if failed, None treated as 0.
        author_is_bot: Explicit bot flag from GitHub PR payload.
        author_login: Author username for pattern matching.

    Returns:
        Dictionary with process metrics: commit_count, files_touched_count,
        dispersion_entropy, ci_pass_flag, and is_known_agent_bot.
    """
    touched_count = len(files_touched) if files_touched else (len(file_churns) if file_churns else 1)
    dispersion_entropy = calculate_dispersion_entropy(file_churns or [1])

    is_bot = 1 if author_is_bot else 0
    if not is_bot and author_login:
        login_lower = author_login.lower()
        if login_lower.endswith("[bot]") or any(sig in login_lower for sig in KNOWN_AGENT_BOTS):
            is_bot = 1

    ci_flag = 1 if ci_passed is True else 0

    return {
        "commit_count": max(1, int(commit_count)),
        "files_touched_count": max(1, int(touched_count)),
        "dispersion_entropy": dispersion_entropy,
        "ci_pass_flag": ci_flag,
        "is_known_agent_bot": is_bot,
    }


def _get_metric_val(source_dict: Dict[str, Any], canonical_name: str, default: float = 0.0) -> float:
    """Helper to look up a metric value using canonical name and aliases."""
    aliases = FEATURE_ALIASES.get(canonical_name, [canonical_name])
    for alias in aliases:
        if alias in source_dict and source_dict[alias] is not None:
            val = source_dict[alias]
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
    return default


def build_feature_vector(
    ast_metrics: Optional[Dict[str, Any]] = None,
    semantic_metrics: Optional[Dict[str, Any]] = None,
    test_metrics: Optional[Dict[str, Any]] = None,
    process_metrics: Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Constructs an exact 28-dimensional feature vector for XGBoost inference.

    Merges inputs from AST, semantic, test, and process metric dictionaries.
    Feature order strictly matches FEATURE_NAMES (F01 through F28).

    Args:
        ast_metrics: F01-F12 structural metrics.
        semantic_metrics: F13-F18 NLP intent metrics.
        test_metrics: F19-F23 test churn metrics.
        process_metrics: F24-F28 provenance and process metrics.

    Returns:
        NumPy array of shape (1, 28) with dtype float32.
    """
    merged: Dict[str, Any] = {}
    if ast_metrics:
        merged.update(ast_metrics)
    if semantic_metrics:
        merged.update(semantic_metrics)
    if test_metrics:
        merged.update(test_metrics)
    if process_metrics:
        merged.update(process_metrics)

    vector: List[float] = []

    for name in FEATURE_NAMES:
        # Sensible defaults based on feature type
        default_val = 0.0
        if name == "commit_count" or name == "files_touched_count":
            default_val = 1.0
        elif name == "ci_pass_flag":
            default_val = 1.0

        val = _get_metric_val(merged, name, default=default_val)
        vector.append(val)

    arr = np.array(vector, dtype=np.float32).reshape(1, -1)
    return arr
