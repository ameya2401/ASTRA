# Production Gating, GitHub Actions, and Product Landing Page

## 1. Overview
ASTRA provides turnkey production enforcement tools enabling engineering teams to prevent defective AI agent pull requests from merging into production branches.

---

## 2. CI/CD Risk Gate (`.github/workflows/astra-gate.yml`)

The risk gate runs on every `pull_request` event:
1. Extracts the unified diff between the base branch and the PR head.
2. Posts the diff and prompt specification to the ASTRA triage endpoint (`https://astra-08bw.onrender.com/api/v1/triage`).
3. If defect probability $P \ge 0.65$ and `risk_tier == "HIGH"`, the workflow fails the step and blocks merge.
4. Generates a GitHub Actions Step Summary from `top_risk_drivers`, `code_hotspots`, and `override_applied`.

---

## 3. Product Landing Page (`landing_page/`) and Interactive Docs (`/docs`)

The product frontend is mounted at `/landing` and `/docs` on the FastAPI service (`ast-triage-core/static/landing/` and `ast-triage-core/static/docs/`):
* **Interactive Triage Simulator (`/landing`):**
  - Calls live FastAPI `POST /api/v1/triage` when reachable and labels the result source explicitly (`Preset Benchmark`, `Live API`, or `Offline Heuristic`).
  - Handles explicit validation error, loading, and empty states.
  - Benchmark presets aligned with verified engine outputs (Django validator fix, OpenHands assertion suppression with 6 deleted assertions, and payment gateway semantic drift).
  - Displays calibrated probability, 3-pillar metrics ($\Delta CC$, intent cosine, deleted assertions), and TreeSHAP feature attributions.
* **Failure Mode Analysis:** Side-by-side comparison of conventional CI/linters vs ASTRA static verification.
* **28-D Feature Matrix:** Accessible tab panels (`role="tablist"` / `role="tab"`) covering Structural AST (F01-F12), Semantic Drift (F13-F18), Test Integrity (F19-F23), and Provenance (F24-F28).
* **Empirical Evaluation & Ablation:** Displays 5-fold CV ablation metrics (`1.0000` ROC-AUC, `0.9981` F1, `0.0022` Brier) alongside the `0.0004` Brier production checkpoint, `77.7 ms` CPU latency, and `103/103` passing tests.
* **Developer Documentation Portal (`/docs`):**
  - Three-column documentation layout with sticky left navigation tree, main reading panel, and right on-page TOC.
  - Real-time search filter (`/` keyboard shortcut), copyable code snippets (cURL, Python `httpx`, JS `fetch`), and interactive API test consoles.

---

## 4. Design System & Accessibility

The frontend uses a high-contrast engineering specification-sheet palette verified for WCAG AA ($\ge 4.5:1$):
* **Palette:** Off-white canvas `#f8f9fa`, white elevated cards `#ffffff`, hairlines `#d8dee4`, charcoal ink `#111827`, muted labels `#52525b`, and a single deep-cobalt accent `#1d4ed8` for primary actions and focus rings.
* **Typography:** `IBM Plex Sans` for UI copy and `IBM Plex Mono` for code, endpoints, and numerical metrics.
* **Responsive & Keyboard Accessibility:** Mobile viewports include an accessible, Escape-closable navigation drawer (`Menu`/`Close`), 44px touch targets, skip link, and `:focus-visible` rings across all controls.
