# Production Gating, GitHub Actions, and Product Landing Page

## 1. Overview
ASTRA provides turnkey production enforcement tools enabling engineering teams to prevent defective AI agent pull requests from merging into production branches.

---

## 2. CI/CD Risk Gate (`.github/workflows/astra-gate.yml`)

The risk gate runs on every `pull_request` event:
1. Extracts the unified diff between the base branch and the PR head.
2. Posts the diff and prompt specification to the ASTRA triage endpoint (`https://astra-08bw.onrender.com/api/v1/triage`).
3. If defect probability $P \ge 0.65$ or if a safety override is triggered (e.g. assertion deletion), the workflow fails the step and blocks merge.
4. Generates a rich GitHub Actions Step Summary with local SHAP attributions and cited AST churn hotspots.

---

## 3. Product Landing Page (`landing_page/`) and Interactive Docs (`/docs`)

The product frontend showcases ASTRA as a commercial-grade developer security platform:
* **Interactive Triage Simulator (`/landing`):**
  - Real-time client and API triage execution.
  - Empirical preset benchmark scenarios (Clean Django refactor, OpenHands assertion deletion, Payment gateway semantic drift).
  - Dynamic TreeSHAP attribution waterfall and Platt calibration defect probability gauge.
* **The "Green CI Mirage" Vulnerability:** Comparative visual matrix demonstrating why standard syntax linters and CI suites pass dangerous agent pull requests.
* **28-D Feature Matrix:** Interactive tabs covering Structural AST, Semantic Intent, Test Protection, and Process Provenance.
* **Mounted in FastAPI:** Accessible at `/landing` on the running service.
* **Developer Documentation Portal (`/docs`):**
  - Classic 3-column / 2-column documentation layout with sticky left navigation tree, main reading panel, and right on-page TOC.
  - Real-time search filter for instant sidebar filtering (supports `/` keyboard shortcut).
  - Categorized guides covering System Overview, Quickstart, Authentication, API Reference, 28-D Feature Matrix, and GitHub Action CI/CD Gate.
  - Tabbed code snippets (cURL, Python `httpx`, JavaScript `fetch`) with one-click copy buttons.
  - Interactive API execution console on each endpoint card, enabling live in-browser testing against running backend routes.
  - Parameter and schema tables detailing request payloads, field types, and response objects.
  - Styled strictly under the Vercel / Geist design system (`#fafafa` canvas, `#ffffff` cards, Geist Sans and Geist Mono typography).

---

## 4. Design System & Aesthetics (`design.md`)

The landing page follows the Vercel / Geist design system:
* **Brand Identity & Logomark:** Geometric delta lockup ("A ASTRA") deployed in the top navigation headers across the Landing Page, Developer Documentation portal, and project README files. Browser favicons use a high-contrast white rounded tile ensuring 100% visibility on both dark and light browser tab themes.
* **Near-White Canvas & Near-Black Ink:** `#fafafa` canvas (`--color-canvas`) with pure white `#ffffff` elevated surfaces and `#171717` ink headings, primary CTAs, and 1px hairline borders (`#ebebeb`).
* **Hero Mesh Gradient:** A subtle multi-stop mesh bloom (cyan `#50e3c2`, blue `#007cf0`, violet `#7928ca`, magenta `#ff0080`, amber `#f9cb28`) strictly confined to the hero as a gentle backdrop.
* **Typography:** Geist Sans with tight negative display tracking (`-2.4px` on Display XL, `-1.28px` on Heading LG) and Geist Mono for uppercase technical spec eyebrows (`.mono-eyebrow`) and code tokens.
* **Bimodal Shape System:** Fully rounded pills (`100px` radius) for marketing CTAs, and tight 6px squares (`rounded.sm`) for app/nav controls.
* **Whisper Depth:** Flat-first depth with 1px hairlines and `0 1px 2px rgba(0,0,0,0.04)` shadows; no heavy glowing blobs or neon gradients.
