"""Idempotency middleware for financial endpoints."""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database.hub import hub
from database.models import FinIdempotencyKey

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_HOURS = 24
IDEMPOTENCY_HEADER = "Idempotency-Key"
MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

# Routes that require idempotency (exact paths)
IDEMPOTENT_EXACT_ROUTES = {
    "/api/v1/ecowallet/earn",
    "/api/v1/ecowallet/redeem",
    "/api/v1/ecowallet/distribute",
    "/api/v1/ledger/entries",
    "/api/v1/marketplace/orders",
    "/api/v1/marketplace/payments",
}

# Parameterized routes that require idempotency
IDEMPOTENT_PARAM_ROUTES = [
    "/api/v1/marketplace/orders/{order_id}/confirm",
    "/api/v1/marketplace/payments/{payment_id}/confirm",
]


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce idempotency for financial operations."""

    def __init__(self, app) -> None:
        super().__init__(app)

    def _requires_idempotency(self, path: str, method: str) -> bool:
        """Check if the route requires idempotency."""
        if method not in {"POST", "PATCH", "PUT", "DELETE"}:
            return False
        # Check exact match
        if path in IDEMPOTENT_EXACT_ROUTES:
            return True
        # Check parameterized routes
        for route in IDEMPOTENT_PARAM_ROUTES:
            import re
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

        # Validate key format (UUID v4)
        import uuid
        try:
            uuid.UUID(idempotency_key)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Invalid Idempotency-Key format. Must be UUID v4.",
                    "code": "INVALID_IDEMPOTENCY_KEY",
                },
            )

        # Read request body for fingerprint
        body = await request.body()
        request_hash = hashlib.sha256(body).hexdigest()

        # Get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None) or "anonymous"

        # Check idempotency key in database
        async with hub.get_async_session() as db:
            from sqlalchemy import select
            from database.models import FinIdempotencyKey

            stmt = select(FinIdempotencyKey).where(
                FinIdempotencyKey.key == idempotency_key,
                FinIdempotencyKey.user_id == user_id
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                if existing.request_hash != hashlib.sha256(await request.body()).hexdigest():
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
            from datetime import datetime, timedelta, UTC
            new_key = FinIdempotencyKey(
                user_id=getattr(request.state, "user_id", "anonymous"),
                key=idempotency_key,
                route=str(request.url.path),
                request_hash=hashlib.sha256(await request.body()).hexdigest(),
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
            # We would store the response here in a real implementation
            # For now, just update the idempotency key status
            async with hub.get_async_session() as db:
                from sqlalchemy import select
                from database.models import FinIdempotencyKey

                stmt = select(FinIdempotencyKey).where(
                    FinIdempotencyKey.key == request.headers.get("Idempotency-Key"),
                    FinIdempotencyKey.user_id == getattr(request.state, "user_id", "anonymous")
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.status = "completed"
                    existing.response_code = response.status_code
                    # Note: response body caching would go here
                    await db.commit()

        return response