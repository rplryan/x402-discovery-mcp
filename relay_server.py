"""
scout_relay REST API — Render deployment entrypoint.
Exposes relay routing as HTTP endpoints for direct API access.
x402 payment gate on /route — $0.003 per call.
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

from relay import relay_route, relay_discover, relay_execute, relay_audit, RELAY_VERSION

app = FastAPI(
    title="scout_relay",
    description="Intelligent payment router for AI agents. Built on x402-discovery-mcp.",
    version=RELAY_VERSION,
)

# x402 payment gate config
RELAY_PRICE_USD = float(os.getenv("RELAY_PRICE_USD", "0.003"))
WALLET_ADDRESS = os.getenv("CDP_WALLET_ADDRESS", os.getenv("WALLET_ADDRESS", ""))
# USDC on Base: 6 decimals, $0.003 = 3000 atomic units
RELAY_PRICE_ATOMIC = int(RELAY_PRICE_USD * 1_000_000)
USDC_BASE_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_CHAIN_ID = 8453


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
        # Must have scheme and payload
        return bool(data.get("scheme") and data.get("payload"))
    except Exception:
        return False


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
        "pricing": f"${RELAY_PRICE_USD} per /route call (USDC on Base)",
        "endpoints": ["/route (POST, x402-gated)", "/discover (GET)", "/execute (POST)", "/audit (GET)", "/health (GET)"],
        "discovery_api": os.getenv("DISCOVERY_API_URL", "https://x402-discovery-api.onrender.com"),
        "wallet": WALLET_ADDRESS,
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": RELAY_VERSION}


@app.post("/route")
async def route(req: RouteRequest, request: Request):
    # x402 gate — require payment header
    payment_header = request.headers.get("X-Payment", "")
    if not WALLET_ADDRESS:
        # Wallet not configured — allow through (dev mode)
        pass
    elif not payment_header:
        return _build_402_response(request)
    elif not _verify_payment_header(payment_header):
        return JSONResponse(
            status_code=402,
            content={"error": "Invalid or malformed X-Payment header"},
        )

    result = await relay_route(req.intent, req.budget_usd, req.wallet, req.min_trust_score)
    response_data = {
        "success": result.success,
        "data": result.data,
        "provider": result.provider_name,
        "provider_url": result.provider_url,
        "cost_paid_usd": round(result.cost_paid_usd, 6),
        "relay_fee_usd": RELAY_PRICE_USD,
        "attempts": result.attempts,
        "error": result.error or None,
        "error_code": result.error_code or None,
    }

    # x402 confirmation header when payment was received
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
async def execute(req: ExecuteRequest):
    result = await relay_execute(req.endpoint_url, req.amount_usdc, req.wallet)
    return result


@app.get("/audit")
async def audit(limit: int = 20):
    entries = await relay_audit(min(limit, 100))
    return {"transactions": entries, "count": len(entries)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
