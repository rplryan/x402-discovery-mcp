"""
scout_relay — Intelligent Payment Router for AI Agents
Routing + execution logic. Imported by relay_tools.py for MCP registration.

Phase 2 additions:
- Agent ID system (per-agent tracking in /tmp/relay_agent_budgets.json)
- Budget enforcement (daily cap, configurable via AGENT_DAILY_BUDGET_USD)
- Placement bid tiebreaker (placement_bids.json, re-read on mtime change)
- Enhanced spend logging (agent_id, relay_fee_usd, downstream_provider_url, placement_bid_applied)
"""
import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from x402 import x402Client
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from x402.http.clients import x402HttpxClient
from eth_account import Account

DISCOVERY_API = os.getenv("DISCOVERY_API_URL", "https://x402-discovery-api.onrender.com")
RELAY_VERSION = "2.0.0"
RELAY_PRICE_USD = float(os.getenv("RELAY_PRICE_USD", "0.003"))
RELAY_RATE = 0.025  # 2.5% of downstream transaction value
MIN_TRUST_SCORE = int(os.getenv("RELAY_MIN_TRUST_SCORE", "50"))
MAX_RETRY_ATTEMPTS = 3
SPEND_LOG_PATH = os.getenv("RELAY_SPEND_LOG", "/tmp/relay_spend.jsonl")

# --- Phase 2: Agent budgets ---
AGENT_BUDGETS_PATH = "/tmp/relay_agent_budgets.json"
AGENT_DAILY_CAP_USD = float(os.getenv("AGENT_DAILY_BUDGET_USD", "10.0"))

# --- Phase 2: Placement bids ---
_PLACEMENT_BIDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "placement_bids.json")
_placement_bids_cache: list = []
_placement_bids_mtime: float = 0.0

logger = logging.getLogger("scout_relay")


@dataclass
class RouteResult:
    success: bool
    data: Any = None
    cost_paid_usd: float = 0.0
    provider_url: str = ""
    provider_name: str = ""
    attempts: int = 0
    agent_id: str = ""
    relay_fee_usd: float = 0.0
    placement_bid_applied: bool = False
    error: str = ""
    error_code: str = ""  # budget_exceeded | daily_budget_exceeded | all_providers_failed | payment_timeout | sdk_error | discovery_error


# ---------------------------------------------------------------------------
# Fee calculation
# ---------------------------------------------------------------------------

def _compute_relay_fee(downstream_usd: float) -> float:
    """fee = max(floor, rate * downstream_tx_value)"""
    return max(RELAY_PRICE_USD, RELAY_RATE * downstream_usd)


# ---------------------------------------------------------------------------
# Spend logging (Phase 2: enhanced fields)
# ---------------------------------------------------------------------------

