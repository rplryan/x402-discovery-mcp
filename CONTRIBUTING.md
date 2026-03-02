# Contributing to x402 Service Discovery

Thanks for building on the x402 protocol! This guide explains how to add your service to the catalog, report bugs, or suggest features.

---

## 1. Register Your x402 Service

The easiest way to contribute is to add your x402-payable API to the live catalog.

### Option A: REST API

```bash
curl -X POST https://x402-discovery-api.onrender.com/register \
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

### Option B: MCP Tool (from inside Claude/Cursor/Windsurf)

Just ask: *"Register my service at https://myapi.example.com — it's a data API that costs $0.01 per call."*

Claude will call `x402_register` directly.

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| name | string | Human-readable service name |
| url | string | HTTPS endpoint implementing x402 |
| price_usd | number | Price per call in USDC |
| category | string | One of: data, compute, agent, utility |
| network | string | One of: base-mainnet, base-sepolia |
| description | string | Brief description of what the service does |

---

## 2. Report a Bug

Open a [GitHub Issue](https://github.com/rplryan/x402-discovery-mcp/issues/new) with:

- What you expected to happen
- What actually happened
- The MCP tool and arguments you used
- The response you received

---

## 3. Suggest a Feature

Check the [Roadmap issue](https://github.com/rplryan/x402-discovery-mcp/issues/3) where you can vote on candidate features with 👍.

---

## 4. Code Contributions

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `python -m pytest`
5. Submit a PR with a clear description of what changed and why

---

## 5. Build an ERC-8004 Attested Service

If you deploy an x402-payable API and want ERC-8004 trust scoring, reach out via a GitHub issue. We can walk you through the attestation process.

---

## Code of Conduct

Be constructive. This is an early-stage ecosystem project — ideas and criticism are welcome, but keep it respectful.

---

*Built on the [Coinbase x402 protocol](https://github.com/coinbase/x402) | MIT License*
