"""
database/models.py - SQLAlchemy 2.0 ORM models for AST-Triage.

Defines the complete relational schema for storing:
    - Repository metadata
    - Pull request records with raw diffs and ground truth labels
    - Extracted 28-dimensional feature vectors
    - Triage predictions with SHAP attributions

Schema matches the DDL specification in the Technical Reference:
    docs/prerequisites/AST_Triage_Technical_Reference.md (Section 2.1)

All models use SQLAlchemy 2.0 Mapped Column syntax with strict type hints.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all AST-Triage ORM models."""
    pass


class Repository(Base):
    """
    Represents a source code repository being monitored.

    Attributes:
        id: Primary key.
        repo_name: Fully qualified repository name (e.g., 'django/django').
        default_branch: Default branch name (e.g., 'main').
        created_at: Timestamp when the repository was first registered.
    """
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    default_branch: Mapped[str] = mapped_column(String(64), default="main")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, repo_name='{self.repo_name}')>"


class PullRequest(Base):
    """
    Stores metadata and raw diff for an incoming pull request.

    Captures the full context needed for feature extraction:
    issue description, author provenance, commit SHAs, and unified diff.

    Attributes:
        ground_truth_status: One of 'MERGED', 'REJECTED_CLOSED', 'REVERTED'.
        ground_truth_label: Binary label — 0 = Merged/Accepted, 1 = Rejected/Defective.
    """
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repo_id", "pr_number", name="unique_repo_pr"),
        Index("idx_pr_repo_num", "repo_id", "pr_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    author_login: Mapped[str] = mapped_column(String(255), nullable=False)
    author_is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    agent_framework: Mapped[str] = mapped_column(
        String(64), default="unknown",
        doc="Agent identifier: 'devin', 'claude-code', 'copilot', etc."
    )
    base_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_diff: Mapped[str] = mapped_column(Text, nullable=False)
    ci_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=None)
    ground_truth_status: Mapped[str] = mapped_column(
        String(32), nullable=False,
        doc="One of: 'MERGED', 'REJECTED_CLOSED', 'REVERTED'"
    )
    ground_truth_label: Mapped[int] = mapped_column(
        Integer, nullable=False,
        doc="Binary: 0 = Merged/Accepted, 1 = Rejected/Defective"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="pull_requests"
    )
    feature_record: Mapped[Optional["FeatureRecord"]] = relationship(
        "FeatureRecord", back_populates="pull_request", uselist=False,
        cascade="all, delete-orphan"
    )
    triage_prediction: Mapped[Optional["TriagePrediction"]] = relationship(
        "TriagePrediction", back_populates="pull_request", uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<PullRequest(id={self.id}, repo_id={self.repo_id}, "
            f"pr_number={self.pr_number}, label={self.ground_truth_label})>"
        )


class FeatureRecord(Base):
    """
    Stores the complete 28-dimensional feature vector extracted from a PR.

    Feature groups:
        F01–F12: Structural AST metrics (nodes, cyclomatic delta, signatures)
        F13–F18: Semantic drift & NLP metrics (cosine similarity, entity overlap)
        F19–F23: Test-to-code churn & asymmetry metrics
        F24–F28: Process, author & provenance metrics

    Each feature column is prefixed with 'f{NN}_' for unambiguous ordering.
    """
    __tablename__ = "feature_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pull_requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ---- Structural AST Features (F01–F12) ----
    f01_ast_nodes_added: Mapped[int] = mapped_column(Integer, nullable=False)
    f02_ast_nodes_deleted: Mapped[int] = mapped_column(Integer, nullable=False)
    f03_ast_nodes_mutated: Mapped[int] = mapped_column(Integer, nullable=False)
    f04_cyclomatic_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    f05_max_nesting_depth_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    f06_func_signatures_modified: Mapped[int] = mapped_column(Integer, nullable=False)
    f07_classes_modified: Mapped[int] = mapped_column(Integer, nullable=False)
    f08_return_types_altered: Mapped[int] = mapped_column(Integer, nullable=False)
    f09_call_graph_fan_out_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    f10_ast_disturbance_index: Mapped[float] = mapped_column(Float, nullable=False)
    f11_try_catch_blocks_added: Mapped[int] = mapped_column(Integer, nullable=False)
    f12_control_flow_churn_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    # ---- Semantic Drift & NLP Features (F13–F18) ----
    f13_intent_diff_cosine_sim: Mapped[float] = mapped_column(Float, nullable=False)
    f14_issue_title_diff_sim: Mapped[float] = mapped_column(Float, nullable=False)
    f15_entity_drift_jaccard: Mapped[float] = mapped_column(Float, nullable=False)
    f16_docstring_to_code_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    f17_semantic_drift_flag: Mapped[int] = mapped_column(Integer, nullable=False)
    f18_issue_token_length: Mapped[int] = mapped_column(Integer, nullable=False)

    # ---- Test Churn & Asymmetry Features (F19–F23) ----
    f19_test_files_modified: Mapped[int] = mapped_column(Integer, nullable=False)
    f20_test_ast_nodes_added: Mapped[int] = mapped_column(Integer, nullable=False)
    f21_test_assertions_deleted: Mapped[int] = mapped_column(Integer, nullable=False)
    f22_test_to_logic_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    f23_mock_patch_count_delta: Mapped[int] = mapped_column(Integer, nullable=False)

    # ---- Process & Provenance Features (F24–F28) ----
    f24_commit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    f25_files_touched_count: Mapped[int] = mapped_column(Integer, nullable=False)
    f26_file_dispersion_entropy: Mapped[float] = mapped_column(Float, nullable=False)
    f27_ci_pass_flag: Mapped[int] = mapped_column(Integer, nullable=False)
    f28_is_known_agent_bot: Mapped[int] = mapped_column(Integer, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    pull_request: Mapped["PullRequest"] = relationship(
        "PullRequest", back_populates="feature_record"
    )

    def __repr__(self) -> str:
        return f"<FeatureRecord(id={self.id}, pr_id={self.pr_id})>"

    def to_vector(self) -> list[float]:
        """
        Returns the 28 features as an ordered list of floats.

        The ordering strictly matches the model training column indices
        (F01 through F28) for direct XGBoost inference.
        """
        return [
            float(self.f01_ast_nodes_added),
            float(self.f02_ast_nodes_deleted),
            float(self.f03_ast_nodes_mutated),
            float(self.f04_cyclomatic_delta),
            float(self.f05_max_nesting_depth_delta),
            float(self.f06_func_signatures_modified),
            float(self.f07_classes_modified),
            float(self.f08_return_types_altered),
            float(self.f09_call_graph_fan_out_delta),
            float(self.f10_ast_disturbance_index),
            float(self.f11_try_catch_blocks_added),
            float(self.f12_control_flow_churn_ratio),
            float(self.f13_intent_diff_cosine_sim),
            float(self.f14_issue_title_diff_sim),
            float(self.f15_entity_drift_jaccard),
            float(self.f16_docstring_to_code_ratio),
            float(self.f17_semantic_drift_flag),
            float(self.f18_issue_token_length),
            float(self.f19_test_files_modified),
            float(self.f20_test_ast_nodes_added),
            float(self.f21_test_assertions_deleted),
            float(self.f22_test_to_logic_ratio),
            float(self.f23_mock_patch_count_delta),
            float(self.f24_commit_count),
            float(self.f25_files_touched_count),
            float(self.f26_file_dispersion_entropy),
            float(self.f27_ci_pass_flag),
            float(self.f28_is_known_agent_bot),
        ]


class TriagePrediction(Base):
    """
    Stores the ML model's risk assessment for a pull request.

    Captures both raw and Platt-calibrated risk scores, the assigned
    risk tier, top 3 SHAP feature attributions, and inference latency.

    Attributes:
        raw_risk_score: Uncalibrated model output logit.
        calibrated_risk_score: Platt-scaled probability in [0.0, 1.0].
        risk_tier: One of 'LOW', 'MEDIUM', 'HIGH'.
        top_shap_feature_{1,2,3}: Feature name of the top SHAP contributors.
        shap_value_{1,2,3}: Corresponding SHAP attribution values.
        inference_latency_ms: End-to-end inference time in milliseconds.
    """
    __tablename__ = "triage_predictions"
    __table_args__ = (
        Index("idx_prediction_tier", "risk_tier"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pull_requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    raw_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_tier: Mapped[str] = mapped_column(
        String(16), nullable=False,
        doc="One of: 'LOW', 'MEDIUM', 'HIGH'"
    )

    # Top 3 SHAP feature attributions
    top_shap_feature_1: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shap_value_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_shap_feature_2: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shap_value_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_shap_feature_3: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shap_value_3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    inference_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    pull_request: Mapped["PullRequest"] = relationship(
        "PullRequest", back_populates="triage_prediction"
    )

    def __repr__(self) -> str:
        return (
            f"<TriagePrediction(id={self.id}, pr_id={self.pr_id}, "
            f"risk={self.calibrated_risk_score:.4f}, tier='{self.risk_tier}')>"
        )
