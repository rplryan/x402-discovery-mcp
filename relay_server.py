"""
scout_relay REST API — Render deployment entrypoint.
Exposes relay routing as HTTP endpoints for direct API access.
x402 payment gate on /route — $0.003 per call.

Phase 2: agent_id tracking, budget enforcement, enhanced /audit endpoint,
placement_bids.json loaded at startup.
"""
import os
import json
import base64
import hashlib
import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from relay import (
    relay_route,
    relay_discover,
    relay_execute,
    relay_audit,
    get_agent_budget_status,
    _load_placement_bids,
    RELAY_VERSION,
    RELAY_PRICE_USD,
)

app = FastAPI(
    title="scout_relay",
    description="Intelligent payment router for AI agents. Built on x402-discovery-mcp.",
    version=RELAY_VERSION,
)

# x402 payment gate config
WALLET_ADDRESS = os.getenv("CDP_WALLET_ADDRESS", os.getenv("WALLET_ADDRESS", ""))
# USDC on Base: 6 decimals, $0.003 = 3000 atomic units
RELAY_PRICE_ATOMIC = int(RELAY_PRICE_USD * 1_000_000)
USUDC_BASE_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_CHAIN_ID = 8453


@app.on_event("startup")
async def startup_event():
    """Pre-load placement bids on startup."""
    bids = _load_placement_bids()
    print(f"[scout_relay] v{RELAY_VERSION} started. Wallet: {WALLET_ADDRESS}. Placement bids loaded: {len(bids)}")


def _build_402_response(request: Request) -> JSONResponse:
    """Return x402-compliant payment required response."""
    nonce = hashlib.sha256(f"{time.time()}{request.url}".encode()).hexdigest()[:16]
    return JSONResponse(
        status_code=402,
        content={
            "x402Version": 1,
            "error": "Payment required for /route",
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "base-mainnet",
                    "maxAmountRequired": str(RELAY_PRICE_ATOMIC),
                    "resource": str(request.url),
                    "description": f"scout_relay routing — ${RELAY_PRICE_USD} per call",
                    "mimeType": "application/json",
                    "payTo": WALLET_ADDRESS,
                    "maxTimeoutSeconds": 300,
                    "asset": USDC_BASE_CONTRACT,
                    "extra": {
                        "name": "USD Coin",
                        "version": "2",
                        "chainId": BASE_CHAIN_ID,
                    },
                }
            ],
        },
        headers={
            "X-Payment-Required": "true",
            "X-Payment-Amount": str(RELAY_PRICE_USD),
            "X-Payment-Asset": "USDC",
            "X-Payment-Network": "base-mainnet",
        },
    )


def _verify_payment_header(payment_header: str) -> bool:
    """Verify X-Payment header. Returns True if payment appears valid."""
    if not payment_header:
        return False
    try:
        decoded = base64.b64decode(payment_header).decode()
        data = json.loads(decoded)
        return bool(data.get("scheme") and data.get("payload"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RouteRequest(BaseModel):
    intent: str
    budget_usd: float
    wallet: Optional[str] = None
    min_trust_score: int = 50
    agent_id: Optional[str] = None  # Phase 2


class ExecuteRequest(BaseModel):
    endpoint_url: str
    amount_usdc: float
    wallet: Optional[str] = None
    agent_id: Optional[str] = None  # Phase 2


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    bids = _load_placement_bids()
    return {
        "service": "scout_relay",
        "version": RELAY_VERSION,
        "description": "Intelligent payment router for AI agents",
        "pricing": f"${RELAY_PRICE_USD} per /route call (USDC on Base)",
        "endpoints": [
            "/route (POST, x402-gated)",
            "/discover (GET)",
            "/execute (POST)",
            "/audit (GET)",
            "/health (GET)",
        ],
        "discovery_api": os.getenv("DISCOVERY_API_URL", "https://x402-discovery-api.onrender.com"),
        "wallet": WALLET_ADDRESS,
        "active_placement_bids": len(bids),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": RELAY_VERSION}


@app.post("/route")
async def route(req: RouteRequest, request: Request):
    # x402 gate — require payment header
    payment_header = request.headers.get("X-Payment", "")
    if not WALLET_ADDRESS:
        pass  # dev mode: wallet not configured
    elif not payment_header:
        return _build_402_response(request)
    elif not _verify_payment_header(payment_header):
        return JSONResponse(
            status_code=402,
            content={"error": "Invalid or malformed X-Payment header"},
        )

    result = await relay_route(
        intent=req.intent,
        budget_usd=req.budget_usd,
        wallet=req.wallet,
        min_trust_score=req.min_trust_score,
        agent_id=req.agent_id,
        payment_header=payment_header or None,
    )

    # Phase 2: daily_budget_exceeded returns 429
    if result.error_code == "daily_budget_exceeded":
        budgets_data = {}  # already loaded inside relay_route
        return JSONResponse(
            status_code=429,
            content={
                "error": "daily_budget_exceeded",
                "limit": float(os.getenv("AGENT_DAILY_BUDGET_USD", "10.0")),
                "message": result.error,
                "agent_id": result.agent_id,
            },
        )

    response_data = {
        "success": result.success,
        "data": result.data,
        "provider": result.provider_name,
        "provider_url": result.provider_url,
        "cost_paid_usd": round(result.cost_paid_usd, 6),
        "relay_fee_usd": round(result.relay_fee_usd, 6),
        "placement_bid_applied": result.placement_bid_applied,
        "agent_id": result.agent_id,
        "attempts": result.attempts,
        "error": result.error or None,
        "error_code": result.error_code or None,
    }

    if payment_header:
        response_data["payment_received"] = True

    return JSONResponse(
        status_code=200,
        content=response_data,
        headers={"X-Payment-Response": base64.b64encode(json.dumps({"success": True}).encode()).decode()},
    )


@app.get("/discover")
async def discover(capability: str, max_price_usd: float = 0.50, min_trust_score: int = 50):
    providers = await relay_discover(capability, max_price_usd, min_trust_score)
    return {"providers": providers, "count": len(providers)}


@app.post("/execute")
async def execute(req: ExecuteRequest, request: Request):
    payment_header = request.headers.get("X-Payment", "")
    result = await relay_execute(
        endpoint_url=req.endpoint_url,
        amount_usdc=req.amount_usdc,
        wallet=req.wallet,
        agent_id=req.agent_id,
        payment_header=payment_header or None,
    )
    return result


@app.get("/audit")
async def audit(
    agent_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100,
):
    """Phase 2: filtered audit log with agent_id, since, and limit query params."""
    entries = await relay_audit(
        limit=min(limit, 500),
        agent_id=agent_id,
        since=since,
    )
    response: dict = {
        "transactions": entries,
        "count": len(entries),
    }
    # Include budget status if agent_id provided
    if agent_id:
        response["agent_budget"] = get_agent_budget_status(agent_id)
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
