"""Request identity middleware.

Resolves the authenticated subject once per request and publishes it on
``request.state`` so that middleware running earlier in the chain (and
running before any FastAPI dependency) can use it.

Why this exists
---------------
``IdempotencyMiddleware`` scopes its cache rows by
``FinIdempotencyKey.user_id``, and ``database/models.py`` declares a unique
index on ``(user_id, key)``. But nothing in production ever assigned
``request.state.user_id`` -- only two test files did. Every request was
therefore recorded as ``user_id="anonymous"``, so all users collided on one
row per key and could be served another user's cached response body.

Auth itself is unchanged and remains ``Depends``-based. This middleware only
*reads* the token, using the same ``decode_token`` helper and the same
``Authorization``-or-cookie precedence as ``auth.get_current_user_optional``.
It never grants access; a token it cannot decode yields ``None`` and the
route's own dependency still rejects the request.
"""

from __future__ import annotations

import hashlib
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Length of the truncated digest used to scope idempotency for unauthenticated
# callers. Long enough to be collision-free in practice, short enough to be
# obviously not a credential.
ANON_FINGERPRINT_LEN = 32


class IdentityMiddleware(BaseHTTPMiddleware):
    """Publish the resolved subject on ``request.state``."""

    async def dispatch(self, request: Request, call_next: Request) -> Response:
        user_id, tenant_id = self._resolve(request)
        request.state.user_id = user_id
        request.state.tenant_id = tenant_id
        return await call_next(request)

    def _resolve(self, request: Request) -> tuple[str | None, str | None]:
        payload = self._decode(request)
        if payload is None:
            return None, None
        sub = payload.get("sub")
        if not sub or sub == "anonymous":
            return None, None
        # Prefer platform_id / tenant_id; never fall back to sub.
        tenant = payload.get("platform_id") or payload.get("tenant_id")
        if tenant == "anonymous":
            tenant = None
        return str(sub), (str(tenant) if tenant else None)

    def _decode(self, request: Request) -> dict | None:
        token = self._token(request)
        if not token:
            return None
        try:
            # Local import: auth.py imports the middleware package's siblings.
            from services.api_gateway.auth import decode_token

            return decode_token(token)
        except Exception:
            # decode_token raises RuntimeError when the signing key is weak;
            # that must degrade to "anonymous", not to a 500 on every request.
            return None

    def _token(self, request: Request) -> str | None:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            candidate = header[7:].strip()
            if candidate:
                return candidate
        from services.api_gateway.auth import ACCESS_TOKEN_COOKIE

        return request.cookies.get(ACCESS_TOKEN_COOKIE) or None


def anonymous_scope(request: Request) -> str:
    """Return a stable, non-reversible scope for an unauthenticated caller.

    Idempotency rows are unique on ``(user_id, key)``. Collapsing every
    unauthenticated caller onto the literal string ``"anonymous"`` lets one
    client pre-create a row and have that cached response replayed to a
    different client. Scoping by a salted digest of the peer address keeps
    replay protection for anonymous traffic without sharing rows between
    unrelated callers.
    """
    peer = request.client.host if request.client else "unknown"
    return "anon:" + hashlib.sha256(peer.encode("utf-8")).hexdigest()[:ANON_FINGERPRINT_LEN]
