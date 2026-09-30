"""Tests for the rate-limit bucket keying.

``RateLimitMiddleware`` keyed purely on the client IP, so every user behind one
NAT or corporate proxy shared a single bucket: five registrations from one office
would return 429 to everyone else on that egress address. The bucket now appends
the authenticated subject when the middleware is configured for it, while the
default stays IP-only so a deployment that does not populate ``request.state``
keeps its previous behaviour.
"""

from __future__ import annotations

from starlette.requests import Request

from services.api_gateway.security import RateLimitMiddleware


def _request(ip: str = "203.0.113.7") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "headers": [(b"host", b"test")],
            "client": (ip, 5000),
        }
    )


def test_default_is_ip_only():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60)
    request = _request()

    assert limiter._bucket(request) == "203.0.113.7"


def test_subject_is_appended_when_enabled():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60, key_by_subject=True)
    request = _request()
    request.state.user_id = "user-a"

    assert limiter._bucket(request) == "203.0.113.7:user-a"


def test_tenant_id_is_used_when_user_id_absent():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60, key_by_subject=True)
    request = _request()
    request.state.tenant_id = "t-9"

    assert limiter._bucket(request) == "203.0.113.7:t-9"


def test_missing_subject_falls_back_to_ip():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60, key_by_subject=True)

    assert limiter._bucket(_request()) == "203.0.113.7"


def test_two_users_behind_one_nat_get_separate_buckets():
    """The regression: one shared bucket per egress address locked out co-workers."""
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60, key_by_subject=True)
    shared_ip = "198.51.100.20"

    alice = _request(shared_ip)
    alice.state.user_id = "alice"
    bob = _request(shared_ip)
    bob.state.user_id = "bob"

    assert limiter.is_allowed(alice)[0] is True
    # Bob is refused only by the per-IP global middleware, not by Alice's spend.
    assert limiter._bucket(alice) != limiter._bucket(bob)


def test_same_user_behind_two_ips_still_separate():
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60, key_by_subject=True)
    first = _request("198.51.100.1")
    first.state.user_id = "alice"
    second = _request("198.51.100.2")
    second.state.user_id = "alice"

    assert limiter._bucket(first) != limiter._bucket(second)


def test_ip_only_mode_keeps_one_shared_bucket():
    """Documented default: the NAT problem persists until the flag is enabled."""
    limiter = RateLimitMiddleware(None, redis_client=None, limit=1, window=60)
    first = _request("198.51.100.30")
    first.state.user_id = "alice"
    second = _request("198.51.100.30")
    second.state.user_id = "bob"

    assert limiter._bucket(first) == limiter._bucket(second) == "198.51.100.30"
    assert limiter.is_allowed(first)[0] is True
    assert limiter.is_allowed(second)[0] is False
