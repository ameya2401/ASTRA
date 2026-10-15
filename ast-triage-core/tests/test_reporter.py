"""
tests/test_reporter.py - Unit tests for GitHub PR comment and summary reporting.
"""
import pytest
from src.api.schemas import SHAPExplanationItem, TriageResponse
from src.integrations.reporter import format_risk_summary, generate_markdown_report


@pytest.fixture
def mock_triage_response() -> TriageResponse:
    """Provides a sample TriageResponse fixture."""
    return TriageResponse(
        pr_number=42,
        repo_name="ameya2401/ASTRA",
        risk_probability=0.125,
        raw_risk_score=-1.94,
        risk_tier="LOW",
        recommendation="FAST-TRACK: High structural integrity, intent aligned, tests verified.",
        top_risk_drivers=[
            SHAPExplanationItem(
                feature_name="intent_diff_cosine",
                shap_value=-0.0456,
                description="intent_diff_cosine = 0.91 (DECREASES_RISK)",
                feature_value=0.91,
                impact="DECREASES_RISK",
            ),
            SHAPExplanationItem(
                feature_name="f04_cyclomatic_delta",
                shap_value=0.0123,
                description="f04_cyclomatic_delta = 1 (INCREASES_RISK)",
                feature_value=1.0,
                impact="INCREASES_RISK",
            ),
        ],
        latency_ms=45.2,
        override_applied=None,
    )


def test_generate_markdown_report(mock_triage_response):
    """Verifies markdown formatting, badges, and collapsible details."""
    report = generate_markdown_report(mock_triage_response, "ameya2401/ASTRA", 42)

    assert "## ASTRA Automated Triage Report" in report
    assert "LOW RISK" in report
    assert "12.5%" in report
    assert "intent_diff_cosine" in report
    assert "FAST-TRACK" in report


def test_format_risk_summary(mock_triage_response):
    """Verifies structured dictionary extraction for notification consumers."""
    summary = format_risk_summary(mock_triage_response)

    assert summary["pr_number"] == 42
    assert summary["repo_name"] == "ameya2401/ASTRA"
    assert summary["risk_tier"] == "LOW"
    assert summary["risk_percent"] == 12.5
    assert "intent_diff_cosine" in summary["primary_drivers"]
    assert summary["latency_ms"] == 45.2
