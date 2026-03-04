"""
scout_relay REST API — Render deployment entrypoint.
Exposes relay routing as HTTP endpoints for direct API access.
"""
import os
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from relay import relay_route, relay_discover, relay_execute, relay_audit, RELAY_VERSION

app = FastAPI(
    title="scout_relay",
    description="Intelligent payment router for AI agents. Built on x402-discovery-mcp.",
    version=RELAY_VERSION,
)


class RouteRequest(BaseModel):
    intent: str
    budget_usd: float
    wallet: Optional[str] = None
    min_trust_score: int = 50


class ExecuteRequest(BaseModel):
    endpoint_url: str
    amount_usdc: float
    wallet: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "scout_relay",
        "version": RELAY_VERSION,
        "description": "Intelligent payment router for AI agents",
        "endpoints": ["/route", "/discover", "/execute", "/audit", "/health"],
        "discovery_api": os.getenv("DISCOVERY_API_URL", "https://x402-discovery-api.onrender.com"),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": RELAY_VERSION}


@app.post("/route")
def route(req: RouteRequest):
    result = relay_route(req.intent, req.budget_usd, req.wallet, req.min_trust_score)
    return {
        "success": result.success,
        "data": result.data,
        "provider": result.provider_name,
        "provider_url": result.provider_url,
        "cost_paid_usd": round(result.cost_paid_usd, 6),
        "attempts": result.attempts,
        "error": result.error or None,
        "error_code": result.error_code or None,
    }


@app.get("/discover")
def discover(capability: str, max_price_usd: float = 0.50, min_trust_score: int = 50):
    providers = relay_discover(capability, max_price_usd, min_trust_score)
    return {"providers": providers, "count": len(providers)}


@app.post("/execute")
def execute(req: ExecuteRequest):
    result = relay_execute(req.endpoint_url, req.amount_usdc, req.wallet)
    return result


@app.get("/audit")
def audit(limit: int = 20):
    entries = relay_audit(min(limit, 100))
    return {"transactions": entries, "count": len(entries)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
