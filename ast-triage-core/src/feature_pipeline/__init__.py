"""
src/feature_pipeline - 28-dimensional feature vector assembly and normalization.

Re-exports:
    - build_feature_vector: Combines AST, semantic, test, and process metrics into a 28-D vector.
    - calculate_dispersion_entropy: Shannon entropy of file churn.
    - extract_test_metrics: Test-to-code churn and asymmetry extraction.
    - extract_process_metrics: Process and provenance metric extraction.
    - FEATURE_NAMES: Ordered 28-feature list matching training columns (F01-F28).
    - FEATURE_ALIASES: Alias mapping for database column names and alternate keys.
    - FeatureNormalizer: Imputation, clipping, and normalization pipeline.
    - impute_missing_values: Numerical cleaning helper.
    - clip_feature_bounds: Algorithmic bound clipping helper.
"""
from src.feature_pipeline.vector_builder import (
    FEATURE_NAMES,
    FEATURE_ALIASES,
    KNOWN_AGENT_BOTS,
    build_feature_vector,
    calculate_dispersion_entropy,
    extract_process_metrics,
    extract_test_metrics,
)
from src.feature_pipeline.normalizer import (
    FEATURE_BOUNDS,
    FeatureNormalizer,
    clip_feature_bounds,
    impute_missing_values,
)

__all__ = [
    "FEATURE_NAMES",
    "FEATURE_ALIASES",
    "KNOWN_AGENT_BOTS",
    "FEATURE_BOUNDS",
    "build_feature_vector",
    "calculate_dispersion_entropy",
    "extract_process_metrics",
    "extract_test_metrics",
    "FeatureNormalizer",
    "clip_feature_bounds",
    "impute_missing_values",
]
