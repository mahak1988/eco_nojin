"""Tenant isolation middleware for FastAPI.

Extracts tenant/platform ID from JWT token claims only.
Sets request.state.tenant_id for downstream use.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts tenant context from requests."""

    async def dispatch(self, request: Request, call_next):
        tenant_id = self._extract_tenant_id(request)
        request.state.tenant_id = tenant_id

        if tenant_id:
            logger.debug(
                "Tenant context: %s for %s %s", tenant_id, request.method, request.url.path
            )

        response: Response = await call_next(request)
        # Do not echo tenant ID in response headers (security)
        return response

    def _extract_tenant_id(self, request: Request) -> str | None:
        """Extract tenant ID from JWT token only."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:].strip()
        try:
            # Import locally to avoid circular imports
            from services.api_gateway.auth import decode_token

            payload = decode_token(token)
            if payload is None:
                return None
            # Prefer platform_id or tenant_id claim; do not fall back to sub
            tenant = payload.get("platform_id") or payload.get("tenant_id")
            return tenant if tenant and tenant != "anonymous" else None
        except Exception:
            return None
