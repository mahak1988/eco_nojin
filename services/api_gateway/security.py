"""Security middlewares for the Eco Nojin API gateway (plan v2.0, phase 0).

Provides the four middlewares referenced by ``main.py``:

- ``HTTPSRedirectMiddleware``  — redirects HTTP to HTTPS **only** when the
  ``ECONOJIN_REQUIRE_HTTPS`` flag is enabled, so local HTTP development and
  test runs are not broken.
- ``RateLimitMiddleware``      — fixed-window rate limiting per client IP;
  uses Redis when a client is injected, otherwise falls back to an
  in-process window (single-worker deployments / tests).
- ``SecurityHeadersMiddleware`` — adds hardened response headers.
- ``RequestIDMiddleware``      — propagates/assigns ``X-Request-ID``.
"""
from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect plain-HTTP requests to HTTPS when explicitly required.

    The redirect is opt-in via ``ECONOJIN_REQUIRE_HTTPS`` so that local
    development (uvicorn on http://localhost) and the automated browser
    tests keep working; production deployments set the flag.
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._required = _flag("ECONOJIN_REQUIRE_HTTPS")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._required and request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(str(url), status_code=308)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-IP rate limiter with Redis or in-memory backend."""

    DEFAULT_LIMIT = int(os.getenv("ECONOJIN_RATELIMIT_PER_MINUTE", "240"))
    WINDOW_SECONDS = 60

    def __init__(self, app: Any, redis_client: Any = None) -> None:
        super().__init__(app)
        self.redis = redis_client
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _check_redis(self, key: str) -> bool:
        assert self.redis is not None
        bucket = f"ratelimit:{key}:{int(time.time() // self.WINDOW_SECONDS)}"
        count = self.redis.incr(bucket)
        if count == 1:
            self.redis.expire(bucket, self.WINDOW_SECONDS)
        return int(count) <= self.DEFAULT_LIMIT

    def _check_memory(self, key: str) -> bool:
        now = time.time()
        window = self._hits[key]
        while window and now - window[0] > self.WINDOW_SECONDS:
            window.popleft()
        if len(window) >= self.DEFAULT_LIMIT:
            return False
        window.append(now)
        return True

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        key = self._client_key(request)
        try:
            allowed = self._check_redis(key) if self.redis is not None else self._check_memory(key)
        except Exception:  # Redis outage must never take the API down
            allowed = self._check_memory(key)
        if not allowed:
            return Response(
                content='{"detail": "rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.WINDOW_SECONDS)},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardened security headers to every response."""

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for name, value in self.HEADERS.items():
            response.headers.setdefault(name, value)
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign or propagate ``X-Request-ID`` for tracing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


__all__ = [
    "HTTPSRedirectMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "RequestIDMiddleware",
]
