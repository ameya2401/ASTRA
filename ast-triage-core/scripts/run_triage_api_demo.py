"""
scripts/run_triage_api_demo.py - Interactive CLI runner for Phase 5 API and Reporter.

Demonstrates end-to-end triage evaluation, REST endpoints, priority queue,
and GitHub markdown comment generation across multiple PR scenarios.

Usage:
    python scripts/run_triage_api_demo.py
"""
import json
import sys
import time
from pathlib import Path

# Ensure root package is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi.testclient import TestClient
from src.api.main import app
from src.api.schemas import PRWebhookPayload, TriageResponse
from src.integrations.reporter import generate_markdown_report


def print_banner(title: str) -> None:
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)


def run_demo() -> None:
    print_banner("ASTRA Phase 5: Live API & Reporter Verification")

    with TestClient(app) as client:
        # 1. Health check
        print("\n[Step 1] Checking API Health Endpoint (GET /api/v1/health)...")
        res = client.get("/api/v1/health")
        print(f"Status Code: {res.status_code}")
        print("Response Body:")
        print(json.dumps(res.json(), indent=2))
        assert res.status_code == 200

        # 2. Scenario A: Clean PR
        print_banner("Scenario A: Clean, Well-Tested PR (Expected LOW Risk)")
        clean_payload = {
            "repo_name": "django/django",
            "pr_number": 19280,
            "title": "Fix division by zero in Cart discount calculations",
            "issue_description": (
                "When an empty cart is evaluated with a percentage discount, "
                "a ZeroDivisionError is raised in calculate_ratio. Return 0.0 when items count is 0."
            ),
            "author_login": "contributor-jane",
            "author_is_bot": False,
            "agent_framework": "human",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "raw_diff": (
                "diff --git a/cart/calc.py b/cart/calc.py\n"
                "--- a/cart/calc.py\n"
                "+++ b/cart/calc.py\n"
                "@@ -10,1 +10,3 @@\n"
                "-    return total / items\n"
                "+    if items == 0:\n"
                "+        return 0.0\n"
                "+    return total / items\n"
                "diff --git a/tests/test_calc.py b/tests/test_calc.py\n"
                "--- a/tests/test_calc.py\n"
                "+++ b/tests/test_calc.py\n"
                "@@ -25,0 +25,3 @@\n"
                "+def test_zero_items():\n"
                "+    assert calculate_discount(0, 50) == 0.0\n"
            ),
            "ci_passed": True,
            "commit_count": 1,
        }

        t0 = time.perf_counter()
        res_clean = client.post("/api/v1/triage/analyze", json=clean_payload)
        t_clean = (time.perf_counter() - t0) * 1000.0

        clean_data = res_clean.json()
        print(f"HTTP Status:       {res_clean.status_code}")
        print(f"Calibrated Risk:   {clean_data['risk_probability']:.4f} ({clean_data['risk_probability'] * 100.0:.1f}%)")
        print(f"Assigned Tier:     {clean_data['risk_tier']}")
        print(f"Recommendation:    {clean_data['recommendation']}")
        print(f"Reported Latency:  {clean_data['latency_ms']} ms (Total HTTP: {t_clean:.1f} ms)")
        print("Top SHAP Drivers:")
        for driver in clean_data.get("top_risk_drivers", []):
            print(f"  * {driver['description']}")

        # 3. Scenario B: Test Cheat PR
        print_banner("Scenario B: Test Cheat PR (Expected HIGH Risk)")
        cheat_payload = {
            "repo_name": "django/django",
            "pr_number": 19281,
            "title": "Fix auth test failures",
            "issue_description": "Fix failing authentication unit tests when sessions expire.",
            "author_login": "autonomous-coder[bot]",
            "author_is_bot": True,
            "agent_framework": "devin",
            "base_sha": "c" * 40,
            "head_sha": "d" * 40,
            "raw_diff": (
                "diff --git a/tests/test_auth.py b/tests/test_auth.py\n"
                "--- a/tests/test_auth.py\n"
                "+++ b/tests/test_auth.py\n"
                "@@ -15,7 +15,0 @@\n"
                "-    assert auth.verify_token(expired_tok) is False\n"
                "-    assert auth.verify_token(malformed_tok) is False\n"
                "-    assert auth.is_session_active(user_id) is False\n"
                "-    assert auth.validate_credentials('bad', 'bad') is False\n"
                "-    assert auth.check_password_hash(bad_hash) is False\n"
                "-    assert auth.enforce_mfa(user_id) is True\n"
                "-    assert auth.is_admin(user_id) is False\n"
            ),
            "ci_passed": True,
            "commit_count": 1,
        }

        res_cheat = client.post("/api/v1/triage/analyze", json=cheat_payload)
        cheat_data = res_cheat.json()
        print(f"HTTP Status:       {res_cheat.status_code}")
        print(f"Calibrated Risk:   {cheat_data['risk_probability']:.4f} ({cheat_data['risk_probability'] * 100.0:.1f}%)")
        print(f"Assigned Tier:     {cheat_data['risk_tier']}")
        print(f"Override Trigger:  {cheat_data.get('override_applied')}")
        print(f"Recommendation:    {cheat_data['recommendation']}")

        # 4. Scenario C: Semantic Drift PR
        print_banner("Scenario C: Semantic Drift PR (Expected HIGH Risk)")
        drift_payload = {
            "repo_name": "django/django",
            "pr_number": 19282,
            "title": "Update README docs for Python 3.12",
            "issue_description": "Update installation instructions in README.md for Python 3.12 support.",
            "author_login": "openhands[bot]",
            "author_is_bot": True,
            "agent_framework": "openhands",
            "base_sha": "e" * 40,
            "head_sha": "f" * 40,
            "raw_diff": (
                "diff --git a/django/db/backends/base/base.py b/django/db/backends/base/base.py\n"
                "--- a/django/db/backends/base/base.py\n"
                "+++ b/django/db/backends/base/base.py\n"
                "@@ -50,2 +50,2 @@\n"
                "-    self.max_connections = 10\n"
                "+    self.max_connections = 9999\n"
            ),
            "ci_passed": True,
            "commit_count": 1,
        }

        res_drift = client.post("/api/v1/triage/analyze", json=drift_payload)
        drift_data = res_drift.json()
        print(f"HTTP Status:       {res_drift.status_code}")
        print(f"Calibrated Risk:   {drift_data['risk_probability']:.4f} ({drift_data['risk_probability'] * 100.0:.1f}%)")
        print(f"Assigned Tier:     {drift_data['risk_tier']}")
        print(f"Override Trigger:  {drift_data.get('override_applied')}")

        # 5. Maintainer Prioritization Queue
        print_banner("Maintainer Queue (GET /api/v1/triage/queue/django/django)")
        res_queue = client.get("/api/v1/triage/queue/django/django?sort_by=risk_asc")
        queue_items = res_queue.json()
        print(f"Retrieved {len(queue_items)} pull requests from database queue:")
        for item in queue_items:
            tier = item["risk_tier"]
            prob = item["risk_probability"] * 100.0
            print(f"  * PR #{item['pr_number']}: [{tier} - {prob:.1f}%] by {item['author_login']} | {item['title']}")

        # 6. Markdown PR Comment Preview
        print_banner("Generated GitHub PR Comment Preview (Markdown Output)")
        triage_obj = TriageResponse(**clean_data)
        markdown_comment = generate_markdown_report(triage_obj, repo_name="django/django", pr_number=19280)
        print(markdown_comment)

    print_banner("Phase 5 Live Verification Completed Successfully")


if __name__ == "__main__":
    run_demo()
