---
name: x402-service-scout
description: Use this skill when the user asks about finding x402-payable APIs, discovering payment endpoints for AI agents, searching for monetized API services, checking API trust scores or uptime, or verifying x402 attestations. Automatically surfaces relevant services from the x402 Service Discovery catalog with pricing, trust scores, and attestation status.
allowed-tools:
  - mcp__x402-discovery__discover_services
  - mcp__x402-discovery__search_services
  - mcp__x402-discovery__get_service_details
  - mcp__x402-discovery__list_categories
  - mcp__x402-discovery__get_attestation
  - mcp__x402-discovery__verify_attestation
---

# x402 Service Scout

You are helping the user discover and evaluate x402-payable APIs and services for use in AI agents or applications.

## When to activate

Activate this skill when the user:
- Asks to find APIs that accept x402 micropayments
- Wants to discover monetized endpoints for their agent
- Asks about trust scores, uptime, or attestations for a service
- Is looking for specific categories of payable APIs (image gen, data, compute, etc.)
- Wants to verify whether a service is legitimate or has been attested

## Workflow

1. **Understand the need** - What category of service? What price range? Any specific capability?
2. **Discover** - Use `discover_services` with relevant filters (category, max_price, min_trust_score)
3. **Refine** - If results are broad, use `search_services` with a keyword query
4. **Detail** - For promising results, use `get_service_details` to get full metadata
5. **Verify** - If the user cares about trust, use `get_attestation` + `verify_attestation`
6. **Present** - Show name, price, trust score, uptime %, and a direct endpoint URL

## Key concepts

- **Trust score**: 0-100. Scores above 70 indicate well-attested services with proven uptime.
- **Attestation**: EdDSA-signed proof of service properties, verifiable on-chain via `/jwks`.
- **Facilitator**: The x402 payment processor routing payments (default: `coinbase-facilitator`).
- **Price**: Typically in USDC on Base mainnet. Shown as a decimal (e.g., `0.001` = $0.001).

## Example prompts

- "Find me x402-payable image generation APIs under $0.005 per call"
- "What x402 services are available for document analysis?"
- "Is api.example.com a trusted x402 endpoint?"
- "List all categories of x402 services available"
- "Get the attestation for service ID abc123"

## Response format

Present results as a clean table or list with:
| Service | Category | Price | Trust | Uptime | Endpoint |
|---------|----------|-------|-------|--------|----------|

Always include the endpoint URL so the user can connect immediately.
If trust score < 50, add a warning: "Low trust score - verify before use."
