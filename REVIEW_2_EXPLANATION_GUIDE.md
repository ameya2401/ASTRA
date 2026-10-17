# ASTRA - Research Project Review 2 Explanation Guide

> **Quick Reference**: Keep this file open during your review with your guide. It provides a structured, plain-language speaking guide covering the problem, the methodology, the engineering pipeline, and the live outcomes.

---

## 1. Quick Opening Pitch (30 - 45 Seconds)

> *"Good morning sir/ma'am. My research project is **ASTRA**, which stands for **AST Triage and Automated Risk Stratification for AI-Authored Pull Requests**.*
>
> *With AI coding agents like GitHub Copilot, Claude Code, and Devin entering production workflows, developers are no longer writing every pull request by hand. The major problem is that AI-written pull requests frequently pass basic syntax linters, yet hide silent regressions, introduce overly complex nesting, or quietly delete test assertions.*
>
> *ASTRA acts as an automated gatekeeper. Before a human software engineer spends time manually reviewing an AI-generated pull request, ASTRA intercepts the PR via GitHub webhooks, extracts 28 structural, semantic, and process features, predicts defect risk using a calibrated machine learning model, and posts an instant inspection card on GitHub with local SHAP explanations."*

---

## 2. The Research Problem: Why Linters and SonarQube Fail Here (1 - 2 Minutes)

If the guide asks: *"Why do we need ASTRA if we already have CI/CD tools, Flake8, or SonarQube?"*

Key points to explain:
1. **Linters are blind to semantic intent:** A linter checks formatting, naming, and basic syntax errors. It cannot tell if the code actually matches what the issue asked for. An AI agent can hallucinate changes to unrelated files, and a linter will still mark it green.
2. **Raw line diffs hide structural disruption:** Standard Git diffs count raw added and deleted lines (`+10 / -2`). They cannot distinguish between adding 10 lines of safe comments versus adding 10 nested branching conditions that break edge cases.
3. **CI tests can be gamed or bypassed:** When AI agents attempt to fix a failing test, they frequently edit the test files directly, suppress assertions, or delete edge-case tests. A standard CI pass flag looks successful, but test coverage was actually degraded.

**ASTRA's Solution:** A multi-modal pipeline that correlates **prompt intent** with **concrete syntax tree churn** and **test protection metrics**.

---

## 3. The End-to-End Technical Workflow (2 - 3 Minutes)

Walk your guide through the four core processing steps:

```
GitHub PR Opened ➔ Webhook Trigger ➔ 3 Analysis Engines ➔ 28-D Vector ➔ Platt-Calibrated XGBoost ➔ SHAP Explainer ➔ PR Report Card
```

### Step 1: Structural AST Differencing (Tree-sitter Engine)
- Instead of raw text lines, we parse both the base (old) and head (new) code into Concrete Syntax Trees using Tree-sitter.
- We measure 12 structural metrics (`F01–F12`), including Cyclomatic Complexity delta ($\Delta \text{CC}$), max nesting depth delta, function signature modifications, and an AST disturbance index.
- **Why Tree-sitter:** Unlike Python's standard `ast` module, Tree-sitter is error-tolerant (`has_error` handling). If an AI agent submits partially malformed code, Tree-sitter still parses the valid subtrees without crashing.

### Step 2: Semantic Intent-to-Diff Alignment (Sentence-Transformers)
- We feed the PR title and description, alongside the normalized code diff, into a dense neural embedding model (`all-MiniLM-L6-v2`).
- We compute cosine similarity (`F13–F14`) and identifier Jaccard drift (`F15`).
- If the agent made edits that drift away from the original prompt description, ASTRA flags semantic drift immediately.

### Step 3: Test Protection and Process Provenance
- We calculate the test-to-logic churn ratio (`F22`) to ensure that new code logic is matched by corresponding test additions.
- We strictly monitor assertion deletions (`F21`). If an agent deletes assertions without adding new tests, ASTRA flags it as high risk.
- We also capture author provenance (`F28`), detecting whether the PR was authored by a bot or a human developer.

### Step 4: 28-D Feature Assembly, Platt-Calibrated XGBoost, and SHAP
- All 28 features are normalized, checked against physiological bounds, and assembled into a NumPy vector.
- The vector is evaluated by an XGBoost classifier calibrated using 5-fold Platt scaling, which converts raw tree logits into a reliable, true defect probability between 0.0 and 1.0.
- We categorize the PR into one of three risk tiers:
  - 🟢 **LOW RISK** (< 25% defect probability): Fast-track approval eligible.
  - 🟡 **MEDIUM RISK** (25% - 65% defect probability): Standard human review with targeted checklist.
  - 🔴 **HIGH RISK** (> 65% defect probability or safety override): Block merge; deep manual audit required.
