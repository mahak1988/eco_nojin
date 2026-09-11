"""Security middleware for the API gateway (Phase 0).

- ``RateLimitMiddleware``: Redis-backed rate limiter per client IP
  with in-memory fallback for single-process deployments.
- ``SecurityHeadersMiddleware``: hardening headers + HSTS in production.
- ``RequestIDMiddleware``: traceable request ids.
- ``HTTPSRedirectMiddleware``: redirect HTTP to HTTPS in production.
"""

import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from engine.hydroma.config.settings import get_settings
from services.security.redis_rate_limit import RedisRateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiter keyed by client IP.

    Falls back to in-memory when Redis is unavailable.
    """

    def __init__(
        self,
        app,
        limit: int | None = None,
        window: int | None = None,
        enabled: bool | None = None,
        redis_client=None,
    ):
        super().__init__(app)
        settings = get_settings()
        self._window = window if window is not None else settings.rate_limit_window_seconds
        self._limit = limit if limit is not None else settings.rate_limit_requests
        self._enabled = enabled if enabled is not None else settings.rate_limit_enabled
        self._limiter = RedisRateLimiter(redis_client=redis_client)

    async def dispatch(self, request: Request, call_next):
        if not self._enabled:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        ok, retry_after = self._limiter.check(client, request.url.path)
        if not ok:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again shortly.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
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


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if getattr(settings, "is_production", False) and request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)
        return await call_next(request)
