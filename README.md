# x402 Service Discovery MCP Server

> **The community-built Bazaar for the x402 agentic economy — 251+ live services, real-time quality signals, facilitator-compatibility checks, and ERC-8004 trust scoring. The discovery layer that Coinbase's own PROJECT-IDEAS.md asked the community to build.**

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-Published-blue?logo=github)](https://registry.modelcontextprotocol.io/servers/io.github.rplryan/x402-discovery-mcp)
[![Smithery Score](https://img.shields.io/badge/Smithery-100%2F100-brightgreen?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://smithery.ai/server/x402-discovery-mcp)
[![API Status](https://img.shields.io/badge/API-Live%20v3.3.0-brightgreen)](https://x402-discovery-api.onrender.com)
[![Services Indexed](https://img.shields.io/badge/Services%20Indexed-251%2B-brightgreen)](https://x402-discovery-api.onrender.com/.well-known/x402-discovery)
[![mcp.so](https://img.shields.io/badge/mcp.so-Submitted-orange)](https://mcp.so/server/x402-discovery-mcp)
[![Glama](https://img.shields.io/badge/Glama-Live-brightgreen)](https://glama.ai/mcp/servers/@rplryan/x402-discovery-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<a href="https://glama.ai/mcp/servers/@rplryan/x402-discovery-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@rplryan/x402-discovery-mcp/badge" />
</a>

---

## What This Is (30 seconds)

**x402** is Coinbase's HTTP-native micropayment standard for the agentic web. An AI agent hits an endpoint, gets an HTTP 402 challenge, pays with USDC on Base, and receives data — no API keys, no subscriptions, pure machine-to-machine.

**The problem:** 251+ x402-payable services exist across the ecosystem. The official x402.org catalog lists names. That's it. No uptime data. No latency scores. No facilitator-compatibility flags. No trust signals. An agent has no way to know which services are actually live, trustworthy, or compatible with its payment flow.

**This MCP server solves it.** Connect any Claude, Cursor, or Windsurf agent directly to the x402 Service Discovery API — a continuously-updated catalog with real quality signals on every entry. Find services, check health, verify facilitator compatibility, and register new endpoints — all from inside your AI workflow.

---

## MCP Tools (5 tools)

| Tool | What It Does | Cost |
|------|-------------|------|
| `x402_discover` | Semantic search across 251+ services by keyword, category, max price | **$0.005 USDC** *(pays via x402 — eats its own dogfood)* |
| `x402_health_check` | Real-time uptime + latency check for any service URL | Free |
| `x402_register` | Register a new x402 service into the live catalog | Free |
| `x402_trust` | ERC-8004 trust score and reputation signals for a service | Free |
| `x402_facilitator_check` | Verify facilitator compatibility before committing to a payment | Free |

---

## Quickstart — 30 Seconds to Discovery

### Option A: Docker (recommended)

Add to your `claude_desktop_config.json`, Cursor MCP settings, or Windsurf config:

```json
{
  "mcpServers": {
    "x402-discovery": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/rplryan/x402-discovery-mcp:latest"]
    }
  }
}
```

### Option B: npx (no Docker required)

```json
{
  "mcpServers": {
    "x402-discovery": {
      "command": "npx",
      "args": ["-y", "@rplryan/x402-discovery-mcp"]
    }
  }
}
```

### Option C: Direct API

The Discovery API is publicly accessible — no authentication required:

```bash
# Search for services
curl "https://x402-discovery-api.onrender.com/discover?query=blockchain+analytics&max_price_usd=0.01"

# Full catalog
curl "https://x402-discovery-api.onrender.com/.well-known/x402-discovery"
```

---

## Why This Matters

### The Discovery Gap in x402

The x402 protocol solves *payment*. It does not solve *discovery*. When 251+ services exist but agents can't find, evaluate, or route to them intelligently, the protocol's full value is unrealized.

This project fills that gap with three layers:

1. **Discovery** — Find x402 services by capability, category, price ceiling
2. **Quality signals** — Uptime %, latency (ms), facilitator compatibility, ERC-8004 trust score
3. **Routing intelligence** — Companion [x402 RouteNet](https://github.com/rplryan/x402-routenet) selects the optimal service from discovery results

### What Makes This Different from x402.org/ecosystem

| Capability | x402.org/ecosystem | This Project |
|------------|-------------------|---------------|
| Service listings | ✅ Names + URLs | ✅ Full metadata |
| Uptime monitoring | ❌ None | ✅ Live health checks |
| Latency data | ❌ None | ✅ Per-service ms scores |
| Facilitator compatibility | ❌ None | ✅ Per-service flag |
| ERC-8004 trust signals | ❌ None | ✅ Reputation scoring |
| Agent-native usage prompts | ❌ None | ✅ `llm_usage_prompt` per service |
| Auto-updated catalog | ❌ Manual | ✅ Scans every 6 hours |
| MCP integration | ❌ None | ✅ 5 tools, registry-published |
| Semantic search | ❌ None | ✅ Keyword + category + price |

---

## Live Catalog Stats

```
Total Services:      251+
Auto-scan interval:  6 hours
Scan sources:        x402.org/ecosystem, awesome-x402, x402scan.com
Categories:          data, compute, agent, utility
Facilitator-compat:  Flagged per service
Trust signals:       ERC-8004 per service
API uptime:          Live at https://x402-discovery-api.onrender.com
```

### Catalog Sample

| Category | Count | Notable Services |
|----------|-------|------------------|
| **data** | 23+ | CoinGecko, Einstein AI, DJD Agent Score, Ordiscan, Nansen, Zapper, AdEx AURA |
| **utility** | 20+ | dTelecom STT, Pinata, Tip.MD, Cybercentry, Trusta Attestation, AsterPay |
| **compute** | 10+ | BlockRun.AI, X402Engine (28 APIs), AurraCloud, AiMo, QuickSilver |
| **agent** | 9+ | Questflow, Ubounty, Bitte Protocol, Farnsworth, SerenaI |

---

## Example: Agent Workflow

```python
# 1. Agent needs blockchain analytics under $0.01
result = x402_discover(
    query="blockchain analytics whale tracking",
    max_price_usd=0.01,
    category="data"
)
# Returns: ranked list with price, uptime %, latency, llm_usage_prompt

# 2. Verify the top result is facilitator-compatible before paying
compat = x402_facilitator_check(url=result[0]["url"])
# Returns: {facilitator_compatible: true, payment_details: {...}}

# 3. Check live health before committing
health = x402_health_check(url=result[0]["url"])
# Returns: {status: "healthy", latency_ms: 142, uptime_pct: 99.1}

# 4. Now pay via x402 — agent proceeds with confidence
```

This is **EIP-712 signed `TransferWithAuthorization`** via the x402 HTTP protocol — not direct ERC-20 transfer. The signature is verified server-side; on-chain settlement via `receiveWithAuthorization` is the next tier.

---

## CDP Builder Grant Context

This project is a direct implementation of two items from Coinbase's own public roadmap:

**From `PROJECT-IDEAS.md` in coinbase/x402:**
> *"Dynamic Endpoint Shopper — An agent that discovers an MCP registry, pays for access, chains results from multiple services"*

**From the CDP x402 facilitator roadmap:**
> *"A discovery layer for buyers (human and agents) to find available services (Bazaar)"*

We built the community Bazaar. It's live. It has 251+ services. It has quality signals the official page doesn't. And it **uses x402 payments itself** — `x402_discover` costs $0.005 USDC, paid via the protocol it serves.

### What We've Shipped (11 days)

| Deliverable | Status |
|-------------|--------|
| x402 Service Discovery API v3.3.0 | ✅ Live on Render |
| x402 Discovery MCP Server | ✅ Docker + GitHub MCP Registry |
| x402 RouteNet v1.0.0 (smart routing) | ✅ Live on Render |
| x402 Payment Harness v1.0.0 (EOA testing) | ✅ PyPI `pip install x402-payment-harness` |
| 251+ services indexed with quality signals | ✅ Auto-updating every 6h |
| ERC-8004 trust layer | ✅ Per-service trust scoring |
| Facilitator compatibility layer | ✅ Pre-payment compatibility check |
| Full HTTP 402 protocol flow proven on Base | ✅ EIP-712 sign → X-PAYMENT header → 200 |
| Smithery score | ✅ 100/100 |
| GitHub MCP Registry | ✅ Published: `io.github.rplryan/x402-discovery-mcp` |

---

## Related Projects

| Project | Description | Status |
|---------|-------------|--------|
| [x402 Discovery API](https://x402-discovery-api.onrender.com) | REST backend powering this MCP server | Live v3.3.0 |
| [x402 RouteNet](https://github.com/rplryan/x402-routenet) | Smart routing across discovered services | Live v1.0.0 |
| [x402 Payment Harness](https://github.com/rplryan/x402-payment-harness) | EOA-based Python library + CLI for x402 payment testing | PyPI v1.0.0 |

---

## Register Your Service

If you're building an x402-enabled service, add it to the catalog:

```bash
curl -X POST https://x402-discovery-api.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Service",
    "url": "https://myservice.example.com/api",
    "price_usd": 0.005,
    "category": "data",
    "description": "What your service does",
    "network": "base-mainnet"
  }'
```

Or use the `x402_register` MCP tool from inside Claude/Cursor/Windsurf.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              AI Agent (Claude / Cursor / Windsurf)  │
│                                                     │
│  x402_discover → x402_health_check → x402_trust     │
│  x402_facilitator_check → x402_register             │
└───────────────────┬─────────────────────────────────┘
                    │ MCP (stdio/Docker)
┌───────────────────▼─────────────────────────────────┐
│          x402 Discovery MCP Server                  │
│          ghcr.io/rplryan/x402-discovery-mcp         │
└───────────────────┬─────────────────────────────────┘
                    │ HTTPS
┌───────────────────▼─────────────────────────────────┐
│     x402 Discovery API (Render, v3.3.0)             │
│     https://x402-discovery-api.onrender.com         │
│                                                     │
│  • 251+ services  • Auto-scan every 6h              │
│  • Health checks  • Facilitator compat flags        │
│  • ERC-8004 trust • llm_usage_prompt per service    │
└─────────────────────────────────────────────────────┘
```

---

## License

MIT

---

*Built on [Coinbase x402 protocol](https://github.com/coinbase/x402) | Base Network | ERC-8004 | Model Context Protocol*
