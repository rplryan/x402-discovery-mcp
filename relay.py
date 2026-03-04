"""
scout_relay — Intelligent Payment Router for AI Agents
Routing + execution logic. Imported by relay_tools.py for MCP registration.
"""
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

# x402 Python SDK (headless, stateless — no subprocess, no session files)
from x402 import x402Client
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from x402.http.clients import x402HttpxClient
from eth_account import Account

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
    error_code: str = ""  # budget_exceeded | all_providers_failed | payment_timeout | sdk_error | discovery_error


def _compute_relay_fee(downstream_usd: float) -> float:
    """fee = max(floor, rate * downstream_tx_value)"""
    return max(RELAY_PRICE_USD, RELAY_RATE * downstream_usd)


def _log_spend(entry: dict) -> None:
    try:
        with open(SPEND_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write spend log: {e}")


def _get_x402_client() -> x402Client:
    """Build a stateless x402Client from EVM_PRIVATE_KEY env var."""
    private_key = os.environ.get("EVM_PRIVATE_KEY")
    if not private_key:
        raise ValueError("EVM_PRIVATE_KEY env var not set")
    account = Account.from_key(private_key)
    client = x402Client()
    register_exact_evm_client(client, EthAccountSigner(account))
    return client


async def _execute_payment(endpoint_url: str, amount_usdc: float, timeout: int = 30) -> dict:
    """
    Execute x402 payment via the x402 Python SDK. Fully headless and stateless.
    The SDK auto-handles the 402 challenge → EIP-3009 signed payment → retry cycle.
    Returns {"success": bool, "output": str, "error": str}
    """
    try:
        client = _get_x402_client()
        async with x402HttpxClient(client) as http:
            response = await asyncio.wait_for(
                http.get(endpoint_url),
                timeout=timeout,
            )
            await response.aread()
            if response.is_success:
                return {"success": True, "output": response.text, "error": ""}
            return {
                "success": False,
                "output": "",
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }
    except asyncio.TimeoutError:
        return {"success": False, "output": "", "error": "payment_timeout"}
    except ValueError as e:
        # EVM_PRIVATE_KEY not set or invalid
        return {"success": False, "output": "", "error": f"sdk_error: {e}"}
    except Exception as e:
        return {"success": False, "output": "", "error": f"sdk_error: {e}"}


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


def relay_route(
    intent: str,
    budget_usd: float,
    wallet: Optional[str] = None,
    min_trust_score: int = MIN_TRUST_SCORE,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
) -> RouteResult:
    """
    Core routing function. Discovers providers, selects best, executes via x402 Python SDK.
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

        exec_result = asyncio.run(_execute_payment(url, price))

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
        if err == "payment_timeout":
            return RouteResult(
                success=False,
                error="Payment execution timed out — not retrying to avoid duplicate charges",
                error_code="payment_timeout",
                attempts=attempts,
            )
        if err.startswith("sdk_error: EVM_PRIVATE_KEY"):
            return RouteResult(
                success=False,
                error="EVM_PRIVATE_KEY not configured on this relay — payment execution unavailable",
                error_code="sdk_error",
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
    result = asyncio.run(_execute_payment(endpoint_url, amount_usdc))
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
