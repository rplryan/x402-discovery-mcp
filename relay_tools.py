"""
scout_relay MCP Tools — registers relay tools into the FastMCP instance from server.py.
Import this module AFTER creating the mcp instance in server.py.
"""
from __future__ import annotations

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from relay import (
    RELAY_PRICE_USD,
    RELAY_VERSION,
    relay_audit,
    relay_discover,
    relay_execute,
    relay_route,
)


def register_relay_tools(mcp: FastMCP) -> None:
    """Register all scout_relay MCP tools into an existing FastMCP instance."""

    @mcp.tool(
        description=(
            f"Route and execute a payment for any x402 service by natural-language intent. "
            f"Discovers the best available provider from the x402 catalog, executes payment "
            f"via Coinbase Agentic Wallet, and returns the result. "
            f"Charges ${RELAY_PRICE_USD:.3f} USDC routing fee per call (scout_relay v{RELAY_VERSION})."
        )
    )
    def scout_route(
        intent: str,
        budget_usd: float,
        wallet: Optional[str] = None,
        min_trust_score: int = 50,
    ) -> str:
        """Route and execute a payment for any x402 service by natural-language intent.

        Args:
            intent: What you need in plain English (e.g. "current BTC price").
            budget_usd: Maximum total spend in USD including routing fee.
            wallet: Coinbase Agentic Wallet session token (optional — uses env if omitted).
            min_trust_score: Minimum trust score 0-100 for provider selection (default 50).

        Returns:
            Result from the provider, or structured error if routing failed.
        """
        result = relay_route(intent, budget_usd, wallet, min_trust_score)
        if result.success:
            return json.dumps({
                "success": True,
                "data": result.data,
                "provider": result.provider_name,
                "provider_url": result.provider_url,
                "cost_paid_usd": round(result.cost_paid_usd, 6),
                "attempts": result.attempts,
            })
        return json.dumps({
            "success": False,
            "error": result.error,
            "error_code": result.error_code,
            "attempts": result.attempts,
        })

    @mcp.tool(
        description=(
            "Discover x402 providers for a capability without executing payment. "
            "Returns ranked list with trust scores, prices, and endpoints."
        )
    )
    def scout_discover(
        capability: str,
        max_price_usd: float = 0.50,
        min_trust_score: int = 50,
    ) -> str:
        """Find available x402 providers for a capability without executing.

        Args:
            capability: What you're looking for (e.g. "weather data", "crypto prices").
            max_price_usd: Maximum price per call in USD (default 0.50).
            min_trust_score: Minimum trust score 0-100 (default 50).

        Returns:
            Ranked list of providers with trust scores, prices, and endpoints.
        """
        providers = relay_discover(capability, max_price_usd, min_trust_score)
        if not providers:
            return f"No providers found for '{capability}' under ${max_price_usd}/call with trust_score >= {min_trust_score}."

        lines = [f"Found {len(providers)} provider(s) for '{capability}':\n"]
        for i, p in enumerate(providers[:10], 1):
            lines.append(
                f"{i}. {p.get('name', '?')} — trust: {p.get('trust_score', '?')}/100 "
                f"| ${p.get('price_per_call', '?')}/call\n"
                f"   {p.get('endpoint_url') or p.get('url', '?')}"
            )
        return "\n".join(lines)

    @mcp.tool(
        description=(
            "Execute payment directly against a known x402 endpoint. "
            "Use when you already know the endpoint URL and price — skips discovery."
        )
    )
    def scout_execute(
        endpoint_url: str,
        amount_usdc: float,
        wallet: Optional[str] = None,
    ) -> str:
        """Execute x402 payment directly against a known endpoint.

        Args:
            endpoint_url: The x402-gated endpoint URL.
            amount_usdc: Amount to pay in USDC.
            wallet: Coinbase Agentic Wallet session token (optional).

        Returns:
            Response from the provider endpoint, or error details.
        """
        result = relay_execute(endpoint_url, amount_usdc, wallet)
        return json.dumps(result)

    @mcp.tool(
        description="View recent scout_relay transaction history — what was purchased, which provider, cost paid."
    )
    def scout_audit(limit: int = 20) -> str:
        """View recent scout_relay transaction log.

        Args:
            limit: Number of recent transactions to return (default 20, max 100).

        Returns:
            Recent transaction log with timestamps, providers, and costs.
        """
        limit = min(limit, 100)
        entries = relay_audit(limit)
        if not entries:
            return "No transactions recorded yet."

        lines = [f"Last {len(entries)} scout_relay transactions:\n"]
        for e in entries:
            status = "✅" if e.get("success") else "❌"
            lines.append(
                f"{status} {e.get('timestamp', '?')[:19]} | "
                f"{e.get('provider', e.get('provider_url', '?'))[:40]} | "
                f"${e.get('amount_paid_usd', 0):.4f}"
                + (f" | {e.get('error', '')}" if not e.get("success") else "")
            )
        return "\n".join(lines)
