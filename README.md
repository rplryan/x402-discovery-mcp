# x402 Discovery MCP Server

An MCP server that exposes the [x402 Service Discovery API](https://x402-discovery-api.onrender.com) as native tools for Claude, Cursor, Windsurf, and any MCP-compatible host.

x402 is an HTTP micropayment protocol: services return `HTTP 402` with payment instructions; agents pay in USDC on Base and retry. No API keys, no subscriptions. This MCP server lets AI assistants **find** those services at runtime.

## Tools

| Tool | Description |
|------|-------------|
| `x402_discover` | Quality-ranked search by capability, price, or keyword |
| `x402_browse` | Full catalog grouped by category (free, always available) |
| `x402_health` | Live health check for a specific service |
| `x402_register` | Register your own x402 endpoint with the discovery layer |

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

## Discovery API

This MCP server wraps the public [x402 Service Discovery API](https://x402-discovery-api.onrender.com):

- `GET /catalog` — full index, free, ungated
- `GET /.well-known/x402-discovery` — machine-readable catalog (RFC 5785)
- `GET /discover?q=research` — x402-gated quality search ($0.005/query)
- `POST /register` — self-service provider registration

## License

MIT
