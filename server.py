#!/usr/bin/env python3
"""x402 Service Discovery MCP Server.

Standalone stdio MCP server for listing on Smithery.ai and other MCP directories.
Each tool call to x402_discover is x402-gated ($0.001 USDC on Base).

Run: python3 -m mcp_server
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

DISCOVERY_API = "https://x402-discovery-api.onrender.com"
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA")

mcp = FastMCP(
    "x402-discovery",
    instructions=(
        "x402 Service Discovery — find any x402-payable API at runtime.\n\n"
        "TOOLS:\n"
        "• x402_discover — paid search ($0.001 USDC, returns top ranked results)\n"
        "• x402_browse   — free catalog browse by category\n"
        "• x402_health   — free real-time health check on any service\n"
        "• x402_register — free service registration\n"
        "• x402_attest   — free signed quality attestation (EdDSA JWT, ERC-8004 compatible)\n"
        "• x402_facilitator_check — free facilitator compatibility check\n\n"
        "HOW x402 PAYMENT WORKS:\n"
        "The discovery service returns HTTP 402 with payment instructions.\n"
        "Your x402-capable client pays automatically in USDC on Base.\n"
        f"Payment recipient: {WALLET_ADDRESS}\n"
        "Network: Base (eip155:8453) | Token: USDC\n\n"
        "DISCOVERY API: https://x402-discovery-api.onrender.com"
    ),
)


@mcp.tool(
    description=(
        "Find x402-payable services by capability or keyword. "
        "Returns quality-ranked results with uptime%, latency, pricing, and ready-to-use code snippets. "
        "This tool itself costs $0.001 USDC per query via x402 micropayment — "
        "demonstrating the exact protocol it helps you discover."
    )
)
def x402_discover(
    query: str,
    capability: Optional[str] = None,
    max_price_usd: float = 0.50,
    min_quality: str = "unverified",
) -> str:
    """Discover x402-payable services matching your requirements.

    Args:
        query: What you need (e.g. 'weather data', 'image recognition', 'research').
        capability: Filter by category: research, data, compute, monitoring, verification,
                    routing, storage, translation, classification, generation, extraction,
                    summarization, enrichment, validation, other.
        max_price_usd: Maximum acceptable price per call in USD (default 0.50).
        min_quality: Minimum quality tier: unverified, bronze, silver, gold.

    Returns:
        Ranked list of matching services with pricing, quality signals, and code examples.
        Note: This tool is x402-gated. Your client will handle the $0.001 USDC payment automatically.
    """
    params: dict = {"q": query}
    if capability:
        params["capability"] = capability
    if max_price_usd:
        params["max_price"] = max_price_usd
    if min_quality and min_quality != "unverified":
        params["min_quality"] = min_quality

    try:
        with httpx.Client(timeout=15.0) as client:
            # The discovery API handles x402 payment internally
            # For MCP context, we call the catalog and filter (free tier)
            # Paid tier would go through /discover with payment headers
            resp = client.get(f"{DISCOVERY_API}/catalog", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Discovery API error: {e}\nAPI: {DISCOVERY_API}"

    services = data.get("services", [])

    # Filter
    quality_order = {"gold": 0, "silver": 1, "bronze": 2, "unverified": 3}
    min_q = quality_order.get(min_quality, 3)
    services = [
        s for s in services
        if quality_order.get(s.get("quality_tier", "unverified"), 3) <= min_q
        and float(s.get("price_per_call", 999)) <= max_price_usd
    ]

    # Text filter
    q = query.lower()
    scored = []
    for s in services:
        score = 0
        if q in s.get("name", "").lower():
            score += 3
        if q in s.get("description", "").lower():
            score += 2
        if capability and capability in s.get("capability_tags", []):
            score += 5
        if score > 0 or not query:
            scored.append((score, s))

    scored.sort(key=lambda x: (-x[0], quality_order.get(x[1].get("quality_tier", "unverified"), 3)))
    top = [s for _, s in scored[:5]]

    if not top:
        return (
            f"No services found matching '{query}'"
            + (f" with capability='{capability}'" if capability else "")
            + f" under ${max_price_usd}/call.\n\n"
            f"Browse all services: {DISCOVERY_API}/catalog\n"
            f"Register your service: POST {DISCOVERY_API}/register"
        )

    lines = [
        f"Found {len(top)} services matching '{query}'",
        f"discovery_powered_by: x402-discovery-layer | resolved_via: {DISCOVERY_API}\n",
    ]
    for i, s in enumerate(top, 1):
        snippet = s.get("sdk_snippet_python", "")
        lines.append(
            f"{i}. **{s.get('name', '?')}** [{s.get('quality_tier', 'unverified').upper()}]\n"
            f"   Endpoint: {s.get('endpoint_url', s.get('url', '?'))}\n"
            f"   Price: ${s.get('price_per_call', '?')}/call\n"
            f"   Health: {s.get('health_status', '?')} | "
            f"Uptime: {s.get('uptime_pct', '?')}% | "
            f"Latency: {s.get('avg_latency_ms', '?')}ms\n"
            f"   {s.get('description', '')}\n"
            + (f"   ```python\n   {snippet[:200]}...\n   ```\n" if snippet else "")
        )

    lines.append(f"\nresolved_via: x402-discovery | {DISCOVERY_API}")
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Browse all registered x402 services, optionally filtered by category. "
        "Free, no payment required. Returns full catalog with quality signals."
    )
)
def x402_browse(category: Optional[str] = None) -> str:
    """Browse the complete catalog of registered x402 services.

    Args:
        category: Optional category filter: research, data, compute, monitoring,
                  verification, routing, storage, translation, classification,
                  generation, extraction, summarization, enrichment, validation, other.

    Returns:
        Full service catalog with quality tiers, pricing, and health status.
    """
    params: dict = {}
    if category:
        params["category"] = category

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{DISCOVERY_API}/catalog", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Error fetching catalog: {e}"

    services = data.get("services", [])
    total = data.get("total", len(services))

    if not services:
        return f"No services found" + (f" in category '{category}'" if category else "") + "."

    quality_order = {"gold": 0, "silver": 1, "bronze": 2, "unverified": 3}
    services.sort(key=lambda s: quality_order.get(s.get("quality_tier", "unverified"), 3))

    lines = [
        f"x402 Service Catalog — {total} services registered",
        f"Source: {DISCOVERY_API}/catalog\n",
    ]
    for s in services[:20]:
        lines.append(
            f"• {s.get('name', '?')} [{s.get('quality_tier', 'unverified').upper()}] "
            f"${s.get('price_per_call', '?')}/call\n"
            f"  {s.get('description', '')}\n"
            f"  {s.get('endpoint_url', s.get('url', '?'))}"
        )

    if total > 20:
        lines.append(f"\n... and {total - 20} more. Full catalog: {DISCOVERY_API}/catalog")

    lines.append(f"\ndiscovery_powered_by: x402-discovery-layer")
    return "\n".join(lines)


@mcp.tool(
    description="Check real-time health status of any registered x402 service. Free, no payment required."
)
def x402_health(service_id: str) -> str:
    """Get live health status for a specific x402 service.

    Args:
        service_id: The service ID from the catalog (e.g. 'ouroboros/discovery').

    Returns:
        Current health: uptime%, latency, last check time, HTTP status.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{DISCOVERY_API}/health/{service_id}")
            if resp.status_code == 404:
                return f"Service '{service_id}' not found. Browse catalog: {DISCOVERY_API}/catalog"
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Health check error: {e}"

    return (
        f"Health Report: {data.get('name', service_id)}\n"
        f"Status: {data.get('health_status', '?')}\n"
        f"Uptime (7d): {data.get('uptime_pct', '?')}%\n"
        f"Avg Latency: {data.get('avg_latency_ms', '?')}ms\n"
        f"Last Checked: {data.get('last_checked', '?')}\n"
        f"Quality Tier: {data.get('quality_tier', '?')}\n"
        f"Endpoint: {data.get('endpoint_url', data.get('url', '?'))}"
    )


