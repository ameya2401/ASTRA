# Phase 5: FastAPI Webhook Gateway & GitHub Bot Commenter

**Goal:** Connect all previous modules into a live REST API that listens to GitHub webhooks and posts risk reports back to PRs.

---

## Instructions for the AI Agent

Act as a Full-Stack Backend & DevOps Engineer.
Write `src/api/routes.py`, `src/api/schemas.py`, and `src/integrations/reporter.py` in `e:\study\ASTRA\ast-triage-core`.

**Requirements:**

1. **Schemas (`schemas.py`):**
   - Define Pydantic models for `PRWebhookPayload`, `SHAPExplanationItem`, and `TriageResponse`.

2. **Endpoints (`routes.py`):**
   - Build a FastAPI endpoint `POST /api/v1/triage/analyze` accepting a Pydantic `PRWebhookPayload`.
   - Asynchronously orchestrate AST extraction, semantic drift embedding, feature assembly, and model inference within a strict 300ms SLA.
   - Combine the outputs into the `TriageResponse`.

3. **GitHub Reporter (`reporter.py`):**
   - Build a markdown comment generator that formats the triage assessment into an elegant GitHub PR comment:
     - Green / Yellow / Red SVG status badge.
     - Calibrated Risk Percentage.
     - Collapsible markdown dropdown containing the top-3 SHAP structural risk drivers.
     - Concrete, actionable recommendation for the human maintainer.
