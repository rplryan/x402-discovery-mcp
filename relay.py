"""
scout_relay — Intelligent Payment Router for AI Agents
Routing + execution logic. Imported by relay_tools.py for MCP registration.
"""
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

DISCOVERY_API = os.getenv("DISCOVERY_API_URL", "https://x402-discovery-api.onrender.com")
RELAY_VERSION = "1.0.0"
RELAY_PRICE_USD = float(os.getenv("RELAY_PRICE_USD", "0.003"))
RELAY_RATE = 0.025  # 2.5% of downstream transaction value
MIN_TRUST_SCORE = int(os.getenv("RELAY_MIN_TRUST_SCORE", "50"))
MAX_RETRY_ATTEMPTS = 3
SPEND_LOG_PATH = os.getenv("RELAY_SPEND_LOG", "/tmp/relay_spend.jsonl")

logger = logging.getLogger("scout_relay")


@dataclass
class RouteResult:
    success: bool
    data: Any = None
    cost_paid_usd: float = 0.0
    provider_url: str = ""
    provider_name: str = ""
    attempts: int = 0
    error: str = ""
    error_code: str = ""  # budget_exceeded | all_providers_failed | awal_timeout | discovery_error


def _compute_relay_fee(downstream_usd: float) -> float:
    """fee = max(floor, rate * downstream_tx_value)"""
    return max(RELAY_PRICE_USD, RELAY_RATE * downstream_usd)


def _log_spend(entry: dict) -> None:
    try:
        with open(SPEND_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write spend log: {e}")


def _discover_providers(
    capability: str,
    max_price_usd: float,
    min_trust_score: int = MIN_TRUST_SCORE,
) -> list:
    """Query x402-discovery-mcp catalog, return ranked providers above trust threshold."""
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{DISCOVERY_API}/catalog",
                params={"q": capability, "max_price": max_price_usd},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"Discovery API error: {e}")
        return []

    services = data.get("services", [])
    candidates = [
        s for s in services
        if s.get("trust_score", 0) >= min_trust_score
        and float(s.get("price_per_call", 9999)) <= max_price_usd
    ]
    return candidates


def _execute_via_awal(endpoint_url: str, amount_usdc: float, timeout: int = 30) -> dict:
    """
    Execute x402 payment via Coinbase Agentic Wallet CLI subprocess.
    Returns {"success": bool, "output": str, "error": str}

    If awal is unavailable, falls back to a structured error (caller handles fallback).
    Note: awal authenticate is ONE-TIME interactive. Subsequent calls are headless.
    """
    try:
        result = subprocess.run(
            ["npx", "awal", "pay-for-service",
             "--endpoint", endpoint_url,
             "--amount", str(amount_usdc)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip(), "error": ""}
        return {"success": False, "output": "", "error": result.stderr.strip() or result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "awal_timeout"}
    except FileNotFoundError:
        return {"success": False, "output": "", "error": "awal_not_installed"}


def relay_route(
    intent: str,
    budget_usd: float,
    wallet: Optional[str] = None,
    min_trust_score: int = MIN_TRUST_SCORE,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
) -> RouteResult:
    """
    Core routing function. Discovers providers, selects best, executes via awal.
    Retries up to max_attempts with next-ranked provider on failure.
    """
    if budget_usd <= 0:
        return RouteResult(
            success=False,
            error="budget_usd must be greater than 0",
            error_code="budget_exceeded",
        )

    relay_fee = _compute_relay_fee(budget_usd)
    effective_budget = budget_usd - relay_fee
    if effective_budget <= 0:
        return RouteResult(
            success=False,
            error=f"Budget ${budget_usd:.4f} is below relay fee ${relay_fee:.4f}",
            error_code="budget_exceeded",
        )

    providers = _discover_providers(intent, effective_budget, min_trust_score)
    if not providers:
        return RouteResult(
            success=False,
            error=f"No providers found for '{intent}' under ${effective_budget:.4f} with trust_score >= {min_trust_score}",
            error_code="all_providers_failed",
        )

    attempts = 0
    last_error = ""

    for provider in providers[:max_attempts]:
        attempts += 1
        url = provider.get("endpoint_url") or provider.get("url", "")
        name = provider.get("name", url)
        price = float(provider.get("price_per_call", 0))

        if price > effective_budget:
            last_error = f"Provider {name} costs ${price:.4f}, exceeds remaining budget"
            continue

        exec_result = _execute_via_awal(url, price)

        _log_spend({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intent": intent,
            "provider": name,
            "provider_url": url,
            "amount_paid_usd": price,
            "relay_fee_usd": relay_fee,
            "success": exec_result["success"],
            "error": exec_result.get("error", ""),
            "attempt": attempts,
        })

        if exec_result["success"]:
            return RouteResult(
                success=True,
                data=exec_result["output"],
                cost_paid_usd=price + relay_fee,
                provider_url=url,
                provider_name=name,
                attempts=attempts,
            )

        err = exec_result.get("error", "unknown")
        if err == "awal_timeout":
            return RouteResult(
                success=False,
                error="Payment execution timed out — not retrying to avoid duplicate charges",
                error_code="awal_timeout",
                attempts=attempts,
            )

        last_error = f"Provider {name} failed: {err}"
        logger.warning(f"Attempt {attempts} failed for {name}: {err}")

    return RouteResult(
        success=False,
        error=f"All {attempts} provider(s) failed. Last error: {last_error}",
        error_code="all_providers_failed",
        attempts=attempts,
    )


def relay_execute(endpoint_url: str, amount_usdc: float, wallet: Optional[str] = None) -> dict:
    """Direct execution against a known x402 endpoint. Skips discovery/ranking."""
    result = _execute_via_awal(endpoint_url, amount_usdc)
    _log_spend({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent": "direct_execute",
        "provider_url": endpoint_url,
        "amount_paid_usd": amount_usdc,
        "success": result["success"],
        "error": result.get("error", ""),
    })
    return result


def relay_discover(capability: str, max_price_usd: float = 0.50, min_trust_score: int = MIN_TRUST_SCORE) -> list:
    """Thin wrapper over discovery catalog. Returns ranked providers without executing."""
    return _discover_providers(capability, max_price_usd, min_trust_score)


def relay_audit(limit: int = 50) -> list:
    """Return last N spend log entries."""
    try:
        with open(SPEND_LOG_PATH) as f:
            lines = f.readlines()
        entries = [json.loads(line) for line in lines if line.strip()]
        return entries[-limit:]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [{"error": str(e)}]
