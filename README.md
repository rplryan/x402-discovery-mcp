# x402 Service Discovery MCP Server

> **The missing discovery layer for x402** — the open HTTP micropayment protocol built by Coinbase. AI agents can pay for services autonomously, but first they need to *find* them. Without discovery, there is no agentic commerce.

[![Live API](https://img.shields.io/badge/API-Live%20v3.2.0-brightgreen)](https://x402-discovery-api.onrender.com)
[![Smithery Score](https://img.shields.io/badge/Smithery-100%2F100-gold)](https://smithery.ai/server/@rplryan/x402-discovery-mcp)
[![On-Chain Verified](https://img.shields.io/badge/On--Chain%20TX-Verified-blue)](https://basescan.org/tx/0xb0ef774a7a26cdb370c305a625b2cf1bd6d7bb98f2ca16119d953bdcebc7e860)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live:** https://x402-discovery-api.onrender.com · **16 services** · **5 categories** · **5 MCP tools** · **ERC-8004 trust layer**

---

## The Problem

x402 is the payment primitive. But a payment primitive without service discovery is a phone system without a phone book.

Today an AI agent that wants to pay for a web search, translation, or data enrichment service must either:
- Be hardcoded with a specific endpoint (brittle, not agentic)
- Prompt the user to find and paste a URL (defeats the purpose)
- Crawl and discover at runtime with no trust signals (risky — no way to verify legitimacy)

**x402 Bazaar** (Coinbase's own web directory) has 33M+ monthly transactions but is a static HTML page — no MCP tools, no trust signals, no facilitator awareness, not queryable by agents. It's a human directory, not an agent-native protocol.

**We built what Bazaar can't be:** a live, queryable, trust-aware, facilitator-compatible service discovery layer that plugs directly into Claude, Cursor, Windsurf, or any MCP host.

---

## Proven: First End-to-End Real Payment

We didn't just build discovery — we proved the full payment stack works:

| Field | Value |
|---|---|
| **Transaction** | [`0xb0ef774...`](https://basescan.org/tx/0xb0ef774a7a26cdb370c305a625b2cf1bd6d7bb98f2ca16119d953bdcebc7e860) |
| **Network** | Base mainnet |
| **Amount** | 0.005 USDC |
| **CDP Wallet** | `0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA` |
| **Block** | 42707833 — confirmed |
| **Method** | EIP-712 TransferWithAuthorization, locally verified |

Agent discovers service → signs EIP-712 challenge → USDC transfers → service delivers. Full loop, real money, Base mainnet.

---

## MCP Tools

| Tool | What It Does | Cost |
|---|---|---|
| `x402_discover` | Quality-ranked search by capability, price, keyword, or category | $0.005/query |
| `x402_browse` | Full catalog grouped by category — 16 services, 5 categories | Free |
| `x402_health` | Live health check for any registered service endpoint | Free |
| `x402_register` | Register your own x402 endpoint into the live catalog | Free |
| `x402_trust` | ERC-8004 on-chain identity, reputation & attestations for a wallet | Free |
| `x402_facilitator_check` | Verify facilitator availability for a network before payment | Free |

---

## Why This Matters for CDP Builders

The CDP roadmap explicitly lists a **discovery layer** as a planned capability. We shipped it — open source, live on Base mainnet, integrated with CDP wallets.

Our CDP integration:
- **CDP Wallet** (`0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA`) is the active payment recipient — all discovery revenue flows on-chain
- Payment verification uses **local EIP-712 signature recovery** (`eth_account`) — no external CDP API dependency for verification
- Compatible with **AgentKit**: any AgentKit-powered agent can call `x402_discover` to find payable services and execute in one workflow
- Built for the **x402 standard** that Coinbase created and is actively expanding

---

## Three-Layer Architecture

```
Discovery  →  Trust  →  Facilitator Compatibility
```

Most x402 implementations handle payment execution. We handle the three critical pre-payment decisions:

1. **Discovery** (`x402_discover`): *What services exist and which are best for my need?*
2. **Trust** (`x402_trust`): *Is this service's wallet legitimate? What's its on-chain reputation?*
3. **Facilitator** (`x402_facilitator_check`): *Will payment actually succeed on this network, or will it silently fail?*

Without all three, agents will discover services they can't safely pay for, or services on networks with no facilitator support.

---

## Trust Layer: ERC-8004

Every service in the catalog includes on-chain trust signals from [ERC-8004](https://github.com/erc-8004/erc-8004-contracts) — the decentralized AI agent trust standard launched January 2026.

```json
{
  "name": "Tavily AI Search",
  "price_usd": 0.002,
  "network": "eip155:8453",
  "facilitator_compatible": true,
  "erc8004_verified": true,
  "erc8004_reputation_score": 92,
  "erc8004_attestations": 14,
  "recommended_facilitator": "https://x402.org/facilitator"
}
```

**The x402 Bazaar has 33M+ transactions/month but avg service fidelity is ~38/100. ERC-8004 trust signals let agents filter for verified, reputable services — not just the cheapest ones.**

---

## Quickstart

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "x402-discovery": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/rplryan/x402-discovery-mcp:latest"]
    }
  }
}
```

### Cursor / Windsurf

```json
{
  "x402-discovery": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "ghcr.io/rplryan/x402-discovery-mcp:latest"]
  }
}
```

### Python directly

```bash
pip install mcp requests
python server.py
```

---

## Example Usage

Once installed, ask Claude:

> *"Find me an x402 API for web research under $0.05 per call with verified on-chain trust"*

Claude calls `x402_discover(capability="research", max_price_usd=0.05)` and returns quality-ranked results with endpoint URLs, pricing, uptime, facilitator compatibility, and ERC-8004 trust scores.

> *"Is this wallet safe to pay? 0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA"*

Claude calls `x402_trust(wallet="0xDBBe...")` and returns on-chain identity, reputation score, attestation count, and `.well-known/erc8004.json` verification.

> *"Can I pay this service on Base mainnet?"*

Claude calls `x402_facilitator_check(network="eip155:8453")` and returns available facilitators (Coinbase, PayAI, RelAI, xpay), their fee structures, and settlement confirmation.

---

## Traction

- **Smithery score: 100/100** — top-ranked x402 MCP server
- **16 live services** across 5 categories (AI, Data, Research, Media, Finance)
- **v3.2.0** with facilitator compatibility layer
- **RouteNet v1.0.0** live at [x402-routenet.onrender.com](https://x402-routenet.onrender.com) — smart routing with 4 strategies (cost, performance, reliability, composite)
- **First real on-chain payment confirmed** — not a testnet demo
- **PR open** on [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (81.7k stars)
- **x402.watch** listing active

---

## Related Projects

- **[x402 RouteNet](https://github.com/rplryan/x402-routenet)** — Smart routing layer: given a capability need, picks the optimal x402 service using cost/performance/reliability strategies
- **[x402 Payment Harness](https://github.com/rplryan/x402-payment-harness)** — Standalone Python library for testing x402 payments without CDP dependencies (EOA-based, EIP-712, no secrets required)

---

## Discovery API

This MCP server wraps the public [x402 Service Discovery API](https://x402-discovery-api.onrender.com):

- `GET /catalog` — full index, free, ungated
- `GET /discover?q=research` — quality search ($0.005/query, requires payment)
- `GET /trust/{wallet}` — ERC-8004 trust lookup for any wallet address
- `POST /facilitator/check` — facilitator availability check
- `GET /.well-known/x402-discovery` — machine-readable catalog (RFC 5785)
- `POST /register` — self-service provider registration

---

## License

MIT

<!-- mcp-name: io.github.rplryan/x402-discovery-mcp -->
