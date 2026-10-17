# Review 2 Presentation Script & Guide

> Complete speaking script, methodology breakdown, and evaluation Q&A for academic and research project reviews.

This guide mirrors the project explanation document at [REVIEW_2_EXPLANATION_GUIDE.md](file:///e:/study/ASTRA/REVIEW_2_EXPLANATION_GUIDE.md).

## Key Presentation Highlights
- **Problem**: Autonomous AI agent PR hallucinations, silent regressions, and assertion suppressions.
- **Three Engines**:
  - Tree-sitter AST structural differencing (`F01–F12`)
  - Sentence-Transformers semantic alignment (`F13–F18`)
  - Test protection and process provenance (`F19–F28`)
- **Classification**: 28-D vector fed into Platt-calibrated XGBoost classifier.
- **Explainability**: Local TreeSHAP attributions citing top 3 risk drivers and code hotspots.
- **Deployment**: Live FastAPI webhook receiver on Render (`https://astra-08bw.onrender.com`).
- **Live Verifications**: [PR #8](https://github.com/ameya2401/ASTRA/pull/8) and [PR #9](https://github.com/ameya2401/ASTRA/pull/9).
