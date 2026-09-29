"""Tenant isolation middleware for FastAPI.

Publishes ``request.state.tenant_id`` for downstream use.

The subject and tenant are resolved exactly once per request by
``IdentityMiddleware``, which sits outside this middleware. Decoding the JWT a
second time here would both duplicate work and risk the two middlewares
disagreeing about the tenant (this one used to read the ``Authorization``
header only, so cookie-authenticated requests got no tenant at all).
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that exposes tenant context to requests."""

    async def dispatch(self, request: Request, call_next):
        tenant_id = self._tenant_id(request)
        request.state.tenant_id = tenant_id

        if tenant_id:
            logger.debug(
                "Tenant context: %s for %s %s", tenant_id, request.method, request.url.path
            )

        response: Response = await call_next(request)
        # Do not echo tenant ID in response headers (security)
        return response

    def _tenant_id(self, request: Request) -> str | None:
        """Return the tenant resolved by ``IdentityMiddleware``.

        Returns ``None`` when the middleware is mounted standalone (for
        example in a test app) rather than trusting a client-supplied header.
        """
        tenant = getattr(request.state, "tenant_id", None)
        return str(tenant) if tenant else None