- **TreeSHAP Explainability:** ASTRA computes local Shapley attribution values for every decision, listing the exact top 3 factors that contributed to the risk score so reviewers understand the reasoning.

---

## 4. Current Progress & Review 2 Deliverables (What We Have Proven)

Explain the concrete milestones completed for Review 2:

1. **104/104 Automated Tests Passing:**
   - 38/38 AST engine unit tests.
   - 34/34 Semantic engine tests.
   - 20/20 Feature pipeline and ML tests.
   - 12/12 End-to-end integration tests.
2. **Cloud Microservice Deployed:**
   - Containerized FastAPI application running live on Render (`https://astra-08bw.onrender.com`).
   - SQLite/PostgreSQL async storage layer initialized with SQLAlchemy 2.0.
3. **Live GitHub App Webhook Integration:**
   - Connected directly to GitHub repository `ameya2401/ASTRA`.
   - Real-time PR interception, processing all 28 features and posting rich triage comments in under 2.2 seconds.

---

## 5. Live Demonstration Guide (Show PR #9 and PR #8)

Open the pull requests directly in the browser to show your guide the live output:

### Pull Request #9: Refactoring Existing Code (Low Risk)
- **Link:** [https://github.com/ameya2401/ASTRA/pull/9](https://github.com/ameya2401/ASTRA/pull/9)
- **What to show your guide:**
  - **The AST Structural Ledger:** Point to the table citing `clip_feature_bounds()` in `normalizer.py`, marked as `⚠️ Refactored`, with `+10 ΔCC` branching delta and `Level 3` nesting.
  - **The Semantic Intent Matrix:** Point to the `64.5%` prompt-to-diff alignment, verifying that the refactoring matched the PR description.
  - **Test Protection:** Show that zero assertions were deleted.
  - **The SHAP Attribution Table:** Show the top risk drivers (`ast_disturbance_index`, `entity_drift_jaccard`, `func_signatures_mod`).

### Pull Request #8: Critical Disturbance PR (High Risk)
- **Link:** [https://github.com/ameya2401/ASTRA/pull/8](https://github.com/ameya2401/ASTRA/pull/8)
- **What to show your guide:**
  - Show how ASTRA caught high AST disturbance, elevated branching, and assigned an immediate 🔴 **HIGH RISK** tier with a comprehensive reviewer inspection checklist.

---

## 6. Common Questions from Evaluators & Model Answers

### Q1: *"Is your machine learning model a black box?"*
> **Answer:** *"No. We specifically integrated TreeSHAP into the inference loop. For every single pull request evaluated, ASTRA computes local Shapley values that calculate the exact marginal contribution of each feature to the final defect probability. The top 3 risk drivers are displayed directly on the GitHub PR card."*

### Q2: *"Why use Tree-sitter instead of Python's standard `ast` library?"*
> **Answer:** *"Python's built-in `ast` module throws a fatal syntax error and halts if code contains any invalid token or incomplete syntax. Tree-sitter is an incremental, error-tolerant parser designed for code editors. If an AI agent hallucinates malformed syntax, Tree-sitter isolates the error node and continues parsing the rest of the AST, allowing ASTRA to measure the disturbance instead of crashing."*

### Q3: *"How is the model trained for Review 2, and what are the plans for Review 3?"*
> **Answer:** *"For Review 2, the pipeline is calibrated on a 400-sample benchmark reflecting realistic PR defect characteristics (4:1 class imbalance, high complexity churn, and assertion suppression anomalies). For the final phase (Review 3), we have mining scripts ready in `scripts/mine_agent_prs.py` to harvest large-scale real-world pull requests from SWE-bench and autonomous agent repositories, alongside an ablation study comparing AST-only versus Semantic-only models."*

### Q4: *"How fast is the evaluation?"*
> **Answer:** *"Because heavy neural models (like MiniLM) and XGBoost estimators are loaded once into memory as thread-safe singletons during application startup, end-to-end inference takes under 2.2 seconds per pull request."*

---

## 7. Next Steps for Final Review (Review 3)

1. **Large-scale empirical dataset mining:** Run `mine_agent_prs.py` to collect real-world PRs from OpenHands and SWE-bench.
2. **Ablation study:** Empirically quantify the performance lift of combining AST metrics with Semantic NLP embeddings versus evaluating them individually.
3. **Research paper write-up:** Export final ROC-AUC, PR-AUC, and reliability calibration curves for publication and capstone documentation.
