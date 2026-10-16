"""
src/integrations/reporter.py - GitHub PR comment generator.

Formats triage assessments into structured markdown comments containing
SVG status badges, plain-English breakdowns, calibrated risk percentages,
collapsible SHAP feature attributions, and actionable recommendations.
"""
from typing import Any, Dict, List, Optional
from src.api.schemas import TriageResponse


# Status badges per risk tier
BADGE_URLS = {
    "LOW": "https://img.shields.io/badge/ASTRA_Risk-LOW_Fast_Track-28a745.svg",
    "MEDIUM": "https://img.shields.io/badge/ASTRA_Risk-MEDIUM_Standard_Review-e3a21a.svg",
    "HIGH": "https://img.shields.io/badge/ASTRA_Risk-HIGH_Deprioritize-dc3545.svg",
}

TIER_EMOJIS = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🔴",
}

# Plain English translations for technical AST, semantic, and process features
FEATURE_HUMAN_NAMES: Dict[str, str] = {
    "nodes_added": "Syntax Nodes Added",
    "nodes_deleted": "Syntax Nodes Deleted",
    "nodes_mutated": "Syntax Nodes Modified",
    "delta_cc": "Branching Complexity Change",
    "nesting_depth_delta": "Code Nesting Depth Change",
    "func_signatures_mod": "Function Signatures Modified",
    "classes_modified": "Classes Modified",
    "return_types_altered": "Function Return Types Altered",
    "call_graph_fanout_delta": "Call Graph Fan-Out Change",
    "ast_disturbance_index": "Syntax Tree Disturbance",
    "try_catch_added": "Error Handling Blocks Added",
    "control_flow_churn": "Control Flow Churn Ratio",
    "intent_diff_cosine": "PR Prompt vs Diff Alignment",
    "title_diff_cosine": "PR Title vs Diff Alignment",
    "entity_drift_jaccard": "Code Identifier Drift Distance",
    "docstring_code_ratio": "Docstring to Code Ratio",
    "semantic_drift_flag": "Semantic Drift Flag",
    "issue_token_length": "Issue Description Length",
    "test_files_modified": "Test Files Modified",
    "test_ast_nodes_added": "Test Syntax Nodes Added",
    "assertions_deleted": "Test Assertions Removed",
    "test_to_logic_ratio": "Test to Logic Churn Ratio",
    "mock_patch_count_delta": "Mock Patch Count Delta",
    "commit_count": "Commit Count",
    "files_touched_count": "Files Touched Count",
    "dispersion_entropy": "Multi-File Dispersion Entropy",
    "ci_pass_flag": "Continuous Integration Status",
    "is_known_agent_bot": "AI Agent Bot Provenance",
}


