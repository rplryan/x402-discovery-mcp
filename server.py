#!/usr/bin/env python3
"""x402 Discovery MCP Server.

Exposes the x402 Service Discovery API as MCP tools so that Claude,
Cursor, Windsurf, and any other MCP-compatible host can discover and
interact with x402-payable services natively.

Run directly:
    python server.py

Or register in your MCP config (see README.md).
"""
from __future__ import annotations

import json
from typing import Optional

import requests
from mcp.server.fastmcp import FastMCP

DISCOVERY_BASE_URL = "https://x402-discovery-api.onrender.com"

mcp = FastMCP(
    "x402-discovery",
    instructions=(
        "Use these tools when you need to find or interact with paid API services "
        "in the x402 ecosystem. x402 services charge micro-payments per call (typically "
        "$0.001–$0.50) and require no API keys — payment IS the auth."
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _catalog() -> list[dict]:
    """Fetch free catalog from discovery API."""
    resp = requests.get(f"{DISCOVERY_BASE_URL}/catalog", timeout=15)
    resp.raise_for_status()
    return resp.json().get("services", [])


def _format_service(s: dict, rank: int) -> str:
    price = s.get("price_per_call", "?")
    quality = s.get("quality_tier", "unverified")
    uptime = s.get("uptime_pct", "?")
    tags = ", ".join(s.get("capability_tags", []))
    return (
        f"{rank}. **{s.get('name', 'Unknown')}** [{quality.upper()}]\n"
        f"   ID: {s.get('service_id', '?')}\n"
        f"   URL: {s.get('endpoint_url', s.get('url', '?'))}\n"
        f"   Price: ${price}/call  |  Uptime: {uptime}%\n"
        f"   Tags: {tags}\n"
        f"   {s.get('description', '')}"
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Search the x402 service catalog for APIs that match a capability or query. "
        "Use this when you need to find a paid service to accomplish a task — for example "
        "when you need web research, data enrichment, AI generation, or any specialized "
        "computation. Returns the top 5 quality-ranked results."
    )
)
def x402_discover(
    capability: Optional[str] = None,
    max_price_usd: float = 0.50,
    query: Optional[str] = None,
) -> str:
    """Quality-ranked service discovery.

    Args:
        capability: Filter by capability tag. Options: research, data, compute,
                    monitoring, verification, routing, storage, translation,
                    classification, generation, extraction, summarization,
                    enrichment, validation, other.
        max_price_usd: Maximum acceptable price per call in USD (default 0.50).
        query: Free-text search — matches against service name and description.

    Returns:
        Top 5 matching services, ranked by quality tier, formatted as text.
    """
    try:
        services = _catalog()
    except requests.RequestException as e:
        return f"Error fetching catalog: {e}"

    # Filter
    if capability:
        services = [
            s for s in services
            if capability in s.get("capability_tags", [])
            or s.get("category") == capability
        ]
    services = [
        s for s in services
        if s.get("price_per_call", 999) <= max_price_usd
    ]
    if query:
        q = query.lower()
        services = [
            s for s in services
            if q in s.get("name", "").lower()
            or q in s.get("description", "").lower()
        ]

    # Sort by quality: gold > silver > bronze > unverified
    order = {"gold": 0, "silver": 1, "bronze": 2, "unverified": 3}
    services.sort(key=lambda s: order.get(s.get("quality_tier", "unverified"), 3))

    top5 = services[:5]
    if not top5:
        return (
            f"No services found matching capability={capability!r}, "
            f"max_price_usd={max_price_usd}, query={query!r}.\n"
            "Try broadening your search or visit "
            f"{DISCOVERY_BASE_URL}/catalog for the full listing."
        )

    lines = [
        f"Found {len(services)} matching services (showing top {len(top5)}):\n"
    ]
    for i, s in enumerate(top5, 1):
        lines.append(_format_service(s, i))
        lines.append("")

    lines.append(
        f"To call any of these services, send an HTTP request to the listed URL. "
        f"Each service uses x402 micropayment — the first response will be HTTP 402 "
        f"with payment instructions (USDC on Base, ~${top5[0].get('price_per_call', '?')}/call)."
    )
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Browse the complete free x402 service catalog, grouped by category. "
        "Use this for an overview of what x402-payable services exist, or when "
        "you want to explore available capabilities before narrowing down."
    )
)
def x402_browse() -> str:
    """Return the full catalog grouped by category.

    Returns:
        All indexed x402 services summarized by category.
    """
    try:
        services = _catalog()
    except requests.RequestException as e:
        return f"Error fetching catalog: {e}"

    if not services:
        return f"No services indexed yet. Visit {DISCOVERY_BASE_URL} for status."

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for s in services:
        cat = s.get("category") or (s.get("capability_tags") or ["other"])[0]
        by_category.setdefault(cat, []).append(s)

    lines = [f"x402 Service Catalog — {len(services)} services across {len(by_category)} categories\n"]
    for cat, svcs in sorted(by_category.items()):
        lines.append(f"## {cat.upper()} ({len(svcs)} services)")
        for s in svcs:
            price = s.get("price_per_call", "?")
            quality = s.get("quality_tier", "unverified")
            lines.append(
                f"  • {s.get('name', '?')} [{quality}] — ${price}/call — "
                f"{s.get('service_id', '?')}"
            )
        lines.append("")

    lines.append(f"Full catalog: {DISCOVERY_BASE_URL}/catalog")
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Check the live health status of a specific x402 service. "
        "Use this before calling a service to verify it is online, or to "
        "investigate a service that recently returned an error."
    )
)
def x402_health(service_id: str) -> str:
    """Check health of a specific x402 service.

    Args:
        service_id: The service identifier, e.g. 'ouroboros/discovery'.
                    Find service IDs using x402_discover or x402_browse.

    Returns:
        Health status including: status (up/down/degraded), latency_ms, uptime_pct.
    """
    try:
        resp = requests.get(
            f"{DISCOVERY_BASE_URL}/health/{service_id}", timeout=15
        )
        if resp.status_code == 404:
            return (
                f"Service '{service_id}' not found in the registry.\n"
                "Use x402_browse to see available service IDs."
            )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return f"Health check failed: {e}"

    status = data.get("status", "unknown")
    emoji = {"up": "✓", "degraded": "⚠", "down": "✗"}.get(status, "?")

    return (
        f"{emoji} {service_id}: {status.upper()}\n"
        f"Latency: {data.get('latency_ms', '?')}ms\n"
        f"Uptime: {data.get('uptime_pct', '?')}%\n"
        f"Last checked: {data.get('checked_at', 'unknown')}\n"
        f"Endpoint: {data.get('endpoint_url', 'unknown')}"
    )