def _log_spend(entry: dict) -> None:
    try:
        with open(SPEND_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write spend log: {e}")


# ---------------------------------------------------------------------------
# Phase 2: Agent ID system
# ---------------------------------------------------------------------------

def _load_agent_budgets() -> dict:
    """Load per-agent budget tracking from disk. Returns empty dict if file missing."""
    try:
        with open(AGENT_BUDGETS_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_agent_budgets(budgets: dict) -> None:
    try:
        with open(AGENT_BUDGETS_PATH, "w") as f:
            json.dump(budgets, f)
    except Exception as e:
        logger.warning(f"Failed to save agent budgets: {e}")


def _get_or_create_agent(budgets: dict, agent_id: str) -> dict:
    """Return agent record, resetting daily counters if UTC date has changed."""
    today = datetime.now(timezone.utc).date().isoformat()
    if agent_id not in budgets:
        budgets[agent_id] = {
            "daily_spent": 0.0,
            "weekly_spent": 0.0,
            "monthly_spent": 0.0,
            "call_count": 0,
            "last_call_utc": None,
            "budget_date": today,
        }
    rec = budgets[agent_id]
    # Reset daily counter at UTC midnight
    if rec.get("budget_date") != today:
        rec["daily_spent"] = 0.0
        rec["budget_date"] = today
    return rec


def _derive_agent_id(payment_header: Optional[str], provided_id: Optional[str]) -> str:
    """Derive agent_id from provided value, payment header wallet, or generate UUID."""
    if provided_id:
        return provided_id
    if payment_header:
        try:
            import base64
            decoded = base64.b64decode(payment_header).decode()
            data = json.loads(decoded)
            # Try to extract wallet/from address from payment payload
            payload = data.get("payload", {})
            from_addr = (
                payload.get("from")
                or payload.get("authorization", {}).get("from")
                or payload.get("wallet")
            )
            if from_addr:
                return f"wallet:{from_addr.lower()}"
        except Exception:
            pass
    return f"anon:{uuid.uuid4().hex[:12]}"


def _check_agent_budget(agent_id: str, cost_usd: float) -> tuple[bool, str, dict]:
    """
    Check if agent can afford this call.
    Returns (allowed, error_msg, budgets_dict).
    Caller must call _save_agent_budgets() after successful spend.
    """
    budgets = _load_agent_budgets()
    rec = _get_or_create_agent(budgets, agent_id)
    cap = AGENT_DAILY_CAP_USD
    if rec["daily_spent"] + cost_usd > cap:
        return (
            False,
            f"daily_budget_exceeded",
            budgets,
        )
    return True, "", budgets


def _record_agent_spend(budgets: dict, agent_id: str, cost_usd: float) -> None:
    """Update agent spend counters and persist."""
    rec = _get_or_create_agent(budgets, agent_id)
    rec["daily_spent"] = round(rec["daily_spent"] + cost_usd, 6)
    rec["weekly_spent"] = round(rec["weekly_spent"] + cost_usd, 6)
    rec["monthly_spent"] = round(rec["monthly_spent"] + cost_usd, 6)
    rec["call_count"] += 1
    rec["last_call_utc"] = datetime.now(timezone.utc).isoformat()
    _save_agent_budgets(budgets)


# ---------------------------------------------------------------------------
# Phase 2: Placement bids
# ---------------------------------------------------------------------------

def _load_placement_bids() -> list:
    """Load placement_bids.json, using mtime cache to avoid redundant disk reads."""
    global _placement_bids_cache, _placement_bids_mtime
    try:
        mtime = os.path.getmtime(_PLACEMENT_BIDS_FILE)
        if mtime == _placement_bids_mtime:
            return _placement_bids_cache
        with open(_PLACEMENT_BIDS_FILE) as f:
            data = json.load(f)
        active = [b for b in data if b.get("active", False) and not b.get("_comment")]
        _placement_bids_cache = active
        _placement_bids_mtime = mtime
        logger.info(f"Loaded {len(active)} active placement bids")
        return active
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning(f"Failed to load placement_bids.json: {e}")
        return []


def _apply_placement_bids(providers: list) -> tuple[list, dict]:
    """
    Apply placement bid tiebreaker. Bid wins ties ONLY — never overrides trust score ordering.
    Returns (reranked_providers, bid_map) where bid_map = {url: bid_per_tx_usd}.
    """
    bids = _load_placement_bids()
    if not bids:
        return providers, {}

    bid_map = {b["provider_url"]: b["bid_per_tx_usd"] for b in bids}

    def sort_key(s):
        trust = s.get("trust_score", 0)
        bid = bid_map.get(s.get("url", ""), 0.0)
        return (-trust, -bid)  # descending trust, then descending bid as tiebreaker

    reranked = sorted(providers, key=sort_key)
    return reranked, bid_map


# ---------------------------------------------------------------------------
# x402 SDK helpers
# ---------------------------------------------------------------------------

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
        return {"success": False, "output": "", "error": f"sdk_error: {e}"}
    except Exception as e:
        return {"success": False, "output": "", "error": f"sdk_error: {e}"}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

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

    services = data.get("endpoints", [])
    candidates = [
        s for s in services
        if s.get("trust_score", 0) >= min_trust_score
        and float(s.get("price_usd", 9999)) <= max_price_usd
    ]
    return candidates


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def relay_route(
    intent: str,
    budget_usd: float,
    wallet: Optional[str] = None,
    min_trust_score: int = MIN_TRUST_SCORE,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    agent_id: Optional[str] = None,
    payment_header: Optional[str] = None,
) -> RouteResult:
    """
    Core routing function. Discovers providers, applies placement bids, executes via x402 SDK.
    Phase 2: checks per-agent daily budget before routing.
    """
    # Derive agent ID
    resolved_agent_id = _derive_agent_id(payment_header, agent_id)

    if budget_usd <= 0:
        return RouteResult(
            success=False,
            error="budget_usd must be greater than 0",
            error_code="budget_exceeded",
            agent_id=resolved_agent_id,
        )

    relay_fee = _compute_relay_fee(budget_usd)
    effective_budget = budget_usd - relay_fee
    if effective_budget <= 0:
        return RouteResult(
            success=False,
            error=f"Budget ${budget_usd:.4f} is below relay fee ${relay_fee:.4f}",
            error_code="budget_exceeded",
            agent_id=resolved_agent_id,
        )

    # Phase 2: per-agent daily budget check
    allowed, err_code, budgets = _check_agent_budget(resolved_agent_id, relay_fee)
    if not allowed:
        cap = AGENT_DAILY_CAP_USD
        rec = budgets.get(resolved_agent_id, {})
        return RouteResult(
            success=False,
            error="Agent daily budget exceeded. Spent: {:0.4f}".format(rec.get("daily_spent", 0)),
            error_code="daily_budget_exceeded",
            agent_id=resolved_agent_id,
        )

    providers = _discover_providers(intent, effective_budget, min_trust_score)
    if not providers:
        return RouteResult(
            success=False,
            error="No providers found for {} under ${:.4f} with trust_score >= {}".format(intent, effective_budget, min_trust_score),
            error_code="all_providers_failed",
            agent_id=resolved_agent_id,
        )

    # Phase 2: apply placement bid tiebreaker
    ranked_providers, bid_map = _apply_placement_bids(providers)

    attempts = 0
    last_error = ""

    for provider in ranked_providers[:max_attempts]:
        attempts += 1
        url = provider.get("url", "")
        name = provider.get("name", url)
        price = float(provider.get("price_usd", 0))
        bid_applied = url in bid_map

        if price > effective_budget:
            last_error = f"Provider {name} costs ${price:.4f}, exceeds remaining budget"
            continue

        exec_result = await _execute_payment(url, price)

        # Phase 2: enhanced spend log
        _log_spend({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": resolved_agent_id,
            "intent": intent,
            "provider": name,
            "downstream_provider_url": url,
            "amount_paid_usd": price,
            "relay_fee_usd": round(relay_fee, 6),
            "placement_bid_applied": bid_applied,
            "success": exec_result["success"],
            "error": exec_result.get("error", ""),
            "attempt": attempts,
        })

        if exec_result["success"]:
            # Record agent spend
            _record_agent_spend(budgets, resolved_agent_id, price + relay_fee)
            return RouteResult(
                success=True,
                data=exec_result["output"],
                cost_paid_usd=price + relay_fee,
                provider_url=url,
                provider_name=name,
                attempts=attempts,
                agent_id=resolved_agent_id,
                relay_fee_usd=round(relay_fee, 6),
                placement_bid_applied=bid_applied,
            )

        err = exec_result.get("error", "unknown")
        if err == "payment_timeout":
            return RouteResult(
                success=False,
                error="Payment execution timed out — not retrying to avoid duplicate charges",
                error_code="payment_timeout",
                attempts=attempts,
                agent_id=resolved_agent_id,
            )
        if err.startswith("sdk_error: EVM_PRIVATE_KEY"):
            return RouteResult(
                success=False,
                error="EVM_PRIVATE_KEY not configured on this relay — payment execution unavailable",
                error_code="sdk_error",
                attempts=attempts,
                agent_id=resolved_agent_id,
            )

        last_error = f"Provider {name} failed: {err}"
        logger.warning(f"Attempt {attempts} failed for {name}: {err}")

    return RouteResult(
        success=False,
        error=f"All {attempts} provider(s) failed. Last error: {last_error}",
        error_code="all_providers_failed",
        attempts=attempts,
        agent_id=resolved_agent_id,
    )


async def relay_execute(
    endpoint_url: str,
    amount_usdc: float,
    wallet: Optional[str] = None,
    agent_id: Optional[str] = None,
    payment_header: Optional[str] = None,
) -> dict:
    """Direct execution against a known x402 endpoint. Skips discovery/ranking."""
    resolved_agent_id = _derive_agent_id(payment_header, agent_id)
    result = await _execute_payment(endpoint_url, amount_usdc)
    relay_fee = _compute_relay_fee(amount_usdc)
    _log_spend({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": resolved_agent_id,
        "intent": "direct_execute",
        "downstream_provider_url": endpoint_url,
        "amount_paid_usd": amount_usdc,
        "relay_fee_usd": round(relay_fee, 6),
        "placement_bid_applied": False,
        "success": result["success"],
        "error": result.get("error", ""),
    })
    return result


async def relay_discover(
    capability: str,
    max_price_usd: float = 0.50,
    min_trust_score: int = MIN_TRUST_SCORE,
) -> list:
    """Thin wrapper over discovery catalog with placement bids applied. Returns ranked providers."""
    providers = _discover_providers(capability, max_price_usd, min_trust_score)
    ranked, _ = _apply_placement_bids(providers)
    return ranked


async def relay_audit(
    limit: int = 50,
    agent_id: Optional[str] = None,
    since: Optional[str] = None,
) -> list:
    """Return spend log entries with optional agent_id and since filters."""
    try:
        with open(SPEND_LOG_PATH) as f:
            lines = f.readlines()
        entries = [json.loads(line) for line in lines if line.strip()]

        if agent_id:
            entries = [e for e in entries if e.get("agent_id") == agent_id]
        if since:
            entries = [e for e in entries if e.get("timestamp", "") >= since]

        return entries[-limit:]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [{"error": str(e)}]


def get_agent_budget_status(agent_id: str) -> dict:
    """Return current budget status for an agent. Used by /audit endpoint."""
    budgets = _load_agent_budgets()
    rec = _get_or_create_agent(budgets, agent_id)
    return {
        "agent_id": agent_id,
        "daily_spent": rec["daily_spent"],
        "daily_cap": AGENT_DAILY_CAP_USD,
        "daily_remaining": round(max(0.0, AGENT_DAILY_CAP_USD - rec["daily_spent"]), 6),
        "weekly_spent": rec["weekly_spent"],
        "monthly_spent": rec["monthly_spent"],
        "call_count": rec["call_count"],
        "last_call_utc": rec["last_call_utc"],
        "budget_date": rec["budget_date"],
    }
