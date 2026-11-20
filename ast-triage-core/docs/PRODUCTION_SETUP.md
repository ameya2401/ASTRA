# ASTRA Production Deployment and Integration Guide

This guide describes how to configure, deploy, and enforce ASTRA (AST Triage & Automated Risk Stratification) across organization repositories to intercept and screen AI-generated pull requests before human review.

---

## Architecture Overview

```
                                      PRODUCTION ARCHITECTURE
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          ▼                                      ▼                                      ▼
1. GitHub Webhook / Action              2. ASTRA Core Microservice             3. Automated Enforcement
   - PR opened or updated                  - HMAC-SHA256 Auth                     - Automated PR comment
   - Sends diff and prompt                 - Tree-sitter AST Diff                 - GitHub Labels assigned
   - Zero repo overhead                    - MiniLM Intent Embedding              - Branch Protection Check
                                           - Platt-Calibrated XGBoost             - Blocks unsafe merges
```

---

## 1. Fast Track: 2-Minute CI/CD Setup (GitHub Actions)

If you already have a GitHub repository, you can enable ASTRA with zero infrastructure setup:

1. In your repository, create the file `.github/workflows/astra-gate.yml`:

```yaml
name: ASTRA Risk Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  statuses: write

jobs:
  triage:
    name: ASTRA AI-PR Risk Triage
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run ASTRA Triage
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > pr_diff.patch
          python3 -c "
          import json, os, urllib.request, sys
          diff_content = open('pr_diff.patch', 'r', errors='ignore').read()
          payload = {
              'repo_name': '${{ github.repository }}',
              'pr_number': ${{ github.event.pull_request.number }},
              'pr_title': '${{ github.event.pull_request.title }}',
              'pr_body': '${{ github.event.pull_request.body || '' }}',
              'raw_diff': diff_content,
              'author_login': '${{ github.actor }}',
              'author_is_bot': False
          }
          req = urllib.request.Request(
              'https://astra-08bw.onrender.com/api/v1/triage',
              data=json.dumps(payload).encode('utf-8'),
              headers={'Content-Type': 'application/json'},
              method='POST'
          )
          with urllib.request.urlopen(req, timeout=30) as resp:
              res = json.loads(resp.read().decode('utf-8'))
          print(f'ASTRA Triage Result: {res[\"risk_tier\"]} ({res[\"risk_probability\"]:.1%})')
          if res.get('risk_tier') == 'HIGH' and res.get('risk_probability', 0) >= 0.65:
              sys.exit(1)
          "
```

2. Under **Repository Settings -> Branches -> Branch Protection Rules**:
   * Enable **Require status checks to pass before merging**.
   * Search for and select **ASTRA AI-PR Risk Triage**.
   * Pull requests flagged as High Risk will now automatically block merge until audited.

---

## 2. Organization Webhook Gateway Setup (Real-Time Triage)

For real-time triage comments with SVG badges and SHAP explanation cards posted directly onto PRs:

1. Navigate to **Repository Settings -> Webhooks -> Add webhook** (or Organization Settings for all repos).
2. Configure settings:
   * **Payload URL:** `https://astra-08bw.onrender.com/api/v1/webhooks/github` (or your private domain)
   * **Content type:** `application/json`
   * **Secret:** Enter a strong random secret token (e.g. generated via `openssl rand -hex 32`).
   * **Which events would you like to trigger this webhook?**
     * Select **Let me select individual events**.
     * Check **Pull requests**.
3. In your ASTRA deployment environment, set the corresponding environment variables:
   ```bash
   GITHUB_WEBHOOK_SECRET="your-configured-webhook-secret"
   GITHUB_TOKEN="ghp_your_github_personal_access_token_or_app_token"
   ```
4. The service will automatically:
   * Intercept incoming PR events in under 2.5 seconds.
   * Verify HMAC-SHA256 request signatures.
   * Post formatted inspection cards with local SHAP attributions.
   * Attach `astra:low-risk`, `astra:medium-risk`, or `astra:high-risk` labels.

---

## 3. Self-Hosted Docker Deployment

To run ASTRA on your own private cloud or on-premise Kubernetes cluster:

```bash
# Clone the repository
git clone https://github.com/ameya2401/ASTRA.git
cd ASTRA/ast-triage-core

# Build container image
docker build -t astra-triage-core:latest .

# Run with environment variables
docker run -d \
  --name astra-service \
  -p 8000:8000 \
  -e GITHUB_TOKEN="ghp_your_token" \
  -e GITHUB_WEBHOOK_SECRET="your_secret" \
  -e DATABASE_URL="sqlite+aiosqlite:///data/astra.db" \
  astra-triage-core:latest
```

Health check endpoint: `GET /health` returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engines": {
    "tree_sitter": "ready",
    "sentence_transformers": "ready",
    "xgboost_classifier": "ready",
    "shap_explainer": "ready"
  }
}
```

---

## 4. Resource Allocation Recommendations

ASTRA is engineered as a lightweight, CPU-optimized microservice. It does **not** require expensive GPU instances:

* **RAM:** 512 MB minimum (1 GB recommended for high concurrent PR load).
* **CPU:** 1 vCPU (2 vCPUs recommended for multi-threaded Tree-sitter parsing).
* **Storage:** 200 MB for model checkpoints and SQLite database.
* **Latency Profile:**
  * Local AST + XGBoost + SHAP inference: ~40 to 80 milliseconds.
  * Sentence embedding inference: ~150 to 300 milliseconds.
  * End-to-end round trip (including GitHub API latency): under 2.2 seconds.