@mcp.tool(
    description=(
        "Register a new x402-payable service with the discovery layer. "
        "Use this to list your own API endpoint so that other agents can "
        "find it at runtime. Registration is free and immediate."
    )
)
def x402_register(
    name: str,
    url: str,
    description: str,
    price_usd: float,
    category: str,
) -> str:
    """Register a new service with the x402 discovery layer.

    Args:
        name: Human-readable service name (e.g. 'My Research API').
        url: The fully-qualified endpoint URL (must be https://).
        description: One sentence describing what the service does.
        price_usd: Price per call in USD (e.g. 0.01).
        category: Primary category. One of: research, data, compute, monitoring,
                  verification, routing, storage, translation, classification,
                  generation, extraction, summarization, enrichment, validation, other.

    Returns:
        Confirmation message with the assigned service_id.
    """
    payload = {
        "name": name,
        "url": url,
        "description": description,
        "price_usd": price_usd,
        "category": category,
    }
    try:
        resp = requests.post(
            f"{DISCOVERY_BASE_URL}/register",
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return f"Registration failed: {detail}"
    except requests.RequestException as e:
        return f"Registration request failed: {e}"

    service_id = data.get("service_id", "unknown")
    return (
        f"Service registered successfully!\n"
        f"Service ID: {service_id}\n"
        f"Name: {name}\n"
        f"URL: {url}\n"
        f"Price: ${price_usd}/call\n"
        f"Category: {category}\n\n"
        f"Your service will be health-checked within 5 minutes. "
        f"View at: {DISCOVERY_BASE_URL}/catalog"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
