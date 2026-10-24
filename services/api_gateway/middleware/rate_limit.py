"""In-process token-bucket rate limiting for authentication-sensitive routes.

The gateway already carries a per-IP sliding-window limiter for the whole API
(``services.api_gateway.security.RateLimitMiddleware``). This layer adds the
brute-force ceiling the credential endpoints need: a bucket per client IP and
route, spent one token per request and refilled at ``max_requests`` per
``window_seconds``. It touches nothing else — every other path passes through
untouched, and the whole layer is inert when disabled.

Configuration (environment, read once at construction):

* ``HYDROMA_AUTH_RATE_LIMIT_ENABLED`` — ``false``/``0``/``no``/``off`` disables
  the layer (test escape hatch; the suite must never enable it by accident);
* ``HYDROMA_AUTH_RATE_LIMIT_MAX_REQUESTS`` — tokens per window per IP+route;
* ``HYDROMA_AUTH_RATE_LIMIT_WINDOW_SECONDS`` — refill window length.

No third-party dependency: the bucket state is a plain ``dict`` in this
process, bounded by an idle sweep so a rotating-identity flood cannot grow it
without limit. The client key is the ASGI peer address — ``X-Forwarded-For``
is deliberately ignored because, without a trusted-proxy chain, it is
caller-controlled and would hand every request a fresh identity.
"""

from __future__ import annotations

import math
import os
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

#: Credential endpoints an attacker would brute-force. ``/token`` is listed
#: defensively: the router declares login/register/refresh today, and a future
#: token endpoint inherits the ceiling instead of being silently unlimited.
DEFAULT_PROTECTED_PATHS = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",
        "/api/v1/auth/register",
    }
)

#: Generous for a human (a real client logs in a handful of times a day) and
#: tight for a credential-stuffing run.
DEFAULT_MAX_REQUESTS = 60
DEFAULT_WINDOW_SECONDS = 60

#: Hard cap on tracked buckets; idle entries are swept before it is reached.
MAX_TRACKED_BUCKETS = 8192

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in _TRUTHY


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


class _TokenBucket:
    """One refillable bucket; tokens are refilled lazily on each spend."""

    __slots__ = ("tokens", "updated_at")

    def __init__(self, tokens: float, now: float) -> None:
        self.tokens = tokens
        self.updated_at = now


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """429 the authentication routes once a client exhausts its bucket.

    Only ``POST`` is counted: an ``OPTIONS`` preflight for a cross-origin
    JSON login is not a credential attempt, and charging preflights would
    let a page drain a victim's budget before the real request is sent.
    """

    def __init__(
        self,
        app: Any,
        *,
        max_requests: int | None = None,
        window_seconds: int | None = None,
        enabled: bool | None = None,
        paths: frozenset[str] | None = None,
    ) -> None:
        super().__init__(app)
        if enabled is None:
            enabled = _env_flag("HYDROMA_AUTH_RATE_LIMIT_ENABLED", True)
        if max_requests is None:
            max_requests = _env_int(
                "HYDROMA_AUTH_RATE_LIMIT_MAX_REQUESTS", DEFAULT_MAX_REQUESTS
            )
        if window_seconds is None:
            window_seconds = _env_int(
                "HYDROMA_AUTH_RATE_LIMIT_WINDOW_SECONDS", DEFAULT_WINDOW_SECONDS
            )
        self.enabled = bool(enabled)
        self.max_requests = int(max_requests)
        self.window_seconds = int(window_seconds)
        self.protected_paths = frozenset(paths) if paths is not None else DEFAULT_PROTECTED_PATHS
        self._refill_per_second = self.max_requests / float(self.window_seconds)
        self._buckets: dict[str, _TokenBucket] = {}
        #: Clock seam: tests advance a fake clock instead of sleeping.
        self._now = time.monotonic

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled or request.method.upper() != "POST":
            return await call_next(request)
        if request.url.path not in self.protected_paths:
            return await call_next(request)

        allowed, retry_after = self._take(self._bucket_key(request))
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many authentication attempts. Retry later."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)

    def _bucket_key(self, request: Request) -> str:
        """Client IP + route. The route is part of the key so exhausting one
        endpoint (say ``/login``) cannot lock a caller out of another."""
        client_host = request.client.host if request.client else "unknown"
        return f"{client_host}|{request.url.path}"

    def _take(self, key: str) -> tuple[bool, int]:
        """Spend one token; return (allowed, Retry-After seconds)."""
        now = self._now()
        bucket = self._buckets.get(key)
        if bucket is None:
            if len(self._buckets) >= MAX_TRACKED_BUCKETS and not self._sweep(now):
                # Every tracked bucket is live. Refuse the new identity rather
                # than evicting a live counter or growing the map without
                # bound: a flood gets a 429, a real client retries shortly.
                return False, max(1, self.window_seconds)
            bucket = _TokenBucket(float(self.max_requests), now)
            self._buckets[key] = bucket
        else:
            elapsed = now - bucket.updated_at
            if elapsed > 0:
                bucket.tokens = min(
                    float(self.max_requests),
                    bucket.tokens + elapsed * self._refill_per_second,
                )
                bucket.updated_at = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True, 0
        retry_after = max(1, math.ceil((1.0 - bucket.tokens) / self._refill_per_second))
        return False, retry_after

    def _sweep(self, now: float) -> int:
        """Drop buckets idle for two windows; return how many were removed."""
        idle_before = now - 2 * self.window_seconds
        idle = [k for k, bucket in self._buckets.items() if bucket.updated_at < idle_before]
        for key in idle:
            del self._buckets[key]
        return len(idle)


__all__ = [
    "AuthRateLimitMiddleware",
    "DEFAULT_MAX_REQUESTS",
    "DEFAULT_PROTECTED_PATHS",
    "DEFAULT_WINDOW_SECONDS",
]
