"""CSRF protection middleware for state-changing requests."""
from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
CSRF_HEADER = "x-csrf-token"
CSRF_COOKIE = "econojin_csrf"
EXEMPT_PREFIXES = ("/api/v1/auth", "/api/v1/newsletter", "/api/v1/pilot", "/dashboard")


class CSRFMiddleware(BaseHTTPMiddleware):
    """Enforce CSRF token on unsafe methods when cookie-based session is used.

    Bearer-only APIs are exempt. This middleware is a no-op for pure JWT
    clients, but protects any future cookie-session endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        csrf_token = request.headers.get(CSRF_HEADER)
        cookie_token = request.cookies.get(CSRF_COOKIE)
        if not csrf_token or not cookie_token or csrf_token != cookie_token:
            logger.warning("CSRF check failed: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )
        return await call_next(request)
