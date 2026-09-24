"""Idempotency middleware for financial endpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database.hub import hub
from database.models import FinIdempotencyKey

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_HOURS = 24
IDEMPOTENCY_HEADER = "Idempotency-Key"
MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

PROTECTED_PREFIXES = (
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/redoc",
)

# Routes that require idempotency (exact paths)
IDEMPOTENT_EXACT_ROUTES = {
    "/api/v1/ecowallet/earn",
    "/api/v1/ecowallet/redeem",
    "/api/v1/ecowallet/distribute",
    "/api/v1/ledger/entries",
    "/api/v1/marketplace/orders",
    "/api/v1/marketplace/payments",
    "/api/v1/marketplace/payments/callback",
    "/api/v1/finance/wallet/earn",
    "/api/v1/finance/wallet/redeem",
    "/api/v1/finance/payments/intent",
}

# Parameterized routes that require idempotency (6-step purchase flow)
IDEMPOTENT_PARAM_ROUTES = [
    "/api/v1/marketplace/orders/{order_id}",
    "/api/v1/marketplace/orders/{order_id}/confirm",
    "/api/v1/marketplace/orders/{order_id}/dispute",
    "/api/v1/marketplace/orders/{order_id}/settle",
    "/api/v1/marketplace/orders/{order_id}/complete",
    "/api/v1/marketplace/payments/{payment_id}/confirm",
    "/api/v1/marketplace/payments/{payment_id}/escrow/release",
    "/api/v1/marketplace/payments/{payment_id}/escrow/refund",
]


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce idempotency for financial operations."""

    def __init__(self, app) -> None:
        super().__init__(app)

    def _body_hash(self, body: bytes) -> str:
        """Generate SHA256 hash of body for idempotency key."""
        return hashlib.sha256(body).hexdigest()

    def _user_id(self, request: Request) -> str:
        """Extract user_id from request state."""
        return getattr(request.state, "user_id", "anonymous")

    def _requires_idempotency(self, path: str, method: str) -> bool:
        """Check if the route requires idempotency."""
        if method not in {"POST", "PATCH", "PUT", "DELETE"}:
            return False
        # Check exact match
        if path in IDEMPOTENT_EXACT_ROUTES:
            return True
        # Check parameterized routes
        for route in IDEMPOTENT_PARAM_ROUTES:
            pattern = route.replace("{", "(?P<").replace("}", ">[^/]+)")
            if re.match(f"^{pattern}$", path):
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        if not self._requires_idempotency(request.url.path, request.method):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Idempotency-Key header required for this operation",
                    "code": "IDEMPOTENCY_KEY_REQUIRED",
                },
            )

        # Validate key format: accept SHA256 hex (64 chars) or UUID v4
        is_sha256 = len(idempotency_key) == 64 and all(
            c in "0123456789abcdefABCDEF" for c in idempotency_key
        )
        if not is_sha256:
            try:
                uuid.UUID(idempotency_key)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid Idempotency-Key format. Must be SHA256 hex or UUID v4.",
                        "code": "INVALID_IDEMPOTENCY_KEY",
                    },
                )

        # Read request body for fingerprint
        body = await request.body()

        # If SHA256 key, validate against formula: SHA256(clientSecret + path + body)
        if is_sha256:
            client_secret = request.headers.get("X-Client-Secret", "")
            path = request.url.path
            computed = hashlib.sha256(
                (client_secret + path + body.decode("utf-8", errors="replace")).encode()
            ).hexdigest()
            if computed != idempotency_key:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Idempotency-Key SHA256 mismatch",
                        "code": "INVALID_IDEMPOTENCY_KEY",
                    },
                )

        request_hash = hashlib.sha256(body).hexdigest()

        # Get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None) or "anonymous"

        # Check idempotency key in database
        async with hub.get_async_session() as db:
            stmt = select(FinIdempotencyKey).where(
                FinIdempotencyKey.key == idempotency_key, FinIdempotencyKey.user_id == user_id
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                if existing.request_hash != request_hash:
                    return JSONResponse(
                        status_code=422,
                        content={
                            "detail": "Idempotency key reused with different payload",
                            "code": "IDEMPOTENCY_KEY_REUSE",
                        },
                    )
                if existing.status == "completed":
                    # Return cached response
                    return JSONResponse(
                        status_code=existing.response_code,
                        content=existing.response_body,
                    )
                elif existing.status == "pending":
                    return JSONResponse(
                        status_code=409,
                        content={
                            "detail": "Request with this idempotency key is already being processed",
                            "code": "IDEMPOTENCY_KEY_IN_PROGRESS",
                        },
                    )

            # Create new idempotency key record

            new_key = FinIdempotencyKey(
                user_id=getattr(request.state, "user_id", "anonymous"),
                key=idempotency_key,
                route=str(request.url.path),
                request_hash=request_hash,
                status="pending",
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
            db.add(new_key)
            await db.commit()
            await db.refresh(new_key)

        # Process the request
        response = await call_next(request)

        # Cache successful responses
        if response.status_code < 400:
            # Capture response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Reconstruct response with cached body
            try:
                cached_content = json.loads(response_body.decode())
            except Exception:
                cached_content = {"detail": "Response cached"}

            # Update idempotency key with response
            async with hub.get_async_session() as db:
                stmt = select(FinIdempotencyKey).where(
                    FinIdempotencyKey.key == idempotency_key, FinIdempotencyKey.user_id == user_id
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.status = "completed"
                    existing.response_code = response.status_code
                    existing.response_body = cached_content
                    await db.commit()

            # Return new response with cached body
            return JSONResponse(
                status_code=response.status_code,
                content=cached_content,
                headers=dict(response.headers),
            )

        return response
