# x402 Service Discovery MCP Server

> [⭐ Star to help others find this](https://github.com/rplryan/x402-discovery-mcp) — if x402Scout has saved you time, a star helps other developers find it

> **The community-built Bazaar for the x402 agentic economy — a continuously growing catalog of live services with real-time quality signals, facilitator-compatibility checks, and ERC-8004 trust scoring. The discovery layer that Coinbase's own PROJECT-IDEAS.md asked the community to build.**

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-Published-blue?logo=github)](https://registry.modelcontextprotocol.io/servers/io.github.rplryan/x402-discovery-mcp)
[![Smithery Score](https://img.shields.io/badge/Smithery-100%2F100-brightgreen?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://smithery.ai/server/x402-discovery-mcp)
[![API Status](https://img.shields.io/badge/API-Live-brightgreen)](https://x402scout.com)
[![Services Indexed](https://img.shields.io/badge/Services%20Indexed-Live%20Catalog-brightgreen)](https://x402scout.com/catalog)
[![scout_relay](https://img.shields.io/badge/scout__relay-v2.1.0-brightgreen)](https://x402-scout-relay.onrender.com)
[![x402scout CLI](https://img.shields.io/badge/CLI-x402scout%201.0.0-brightgreen)](https://www.npmjs.com/package/x402scout)
[![ScoutGate](https://img.shields.io/badge/ScoutGate-v1.0.0-brightgreen)](https://x402-scoutgate.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ScoutGate — Instant x402 API Monetization

> Wrap any existing API in x402 payments in under 2 minutes — no protocol knowledge required

The x402 ecosystem's biggest friction point has been supply-side: getting an API *behind* x402 payments requires understanding EIP-712 headers, facilitator registration, and settlement logic. ScoutGate removes all of it.

```bash
# Register your existing API (30 seconds)
curl -X POST https://x402-scoutgate.onrender.com/register \  -H "Content-Type: application/json" \  -d '{"api_url": "https://your-api.com", "wallet_address": "0xYourWallet", "price_usd": 0.01, "name": "My API"}'
# Returns: {"proxy_url": "https://x402-scoutgate.onrender.com/api/abc123", "api_id": "abc123"}
```

That's it. Your API is now **x402-enabled**, **auto-listed in x402Scout**, and **settling on Base mainnet** in real USDC. ScoutGate handles facilitator integration, EIP-712 verification, and settlement.

**Fee model:** 2% per transaction (min $0.002). **Live at:** https://x402-scoutgate.onrender.com | [Register your API](https://x402scout.com/register)

---

## Terminal CLI — x402scout

> Search the full x402 service catalog from your terminal

```bash
# Install (npm)
npm install -g x402scout

# Search
x402scout search "weather data"

# Top services by trust score
x402scout top 10

# Browse by category
x402scout browse data

# Scan a URL for x402 compliance
x402scout scan https://api.yourservice.com

# Ecosystem stats
x402scout stats
```

See [cli/README.md](cli/README.md) for full usage.

---

## scout_relay — Autonomous Payment Router

> Route, execute, and audit x402 payments in a single call

Where the Discovery MCP finds *what* to call, **scout_relay** handles *calling it* — discovering the best service, making the x402 payment, retrying on failure, and returning the result. One call. Fully autonomous.

```bash
# Route an intent to the best matching x402 service
curl -X POST https://x402-scout-relay.onrender.com/route \
  -H "Content-Type: application/json" \
  -H "X-Payment: <your-x402-payment-header>" \
  -d '{"intent": "blockchain analytics for wallet 0xABC", "max_budget_usd": 0.05}'
```

**4 MCP tools — add to any MCP client:**

| Tool | What It Does |
|------|--------------|
| `scout_route` | Discover best service for an intent + execute payment |
| `scout_discover` | Query the discovery catalog without executing |
| `scout_execute` | Execute payment to a known service URL |
| `scout_audit` | View spend log and agent budget status |

**Fee model:** `max($0.003, 2.5% of downstream transaction value)` per routed call.

**Placement bids:** Providers can register routing priority bids at `POST /placement/bid` (x402-gated, $0.01 registration fee). Bids are used as tiebreakers after trust-score filtering — merit first, always.

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Service health + version |
| `POST /route` | Route an intent (x402-gated) |
| `POST /execute` | Execute to a known URL (x402-gated) |
| `GET /discover` | Catalog discovery (free) |
| `GET /audit` | Spend log (free) |
| `POST /placement/bid` | Register a provider placement bid (x402-gated, $0.01) |
| `GET /placement/bids` | View all active placement bids (public) |

**Live at:** https://x402-scout-relay.onrender.com

---

## What This Is (30 seconds)

**x402** is Coinbase's HTTP-native micropayment standard for the agentic web. An AI agent hits an endpoint, gets an HTTP 402 challenge, pays with USDC on Base, and receives data — no API keys, no subscriptions, pure machine-to-machine.

**The problem:** Hundreds of x402-payable services exist across the ecosystem. The official x402.org catalog lists names. That's it. No uptime data. No latency scores. No facilitator-compatibility flags. No trust signals. An agent has no way to know which services are actually live, trustworthy, or compatible with its payment flow.

**This MCP server solves it.** Connect any Claude, Cursor, or Windsurf agent directly to the x402 Service Discovery API — a continuously-updated catalog with real quality signals on every entry. Find services, check health, verify facilitator compatibility, and register new endpoints — all from inside your AI workflow.

---

## MCP Tools (5 discovery + 4 relay = 9 total)

### Discovery Tools
| Tool | What It Does | Cost |
|------|-------------|------|
| `x402_discover` | Semantic search across the live catalog by keyword, category, max price | **$0.010 USDC** *(pays via x402)* |
| `x402_health` | Real-time uptime + latency check for any registered service | **$0.001 USDC** *(pays via x402)* |
| `x402_register` | Register a new x402 service (HTTPS-only, rate-limited) | Free |
| `x402_attest` | ERC-8004 trust score and reputation signals for a service | Free |
| `x402_scan` | Full x402 compliance scan: live config, trust score, mismatch detection | **$0.010 USDC** *(pays via x402)* |

### Relay Tools (via scout_relay)
| Tool | What It Does | Cost |
|------|-------------|------|
| `scout_route` | Discover best service for an intent + execute x402 payment | max($0.003, 2.5%) |
| `scout_discover` | Query discovery catalog without executing | Free |
| `scout_execute` | Execute x402 payment to a known service URL | max($0.003, 2.5%) |
| `scout_audit` | View agent spend log and budget status | Free |

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
curl "https://x402scout.com/discover?query=blockchain+analytics&max_price_usd=0.01"

# Full catalog
curl "https://x402scout.com/.well-known/x402-discovery"
```

---

## Why This Matters

### The Discovery Gap in x402

The x402 protocol solves *payment*. It does not solve *discovery*. When hundreds of services exist but agents can't find, evaluate, or route to them intelligently, the protocol's full value is unrealized.

This project fills that gap with three layers:

1. **Discovery** — Find x402 services by capability, category, price ceiling
2. **Quality signals** — Uptime %, latency (ms), facilitator compatibility, ERC-8004 trust score
3. **Execution** — scout_relay discovers, pays, retries, and returns results autonomously

### What Makes This Different from x402.org/ecosystem

| Capability | x402.org/ecosystem | This Project |
|------------|-------------------|--------------|
| Service listings | ✅ Names + URLs | ✅ Full metadata |
| Uptime monitoring | ❌ None | ✅ Live health checks |
| Latency data | ❌ None | ✅ Per-service ms scores |
| Facilitator compatibility | ❌ None | ✅ Per-service flag |
| ERC-8004 trust signals | ❌ None | ✅ Reputation scoring |
| Agent-native usage prompts | ❌ None | ✅ `llm_usage_prompt` per service |
| Auto-updated catalog | ❌ Manual | ✅ Scans every 6 hours |
| MCP integration | ❌ None | ✅ 9 tools, registry-published |
| Semantic search | ❌ None | ✅ Keyword + category + price |
| Autonomous execution | ❌ None | ✅ scout_relay — discover + pay + retry |
| Agent integration hints | ❌ None | ✅ `howToUse` block per service — exact x402 payment steps |

---

## Live Catalog Stats

```
Total Services:      Live — check https://x402scout.com/catalog
Auto-scan interval:  6 hours
Scan sources:        x402.org/ecosystem, awesome-x402, GitHub search
Categories:          data, compute, agent, utility
Facilitator-compat:  Flagged per service
Trust signals:       ERC-8004 per service
Primary URL:         https://x402scout.com
Trust scores:        0-100 per service (ERC-8004 based)
Payment metadata:    x402Config (address, asset, version) per service
Router:              Live at https://x402-scout-relay.onrender.com
```

### Catalog Sample

| Category | Count | Notable Services |
|----------|-------|------------------|
| **data** | [Live](https://x402scout.com/catalog) | CoinGecko, Einstein AI, DJD Agent Score, Ordiscan, Nansen, Zapper, AdEx AURA |
| **utility** | [Live](https://x402scout.com/catalog) | dTelecom STT, Pinata, Tip.MD, Cybercentry, Trusta Attestation, AsterPay |
| **compute** | [Live](https://x402scout.com/catalog) | BlockRun.AI, X402Engine, AurraCloud, AiMo, QuickSilver |
| **agent** | [Live](https://x402scout.com/catalog) | Questflow, Ubounty, Bitte Protocol, Farnsworth, SerenaI |

---

## Example: Agent Workflow

### Discovery only
```python
# 1. Agent needs blockchain analytics under $0.01
result = x402_discover(
    query="blockchain analytics whale tracking",
    max_price_usd=0.01,
    category="data"
)
# Returns: ranked list with price, uptime %, latency, llm_usage_prompt

# 2. Scan for compliance + trust before paying
scan = x402_scan(url=result[0]["url"])

# 3. Check live health before committing
health = x402_health(url=result[0]["url"])
```

### Full autonomous execution via scout_relay
```python
# One call — discovery + payment + retry handled automatically
result = scout_route(
    intent="blockchain analytics for wallet 0xABC",
    max_budget_usd=0.05
)
# Returns: {result: {...}, provider: "...", fee_usd: 0.003, trust_score: 82}
```

Payments use **EIP-712 signed `TransferWithAuthorization`** via the x402 HTTP protocol — not direct ERC-20 transfer. Signature verified server-side; on-chain settlement via `receiveWithAuthorization`.

---

## CDP Builder Grant Context

This project is a direct implementation of two items from Coinbase's own public roadmap:

**From `PROJECT-IDEAS.md` in coinbase/x402:**
> *"Dynamic Endpoint Shopper — An agent that discovers an MCP registry, pays for access, chains results from multiple services"*

**From the CDP x402 facilitator roadmap:**
> *"A discovery layer for buyers (human and agents) to find available services (Bazaar)"*

We built the community Bazaar. It's live. It has quality signals the official page doesn't. And it **uses x402 payments itself** — `x402_discover` costs $0.010 USDC, paid via the protocol it serves. scout_relay extends this: it *routes and executes* x402 payments autonomously, charging its own x402 fee for the service.

### What We've Shipped (11 days)

| Deliverable | Status |
|-------------|---------|
| x402 Service Discovery API v3.7.0 | ✅ Live on Render |
| x402 Discovery MCP Server | ✅ Docker + GitHub MCP Registry |
| x402 RouteNet v1.0.0 (smart routing) | ✅ Live on Render |
| x402 Payment Harness v1.0.0 (EOA testing) | ✅ PyPI `pip install x402-payment-harness` |
| Continuously growing catalog with quality signals | ✅ Auto-updating every 6h |
| ERC-8004 trust layer | ✅ Per-service trust scoring |
| Facilitator compatibility layer | ✅ Pre-payment compatibility check |
| Full HTTP 402 protocol flow proven on Base | ✅ EIP-712 sign → X-PAYMENT header → 200 |
| x402scout CLI v1.0.0 | ✅ `npm install -g x402scout` |
| scout_relay v2.1.0 (payment router) | ✅ Live on Render |
| Provider placement bids (POST /placement/bid) | ✅ Live — x402-gated, self-serve |
| x402Config payment metadata in catalog | ✅ payment_address, asset_contract, x402Version per service |
| `/scan` compliance endpoint (paid) | ✅ Live — compliance grade, mismatch detection, trust score |
| `howToUse` integration blocks | ✅ Per-service exact x402 payment steps in /discover results |
| Landing page (x402scout.com) | ✅ NVG green design, live stats, code snippets |
| Endpoint security hardening | ✅ SSRF guard, rate limiting, HTTPS-only on /register |
| Smithery score | ✅ 100/100 |
| GitHub MCP Registry | ✅ Published: `io.github.rplryan/x402-discovery-mcp` |
| **ScoutGate v1.0.0** (x402 API monetization gateway) | ✅ Live on Render — wrap any API in x402 payments in 30 seconds |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              AI Agent (Claude / Cursor / Windsurf)  │
│                                                     │
│  x402_discover → x402_health → x402_attest         │
│  x402_scan → x402_register → x402_health           │
│                                                     │
│  scout_route → scout_execute → scout_audit          │
└──────────┬──────────────────────────┬───────────────┘
           │ MCP (stdio/Docker)       │ REST / MCP
┌──────────▼──────────┐    ┌──────────▼──────────────┐
│  x402 Discovery     │    │  scout_relay v2.1.0      │
│  MCP Server         │    │  x402-scout-relay        │
│  ghcr.io/rplryan/   │    │  .onrender.com           │
│  x402-discovery-mcp │    │  Fee: max($0.003, 2.5%)  │
└──────────┬──────────┘    └──────────┬───────────────┘
           │ HTTPS                    │ HTTPS
           └──────────────┬───────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│     x402 Discovery API (Render, v3.7.0)             │
│     https://x402scout.com                          │
│                                                     │
│  • Growing catalog  • Auto-scan every 6h            │
│  • Health checks  • Facilitator compat flags        │
│  • ERC-8004 trust • llm_usage_prompt per service    │
└─────────────────────────────────────────────────────┘
```

---

## Related Projects

| Project | Description | Status |
|---------|-------------|--------|
| [x402 Discovery API](https://x402scout.com) | REST backend powering this MCP server | Live v3.7.0 |
| [scout_relay](https://x402-scout-relay.onrender.com) | Autonomous x402 payment router — discover + execute + audit in one call | Live v2.1.0 |
| [x402 RouteNet](https://github.com/rplryan/x402-routenet) | Smart routing across discovered services | Live v1.0.0 |
| [x402 Payment Harness](https://github.com/rplryan/x402-payment-harness) | EOA-based Python library + CLI for x402 payment testing | PyPI v1.0.0 |
| [ScoutGate](https://x402-scoutgate.onrender.com) | Wrap any existing API in x402 payments in 30 seconds — no protocol knowledge required | Live v1.0.0 |

---

## Register Your Service

If you're building an x402-enabled service, add it to the catalog:

```bash
curl -X POST https://x402scout.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Service",
    "url": "https://myservice.example.com/api",
    "price_usd": 0.010,
    "category": "data",
    "description": "What your service does",
    "network": "base-mainnet"
  }'
```

Or use the `x402_register` MCP tool from inside Claude/Cursor/Windsurf.

**Want routing priority?** Register a placement bid at `POST https://x402-scout-relay.onrender.com/placement/bid` (x402-gated, $0.01 registration fee). Your service gets weighted as a tiebreaker after trust-score filtering — merit first, always.

---

## License

MIT

---

*Built on [Coinbase x402 protocol](https://github.com/coinbase/x402) | Base Network | ERC-8004 | Model Context Protocol*