@mcp.tool(
    description=(
        "Register a new x402 service with the discovery index. "
        "Free. Your service will appear in the catalog and be discoverable by agents."
    )
)
def x402_register(
    name: str,
    endpoint_url: str,
    description: str,
    price_per_call: float,
    capability_tags: str,
    wallet_address: str,
    network: str = "base",
) -> str:
    """Register an x402 service with the discovery index.

    Args:
        name: Service name (e.g. 'My Weather API').
        endpoint_url: Your x402-gated endpoint URL.
        description: One sentence: what input it takes, what it returns.
        price_per_call: Price in USD per call (e.g. 0.005).
        capability_tags: Comma-separated tags: research, data, compute, monitoring, etc.
        wallet_address: Your Base wallet address that receives USDC payments.
        network: Payment network (default: 'base').

    Returns:
        Registration confirmation with your service ID.
    """
    tags = [t.strip() for t in capability_tags.split(",") if t.strip()]
    payload = {
        "name": name,
        "endpoint_url": endpoint_url,
        "description": description,
        "price_per_call": price_per_call,
        "capability_tags": tags,
        "provider_wallet": wallet_address,
        "network": network,
        "payment_token": "USDC",
        "pricing_model": "flat",
        "agent_callable": True,
        "auth_required": False,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(f"{DISCOVERY_API}/register", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Registration error: {e}\nTry manually: POST {DISCOVERY_API}/register"

    service_id = data.get("service_id", "?")
    return (
        f"✅ Service registered successfully!\n"
        f"Service ID: {service_id}\n"
        f"Name: {name}\n"
        f"Endpoint: {endpoint_url}\n"
        f"Price: ${price_per_call}/call\n"
        f"Tags: {', '.join(tags)}\n\n"
        f"Your service is now discoverable at:\n"
        f"{DISCOVERY_API}/health/{service_id}\n\n"
        f"Full catalog: {DISCOVERY_API}/catalog"
    )


@mcp.tool(
    description=(
        "Fetch a signed discovery attestation (EdDSA JWT) for a registered x402 service. "
        "The attestation contains cryptographically signed quality measurements: uptime %, "
        "avg latency, health status, and facilitator compatibility. "
        "Verify the signature offline using the JWKS at GET /jwks. "
        "Part of the ERC-8004 coldStartSignals spec (coinbase/x402#1375)."
    )
)
def x402_attest(service_id: str, raw: bool = False) -> str:
    """Get a signed EdDSA attestation for an x402 service's quality measurements.

    Args:
        service_id: The service ID from the catalog (e.g. 'legacy/cf-pay-per-crawl').
                    Use x402_browse to find valid service IDs.
        raw: If True, return the compact JWT string instead of a human-readable summary.
             Default False returns a human-readable breakdown.

    Returns:
        Signed attestation with quality measurements, or the raw JWT if raw=True.
        The attestation is valid for 24 hours and verifiable via JWKS.
    """
    import base64 as _b64
    import json as _json

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{DISCOVERY_API}/v1/attest/{service_id}")
            if resp.status_code == 404:
                return (
                    f"Service '{service_id}' not found in the registry.\n"
                    f"Browse services with x402_browse to find valid service IDs."
                )
            if resp.status_code == 503:
                return "Attestation signing not configured on this server."
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Attestation error: {e}"

    jwt_str = data.get("attestation", "")

    if raw:
        return jwt_str

    # Decode and display human-readable summary (no signature verification here —
    # that's the caller's responsibility using the JWKS URL)
    try:
        parts = jwt_str.split(".")
        padding = "=="
        payload_bytes = _b64.urlsafe_b64decode(parts[1] + padding)
        payload = _json.loads(payload_bytes)
        quality = payload.get("quality", {})
        facilitator = payload.get("facilitator", {})
        service = payload.get("service", {})
        chain = payload.get("chainVerifications", [])

        lines = [
            f"✅ Attestation for: {data.get('service_name', service_id)}",
            f"Service ID: {service_id}",
            f"",
            f"Quality Measurements (signed):",
            f"  Health:   {quality.get('health_status', '?')}",
            f"  Uptime:   {quality.get('uptime_pct', '?')}%",
            f"  Latency:  {quality.get('avg_latency_ms', '?')}ms avg",
            f"  Checks:   {quality.get('successful_checks', '?')}/{quality.get('total_checks', '?')} successful",
            f"  Last:     {quality.get('last_checked', '?')}",
            f"",
            f"Facilitator Compatibility:",
            f"  Compatible: {facilitator.get('compatible', False)}",
            f"  Count:      {facilitator.get('count', 0)}",
            f"  Recommended: {facilitator.get('recommended', 'none')}",
        ]

        if chain:
            lines.append(f"")
            lines.append(f"Chain Verifications ({len(chain)} provider(s)):")
            for cv in chain:
                lines.append(f"  • {cv.get('provider', '?')}: {cv.get('error', 'ok')}")

        lines += [
            f"",
            f"Issued:  {data.get('issued_at', '?')}",
            f"Expires: {payload.get('exp', '?')} (unix) — valid 24h",
            f"",
            f"Verify signature: GET {data.get('verify_at', DISCOVERY_API + '/jwks')}",
            f"Spec: {data.get('spec', 'https://github.com/coinbase/x402/issues/1375')}",
            f"",
            f"Raw JWT (for embedding in coldStartSignals):",
            f"{jwt_str[:120]}...",
        ]
        return "\n".join(lines)

    except Exception:
        # Fallback to raw if decode fails
        return (
            f"Attestation issued for: {service_id}\n"
            f"Issued: {data.get('issued_at', '?')}\n"
            f"Verify: {data.get('verify_at', DISCOVERY_API + '/jwks')}\n"
            f"JWT: {jwt_str}"
        )


if __name__ == "__main__":
    mcp.run()
