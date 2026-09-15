"""Tenant isolation middleware for FastAPI.

Extracts tenant/platform ID from:
1. JWT token claims (preferred)
2. X-Tenant-Id header (for API key auth)

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
            logger.debug("Tenant context: %s for %s %s", tenant_id, request.method, request.url.path)

        response: Response = await call_next(request)
        # Add tenant context header for debugging (dev only)
        if tenant_id:
            response.headers.setdefault("X-Tenant-Id", tenant_id)
        return response

    def _extract_tenant_id(self, request: Request) -> str | None:
        """Extract tenant ID from request."""
        # 1. Check header first (API key auth)
        header_tenant = request.headers.get("X-Tenant-Id") or request.headers.get("X-Platform-Id")
        if header_tenant:
            return header_tenant.strip() or None

        # 2. Check JWT token (if Authorization header present)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            try:
                import jwt as jwt_lib
                from engine.hydroma.config.settings import get_settings
                settings = get_settings()
                payload = jwt_lib.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
                tenant = payload.get("platform_id") or payload.get("tenant_id") or payload.get("sub")
                return tenant if tenant != "anonymous" else None
            except Exception:
                pass

        return None
