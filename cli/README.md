# x402scout CLI

> 🛰️ Terminal search & discovery client for the x402 agent economy

[![npm](https://img.shields.io/badge/npm-%40rplryan%2Fx402scout-brightgreen)](https://github.com/rplryan/x402-discovery-mcp/pkgs/npm/x402scout)

```bash
# Install globally (requires GitHub Packages auth)
npm install -g @rplryan/x402scout --registry=https://npm.pkg.github.com
```

## Commands

### Search services
```bash
x402scout search "weather data"
```
```
🛰️  x402Scout — Searching for: "weather data"
──────────────────────────────────────────────────────────────
┌──────────────────────────────────┬─────────┬────────────┬──────────┐
│ SERVICE                          │ TRUST   │ CATEGORY   │ PRICE    │
├──────────────────────────────────┼─────────┼────────────┼──────────┤
│ ✅ OpenWeather x402              │   87    │ data       │ $0.0010  │
│ ⚠️  WeatherOracle                │   44    │ data       │ $0.0025  │
└──────────────────────────────────┴─────────┴────────────┴──────────┘

  2 results · powered by x402scout.com
```

### Top services by trust score
```bash
x402scout top 10
```

### Browse by category
```bash
x402scout browse data
x402scout browse agent
x402scout browse utility
```

### Scan a URL for x402 compliance
```bash
x402scout scan https://api.yourservice.com
```
```
🛰️  x402Scout — Scanning: https://api.yourservice.com
──────────────────────────────────────────────────────────────
  ✅ Trust Score:   78    B — x402 Compliant

  Signals:
    ✓ Returns 402 status code
    ✓ x402Version header present
    ✓ Payment scheme detected
```

### Ecosystem stats
```bash
x402scout stats
```
```
🛰️  x402Scout — Ecosystem Stats
──────────────────────────────────────────────────────────────

  Total Services:    343
  Avg Trust Score:    28
  Healthy:           298 / 343
  With Pricing:       87 / 343

  Trust Distribution:
    ● High (≥70):    12
    ● Mid  (40–69):  31
    ● Low  (<40):   300

  Top Categories:
    data          ████████████████████ 156
    utility       ████████████ 89
    agent         █████████ 67
    text          ██████ 31

  Source: x402scout.com · Updates every 6h · 343 services
```

## Install via GitHub Packages

1. Create a GitHub Personal Access Token with `read:packages` scope
2. Add to `~/.npmrc`:
   ```
   //npm.pkg.github.com/:_authToken=YOUR_TOKEN
   @rplryan:registry=https://npm.pkg.github.com
   ```
3. Install:
   ```bash
   npm install -g @rplryan/x402scout
   ```

## Development

```bash
git clone https://github.com/rplryan/x402-discovery-mcp
cd x402-discovery-mcp/cli
npm install
node bin/x402scout.js stats
```

## API

All data comes from [x402scout.com](https://x402scout.com) — 340+ live x402-enabled services, updated every 6 hours.

**Trust Score** (0–100) is computed from:
- Uptime percentage (40%)
- x402 protocol compliance (30%)
- Facilitator compatibility (20%)
- Response time (10%)

| Score | Grade | Icon |
|-------|-------|------|
| ≥ 70 | Trusted | ✅ |
| 40–69 | Moderate | ⚠️ |
| < 40 | Unverified | ❌ |

## License

MIT
