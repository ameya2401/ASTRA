"""
setup.py - Package configuration for ast-triage-core.

AST-Triage: Automated risk-scoring system for AI-agent-generated
GitHub Pull Requests using Tree-sitter AST differencing,
sentence-transformers semantic alignment, and Platt-calibrated
XGBoost classification.
"""
from setuptools import setup, find_packages

setup(
    name="ast-triage-core",
    version="0.1.0",
    description=(
        "Automated risk-scoring system for AI-agent-generated GitHub PRs "
        "using AST differencing, semantic alignment, and calibrated ML classification."
    ),
    author="ASTRA Team",
    python_requires=">=3.11",
    packages=find_packages(where=".", include=["config*", "database*", "src*"]),
    install_requires=[
        "fastapi>=0.111.0",
        "uvicorn[standard]>=0.30.0",
        "pydantic>=2.7.0",
        "pydantic-settings>=2.3.0",
        "tree-sitter>=0.22.0",
        "tree-sitter-python>=0.22.0",
        "xgboost>=2.0.0",
        "scikit-learn>=1.5.0",
        "sentence-transformers>=3.0.0",
        "shap>=0.45.0",
        "sqlalchemy[asyncio]>=2.0.30",
        "aiosqlite>=0.20.0",
        "pyarrow>=16.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "httpx>=0.27.0",
        ],
    },
)
