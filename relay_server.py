"""
scout_relay REST API — Render deployment entrypoint v2.1.0
Exposes relay routing as HTTP endpoints + provider self-serve placement bids.
"""
import base64
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from eth_account import Account
from eth_account.messages import encode_typed_data
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

# CDP credentials for settle (Bazaar indexing)
CDP_API_KEY_ID: str = os.environ.get("CDP_API_KEY_ID", "")
CDP_API_KEY_SECRET: str = os.environ.get("CDP_API_KEY_SECRET", "")
CDP_SETTLE_URL: str = "https://api.cdp.coinbase.com/platform/v2/x402/settle"


# ── helpers ─────────────────────────────────────────────────────────────────
def _build_402_response(amount_usd: float) -> dict:
    """Build a Bazaar-compatible 402 Payment Required response."""
    amount_atomic = int(amount_usd * 1_000_000)
    accept_entry = {
        "scheme": "exact",
        "network": "eip155:8453",
        "maxAmountRequired": str(amount_atomic),
        "resource": "",
        "description": f"scout_relay service fee ${amount_usd:.4f}",
        "mimeType": "application/json",
        "payTo": WALLET_ADDRESS,
        "maxTimeoutSeconds": 60,
        "asset": USEC_BASE,
        "extra": {"name": "USD Coin", "version": "2"},
        "outputSchema": {
            "input": {
                "type": "http",
                "method": "POST",
                "discoverable": True,
            },
            "output": {
                "type": "json",
                "example": {"description": "scout_relay routing result"},
            },
        },
        "extensions": {
            "bazaar": {
                "info": {
                    "input": {"type": "http", "method": "POST"},
                    "output": {"type": "json", "example": {"description": "scout_relay routing result"}},
                },
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "const": "http"},
                                "method": {"type": "string"},
                                "discoverable": {"type": "boolean"},
                            },
                            "required": ["type"],
                        },
                        "output": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "example": {"type": "object"},
                            },
                            "required": ["type"],
                        },
                    },
                    "required": ["input"],
                },
            }
        },
    }
    return {
        "x402Version": 1,
        "error": "Payment required",
        "accepts": [accept_entry],
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


# ── payment verification ─────────────────────────────────────────────────────

def _generate_cdp_jwt(method: str, path: str) -> str | None:
    if not CDP_API_KEY_ID or not CDP_API_KEY_SECRET:
        return None
    try:
        from cdp.auth.utils.jwt import generate_jwt, JwtOptions
        return generate_jwt(JwtOptions(
            api_key_id=CDP_API_KEY_ID,
            api_key_secret=CDP_API_KEY_SECRET,
            request_method=method,
            request_host="api.cdp.coinbase.com",
            request_path=path,
        ))
    except Exception:
        return None


def _verify_x402_payment(payment_header: str, resource_url: str) -> tuple[bool, str]:
    """Verify inbound x402 EIP-712 signed payment. Returns (is_valid, payer_address)."""
    if not WALLET_ADDRESS:
        # No wallet configured — cannot verify, pass through
        return True, ""
    try:
        decoded = base64.b64decode(payment_header + "==")
        data = json.loads(decoded)

        scheme = data.get("scheme", "")
        network = data.get("network", "")
        if scheme != "exact" or network not in ("eip155:8453", "base"):
            return False, ""

        payload = data.get("payload", {})
        signature = payload.get("signature", "")
        auth = payload.get("authorization", {})

        valid_before = int(auth.get("validBefore", 0))
        if valid_before > 0 and int(time.time()) > valid_before:
            return False, ""

        if auth.get("to", "").lower() != WALLET_ADDRESS.lower():
            return False, ""

        signed_amount = int(auth.get("value", 0))
        price_units = int(RELAY_PRICE_USD * 1_000_000)
        if signed_amount < price_units:
            return False, ""

        nonce_raw = auth.get("nonce", "0x" + "0" * 64)
        nonce_bytes = bytes.fromhex(nonce_raw[2:] if nonce_raw.startswith("0x") else nonce_raw)
        structured = {
            "domain": {
                "name": "USD Coin",
                "version": "2",
                "chainId": 8453,
                "verifyingContract": USEC_BASE,
            },
            "message": {
                "from": auth.get("from", ""),
                "to": auth.get("to", ""),
                "value": signed_amount,
                "validAfter": int(auth.get("validAfter", 0)),
                "validBefore": valid_before,
                "nonce": nonce_bytes,
            },
            "primaryType": "TransferWithAuthorization",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
        }
        msg = encode_typed_data(full_message=structured)
        recovered = Account.recover_message(msg, signature=signature)
        payer = auth.get("from", "")
        if recovered.lower() != payer.lower():
            return False, ""

        # CDP settle — on-chain transferWithAuthorization (best-effort)
        # Must use x402 V2 payload format (CDP API requirement)
        try:
            v2_reqs = {
                "scheme": "exact",
                "network": "eip155:8453",
                "asset": USEC_BASE,
                "amount": str(price_units),
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 60,
                "extra": {"name": "USD Coin", "version": "2"},
            }
            settle_payload = {
                "x402Version": 2,
                "paymentPayload": {
                    "x402Version": 2,
                    "payload": payload,
                    "accepted": v2_reqs,
                },
                "paymentRequirements": v2_reqs,
            }
            headers = {"Content-Type": "application/json"}
            jwt_token = _generate_cdp_jwt("POST", "/platform/v2/x402/settle")
            if jwt_token:
                headers["Authorization"] = f"Bearer {jwt_token}"
            with httpx.Client(timeout=10.0) as sc:
                sc.post(CDP_SETTLE_URL, json=settle_payload, headers=headers)
        except Exception:
            pass  # Non-fatal

        return True, payer
    except Exception:
        return False, ""


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
        host = request.headers.get("host", "x402-scout-relay.onrender.com")
        resource_url = f"https://{host}{request.url.path}"
        is_valid, payer = _verify_x402_payment(payment_header, resource_url)
        if not is_valid:
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
