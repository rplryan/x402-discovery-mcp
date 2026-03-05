"""
scout_relay REST API — Render deployment entrypoint v2.1.0
Exposes relay routing as HTTP endpoints + provider self-serve placement bids.
"""
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── local relay logic ───────────────────────────────────────────────────────
from relay import (
    relay_route,
    relay_discover,
    relay_execute,
    relay_audit,
    RELAY_VERSION,
    RELAY_PRICE_USD,
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# ── config ──────────────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 10000))
WALLET_ADDRESS = os.environ.get("CDP_WALLET_ADDRESS") or os.environ.get("WALLET_ADDRESS", "")
USEC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base

BIDS_FILE = Path("/tmp/placement_bids.json")
BIDS_REGISTRATION_FEE_USD = float(os.environ.get("BID_REGISTRATION_FEE_USD", "0.01"))


# ── helpers ─────────────────────────────────────────────────────────────────
def _build_402_response(amount_usd: float) -> dict:
    """Build a 402 Payment Required response for the given amount."""
    amount_atomic = int(amount_usd * 1_000_000)
    return {
        "x402Version": 1,
        "error": "Payment required",
        "accepts": [{
            "scheme": "exact",
            "network": "base-mainnet",
            "maxAmountRequired": str(amount_atomic),
            "resource": "",
            "description": f"scout_relay service fee ${amount_usd:.4f}",
            "mimeType": "application/json",
            "payTo": WALLET_ADDRESS,
            "maxTimeoutSeconds": 60,
            "asset": USEC_BASE,
            "extra": {
                "name": "USD Coin",
                "version": "2",
            },
        }],
    }


def _load_bids() -> dict:
    """Load placement_bids.json, return {} if missing or corrupt."""
    try:
        if BIDS_FILE.exists():
            return json.loads(BIDS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_bids(bids: dict) -> None:
    BIDS_FILE.write_text(json.dumps(bids, indent=2))


# ── lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("scout_relay v%s starting on port %d", RELAY_VERSION, PORT)
    yield


# ── app ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="scout_relay",
    description="x402 routing and execution layer for the x402Scout ecosystem",
    version=RELAY_VERSION,
    lifespan=lifespan,
)


# ── models ──────────────────────────────────────────────────────────────────
class RouteRequest(BaseModel):
    intent: str
    budget_usd: float = Field(default=1.0, ge=0.001)
    agent_id: Optional[str] = None
    wallet_address: Optional[str] = None
    private_key: Optional[str] = None


class ExecuteRequest(BaseModel):
    url: str
    amount_usd: float = Field(default=0.01, ge=0.0001)
    agent_id: Optional[str] = None
    wallet_address: Optional[str] = None
    private_key: Optional[str] = None


class PlacementBidRequest(BaseModel):
    capability_category: str = Field(
        ...,
        description="Category of service capability (e.g. 'crypto_prices', 'data', 'agent')",
    )
    bid_per_transaction: float = Field(
        ..., ge=0.0001,
        description="Fee paid to scout_relay per transaction routed to this provider",
    )
    wallet_address: str = Field(
        ...,
        description="Provider's wallet address (Base USDC) for settlement",
    )
    provider_id: str = Field(
        ...,
        description="Unique identifier for this provider (e.g. service name or URL slug)",
    )
    service_url: Optional[str] = Field(
        default=None,
        description="Service URL — must already be registered in x402Scout catalog",
    )
    contact_email: Optional[str] = None


# ── middleware: x402 gate ────────────────────────────────────────────────────
GATED_PATHS = {"/route", "/execute"}


@app.middleware("http")
async def x402_gate(request: Request, call_next):
    if request.method == "POST" and request.url.path in GATED_PATHS:
        payment_header = request.headers.get("X-Payment")
        if not payment_header:
            return JSONResponse(
                status_code=402,
                content=_build_402_response(RELAY_PRICE_USD),
                headers={"x402Version": "1"},
            )
    return await call_next(request)


# ── routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": RELAY_VERSION,
        "relay_price_usd": RELAY_PRICE_USD,
        "wallet_address": WALLET_ADDRESS,
        "bids_active": len(_load_bids()),
    }