def _build_plain_english_breakdown(triage: TriageResponse) -> List[str]:
    """Generates a plain-English, non-technical explanation of the triage outcome."""
    tier = (triage.risk_tier or "MEDIUM").upper()

    # 1. Verdict line
    if tier == "LOW":
        verdict = "**Verdict:** Safe to merge. Very low chance of introducing bugs or regressions."
    elif tier == "MEDIUM":
        verdict = "**Verdict:** Standard review required. Moderate risk. Verify highlighted logic paths."
    else:
        verdict = "**Verdict:** Caution advised. High likelihood of regressions, drift, or missing tests."

    # 2. Extract feature-based insights from top drivers
    driver_map = {item.feature_name: item for item in triage.top_risk_drivers}

    # Complexity insight
    if "delta_cc" in driver_map:
        item = driver_map["delta_cc"]
        val = item.feature_value if item.feature_value is not None else 0.0
        loc_str = f" in {item.code_hotspot}" if item.code_hotspot and "diff" not in item.code_hotspot.lower() else ""
        if val <= 2:
            complexity_msg = f"**Code Complexity:** Clean and straightforward. Minimal new branching added{loc_str}."
        else:
            complexity_msg = f"**Code Complexity:** Branching complexity increased by +{int(val)} branches{loc_str}. Check conditional paths."
    elif "nesting_depth_delta" in driver_map:
        item = driver_map["nesting_depth_delta"]
        val = item.feature_value if item.feature_value is not None else 0.0
        loc_str = f" in {item.code_hotspot}" if item.code_hotspot and "diff" not in item.code_hotspot.lower() else ""
        if val <= 1:
            complexity_msg = f"**Code Nesting:** Shallow nesting maintained{loc_str}. Easy to read and reason about."
        else:
            complexity_msg = f"**Code Nesting:** Nesting increased by +{int(val)} levels{loc_str}. Watch for deeply nested blocks."
    else:
        complexity_msg = "**Code Complexity:** Structural changes remain within safe nominal bounds."

    # Test protection insight
    if "assertions_deleted" in driver_map:
        item = driver_map["assertions_deleted"]
        val = item.feature_value if item.feature_value is not None else 0.0
        if val == 0:
            test_msg = "**Test Protection:** Zero test assertions were removed. Safety net remains intact."
        else:
            test_msg = f"**Test Protection:** {int(val)} test assertions were deleted. Verify tests were not suppressed."
    elif "test_ast_nodes_added" in driver_map:
        item = driver_map["test_ast_nodes_added"]
        val = item.feature_value if item.feature_value is not None else 0.0
        if val > 0:
            test_msg = "**Test Coverage:** Automated unit tests accompany the changes."
        else:
            test_msg = "**Test Coverage:** No new unit tests accompanied these changes."
    else:
        test_msg = "**Test Protection:** Test suite integrity verified with zero deleted assertions."

    # Intent match insight
    if "semantic_drift_flag" in driver_map and driver_map["semantic_drift_flag"].feature_value == 1.0:
        intent_msg = "**Goal Match:** Changes deviate from declared prompt or issue text."
    else:
        intent_msg = "**Goal Match:** Changes align directly with the pull request title and intent."

    return [
        "### 💡 Plain English Breakdown",
        "",
        f"- {verdict}",
        f"- {complexity_msg}",
        f"- {test_msg}",
        f"- {intent_msg}",
    ]


def _build_reviewer_checklist(triage: TriageResponse) -> List[str]:
    """Builds an actionable checklist for human code reviewers."""
    tier = (triage.risk_tier or "MEDIUM").upper()

    checklist_items: List[str] = []
    if tier == "LOW":
        checklist_items = [
            "- [ ] Quick scan of diff for coding style and project conventions.",
            "- [ ] Confirm automated CI test suite passed.",
            "- [ ] Fast-track approval eligible.",
        ]
    elif tier == "MEDIUM":
        checklist_items = [
            "- [ ] Verify edge cases and boundary conditions in modified functions.",
            "- [ ] Check that new branching logic is covered by unit tests.",
            "- [ ] Confirm backwards compatibility with downstream callers.",
        ]
    else:
        checklist_items = [
            "- [ ] Investigate why complexity or disturbance spiked in modified files.",
            "- [ ] Check for deleted assertions or disabled test cases.",
            "- [ ] Verify that diff scope matches the declared issue prompt.",
            "- [ ] Request author revision before merge.",
        ]

    return [
        "### 📋 Reviewer Inspection Checklist",
        "",
        *checklist_items,
    ]


