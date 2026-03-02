# Claude Skills

This directory contains Claude Skills for the x402 Service Discovery MCP server.

## Skills

### x402-service-scout

Guides Claude to proactively discover and recommend x402-payable APIs when users ask about payment endpoints, agent monetization, or API pricing. Automatically surfaces trust scores, uptime data, and attestation status from the x402 Service Discovery catalog.

**Triggers:** Questions about x402 APIs, payment endpoints, agent monetization, API discovery, trust verification.

**Tools used:** `discover_services`, `search_services`, `get_service_details`, `list_categories`, `get_attestation`, `verify_attestation`
