# GitHub Webhook Ingestion & Markdown PR Reporter

> Specifications for cryptographic webhook verification, asynchronous GitHub API interaction, and PR review comment formatting.

---

## 1. Webhook Authentication

GitHub webhooks deliver event payloads signed via HMAC-SHA256 in the `X-Hub-Signature-256` HTTP header. The secret is shared between GitHub and the ASTRA deployment via the `GITHUB_WEBHOOK_SECRET` environment variable.

### 1.1 Verification Algorithm

```python
computed_sig = hmac.new(
    secret.encode("utf-8"),
    payload_bytes,
    hashlib.sha256,
).hexdigest()
is_valid = hmac.compare_digest(given_sig, computed_sig)
```

Constant-time comparison using `hmac.compare_digest` prevents timing attacks on webhook ingress.

---

## 2. Asynchronous GitHub Client

The client in `src/integrations/github_client.py` uses non-blocking `httpx.AsyncClient` calls to communicate with GitHub:

- `post_pr_comment(repo_name, pr_number, comment_body)`: Sends an HTTP POST to `/repos/{repo}/issues/{number}/comments` with status verification.
- `get_pr_diff(repo_name, pr_number)`: Requests unified diff text via `Accept: application/vnd.github.v3.diff`.
- `get_pr_details(repo_name, pr_number)`: Fetches repository metadata and author profiles.
- `add_pr_labels(repo_name, pr_number, labels)`: Attaches risk labels (such as `astra:low-risk`, `astra:medium-risk`, `astra:high-risk`) via `/repos/{repo}/issues/{number}/labels`.

---

## 3. PR Review Comment Formatting

The markdown reporter in `src/integrations/reporter.py` compiles risk assessments into GitHub-flavored markdown.

### 3.1 Visual & Structural Components

1. **SVG Status Badges**:
   - LOW Risk: Green badge indicating fast-track eligibility.
   - MEDIUM Risk: Yellow badge indicating standard human review.
   - HIGH Risk: Red badge indicating deprioritize or reject advice.
2. **Defect Probability Percentage**: Calibrated percentage derived from Platt sigmoid scaling.
3. **Plain English Breakdown**: Non-technical summary translating raw statistics into clear statements covering Verdict, What Changed, Code Complexity, Test Protection, and Goal Alignment.
4. **AST Structural Differencing Ledger**: Detailed Tree-sitter table citing specific functions, line spans, churn classification (Refactored vs Added), cyclomatic complexity jumps ($\Delta \text{CC}$), max nesting levels, and total syntax churn pills.
5. **Semantic Intent & Verification Matrix**: Dense Sentence-Transformers (`all-MiniLM-L6-v2`) cosine alignment percentage, prompt drift flags, and test-to-logic ratios.
6. **Engineering Decision Rationale**: Transparent explanation clarifying how the machine learning model reached its risk classification based on structural disturbance and test safety nets.
7. **Reviewer Inspection Checklist**: Actionable checkboxes tailored to the detected risk tier.
8. **Assessment Summary with Model Certainty**: Defect probability, risk tier, analysis latency, raw score, model confidence level, and author provenance.
9. **Collapsible SHAP Breakdown**: An HTML `<details>` section containing a tabular ledger of the top-3 marginal risk drivers, their friendly plain language names, observed values, directional impacts, and exact Code Location Hotspots (function name and line range).
10. **Actionable Recommendation**: Specific guidance tailored to the detected risk tier and active safety overrides.

### 3.2 Sample Comment Output

```markdown
## ASTRA Automated Triage Report

[![Risk Tier](https://img.shields.io/badge/ASTRA_Risk-LOW_Fast_Track-28a745.svg)](#)

**Risk Evaluation for django/django #19283:** 🟢 **LOW RISK** (14.2% defect probability)

> **Recommendation:** FAST-TRACK: High structural integrity, intent aligned, tests verified.

### 💡 Plain English Breakdown

- **Verdict:** Safe to merge. Very low chance of introducing bugs or regressions.
- **What Changed:** Modified `format_query()` in `utils.py`.
- **Code Complexity:** Clean and straightforward. Minimal new branching added in `src/utils.py:L45-72 (format_query)`.
- **Test Protection:** Zero test assertions were removed. Safety net remains intact.
- **Goal Match:** Changes align directly with the pull request title and intent.

### 🔬 AST Structural Differencing Ledger (Tree-sitter)

| Modified Function / Scope | File & Coordinates | Churn Type | Branching Delta | Max Nesting Depth |
| :--- | :--- | :--- | :--- | :--- |
| `format_query()` | `utils.py:L45-72` | ➕ Added / Clean | **+1 ΔCC** | Level 2 |

> ℹ️ Syntax Churn: `+35 / -0` AST nodes | Syntax Disturbance Index: `0.12`

### 🧠 Semantic Intent & Verification Matrix

- **Prompt-to-Diff Cosine Alignment:** `89.4%` (via Sentence-Transformers `all-MiniLM-L6-v2`) [✅ **Verified Aligned** (high semantic fidelity)]
- **Test-to-Logic Churn Ratio:** `0.85` (ratio of test syntax nodes to logic syntax nodes)
- **Test Protection Status:** ✅ Zero test assertions removed. Safety net remains intact.

### ⚙️ Engineering Decision Rationale

ASTRA classified this PR as **LOW RISK** (14.2% defect probability). Concrete syntax tree differencing confirms minimal structural disturbance, high intent-to-diff alignment, and verified test suite integrity, qualifying this PR for fast-track review.

### 📋 Reviewer Inspection Checklist

- [ ] Quick scan of diff for coding style and project conventions.
- [ ] Confirm automated CI test suite passed.
- [ ] Fast-track approval eligible.

### Review Assessment Summary

- **Calibrated Defect Probability:** `0.1425` (14.2%)
- **Risk Classification Tier:** `LOW`
- **Analysis Latency:** `38.2 ms`
- **Raw Decision Score:** `-1.7946`
- **Confidence Rating:** `HIGH` (98.0% model certainty)
- **Author Provenance:** 👤 Contributor (`@octocat`)

<details>
<summary><b>Top Structural and Semantic Risk Drivers (SHAP Attribution)</b></summary>

| Rank | Feature | Plain Language Meaning | Impact | Marginal SHAP | Details | Code Location Hotspot |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `intent_diff_cosine` | PR Prompt vs Diff Alignment | Decreases Risk | `-0.0456` | intent_diff_cosine = 0.89 (DECREASES_RISK) | Diff global |
| 2 | `delta_cc` | Branching Complexity Change | Increases Risk | `+0.0123` | delta_cc = 1 (INCREASES_RISK) | `src/utils.py:L45-72 (format_query)` |

</details>

---
*Automated risk stratification generated by ASTRA. Intended for triage guidance and review prioritization, not autonomous merging.*
```
