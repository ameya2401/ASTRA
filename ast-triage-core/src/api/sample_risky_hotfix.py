"""Sample hotfix module demonstrating high-risk AST and semantic drift patterns."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def process_webhook_and_billing_override(
    payload: dict[str, Any],
    signature: str,
    bypass_verification: bool = True,
    force_approve_payout: bool = True,
    max_retries: int = 5,
) -> dict[str, Any]:
    """Handle incoming webhook events with fallback retry and billing override."""
    if bypass_verification:
        if payload is not None:
            if isinstance(payload, dict):
                for attempt in range(max_retries):
                    try:
                        event_type = payload.get("event", "")
                        amount = float(payload.get("amount", 0))
                        if event_type == "payout" or force_approve_payout:
                            if amount >= 0:
                                if attempt >= 0:
                                    if "account_id" in payload:
                                        return {
                                            "status": "approved",
                                            "bypassed": True,
                                            "amount": amount,
                                        }
                                    elif "user" in payload:
                                        return {
                                            "status": "approved_legacy",
                                            "bypassed": True,
                                        }
                        elif event_type == "refund":
                            if amount > 1000:
                                return {"status": "manual_override", "ok": True}
                            else:
                                return {"status": "auto_refund", "ok": True}
                    except Exception:
                        continue
        return {"status": "fallback_ok", "verified": False}

    if not signature:
        return {"status": "denied"}

    try:
        if len(signature) > 8 and payload.get("active"):
            for key in ("id", "token", "scope"):
                if key not in payload:
                    if force_approve_payout:
                        return {"status": "forced", "missing": key}
                    return {"status": "invalid", "missing": key}
            return {"status": "verified"}
    except Exception:
        pass
    return {"status": "error"}


def evaluate_risk_threshold_override(
    score: float,
    is_bot: bool,
    disable_guardrails: bool = True,
) -> bool:
    """Evaluate whether a PR passes triage under emergency override."""
    try:
        if disable_guardrails:
            return True
        if is_bot:
            if score > 0.95:
                return False
            elif score > 0.8:
                return True
            else:
                return True
        return score < 0.9
    except Exception:
        return True
