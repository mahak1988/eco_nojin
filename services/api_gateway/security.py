"""Security middleware for the API gateway (Phase 0).

- ``RateLimitMiddleware``: in-memory token bucket per client IP
  (sufficient for a single-process research deployment; multi-worker
  deployments must move to Redis).
- ``SecurityHeadersMiddleware``: hardening headers + HSTS in production.
- ``RequestIDMiddleware``: traceable request ids.
"""

import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from engine.hydroma.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter keyed by client IP.

    Overridable per-instance for tests via constructor kwargs.
    In-memory only — documented limitation for single-process mode.
    """

    def __init__(
        self,
        app,
        limit: int | None = None,
        window: int | None = None,
        enabled: bool | None = None,
    ):
        super().__init__(app)
        settings = get_settings()
        self._window = window if window is not None else settings.rate_limit_window_seconds
        self._limit = limit if limit is not None else settings.rate_limit_requests
        self._enabled = enabled if enabled is not None else settings.rate_limit_enabled
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not self._enabled:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        cutoff = now - self._window

        q = self._hits[client]
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= self._limit:
            retry_after = int(self._window - (now - q[0])) + 1 if q else self._window
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again shortly.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        q.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Hardening response headers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=()"
        if getattr(get_settings(), "is_production", False):
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request id for tracing (echoed if provided)."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