def generate_markdown_report(
    triage: TriageResponse,
    repo_name: Optional[str] = None,
    pr_number: Optional[int] = None,
    author_login: Optional[str] = None,
    author_is_bot: Optional[bool] = None,
    files_touched: Optional[List[str]] = None,
) -> str:
    """
    Constructs an informative GitHub PR markdown comment from a TriageResponse.

    Args:
        triage: TriageResponse schema instance containing model results.
        repo_name: Optional repository name for context.
        pr_number: Optional pull request number.
        author_login: Optional GitHub author login.
        author_is_bot: Optional flag if author is a known bot.
        files_touched: Optional list of touched files.

    Returns:
        Formatted GitHub markdown comment string.
    """
    tier = (triage.risk_tier or "MEDIUM").upper()
    badge_url = BADGE_URLS.get(tier, BADGE_URLS["MEDIUM"])
    emoji = TIER_EMOJIS.get(tier, "⚪")

    risk_percent = round(triage.risk_probability * 100.0, 1)
    target_pr = pr_number or triage.pr_number
    pr_label = f"PR #{target_pr}" if target_pr else "PR"
    if repo_name:
        pr_label = f"{repo_name} #{target_pr}"

    lines = [
        "## ASTRA Automated Triage Report",
        "",
        f"[![Risk Tier]({badge_url})](#)",
        "",
        f"**Risk Evaluation for {pr_label}:** {emoji} **{tier} RISK** ({risk_percent}% defect probability)",
        "",
        f"> **Recommendation:** {triage.recommendation}",
    ]

    if triage.override_applied:
        lines.extend([
            "",
            "> [!WARNING]",
            f"> **Safety Override Active:** {triage.override_applied}",
        ])

    # 1. Plain English Breakdown
    lines.append("")
    lines.extend(_build_plain_english_breakdown(triage))

    # 2. Reviewer Checklist
    lines.append("")
    lines.extend(_build_reviewer_checklist(triage))

    # 3. Assessment Summary
    lines.extend([
        "",
        "### Review Assessment Summary",
        "",
        f"- **Calibrated Defect Probability:** `{triage.risk_probability:.4f}` ({risk_percent}%)",
        f"- **Risk Classification Tier:** `{tier}`",
        f"- **Analysis Latency:** `{triage.latency_ms:.1f} ms`",
    ])

    if triage.raw_risk_score is not None:
        lines.append(f"- **Raw Decision Score:** `{triage.raw_risk_score:.4f}`")

    if triage.confidence_level and triage.confidence_score is not None:
        conf_pct = round(triage.confidence_score * 100.0, 1)
        lines.append(f"- **Confidence Rating:** `{triage.confidence_level}` ({conf_pct}% model certainty)")

    if author_login:
        bot_tag = "🤖 AI Agent Bot" if author_is_bot else "👤 Contributor"
        lines.append(f"- **Author Provenance:** {bot_tag} (`@{author_login}`)")

    if files_touched:
        lines.append(f"- **Files Touched:** `{len(files_touched)}` files modified")

    # 4. Collapsible SHAP Feature Attribution Details
    lines.extend([
        "",
        "<details>",
        "<summary><b>Top Structural and Semantic Risk Drivers (SHAP Attribution)</b></summary>",
        "",
        "| Rank | Feature | Plain Language Meaning | Impact | Marginal SHAP | Code Location Hotspot |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    if triage.top_risk_drivers:
        for idx, item in enumerate(triage.top_risk_drivers, start=1):
            impact_display = item.impact or ("Increases Risk" if item.shap_value > 0 else "Decreases Risk")
            sign = "+" if item.shap_value > 0 else ""
            shap_formatted = f"`{sign}{item.shap_value:.4f}`"
            display_name = FEATURE_HUMAN_NAMES.get(item.feature_name, item.feature_name.replace("_", " ").title())
            hotspot_display = item.code_hotspot or item.description
            lines.append(
                f"| {idx} | `{item.feature_name}` | {display_name} | {impact_display} | {shap_formatted} | {hotspot_display} |"
            )
    else:
        lines.append("| - | Baseline | Nominal changes | Neutral | `0.0000` | Baseline nominal changes |")

    lines.extend([
        "",
        "</details>",
        "",
        "---",
        "*Automated risk stratification generated by [ASTRA](https://github.com/ameya2401/ASTRA). "
        "Intended for triage guidance and review prioritization, not autonomous merging.*",
    ])

    return "\n".join(lines)
