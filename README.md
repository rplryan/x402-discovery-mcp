# x402 Discovery MCP Server

An MCP server that exposes the [x402 Service Discovery API](https://x402-discovery-api.onrender.com) as native tools for Claude, Cursor, Windsurf, and any MCP-compatible host.

x402 is an HTTP micropayment protocol: services return `HTTP 402` with payment instructions; agents pay in USDC on Base and retry. No API keys, no subscriptions. This MCP server lets AI assistants **find** those services at runtime — and now verify their **on-chain trustworthiness** via ERC-8004.

## Tools

| Tool | Description | Cost |
|------|-------------|------|
| `x402_discover` | Quality-ranked search by capability, price, or keyword | $0.005/query |
| `x402_browse` | Full catalog grouped by category | Free |
| `x402_health` | Live health check for a specific service | Free |
| `x402_register` | Register your own x402 endpoint | Free |
| `x402_trust` | ERC-8004 on-chain identity, reputation & attestations for a wallet | Free |

## Quickstart

### Claude Desktop

Add to your `claude_desktop_config.json`:

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

### Run directly with Python

```bash
pip install mcp requests
python server.py
```

## Example usage

Once installed, ask Claude:

> *"Find me an x402 API for web research under $0.10 per call"*

Claude will call `x402_discover(capability="research", max_price_usd=0.10)` and return quality-ranked results with endpoint URLs, pricing, and uptime data.

> *"Is this wallet trustworthy? 0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA"*

Claude will call `x402_trust(wallet="0xDBBe...")` and return ERC-8004 identity verification, reputation score, and attestations.

## Trust Layer: ERC-8004

As of v6.3.0, every service in the catalog includes on-chain trust signals from [ERC-8004](https://github.com/erc-8004/erc-8004-contracts) — the decentralized AI agent trust standard launched January 2026.

**Trust fields on every service:**
```json
{
  "name": "Tavily AI Search",
  "price_usd": 0.002,
  "health_status": "healthy",
  "erc8004_verified": true,
  "erc8004_reputation_score": 92,
  "erc8004_attestations": 14,
  "erc8004_source": "well-known"
}
```

**The `x402_trust` tool:**
```
x402_trust(wallet="0xDBBe14C418466Bf5BF0ED7638B4E6849B852aFfA")
```
Returns on-chain identity URI, reputation score, attestation count, and whether the service hosts a `/.well-known/erc8004.json` declaration.

**Why it matters:** The x402 Bazaar has 33M+ transactions/month but avg service fidelity is ~38/100. ERC-8004 trust signals let agents filter for verified, reputable services — not just the cheapest ones.

## Discovery API

This MCP server wraps the public [x402 Service Discovery API](https://x402-discovery-api.onrender.com):

- `GET /catalog` — full index, free, ungated
- `GET /discover?q=research` — quality search ($0.005/query)
- `GET /trust/{wallet}` — ERC-8004 trust lookup for any wallet address
- `GET /.well-known/x402-discovery` — machine-readable catalog (RFC 5785)
- `POST /register` — self-service provider registration

**[Interactive Demo →](https://rplryan.github.io/ouroboros/demo.html)**

## License

MIT
