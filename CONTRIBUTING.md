# Contributing to x402 Service Discovery

Thank you for your interest in contributing! Here's how you can help the x402 ecosystem grow.

---

## Registering a New x402 Service

The easiest way to contribute is to register an x402-compatible API endpoint in the discovery catalog.

### Requirements

Your service must implement the [x402 payment standard](https://github.com/coinbase/x402):

- HTTP `402 Payment Required` response with x402 payment headers
- USDC payments on Base (Base Mainnet or Base Sepolia for testing)
- A publicly accessible endpoint URL

### How to Register

**Option 1: Via the MCP tool (recommended)**
```
x402_register(url="https://your-api.example.com/endpoint", category="your-category")
```

**Option 2: Via the REST API**
```bash
curl -X POST https://x402-discovery-api.onrender.com/register \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://your-api.example.com/endpoint", "category": "your-category"}'
```

**Option 3: Open an issue**
Open a [New Registration issue](https://github.com/rplryan/x402-discovery-mcp/issues/new?template=register.md) with your endpoint URL and category.

### Service Categories

Available categories: `search`, `generation`, `data`, `analytics`, `nlp`, `vision`, `audio`, `finance`, `infrastructure`, `other`

---

## Code Contributions

### Setup

```bash
git clone https://github.com/rplryan/x402-discovery-mcp
cd x402-discovery-mcp
pip install -r requirements.txt
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Pull Request Guidelines

1. Fork the repo and create a feature branch
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Open a PR with a description of what changed and why

---

## Reporting Issues

- **Bug report**: [Open a bug issue](https://github.com/rplryan/x402-discovery-mcp/issues/new)
- **Feature request**: Comment on the [Roadmap issue](https://github.com/rplryan/x402-discovery-mcp/issues) with a 👍
- **Security issue**: Email x402scout@proton.me — do not open a public issue

---

## Community

Share what you built in the [Show and Tell discussion](https://github.com/rplryan/x402-discovery-mcp/discussions/1).

Questions? Open a discussion or email x402scout@proton.me.
