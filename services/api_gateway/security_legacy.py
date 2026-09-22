from __future__ import annotations

"""Security middlewares for the Eco Nojin API gateway (plan v2.0, phase 0).

Provides the four middlewares referenced by ``main.py``:

- ``HTTPSRedirectMiddleware``  — redirects HTTP to HTTPS **only** when the
  ``ECONOJIN_REQUIRE_HTTPS`` flag is enabled, so local HTTP development and
  test runs are not broken.
- ``RateLimitMiddleware``      — fixed/sliding-window rate limiting per client IP;
  uses Redis when a client is injected, otherwise falls back to an
  in-process window (single-worker deployments / tests).
  Supports trusted proxy configuration for X-Forwarded-For header.
- ``SecurityHeadersMiddleware`` — adds hardened response headers.
- ``RequestIDMiddleware``      — propagates/assigns ``X-Request-ID``.
"""

import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any, ClassVar

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
    """Sliding-window per-IP rate limiter with Redis or in-memory backend.

    Features:
    - Trusted proxy support: only trusts X-Forwarded-For from configured proxy IPs
    - Redis backend with connection pooling for multi-worker deployments
    - In-memory fallback for single-worker/test deployments
    - Sliding window algorithm for more accurate limiting
    - Rate limit headers in responses (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
    - Graceful fallback to in-memory on Redis failure
    """

    DEFAULT_LIMIT = int(os.getenv("ECONOJIN_RATELIMIT_PER_MINUTE", "240"))
    WINDOW_SECONDS = 60

    def __init__(
        self,
        app: Any,
        redis_client: Any = None,
        limit: int | None = None,
        window: int | None = None,
        enabled: bool = True,
        trusted_proxies: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.redis = redis_client
        self.enabled = enabled
        self.limit = int(limit) if limit is not None else self.DEFAULT_LIMIT
        self.window_seconds = int(window) if window is not None else self.WINDOW_SECONDS
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        # Trusted proxy IPs (CIDR notation supported via ipaddress module)
        self.trusted_proxies = trusted_proxies or []
        self._trusted_proxy_networks = []
        if self.trusted_proxies:
            import ipaddress

            for proxy in self.trusted_proxies:
                try:
                    self._trusted_proxy_networks.append(ipaddress.ip_network(proxy, strict=False))
                except ValueError:
                    pass

    def _client_key(self, request: Request) -> str:
        """Extract client IP with trusted proxy validation."""
        # Check if request comes from a trusted proxy
        client_host = request.client.host if request.client else "unknown"

        # Check if the immediate client is a trusted proxy
        is_trusted = False
        if self._trusted_proxy_networks:
            import ipaddress

            try:
                client_ip = ipaddress.ip_address(client_host)
                for network in self._trusted_proxy_networks:
                    if client_ip in network:
                        is_trusted = True
                        break
            except ValueError:
                pass

        if is_trusted:
            # Trust X-Forwarded-For from trusted proxy
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                # Take the first IP in the chain (original client)
                forwarded_ip = fwd.split(",")[0].strip()
                # Validate it's a valid IP
                import ipaddress

                try:
                    ipaddress.ip_address(forwarded_ip)
                    return forwarded_ip
                except ValueError:
                    pass

        # Fall back to direct client IP
        return client_host

    def _check_redis(self, key: str) -> tuple[bool, int, int]:
        """Check rate limit using Redis sliding window.

        Returns: (allowed, remaining, reset_time)
        """
        assert self.redis is not None
        now = time.time()
        window_start = now - self.window_seconds

        # Use a sorted set with timestamps as scores for sliding window
        key_name = f"ratelimit:{key}"

        pipe = self.redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key_name, 0, window_start)
        # Count current requests
        pipe.zcard(key_name)
        # Add current request
        pipe.zadd(key_name, {str(time.time()): time.time()})
        # Set expiry
        pipe.expire(key_name, self.window_seconds + 1)
        results = pipe.execute()

        current_count = results[1]
        allowed = current_count < self.limit
        remaining = max(0, self.limit - current_count - (1 if allowed else 0))
        reset_time = int(now + self.window_seconds)

        return allowed, remaining, reset_time

    def _check_memory(self, key: str) -> tuple[bool, int, int]:
        """Check rate limit using in-memory sliding window."""
        now = time.time()
        window_start = now - self.window_seconds
        window = self._hits[key]

        # Remove expired entries
        while window and window[0] < window_start:
            window.popleft()

        current_count = len(window)
        allowed = current_count < self.limit
        remaining = max(0, self.limit - current_count - (1 if allowed else 0))
        reset_time = int(now + self.window_seconds)

        if allowed:
            window.append(now)

        return allowed, remaining, reset_time

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        key = self._client_key(request)
        try:
            if self.redis is not None:
                allowed, remaining, reset_time = self._check_redis(key)
            else:
                allowed, remaining, reset_time = self._check_memory(key)
        except Exception:  # Redis outage must never take the API down
            allowed, remaining, reset_time = self._check_memory(key)

        if not allowed:
            retry_after = max(1, self.window_seconds)
            return Response(
                content='{"detail": "rate limit exceeded", "retry_after_seconds": %d}'
                % retry_after,
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.window_seconds)),
                },
            )

        response = await call_next(request)
        # Add rate limit headers to all responses
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardened security headers to every response."""

    HEADERS: ClassVar[dict[str, str]] = {
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
    "RequestIDMiddleware",
    "SecurityHeadersMiddleware",
]
