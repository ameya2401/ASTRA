"""
src.semantic_engine - NLP-based intent alignment and semantic drift detection.

Provides semantic comparison between pull request issue specifications
and code diffs to compute the 6 NLP features (F13–F18) used by AST-Triage:
    - F13: intent_diff_cosine   (Cosine similarity between issue and diff embeddings)
    - F14: title_diff_cosine    (Cosine similarity between title and diff embeddings)
    - F15: entity_drift_jaccard (Jaccard distance over extracted code identifiers)
    - F16: docstring_code_ratio (Docstring/comment lines vs executable code lines)
    - F17: semantic_drift_flag  (Binary indicator: 1 if cosine < 0.45 else 0)
    - F18: issue_token_length   (Count of tokens in issue description)

Modules:
    embedder:        Sentence-transformers singleton wrapper for embedding generation
    drift_analyzer:  Cosine distance and entity drift calculator
"""
from src.semantic_engine.embedder import (
    EMBEDDING_DIM,
    SentenceEmbedder,
    get_embedder,
)
from src.semantic_engine.drift_analyzer import (
    PYTHON_KEYWORDS,
    SEMANTIC_DRIFT_THRESHOLD,
    SemanticDriftAnalyzer,
    SemanticMetrics,
    compute_docstring_code_ratio,
    compute_entity_jaccard_distance,
    compute_issue_token_length,
    compute_semantic_drift,
    extract_code_identifiers,
    normalize_diff,
    normalize_text,
)

__all__ = [
    "EMBEDDING_DIM",
    "PYTHON_KEYWORDS",
    "SEMANTIC_DRIFT_THRESHOLD",
    "SentenceEmbedder",
    "get_embedder",
    "SemanticDriftAnalyzer",
    "SemanticMetrics",
    "compute_docstring_code_ratio",
    "compute_entity_jaccard_distance",
    "compute_issue_token_length",
    "compute_semantic_drift",
    "extract_code_identifiers",
    "normalize_diff",
    "normalize_text",
]
