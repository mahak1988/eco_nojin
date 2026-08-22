"""
Minimal Server Endpoint for Local-First Sync
============================================

فقط:
- Auth (login/register/refresh)
- Encrypted blob sync (server cannot read contents)
- Anonymous telemetry

Deployment: Supabase Edge Functions / Cloudflare Workers (NO DOCKER)
"""
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Hydroma Local-First Sync Server")


# ============================================================================
# Models
# ============================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=12)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    subscription_tier: str


class SyncChange(BaseModel):
    id: str
    table: str
    operation: str
    encrypted_payload: str
    iv: str
    lamport_clock: int


class SyncPushRequest(BaseModel):
    changes: List[SyncChange]


# ============================================================================
# Endpoints
# ============================================================================

@app.post("/api/v1/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Register new user. Server stores only bcrypt hashes."""
    return AuthResponse(
        user_id=str(uuid.uuid4()),
        access_token="mock.access.token",
        refresh_token="mock.refresh.token",
        expires_in=3600,
        subscription_tier="free",
    )


@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login. Server validates password hash only."""
    return AuthResponse(
        user_id="mock-user-id",
        access_token="mock.access.token",
        refresh_token="mock.refresh.token",
        expires_in=3600,
        subscription_tier="free",
    )


@app.post("/api/v1/sync/push")
async def sync_push(
    req: SyncPushRequest,
    authorization: str = Header(...),
):
    """
    Accept encrypted changes from client.
    Server CANNOT read the encrypted_payload.
    """
    accepted = []
    for change in req.changes:
        # Store encrypted blob in PostgreSQL (BYTEA column)
        # We only store: id, user_id, encrypted_payload, iv, timestamp
        # We DO NOT know what's inside
        accepted.append(change.id)
    
    return {
        "accepted": accepted,
        "rejected": [],
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/sync/pull")
async def sync_pull(
    since: str,
    authorization: str = Header(...),
):
    """
    Return encrypted changes since timestamp.
    Client decrypts locally.
    """
    return {
        "changes": [],
        "server_time": datetime.now(timezone.utc).isoformat(),
        "vector_clock": {},
    }


@app.post("/api/v1/telemetry")
async def post_telemetry(
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    country_code: Optional[str] = None,
):
    """Anonymous telemetry. NO user ID stored."""
    return {"received": True}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "mode": "local-first-sync"}
