from __future__ import annotations

"""Security middlewares for the Eco Nojin API gateway.

Provides:
- HTTPSRedirectMiddleware: redirect HTTP to HTTPS (opt-in)
- RateLimitMiddleware: sliding-window per-IP rate limit (Redis/in-memory)
- SecurityHeadersMiddleware: hardened response headers
- RequestIDMiddleware: propagate/assign X-Request-ID + correlation context
"""

import contextlib
import hmac
import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any, ClassVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from services.api_gateway.observability.structured_logger import (
    set_correlation_id,
)

logger = structlog.get_logger("econojin.security")


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._required = _flag("ECONOJIN_REQUIRE_HTTPS")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._required and request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(str(url), status_code=308)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
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
        self.trusted_proxies = trusted_proxies or []
        self._trusted_proxy_networks = []
        if self.trusted_proxies:
            import ipaddress

            for proxy in self.trusted_proxies:
                with contextlib.suppress(ValueError):
                    self._trusted_proxy_networks.append(ipaddress.ip_network(proxy, strict=False))

    def _client_key(self, request: Request) -> str:
        client_host = request.client.host if request.client else "unknown"
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
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                forwarded_ip = fwd.split(",")[0].strip()
                try:
                    ipaddress.ip_address(forwarded_ip)
                    return forwarded_ip
                except ValueError:
                    pass
        return client_host

    def _check_redis(self, key: str) -> tuple[bool, int, int]:
        assert self.redis is not None
        now = time.time()
        window_start = now - self.window_seconds
        key_name = f"ratelimit:{key}"
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key_name, 0, window_start)
        pipe.zcard(key_name)
        pipe.zadd(key_name, {str(time.time()): time.time()})
        pipe.expire(key_name, self.window_seconds + 1)
        results = pipe.execute()
        current_count = results[1]
        allowed = current_count < self.limit
        remaining = max(0, self.limit - current_count - (1 if allowed else 0))
        reset_time = int(now + self.window_seconds)
        return allowed, remaining, reset_time

    def _check_memory(self, key: str) -> tuple[bool, int, int]:
        now = time.time()
        window_start = now - self.window_seconds
        window = self._hits[key]
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
        except Exception:
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
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    HEADERS: ClassVar[dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for name, value in self.HEADERS.items():
            response.headers.setdefault(name, value)
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_correlation_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class APIKeyGuardMiddleware(BaseHTTPMiddleware):
    """Middleware that validates X-API-Key for telco webhook endpoints."""

    PROTECTED_PREFIXES = ("/api/v1/ussd", "/api/v1/voice", "/api/v1/sms")

    def __init__(self, app: Any, api_key: str | None = None) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._api_key and any(request.url.path.startswith(p) for p in self.PROTECTED_PREFIXES):
            provided = request.headers.get("X-API-Key")
            if not provided or not hmac.compare_digest(provided, self._api_key):
                return Response(
                    content='{"detail": "Invalid API key"}',
                    status_code=401,
                    media_type="application/json",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        return await call_next(request)


__all__ = [
    "APIKeyGuardMiddleware",
    "HTTPSRedirectMiddleware",
    "RateLimitMiddleware",
    "RequestIDMiddleware",
    "SecurityHeadersMiddleware",
]
