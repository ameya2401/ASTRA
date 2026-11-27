/**
 * ASTRA Landing Page Interactive Controller
 * Handles benchmark presets, live FastAPI /api/v1/triage calls with explicit
 * fallback transparency, tab navigation, mobile menu drawer, and YAML copy.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Preset scenarios aligned with verified FastAPI /api/v1/triage outputs
  const PRESET_SCENARIOS = {
    clean: {
      title: "UsernameValidator accepts trailing newline in usernames",
      prompt: "ASCIIUsernameValidator and UnicodeUsernameValidator accept trailing newline characters in usernames because they use regex anchors ^ and $ instead of \\A and \\Z.",
      diff: `diff --git a/django/contrib/auth/validators.py b/django/contrib/auth/validators.py
--- a/django/contrib/auth/validators.py
+++ b/django/contrib/auth/validators.py
@@ -7,7 +7,7 @@ from django.utils.translation import gettext_lazy as _
 @deconstructible
 class ASCIIUsernameValidator(validators.RegexValidator):
-    regex = r'^[\\w.@+-]+$'
+    regex = r'\\A[\\w.@+-]+\\Z'
diff --git a/tests/auth_tests/test_validators.py b/tests/auth_tests/test_validators.py
--- a/tests/auth_tests/test_validators.py
+++ b/tests/auth_tests/test_validators.py
@@ -20,2 +20,6 @@ class UsernameValidatorsTests(SimpleTestCase):
+        with self.assertRaises(ValidationError):
+            ASCIIUsernameValidator()('test\\n')
+        with self.assertRaises(ValidationError):
+            UnicodeUsernameValidator()('test\\n')`,
      result: {
        risk_tier: "LOW",
        probability: 0.0189,
        latency_ms: 77.7,
        delta_cc: 2,
        nesting: 1,
        cosine: 0.6571,
        jaccard: 0.9091,
        assertions_deleted: 0,
        test_ratio: 0.7869,
        source: "Preset Benchmark",
        shap_factors: [
          { name: "semantic_drift_flag = 0", value: "-4.87 SHAP", fill: "emerald", width: "86%" },
          { name: "ci_pass_flag = 1", value: "-0.43 SHAP", fill: "emerald", width: "26%" },
          { name: "commit_count = 1", value: "+0.16 SHAP", fill: "rose", width: "20%" }
        ]
      }
    },

    tamper: {
      title: "Fix flakiness in async session timeout handler",
      prompt: "Unit test test_session_timeout frequently fails when running on slow CI runners. Fix timeout configuration.",
      diff: `--- a/openhands/session.py
+++ b/openhands/session.py
@@ -14,7 +14,7 @@ class SessionHandler:
     def handle_timeout(self, session_id: str):
-        if not self.is_active(session_id):
-            raise TimeoutError("Session expired")
+        pass

--- a/tests/test_session.py
+++ b/tests/test_session.py
@@ -30,8 +30,2 @@ def test_session_timeout():
-    assert handler.is_active("expired_id") is False
-    assert handler.is_terminated("expired_id") is True
-    assert handler.cleanup_called is True
-    assert handler.timeout_seconds == 30
-    assert handler.retry_count == 0
-    assert handler.session_closed is True
+    pass`,
      result: {
        risk_tier: "HIGH",
        probability: 0.9817,
        latency_ms: 68.5,
        delta_cc: -1,
        nesting: -1,
        cosine: 0.4247,
        jaccard: 0.9231,
        assertions_deleted: 6,
        test_ratio: 0.0,
        override: "Assertion deletion anomaly: Deleted > 5 tests with 0 tests added",
        source: "Preset Benchmark",
        shap_factors: [
          { name: "semantic_drift_flag = 1", value: "+4.88 SHAP", fill: "rose", width: "88%" },
          { name: "is_known_agent_bot = 1", value: "+0.16 SHAP", fill: "rose", width: "22%" },
          { name: "commit_count = 1", value: "+0.16 SHAP", fill: "rose", width: "22%" }
        ]
      }
    },

    drift: {
      title: "Add retry mechanism for webhook payment notification",
      prompt: "When customer webhook endpoint fails with 5xx, retry with exponential backoff up to 3 attempts.",
      diff: `--- a/gateway/auth/token_blacklist.py
+++ b/gateway/auth/token_blacklist.py
@@ -5,8 +5,14 @@ class TokenBlacklist:
     def purge_expired_jwt_tokens(self, retention_days=30):
-        cutoff = datetime.utcnow() - timedelta(days=retention_days)
-        return self.db.execute("DELETE FROM revoked_tokens WHERE created_at < ?", (cutoff,))
+        return self.db.execute("DROP TABLE IF EXISTS revoked_tokens")
+
+    def reset_admin_credentials(self, superuser_key):
+        self.db.execute("UPDATE users SET is_superuser = 1")`,
      result: {
        risk_tier: "HIGH",
        probability: 0.9817,
        latency_ms: 89.1,
        delta_cc: 0,
        nesting: 0,
        cosine: 0.2105,
        jaccard: 1.0,
        assertions_deleted: 0,
        test_ratio: 0.0,
        override: "Semantic drift override: PR intent deviates from prompt (F17=1)",
        source: "Preset Benchmark",
        shap_factors: [
          { name: "semantic_drift_flag = 1", value: "+4.88 SHAP", fill: "rose", width: "88%" },
          { name: "is_known_agent_bot = 1", value: "+0.16 SHAP", fill: "rose", width: "22%" },
          { name: "commit_count = 1", value: "+0.16 SHAP", fill: "rose", width: "22%" }
        ]
      }
    }
  };

  const inputTitle = document.getElementById("sim-title");
  const inputPrompt = document.getElementById("sim-prompt");
  const inputDiff = document.getElementById("sim-diff");
  const btnRunTriage = document.getElementById("btn-run-triage");
  const simBtnLabel = document.getElementById("sim-btn-label");
  const simSpinner = document.getElementById("sim-spinner");
  const simErrorBanner = document.getElementById("sim-error-banner");

  const simLoadingState = document.getElementById("sim-loading-state");
  const simEmptyState = document.getElementById("sim-empty-state");
  const simResultBody = document.getElementById("sim-result-body");

  const btnClean = document.getElementById("btn-scenario-clean");
  const btnTamper = document.getElementById("btn-scenario-tamper");
  const btnDrift = document.getElementById("btn-scenario-drift");

  const verdictBanner = document.getElementById("sim-verdict-banner");
  const verdictTag = document.getElementById("sim-verdict-tag");
  const verdictTitle = document.getElementById("sim-verdict-title");
  const verdictDesc = document.getElementById("sim-verdict-desc");
  const gaugeVal = document.getElementById("sim-gauge-val");
  const gaugeCaption = document.getElementById("sim-gauge-caption");
  const latencyBadge = document.getElementById("sim-latency-badge");
  const sourceBadge = document.getElementById("sim-source-badge");

  const statCC = document.getElementById("sim-stat-cc");
  const statNesting = document.getElementById("sim-stat-nesting");
  const statCosine = document.getElementById("sim-stat-cosine");
  const statJaccard = document.getElementById("sim-stat-jaccard");
  const statAssertions = document.getElementById("sim-stat-assertions");
  const statTestRatio = document.getElementById("sim-stat-testratio");
  const shapList = document.getElementById("sim-shap-list");

  function setError(message) {
    if (!simErrorBanner) return;
    if (!message) {
      simErrorBanner.hidden = true;
      simErrorBanner.textContent = "";
    } else {
      simErrorBanner.hidden = false;
      simErrorBanner.textContent = message;
    }
  }

  function setLoading(isLoading) {
    if (btnRunTriage) btnRunTriage.disabled = isLoading;
    if (simSpinner) simSpinner.hidden = !isLoading;
    if (simBtnLabel) simBtnLabel.textContent = isLoading ? "Inspecting..." : "Run ASTRA Inspection";
    if (simLoadingState) simLoadingState.hidden = !isLoading;
    if (simResultBody) simResultBody.hidden = isLoading;
    if (simEmptyState) simEmptyState.hidden = true;
  }

  function setScenario(key) {
    [btnClean, btnTamper, btnDrift].forEach(b => {
      if (b) {
        b.classList.remove("active");
        b.setAttribute("aria-pressed", "false");
      }
    });

    const btnMap = { clean: btnClean, tamper: btnTamper, drift: btnDrift };
    if (btnMap[key]) {
      btnMap[key].classList.add("active");
      btnMap[key].setAttribute("aria-pressed", "true");
    }

    const data = PRESET_SCENARIOS[key];
    if (!data) return;

    setError("");
    if (inputTitle) inputTitle.value = data.title;
    if (inputPrompt) inputPrompt.value = data.prompt;
    if (inputDiff) inputDiff.value = data.diff;

    if (simEmptyState) simEmptyState.hidden = true;
    if (simLoadingState) simLoadingState.hidden = true;
    if (simResultBody) simResultBody.hidden = false;

    renderTriageResult(data.result);
  }

  if (btnClean) btnClean.addEventListener("click", () => setScenario("clean"));
  if (btnTamper) btnTamper.addEventListener("click", () => setScenario("tamper"));
  if (btnDrift) btnDrift.addEventListener("click", () => setScenario("drift"));

  function renderTriageResult(res) {
    if (!verdictBanner) return;

    const tier = (res.risk_tier || "LOW").toUpperCase();
    verdictBanner.className = "verdict-banner " + tier.toLowerCase();
    if (verdictTag) verdictTag.textContent = tier;

    if (verdictTitle) {
      const label = tier === "HIGH" ? "BLOCKED" : (tier === "MEDIUM" ? "REVIEW REQUIRED" : "APPROVED");
      verdictTitle.textContent = `${tier} RISK (${label})`;
    }

    if (verdictDesc) {
      if (res.override) {
        verdictDesc.textContent = res.override;
      } else if (tier === "HIGH") {
        verdictDesc.textContent = "High defect probability detected. Merge blocked pending maintainer audit.";
      } else if (tier === "MEDIUM") {
        verdictDesc.textContent = "Moderate structural shift. Standard peer review checklist required.";
      } else {
        verdictDesc.textContent = "Fast-track merge eligible. No test suppression or semantic drift detected.";
      }
    }

    if (gaugeVal) gaugeVal.textContent = (res.probability * 100).toFixed(1) + "%";
    if (gaugeCaption) {
      gaugeCaption.textContent = (res.override && res.probability < 0.65) ? "Model Score (Override)" : "Defect Prob";
    }
    if (latencyBadge) latencyBadge.textContent = `${res.latency_ms.toFixed(1)} ms`;

    if (sourceBadge) {
      sourceBadge.textContent = res.source || "Preset Benchmark";
      sourceBadge.className = "source-tag";
      if (res.source === "Live API") {
        sourceBadge.classList.add("live");
      } else if (res.source === "Offline Heuristic") {
        sourceBadge.classList.add("fallback");
      }
    }

    if (statCC) statCC.textContent = (res.delta_cc > 0 ? "+" : "") + res.delta_cc;
    if (statNesting) statNesting.textContent = `Nesting: ${res.nesting >= 0 ? "+" : ""}${res.nesting}`;

    if (statCosine) {
      statCosine.textContent = (res.cosine * 100).toFixed(1) + "%";
      statCosine.className = "pillar-val " + (res.cosine < 0.45 ? "text-danger" : "text-success");
    }
    if (statJaccard) statJaccard.textContent = `Jaccard: ${res.jaccard.toFixed(2)}`;

    if (statAssertions) {
      statAssertions.textContent = `${res.assertions_deleted} Deleted`;
      statAssertions.className = "pillar-val " + (res.assertions_deleted > 0 ? "text-danger" : "text-success");
    }
    if (statTestRatio) statTestRatio.textContent = `Test Ratio: ${res.test_ratio.toFixed(2)}`;

    if (shapList) {
      shapList.innerHTML = "";
      (res.shap_factors || []).forEach(f => {
        const item = document.createElement("div");
        item.className = "shap-factor-row";
        const isDanger = f.fill === "rose" || (typeof f.value === "string" && f.value.includes("+"));
        const colorClass = isDanger ? "text-danger" : "text-success";
        const fillClass = isDanger ? "rose" : "emerald";

        const metaRow = document.createElement("div");
        metaRow.className = "shap-meta-row";

        const nameSpan = document.createElement("span");
        nameSpan.className = "shap-name";
        nameSpan.textContent = f.name;

        const valSpan = document.createElement("span");
        valSpan.className = `shap-val ${colorClass}`;
        valSpan.textContent = f.value;

        metaRow.appendChild(nameSpan);
        metaRow.appendChild(valSpan);

        const track = document.createElement("div");
        track.className = "progress-track";

        const fill = document.createElement("div");
        fill.className = `progress-fill ${fillClass}`;
        fill.style.width = f.width;
        track.appendChild(fill);

        item.appendChild(metaRow);
        item.appendChild(track);
        shapList.appendChild(item);
      });
    }
  }

  async function runTriageInspection() {
    const diff = (inputDiff ? inputDiff.value : "").trim();
    const title = (inputTitle ? inputTitle.value : "").trim();
    const prompt = (inputPrompt ? inputPrompt.value : "").trim();

    if (!diff) {
      setError("Paste a unified diff or select one of the benchmark scenarios above before running inspection.");
      if (simResultBody) simResultBody.hidden = true;
      if (simEmptyState) simEmptyState.hidden = false;
      return;
    }

    if (!title) {
      setError("Enter a pull request title so the semantic engine can compute alignment.");
      return;
    }

    setError("");
    setLoading(true);

    const addedCodeLines = (diff.match(/^\+[^+]/gm) || []).length;
    const addedTestLines = (diff.match(/^\+[^+].*(test_|def test|assert)/gm) || []).length;
    const deletedAssertions = (diff.match(/^-[^-].*(assert\s|assert\(|self\.assert|pytest\.raises)/gm) || []).length;

    let deltaCC = 0;
    diff.split("\n").forEach(line => {
      if (line.startsWith("+") && !line.startsWith("+++")) {
        if (/\b(if|elif|for|while|except|and|or)\b/.test(line)) {
          deltaCC++;
        }
      }
    });

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      const apiUrl = isLocal ? "/api/v1/triage" : "https://astra-08bw.onrender.com/api/v1/triage";

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_name: "demo/repo",
          pr_number: 1,
          title: title,
          issue_description: prompt || title,
          raw_diff: diff,
          author_login: "demo-agent",
          author_is_bot: true
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const liveData = await response.json();
        const summary = liveData.metrics_summary || {};
        const shapConverted = (liveData.top_risk_drivers || []).map(feat => {
          const isDanger = feat.impact === "INCREASES_RISK" || feat.shap_value > 0;
          const valStr = Number.isInteger(feat.feature_value)
            ? String(feat.feature_value)
            : (feat.feature_value !== null && feat.feature_value !== undefined ? Number(feat.feature_value).toFixed(2) : "");
          const label = valStr ? `${feat.feature_name} = ${valStr}` : feat.feature_name;
          return {
            name: label,
            value: `${feat.shap_value >= 0 ? "+" : ""}${Number(feat.shap_value).toFixed(2)} SHAP`,
            fill: isDanger ? "rose" : "emerald",
            width: `${Math.min(100, Math.max(18, Math.abs(feat.shap_value) * 18))}%`
          };
        });

        setLoading(false);
        renderTriageResult({
          risk_tier: liveData.risk_tier,
          probability: liveData.risk_probability,
          latency_ms: liveData.latency_ms || 45.0,
          delta_cc: summary.delta_cc !== undefined ? summary.delta_cc : deltaCC,
          nesting: summary.nesting_depth_delta !== undefined ? summary.nesting_depth_delta : 0,
          cosine: summary.intent_diff_cosine !== undefined ? summary.intent_diff_cosine : 0.0,
          jaccard: summary.entity_drift_jaccard !== undefined ? summary.entity_drift_jaccard : 0.0,
          assertions_deleted: summary.assertions_deleted !== undefined ? summary.assertions_deleted : deletedAssertions,
          test_ratio: summary.test_to_logic_ratio !== undefined ? summary.test_to_logic_ratio : (addedCodeLines > 0 ? addedTestLines / addedCodeLines : 0.0),
          override: liveData.override_applied,
          source: "Live API",
          shap_factors: shapConverted
        });
        return;
      }
    } catch (_err) {
      // Fall through to deterministic browser fallback when backend is unreachable
    }

    // Deterministic browser preview fallback when FastAPI backend is unreachable
    let tier = "LOW";
    let prob = 0.05;
    let override = null;

    if (deletedAssertions > 5 && addedTestLines === 0) {
      tier = "HIGH";
      prob = 0.9817;
      override = `Assertion deletion anomaly: Deleted ${deletedAssertions} assertions with 0 tests added`;
    } else if (diff.toLowerCase().includes("drop table") || (prompt.toLowerCase().includes("webhook") && diff.toLowerCase().includes("token"))) {
      tier = "HIGH";
      prob = 0.9817;
      override = "Semantic drift override: PR intent deviates from prompt (F17=1)";
    } else if (deltaCC > 8) {
      tier = "HIGH";
      prob = 0.745;
    } else if (deltaCC > 3) {
      tier = "MEDIUM";
      prob = 0.420;
    }

    const shapFactors = tier === "HIGH" ? [
      { name: deletedAssertions > 0 ? `assertions_deleted = ${deletedAssertions}` : "semantic_drift_flag = 1", value: "+4.88 SHAP", fill: "rose", width: "86%" },
      { name: `delta_cc = ${deltaCC}`, value: "+1.12 SHAP", fill: "rose", width: "44%" },
      { name: "is_known_agent_bot = 1", value: "+0.16 SHAP", fill: "rose", width: "22%" }
    ] : [
      { name: "semantic_drift_flag = 0", value: "-4.87 SHAP", fill: "emerald", width: "86%" },
      { name: "assertions_deleted = 0", value: "-0.85 SHAP", fill: "emerald", width: "40%" },
      { name: `delta_cc = ${deltaCC}`, value: "-0.42 SHAP", fill: "emerald", width: "26%" }
    ];

    setLoading(false);
    renderTriageResult({
      risk_tier: tier,
      probability: prob,
      latency_ms: 14.2,
      delta_cc: deltaCC,
      nesting: deltaCC > 4 ? 2 : 0,
      cosine: tier === "HIGH" ? 0.32 : 0.78,
      jaccard: tier === "HIGH" ? 0.85 : 0.35,
      assertions_deleted: deletedAssertions,
      test_ratio: addedCodeLines > 0 ? addedTestLines / addedCodeLines : 0.0,
      override: override,
      source: "Offline Heuristic",
      shap_factors: shapFactors
    });
  }

  if (btnRunTriage) {
    btnRunTriage.addEventListener("click", runTriageInspection);
  }

  // Initialize with Clean Scenario
  setScenario("clean");

  // Feature Matrix Tab Switching with ARIA sync
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      tabPanes.forEach(p => {
        p.classList.remove("active");
        p.hidden = true;
      });

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const targetId = btn.getAttribute("data-tab");
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add("active");
        targetPane.hidden = false;
      }
    });
  });

  // Copy Workflow YAML
  const btnCopyYaml = document.getElementById("btn-copy-yaml");
  const copyText = document.getElementById("copy-text");
  const yamlCode = document.getElementById("yaml-code");

  if (btnCopyYaml && yamlCode && copyText) {
    btnCopyYaml.addEventListener("click", () => {
      navigator.clipboard.writeText(yamlCode.textContent).then(() => {
        copyText.textContent = "Copied YAML";
        setTimeout(() => {
          copyText.textContent = "Copy Workflow YAML";
        }, 2000);
      });
    });
  }

  // Mobile Menu Toggle (accessible, Escape-closable)
  const mobileMenuToggle = document.getElementById("mobile-menu-toggle");
  const mobileNavDrawer = document.getElementById("mobile-nav-drawer");

  if (mobileMenuToggle && mobileNavDrawer) {
    const closeDrawer = () => {
      mobileNavDrawer.hidden = true;
      mobileMenuToggle.setAttribute("aria-expanded", "false");
      mobileMenuToggle.textContent = "Menu";
    };

    mobileMenuToggle.addEventListener("click", () => {
      const isOpen = mobileMenuToggle.getAttribute("aria-expanded") === "true";
      if (isOpen) {
        closeDrawer();
      } else {
        mobileNavDrawer.hidden = false;
        mobileMenuToggle.setAttribute("aria-expanded", "true");
        mobileMenuToggle.textContent = "Close";
      }
    });

    mobileNavDrawer.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", closeDrawer);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && mobileMenuToggle.getAttribute("aria-expanded") === "true") {
        closeDrawer();
        mobileMenuToggle.focus();
      }
    });
  }

  // Smooth Return to Top for Header & Footer Brand Logos
  const brandLinks = document.querySelectorAll(".nav-brand, .footer-brand-link");
  brandLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      const isLanding = window.location.pathname.endsWith("/landing") ||
                        window.location.pathname.endsWith("/landing/") ||
                        window.location.pathname === "/" ||
                        window.location.pathname.includes("index.html");
      if (isLanding) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (window.location.hash) {
          history.pushState(null, "", window.location.pathname);
        }
      }
    });
  });
});
