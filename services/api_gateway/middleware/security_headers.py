"""Security response headers middleware (ASVS-lite hardening).

Mounted on the gateway beside the other request-path layers. Every response
carries the same small header set so a route cannot forget one:

* ``X-Content-Type-Options: nosniff`` — no MIME sniffing of responses;
* ``X-Frame-Options: DENY`` — no framing (clickjacking);
* ``Referrer-Policy: strict-origin-when-cross-origin`` — no full-URL referrer
  leaks to third parties;
* ``Permissions-Policy`` — deny the browser features this API never uses;
* ``Strict-Transport-Security`` — sent **only** when the request reached the
  app over HTTPS (directly, or through a proxy that reported the original
  protocol via ``X-Forwarded-Proto``). HSTS on a plaintext response is
  ignored by every browser, so a stale value from an inner layer is removed
  rather than echoed.

The **Content-Security-Policy is deliberately not declared here.** Starlette
makes the later-added middleware the outermost one, and both this layer and
``services.api_gateway.security.SecurityHeadersMiddleware`` used ``setdefault``
— so whichever ran last won, and this layer's policy was dead configuration
that ``/api/v1/security/status`` still reported as enforced (2026-10-12 review
finding 8). One layer now owns the CSP — the deny-all policy with the
docs-scoped exception in ``services.api_gateway.security`` — and the status
endpoint reports that layer.
"""

from __future__ import annotations

from typing import ClassVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

#: Header a TLS-terminating reverse proxy uses to report the original scheme.
FORWARDED_PROTO_HEADER = "X-Forwarded-Proto"

HSTS_POLICY = "max-age=31536000; includeSubDomains"

HSTS_HEADER = "Strict-Transport-Security"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach the hardened header set to every response.

    ``setdefault`` is used for the shared headers so a route (or the inner
    ``services.api_gateway.security`` layer, which owns the CSP) that sets its
    own value is not overridden.
    """

    #: Read by ``/api/v1/security/status`` to report the enforced headers
    #: honestly. The CSP is **not** part of this map — see the module docstring.
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

        if self._is_https(request):
            response.headers.setdefault(HSTS_HEADER, HSTS_POLICY)
        else:
            # A plaintext response must not carry HSTS: the header is only
            # honoured on secure transport, and an inner layer may already
            # have set it unconditionally.
            del response.headers[HSTS_HEADER]
        return response

    @staticmethod
    def _is_https(request: Request) -> bool:
        """Whether this request travelled over HTTPS.

        The ASGI scope scheme is the primary signal. Behind a TLS-terminating
        proxy the scope stays ``http`` and the proxy reports the original
        protocol in ``X-Forwarded-Proto``; honouring it only adds an HSTS
        header, which a browser ignores on plaintext anyway.
        """
        if request.url.scheme == "https":
            return True
        forwarded = request.headers.get(FORWARDED_PROTO_HEADER, "")
        return forwarded.split(",")[0].strip().lower() == "https"


__all__ = ["HSTS_POLICY", "SecurityHeadersMiddleware"]
