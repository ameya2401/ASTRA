"""
src - Core source modules for AST-Triage.

Sub-packages:
    ast_engine:       Tree-sitter AST parsing and structural diff analysis
    semantic_engine:  Sentence-transformers intent alignment and drift detection
    feature_pipeline: 28-dimensional feature vector assembly and normalization
    ml_engine:        XGBoost training, calibrated inference, and SHAP explanations
    api:              FastAPI application, routes, and request/response schemas
    integrations:     GitHub API client and PR comment reporter
"""
