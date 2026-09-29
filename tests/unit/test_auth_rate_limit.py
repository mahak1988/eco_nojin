"""Regression tests for the auth endpoint rate limiters.

Two independent bugs disabled the limit on ``POST /api/v1/auth/register`` and
``POST /api/v1/auth/forgot-password``:

1. ``routers/auth.py`` reassigned ``_register_limiter.DEFAULT_LIMIT = 5`` after
   construction. The constructor reads the class attribute and copies it to
   ``self.limit``, so the reassignment only created a shadowing instance
   attribute and the effective limit stayed at the 240/min global default.
2. ``_check_memory`` returns a 3-tuple ``(allowed, remaining, reset_time)``. The
   caller assigned it to ``allowed`` and then tested ``if not allowed``; a
   non-empty tuple is always truthy, so the 429 was never raised.
"""

from __future__ import annotations

import pytest
from starlette.requests import Request

from services.api_gateway.routers import auth as auth_router
from services.api_gateway.security import RateLimitMiddleware


def _request(ip: str = "203.0.113.9") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/register",
        "headers": [(b"host", b"test")],
        "client": (ip, 5000),
    }
    return Request(scope)


def test_constructor_limit_override_is_honoured():
    """Passing limit= must change the effective limit."""
    limiter = RateLimitMiddleware(None, redis_client=None, limit=5, window=60)

    assert limiter.limit == 5
    assert limiter.window_seconds == 60


def test_reassigning_class_attribute_after_construction_does_not_apply():
    """Documents the shadowing trap that made the original limit a no-op."""
    limiter = RateLimitMiddleware(None, redis_client=None)
    limiter.DEFAULT_LIMIT = 5

    assert limiter.limit == RateLimitMiddleware.DEFAULT_LIMIT
    assert limiter.limit != 5


def test_auth_limiters_have_the_intended_limits():
    """The module-level limiters must carry 5/min and 3/min."""
    assert auth_router._register_limiter.limit == 5
    assert auth_router._forgot_limiter.limit == 3


def test_is_allowed_blocks_after_the_limit():
    """The 6th request inside the window must be refused."""
    limiter = RateLimitMiddleware(None, redis_client=None, limit=5, window=60)
    request = _request()

    results = [limiter.is_allowed(request)[0] for _ in range(7)]

    assert results[:5] == [True] * 5
    assert results[5] is False
    assert results[6] is False


def test_is_allowed_returns_a_real_bool_not_a_tuple():
    """Regression guard: a non-empty tuple is always truthy."""
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60)
    request = _request()

    first = limiter.is_allowed(request)
    second = limiter.is_allowed(request)

    assert isinstance(first[0], bool)
    assert isinstance(second[0], bool)
    assert first[0] is True
    assert second[0] is False
    assert bool(second) is True  # the tuple itself, but the element is False


def test_limiters_are_isolated_per_client():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60)

    assert limiter.is_allowed(_request("198.51.100.1"))[0] is True
    assert limiter.is_allowed(_request("198.51.100.2"))[0] is True
    assert limiter.is_allowed(_request("198.51.100.1"))[0] is False


@pytest.mark.asyncio
async def test_register_rate_limit_raises_after_five_attempts():
    """The dependency must raise HTTPException(429) once the limit is hit."""
    from fastapi import HTTPException

    auth_router._register_limiter._hits.clear()
    request = _request()

    for _ in range(5):
        await auth_router._check_register_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        await auth_router._check_register_rate_limit(request)

    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


@pytest.mark.asyncio
async def test_forgot_rate_limit_raises_after_three_attempts():
    from fastapi import HTTPException

    auth_router._forgot_limiter._hits.clear()
    request = _request()

    for _ in range(3):
        await auth_router._check_forgot_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        await auth_router._check_forgot_rate_limit(request)

    assert exc.value.status_code == 429
