# x402 Service Discovery MCP Server

> **The most comprehensive index of x402-payable services on Base — 251+ services, real-time quality signals, and agent-native tools. Built for Claude, Cursor, Windsurf, and any MCP-compatible AI agent.**

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.rplryan%2Fx402--discovery--mcp-blue)](https://registry.modelcontextprotocol.io/servers/io.github.rplryan/x402-discovery-mcp)
[![API Status](https://img.shields.io/badge/API-Live%20v3.3.0-brightgreen)](https://x402-discovery-api.onrender.com)
[![Services](https://img.shields.io/badge/Services%20Indexed-251%2B-brightgreen)](https://x402-discovery-api.onrender.com/.well-known/x402-discovery)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What This Does

x402 is Coinbase's HTTP-native micropayment standard for the agentic web. An AI agent hits an endpoint, gets an HTTP 402 response, pays with USDC on Base, and the endpoint returns data. No API keys. No subscriptions. Pay-per-use, machine-to-machine.

**The problem:** 251+ x402-payable services exist across the ecosystem but there's no way for an agent to find and evaluate them. Which ones are live? Which have the lowest latency? Which are facilitator-compatible?

**This MCP server is the answer.** It connects any Claude, Cursor, or Windsurf agent directly to the x402 Service Discovery API: a live, continuously-updated catalog.

## MCP Tools (6 total)

| Tool | Description | Cost |
|------|-------------|------|
| `x402_discover` | Search 251+ services by keyword, category, capability | $0.005 USDC |
| `x402_register` | Register a new service in the catalog | Free |
| `x402_health` | Real-time health + latency for any service | Free |
| `x402_catalog` | Browse the full catalog with filters | Free |
| `x402_report` | Report agent payment outcome | Free |
| `x402_facilitator_check` | Check facilitator compatibility | Free |

## Quickstart (30 seconds)

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

Add to Claude Desktop config or Cursor MCP settings. Done.

## Why This Exists

The x402 ecosystem has 251+ services across data, compute, agent, and utility categories. Without discovery infrastructure, agents cannot find or evaluate them. This is the Yellow Pages for the payable web.

**Quality signals per service:**
- Uptime percentage (rolling 30-day)
- Average latency (ms)
- Facilitator compatibility (required for automated payments)
- ERC-8004 trust signals
- Agent-native `llm_usage_prompt` and Python SDK snippets

**Auto-growth:** Catalog scans x402.org/ecosystem and awesome-x402 every 6 hours.

## Example

```python
# Find a live blockchain analytics service under $0.01
result = x402_discover(query="blockchain analytics", max_price_usd=0.01)
# Returns ranked services with price, uptime, latency, usage examples

# Before paying, verify facilitator compatibility
compat = x402_facilitator_check(url="https://einsteinai.io/api")
# Returns: facilitator_compatible=true/false, payment_details
```

## Related Projects

| Project | Description | Status |
|---------|-------------|--------|
| [x402 Discovery API](https://x402-discovery-api.onrender.com) | Backend API | Live v3.3.0 |
| [x402 RouteNet](https://github.com/rplryan/x402-routenet) | Smart payment routing | Live v1.0.0 |
| [x402 Payment Harness](https://github.com/rplryan/x402-payment-harness) | EOA testing toolkit | PyPI v1.0.0 |

## Catalog Sample

| Category | Count | Notable Services |
|----------|-------|------------------|
| data | 23+ | CoinGecko, Einstein AI, DJD Score, Ordiscan, Nansen |
| utility | 20+ | dTelecom STT, Pinata, Tip.MD, Cybercentry |
| compute | 10+ | BlockRun.AI, X402Engine, AurraCloud |
| agent | 9+ | Questflow, Ubounty, Bitte Protocol |

## Contributing

Register your x402 service for free:

```bash
curl -X POST https://x402-discovery-api.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{"name": "My Service", "url": "https://...", "price_usd": 0.01, "category": "data"}'
```

## License

MIT

---
*Built on Coinbase x402 protocol | Base Network | ERC-8004 | MCP*
