"""
tests/test_end_to_end.py - End-to-end integration tests.

Validates the complete triage pipeline:
    1. PR payload ingestion
    2. AST feature extraction
    3. Semantic drift computation
    4. Feature vector assembly
    5. Model inference and calibration
    6. SHAP explanation generation
    7. Response formatting

Implementation: Phase 5
"""