@app.get("/")
async def root():
    return {
        "service": "scout_relay",
        "version": RELAY_VERSION,
        "wallet_address": WALLET_ADDRESS,
        "endpoints": ["/route", "/execute", "/discover", "/audit", "/placement/bid", "/placement/bids", "/health"],
        "docs": "/docs",
    }


@app.post("/route")
async def route(req: RouteRequest):
    result = await relay_route(
        intent=req.intent,
        budget_usd=req.budget_usd,
        wallet=req.wallet_address,
    )
    return result


@app.post("/execute")
async def execute(req: ExecuteRequest):
    result = await relay_execute(
        endpoint_url=req.url,
        amount_usdc=req.amount_usd,
        agent_id=req.agent_id,
        wallet=req.wallet_address,
    )
    return result


@app.get("/discover")
async def discover(intent: str = "", limit: int = 10):
    return await relay_discover(capability=intent, max_price_usd=1.0)


@app.get("/audit")
async def audit(agent_id: Optional[str] = None, limit: int = 50):
    return await relay_audit(agent_id=agent_id, limit=limit)


# ── placement bid endpoints ───────────────────────────────────────────────────

@app.post("/placement/bid")
async def placement_bid(req: PlacementBidRequest, request: Request):
    """
    x402-gated provider self-serve bid registration.
    Providers pay BID_REGISTRATION_FEE_USD (default $0.01) to register a placement bid.
    Payment is required via X-Payment header (x402 standard).
    Once paid, the bid is written to placement_bids.json and takes effect immediately
    via hot-reload in relay.py.
    """
    # Check x402 payment header
    payment_header = request.headers.get("X-Payment")
    if not payment_header:
        return JSONResponse(
            status_code=402,
            content=_build_402_response(BIDS_REGISTRATION_FEE_USD),
            headers={"x402Version": "1"},
        )

    # Load existing bids
    bids = _load_bids()

    # Upsert the bid
    provider_key = req.provider_id
    bids[provider_key] = {
        "capability_category": req.capability_category,
        "bid_per_transaction": req.bid_per_transaction,
        "wallet_address": req.wallet_address,
        "provider_id": req.provider_id,
        "service_url": req.service_url,
        "contact_email": req.contact_email,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payment_header_preview": payment_header[:20] + "..." if len(payment_header) > 20 else payment_header,
        "active": True,
    }

    _save_bids(bids)

    log.info(
        "Placement bid registered: provider=%s category=%s bid=$%.4f",
        req.provider_id,
        req.capability_category,
        req.bid_per_transaction,
    )

    return {
        "status": "registered",
        "provider_id": req.provider_id,
        "capability_category": req.capability_category,
        "bid_per_transaction": req.bid_per_transaction,
        "message": (
            f"Bid registered. Routing tiebreaker active immediately. "
            f"Settlement occurs monthly via Base USDC to {req.wallet_address}."
        ),
        "total_bids_active": len([b for b in bids.values() if b.get("active")]),
    }


@app.get("/placement/bids")
async def get_placement_bids():
    """
    Read-only view of all active placement bids.
    Public — allows providers to see current competition.
    """
    bids = _load_bids()
    active_bids = [
        {
            "provider_id": v["provider_id"],
            "capability_category": v["capability_category"],
            "bid_per_transaction": v["bid_per_transaction"],
            "service_url": v.get("service_url"),
            "registered_at": v.get("registered_at"),
        }
        for v in bids.values()
        if v.get("active")
    ]
    return {
        "total_active_bids": len(active_bids),
        "bids": sorted(active_bids, key=lambda x: x["bid_per_transaction"], reverse=True),
    }


# ── entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("relay_server:app", host="0.0.0.0", port=PORT, log_level="info")
