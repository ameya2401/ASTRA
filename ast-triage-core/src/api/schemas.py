"""
src/api/schemas.py - Pydantic request and response schemas.

Defines validated data transfer objects for webhook payloads,
triage assessments, SHAP explanations, queue items, and health checks.
Strictly conforms to Pydantic v2 conventions.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SHAPExplanationItem(BaseModel):
    """
    Attribution record for an individual feature from TreeSHAP.

    Captures the feature name, its numerical value, its marginal Shapley value,
    and a human-readable description for developer feedback.
    """
    model_config = ConfigDict(extra="ignore")

    feature_name: str = Field(..., description="Canonical feature name (e.g. assertions_deleted)")
    shap_value: float = Field(..., description="Marginal Shapley attribution value")
    description: str = Field(..., description="Human-readable impact description")
    feature_value: Optional[float] = Field(None, description="Actual observed feature value in PR")
    impact: Optional[str] = Field(None, description="Directional impact: INCREASES_RISK or DECREASES_RISK")


class PRWebhookPayload(BaseModel):
    """
    Input schema for incoming pull request analysis requests.

    Captures context needed across AST differencing, semantic drift calculation,
    test churn analysis, and author provenance features.
    """
    model_config = ConfigDict(extra="ignore")

    repo_name: str = Field(..., description="Repository name in owner/repo format", examples=["django/django"])
    pr_number: int = Field(..., ge=1, description="Pull request number", examples=[101])
    title: str = Field(..., description="Pull request title", examples=["Fix unhandled ZeroDivisionError in Cart"])
    issue_description: str = Field(..., description="Issue specification or prompt provided to the agent")
    author_login: str = Field(default="", description="GitHub username or bot login")
    author_is_bot: bool = Field(default=False, description="Flag indicating if the author is a known bot")
    agent_framework: str = Field(default="unknown", description="Agent tool identifier (devin, copilot, claude-code)")
    base_sha: str = Field(default="", description="Base commit SHA before PR changes")
    head_sha: str = Field(default="", description="Head commit SHA for the PR")
    raw_diff: str = Field(default="", description="Unified git diff content")
    ci_passed: Optional[bool] = Field(default=True, description="Continuous integration status")
    files_touched: Optional[List[str]] = Field(default=None, description="List of modified file paths")
    file_churns: Optional[List[int]] = Field(default=None, description="Line churn counts per file")
    commit_count: Optional[int] = Field(default=1, ge=1, description="Number of commits in the pull request")


class TriageResponse(BaseModel):
    """
    Complete risk assessment response returned by the triage API.

    Contains the calibrated risk probability, categorical risk tier,
    human-actionable recommendation, top risk-increasing SHAP features,
    and end-to-end inference latency.
    """
    model_config = ConfigDict(extra="ignore")

    pr_number: int = Field(..., description="Pull request number")
    repo_name: Optional[str] = Field(default=None, description="Repository name")
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Platt-calibrated defect probability")
    raw_risk_score: Optional[float] = Field(default=None, description="Uncalibrated model logit")
    risk_tier: str = Field(..., description="Categorical tier: LOW, MEDIUM, or HIGH")
    recommendation: str = Field(..., description="Actionable recommendation for code reviewers")
    top_risk_drivers: List[SHAPExplanationItem] = Field(
        default_factory=list,
        description="Top features driving the PR risk assessment",
    )
    latency_ms: float = Field(..., ge=0.0, description="Total analysis latency in milliseconds")
    override_applied: Optional[str] = Field(
        default=None,
        description="Safety override rule triggered, if applicable",
    )


class TriageQueueItem(BaseModel):
    """
    Summary representation of a pull request inside the maintainer review queue.
    """
    model_config = ConfigDict(extra="ignore")

    pr_number: int
    repo_name: str
    title: str
    risk_tier: str
    risk_probability: float
    author_login: str
    ci_passed: Optional[bool] = None
    created_at: Optional[str] = None


class HealthResponse(BaseModel):
    """
    System status and service health check response.
    """
    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="healthy", description="Service health state")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application release version")
    model_loaded: bool = Field(default=True, description="Whether XGBoost and SHAP models are loaded in memory")
    database_connected: bool = Field(default=True, description="Whether the database connection is operational")


class GitHubWebhookAck(BaseModel):
    """
    Acknowledgement returned to GitHub native webhook calls.
    """
    model_config = ConfigDict(extra="ignore")

    status: str = Field(..., description="Processing status (e.g. processed, ignored, error)")
    event: str = Field(..., description="GitHub event type (e.g. pull_request, ping)")
    action: Optional[str] = Field(default=None, description="Action sub-type (opened, synchronize, etc.)")
    message: str = Field(..., description="Informative status message")
    triage_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Abbreviated triage result if evaluation ran",
    )
