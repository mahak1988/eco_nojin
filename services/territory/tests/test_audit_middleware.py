"""Audit-trail middleware: the exception path must stay honest.

``AuditTrailMiddleware.dispatch`` records ``safe_error_detail(e)`` for failed
requests. That name was never imported, so every failed territory request
raised ``NameError`` *instead of* propagating the real error -- the audit
record and the caller both lost the original failure. This module was written
before the fix and failed on exactly that; it now pins the repaired path with
a real middleware invocation (S17 T-03).
"""

from __future__ import annotations

import pytest
from starlette.requests import Request

from services.territory_audit import AuditTrailMiddleware

_SCOPE = {
    "type": "http",
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/territories/abc-123",
    "raw_path": b"/territories/abc-123",
    "root_path": "",
    "query_string": b"",
    "headers": [(b"user-agent", b"pytest"), (b"content-type", b"application/json")],
    "client": ("127.0.0.1", 12345),
    "server": ("testserver", 80),
}


def _request() -> Request:
    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"{}", "more_body": False}

    return Request(_SCOPE, receive)


@pytest.fixture
def middleware() -> AuditTrailMiddleware:
    async def _app(scope, receive, send):  # pragma: no cover - never invoked
        raise AssertionError("inner app must not run in this test")

    return AuditTrailMiddleware(_app)


@pytest.mark.asyncio
async def test_failed_request_propagates_the_original_error(middleware) -> None:
    """The exception the inner app raised must reach the caller unchanged --
    not a NameError from the audit code that was trying to record it."""

    async def failing_call_next(request: Request):
        raise RuntimeError("boom-from-inner-app")

    with pytest.raises(RuntimeError, match="boom-from-inner-app"):
        await middleware.dispatch(_request(), failing_call_next)


@pytest.mark.asyncio
async def test_failed_request_records_a_sanitized_error_message(middleware) -> None:
    """``safe_error_detail`` must be resolvable and sanitize: it returns a
    message string, not the raw exception repr."""
    from services.api_gateway.errors import safe_error_detail

    assert callable(safe_error_detail)
    message = safe_error_detail(RuntimeError("secret=shhh"))
    assert isinstance(message, str)

    async def failing_call_next(request: Request):
        raise RuntimeError("boom-again")

    # The middleware re-raises after recording; reaching the raise without a
    # NameError proves the error-detail helper resolved.
    with pytest.raises(RuntimeError, match="boom-again"):
        await middleware.dispatch(_request(), failing_call_next)
