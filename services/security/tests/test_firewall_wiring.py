"""P0 regression tests.

Covers the three fixes:
  1. the spider firewall (WAF / honeypot / anomaly) is really mounted
  2. the status handler reads the live middleware stack instead of hardcoding
  3. the rate limiter cannot be bypassed by rotating request paths
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.security.honeypot import honeypot
from services.security.middleware import SpiderFirewallMiddleware, _client_ip, _parse_networks
from services.security.rate_limit import RateLimiter
from services.security.waf import waf_engine


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def mounted_names(app) -> set[str]:
    """Mirror of the status handler's stack introspection."""
    names: set[str] = set()
    stack = getattr(app, "middleware_stack", None)
    for mw in getattr(stack, "middlewares", ()) or ():
        cls = getattr(mw, "cls", None)
        if cls is not None:
            names.add(cls.__name__)
    layer, guard = stack, 0
    while layer is not None and guard < 64:
        names.add(type(layer).__name__)
        layer = getattr(layer, "app", None)
        guard += 1
    return names


class FakePipeline:
    def __init__(self, store):
        self.store = store
        self.ops: list[tuple] = []

    def zadd(self, key, mapping):
        self.ops.append(("zadd", key, mapping))

    def zremrangebyscore(self, key, lo, hi):
        self.ops.append(("zrem", key, (lo, hi)))

    def zcard(self, key):
        self.ops.append(("zcard", key))

    def expire(self, key, ttl):
        self.ops.append(("expire", key, ttl))

    def execute(self):
        out = []
        for op, key, *rest in self.ops:
            z = self.store.setdefault(key, {})
            if op == "zadd":
                for member, score in rest[0].items():
                    z[member] = score
                out.append(1)
            elif op == "zrem":
                lo, hi = rest[0]
                for member in [m for m, s in z.items() if lo <= s <= hi]:
                    del z[member]
                out.append(1)
            elif op == "zcard":
                out.append(len(z))
            else:
                out.append(True)
        return out


class FakeRedis:
    def __init__(self):
        self.store: dict[str, dict] = {}

    def pipeline(self):
        return FakePipeline(self.store)


@pytest.fixture(scope="module")
def gateway():
    from services.api_gateway.main import app

    return app


@pytest.fixture(scope="module")
def gateway_client(gateway):
    # any request materialises the lazily-built middleware stack
    with TestClient(gateway, raise_server_exceptions=False) as c:
        c.get("/health")
        yield c


@pytest.fixture(autouse=True)
def _reset_state():
    waf_engine.events.clear()
    honeypot._blocked.clear()
    honeypot.hits.clear()
    return None


# --------------------------------------------------------------------------
# 1. the firewall is mounted
# --------------------------------------------------------------------------
def test_spider_firewall_is_actually_mounted(gateway_client, gateway):
    names = mounted_names(gateway)
    assert "SpiderFirewallMiddleware" in names, (
        "SpiderFirewallMiddleware is registered but absent from the app stack; "
        "WAF/honeypot/anomaly would inspect no traffic"
    )


def test_normal_request_is_marked_by_the_firewall(gateway_client):
    # /health is on the firewall's exempt list, so use a routed path
    r = gateway_client.get("/api/v1/land", headers={"User-Agent": "Mozilla/5.0"})
    assert r.headers.get("x-econojin-firewall") == "active", r.text


def test_honeypot_trap_is_answered_in_the_request_path(gateway_client):
    r = gateway_client.get("/.env")
    assert r.status_code == 404
    assert honeypot.hits, "honeypot recorded no hit: the layer is not in the path"


def test_honeypot_hit_blocks_the_caller(gateway_client):
    gateway_client.get("/wp-login.php")
    assert honeypot.hits


def test_waf_blocks_sqli_in_the_request_path(gateway_client):
    before = len(waf_engine.events)
    r = gateway_client.post(
        "/api/v1/security-probe",
        content="a' union select 1,2,3--",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 403, r.text
    assert len(waf_engine.events) > before, "WAF did not record a block"


def test_waf_blocks_scanner_user_agent(gateway_client):
    r = gateway_client.get("/api/v1/land", headers={"User-Agent": "sqlmap/1.7"})
    assert r.status_code == 403


# --------------------------------------------------------------------------
# 2. the status handler tells the truth
# --------------------------------------------------------------------------
def _status_app(with_firewall: bool) -> FastAPI:
    from services.api_gateway.routers import security_router

    app = FastAPI()
    if with_firewall:
        app.add_middleware(SpiderFirewallMiddleware, enable_rate_limit=False)
    app.include_router(security_router.router)
    return app


def test_status_reports_unmounted_layer_as_inactive():
    with TestClient(_status_app(with_firewall=False)) as c:
        layers = c.get("/api/v1/security/status").json()["layers"]
    assert layers["waf"]["active"] is False
    assert layers["waf"]["enforcement"] == "not_mounted"
    assert layers["honeypot"]["active"] is False
    assert layers["anomaly"]["active"] is False


def test_status_reports_mounted_layer_as_active():
    with TestClient(_status_app(with_firewall=True)) as c:
        layers = c.get("/api/v1/security/status").json()["layers"]
    assert layers["waf"]["active"] is True
    assert layers["waf"]["enforcement"] == "spider_firewall"
    assert layers["honeypot"]["active"] is True
    assert layers["anomaly"]["active"] is True


def test_status_does_not_hardcode_active_flags():
    with TestClient(_status_app(with_firewall=False)) as c:
        body = c.get("/api/v1/security/status").json()
    layers = body["layers"]
    # every layer that is not actually mounted must not claim to be active
    for name in ("waf", "honeypot", "anomaly", "circuit_breaker", "rbac_audit"):
        assert layers[name]["active"] is False, f"{name} falsely reports active"
    # gateway-owned layers are absent from this bare app and must say so
    for name in ("rate_limit", "headers", "csrf", "https_redirect", "request_id"):
        assert layers[name]["active"] is False, f"{name} falsely reports active"


# --------------------------------------------------------------------------
# 3. rate limiter: the path-rotation bypass must stay closed
# --------------------------------------------------------------------------
def test_rate_limit_survives_path_rotation():
    """The original key was f"rate:{ip}:{path}", so every new path reset the
    budget. 200 requests across 200 distinct paths must still stop at 120."""
    rl = RateLimiter()
    allowed = sum(rl.check("9.9.9.1", f"/api/v1/farms/{i}")[0] for i in range(200))
    assert allowed == 120, f"path rotation bypassed the limit: allowed {allowed}"


def test_auth_limit_survives_auth_path_rotation():
    """Same bypass on the brute-force ceiling: 10/min must hold across paths."""
    rl = RateLimiter()
    auth_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",
        "/api/v1/auth/signup",
        "/api/v1/auth/verify",
        "/api/v1/auth/reset",
        "/api/v1/auth/me",
        "/api/v1/auth/session",
        "/api/v1/auth/oauth",
        "/api/v1/auth/check",
    ]
    allowed = sum(rl.check("9.9.9.2", p)[0] for p in auth_paths)
    assert allowed == 10, f"auth path rotation bypassed the limit: allowed {allowed}"


def test_rate_limit_is_per_ip_not_global():
    a = RateLimiter()
    b = RateLimiter()
    for _ in range(120):
        a.check("9.9.9.3", "/api/v1/x")
    assert a.check("9.9.9.3", "/api/v1/x")[0] is False
    assert b.check("9.9.9.4", "/api/v1/x")[0] is True


def test_user_budget_is_tracked_per_subject():
    rl = RateLimiter()
    for _ in range(10):
        rl.check("9.9.9.5", "/api/v1/x", user_id="alice")
    # a different subject on the same IP is unaffected by the IP counter
    assert rl.check("9.9.9.5", "/api/v1/x", user_id="bob")[0] is True


def test_redis_path_matches_memory_path():
    """Both backends must enforce the same ceilings (the old code diverged)."""
    paths = [f"/api/v1/item/{i}" for i in range(150)]
    mem = RateLimiter()
    red = RateLimiter(redis_client=FakeRedis())

    mem_allowed = sum(mem.check("9.9.9.6", p)[0] for p in paths)
    red_allowed = sum(red.check("9.9.9.6", p)[0] for p in paths)
    assert mem_allowed == red_allowed == 120


def test_redis_auth_limit_matches_memory_path():
    mem = RateLimiter()
    red = RateLimiter(redis_client=FakeRedis())
    auth_paths = [f"/api/v1/auth/{i}" for i in range(30)]
    mem_allowed = sum(mem.check("9.9.9.7", p)[0] for p in auth_paths)
    red_allowed = sum(red.check("9.9.9.7", p)[0] for p in auth_paths)
    assert mem_allowed == red_allowed == 10


def test_window_slides_so_the_limit_recovers():
    rl = RateLimiter()
    for _ in range(120):
        rl.check("9.9.9.8", "/api/v1/x")
    assert rl.check("9.9.9.8", "/api/v1/x")[0] is False
    # fast-forward past the window
    rl._memory["9.9.9.8"] = deque([time.time() - 120] * 120)
    assert rl.check("9.9.9.8", "/api/v1/x")[0] is True


# --------------------------------------------------------------------------
# 4. adversary playbook: bypasses found by re-attacking the mounted firewall
# --------------------------------------------------------------------------
def _probe_app(**fw_kwargs):
    app = FastAPI()

    @app.get("/api/v1/x")
    def _x():
        return {"ok": True}

    app.add_middleware(SpiderFirewallMiddleware, **fw_kwargs)
    return app


def test_spoofed_forwarded_for_cannot_mint_a_new_identity():
    """A caller used to rotate X-Forwarded-For to reset every IP-keyed
    control. With no trusted proxy configured the header must be ignored."""
    with TestClient(_probe_app(enable_rate_limit=False)) as c:
        codes = {
            c.get("/api/v1/x", headers={"X-Forwarded-For": f"10.0.0.{i}"}).status_code
            for i in range(50)
        }
    assert codes == {200}


def test_forwarded_for_is_ignored_without_trusted_proxy():
    scope = {
        "headers": [(b"x-forwarded-for", b"9.9.9.9"), (b"host", b"x")],
        "client": ("testclient", 1234),
    }
    assert _client_ip(scope, []) == "testclient"
    assert _client_ip(scope, None) == "testclient"


def test_forwarded_for_is_honoured_only_from_a_trusted_peer():
    trusted = _parse_networks("10.0.0.0/8")
    from_proxy = {
        "headers": [(b"x-forwarded-for", b"9.9.9.9"), (b"host", b"x")],
        "client": ("10.0.0.1", 1234),
    }
    from_stranger = {
        "headers": [(b"x-forwarded-for", b"9.9.9.9"), (b"host", b"x")],
        "client": ("203.0.113.7", 1234),
    }
    assert _client_ip(from_proxy, trusted) == "9.9.9.9"
    assert _client_ip(from_stranger, trusted) == "203.0.113.7"


def test_malformed_forwarded_for_falls_back_to_the_peer():
    trusted = _parse_networks("10.0.0.0/8")
    scope = {
        "headers": [(b"x-forwarded-for", b"not-an-ip"), (b"host", b"x")],
        "client": ("10.0.0.1", 1234),
    }
    assert _client_ip(scope, trusted) == "10.0.0.1"


def test_honeypot_ban_is_enforced_on_normal_paths():
    """`hit()` records a 15-minute ban that the firewall never consulted,
    so a scanner could return to the real endpoints immediately."""
    with TestClient(_probe_app(enable_rate_limit=False)) as c:
        assert c.get("/.env").status_code == 404
        assert honeypot.is_blocked("testclient")
        follow_up = c.get("/api/v1/x")
    assert follow_up.status_code == 403


def test_percent_encoded_sqli_is_caught():
    """Encoded injection decoded to zero on the old raw-text scan."""
    for payload in (
        "%55%4e%49%4f%4e%20%73%45%4c%45%43%54",
        "a%20union%20select%201",
        "%2555%254e%2549%254f%254e%2520%2573%2545%254c%2545%2543%2554",
    ):
        allowed, _, hits, _ = waf_engine.check("POST", "/api/v1/x", payload, "", "Mozilla/5.0")
        assert not allowed, f"encoded payload bypassed the WAF: {payload}"
        assert "sqli-union" in hits


def test_encoded_xss_is_caught():
    allowed, _, hits, _ = waf_engine.check(
        "POST", "/api/v1/x", "", "%3Cscript%3Ealert(1)%3C/script%3E", "Mozilla/5.0"
    )
    assert not allowed
    assert "xss-script" in hits


def test_query_plus_is_decoded_to_space():
    allowed, _, hits, _ = waf_engine.check(
        "GET", "/api/v1/x", "id=1+union+select+1", "", "Mozilla/5.0"
    )
    assert not allowed
    assert "sqli-union" in hits


def test_honeypot_normalises_case_slash_and_dot_segments():
    for path in ("/admin.php", "/ADMIN.PHP", "/admin.php/", "/x/../admin.php", "/.ENV", "/.env/"):
        assert honeypot.is_trap(path), f"honeypot missed {path}"


def test_honeypot_still_ignores_ordinary_paths():
    for path in ("/api/v1/land", "/api/v1/farms/1", "/", "/admin"):
        assert not honeypot.is_trap(path), f"false positive on {path}"


def test_scanner_user_agent_still_blocked_after_normalisation():
    allowed, _, hits, _ = waf_engine.check("GET", "/api/v1/x", "", "", "sqlmap/1.7")
    assert not allowed
    assert "scanner-ua" in hits


def test_legitimate_traffic_still_passes():
    for path, query, body in (
        ("/api/v1/land", "page=2&size=20", ""),
        ("/api/v1/farms/42", "", '{"name":"Bendsar plot","area_ha":12.5}'),
        ("/api/v1/auth/login", "", '{"username":"farmer@example.com","password":"x"}'),
    ):
        allowed, score, hits, _ = waf_engine.check("POST", path, query, body, "Mozilla/5.0")
        assert allowed, f"false positive on {path} (score={score}, hits={hits})"


# --------------------------------------------------------------------------
# 6. bounded state: rotating identities must not grow memory without limit
# --------------------------------------------------------------------------
def test_anomaly_profiles_are_evicted_when_idle():
    from services.security.anomaly import PROFILE_TTL, AnomalyDetector

    det = AnomalyDetector()
    for i in range(5_000):
        det.score(f"10.1.{i // 256}.{i % 256}", 200, "q=1", 10)
    assert len(det._vol) == 5_000

    # pretend every profile went quiet long ago
    det._vol = defaultdict(deque, {ip: deque([time.time() - PROFILE_TTL - 1]) for ip in det._vol})
    det.score("10.9.9.9", 200, "q=1", 10)
    assert len(det._vol) == 1, "idle profiles were not evicted"


def test_anomaly_respects_the_hard_profile_cap():
    from services.security.anomaly import AnomalyDetector

    det = AnomalyDetector(max_profiles=50)
    for i in range(500):
        det.score(f"10.2.0.{i // 256}.{i % 256}", 200, "q=1", 10)
    assert len(det._vol) <= 51


def test_honeypot_hits_and_bans_stay_bounded():
    from services.security.honeypot import MAX_BLOCKED, MAX_HITS

    for i in range(MAX_HITS + 500):
        honeypot.hit(f"10.3.{i // 256}.{i % 256}", "/.env", "scanner")
    assert len(honeypot.hits) <= MAX_HITS
    assert len(honeypot._blocked) <= MAX_BLOCKED


def test_waf_event_log_stays_bounded():
    from services.security.waf import MAX_EVENTS

    for i in range(MAX_EVENTS + 250):
        waf_engine.check("POST", f"/api/v1/x?i={i}", "", "a' union select 1--", "sqlmap")
    assert len(waf_engine.events) <= MAX_EVENTS


def test_rate_limiter_buckets_stay_bounded():
    from services.security.rate_limit import PROFILE_TTL

    rl = RateLimiter()
    for i in range(3_000):
        rl.check(f"10.4.{i // 256}.{i % 256}", "/api/v1/x")
    assert len(rl._memory) == 3_000

    rl._memory = defaultdict(
        deque, {ip: deque([time.time() - PROFILE_TTL - 1]) for ip in rl._memory}
    )
    rl.check("10.9.9.9", "/api/v1/x")
    assert len(rl._memory) == 1, "idle client buckets were not evicted"


def test_eviction_does_not_weaken_an_active_limit():
    """Eviction must only drop *idle* state, never reset a live counter."""
    rl = RateLimiter()
    for _ in range(120):
        rl.check("10.5.5.5", "/api/v1/x")
    assert rl.check("10.5.5.5", "/api/v1/x")[0] is False


# --------------------------------------------------------------------------
# 7. hard cap must fail closed, not grant extra quota
# --------------------------------------------------------------------------
def test_hard_cap_refuses_new_identities_instead_of_evicting_live_ones():
    rl = RateLimiter(max_buckets=10)
    for i in range(10):
        assert rl.check(f"10.6.0.{i}", "/api/v1/x")[0] is True
    assert len(rl._memory) == 10

    # capacity reached: a new caller is refused, and nothing is evicted
    assert rl.check("10.6.9.9", "/api/v1/x")[0] is False
    assert len(rl._memory) == 10, "a live bucket was evicted to make room"


def test_hard_cap_does_not_hand_out_fresh_quota_on_rotation():
    """The cap must not become the loophole: rotating past capacity must not
    let a caller exceed the general ceiling."""
    rl = RateLimiter(max_buckets=10)
    for i in range(10):
        for _ in range(119):
            rl.check(f"10.7.0.{i}", "/api/v1/x")
    # each of the ten identities is now at 119/120
    granted = sum(rl.check(f"10.7.0.{i}", "/api/v1/x")[0] for i in range(10))
    assert granted == 10, "rotating identities bought more than 1 request each"
    assert rl.check("10.7.9.9", "/api/v1/x")[0] is False


def test_existing_client_is_unaffected_by_the_cap():
    rl = RateLimiter(max_buckets=2)
    rl.check("10.8.0.1", "/api/v1/x")
    rl.check("10.8.0.2", "/api/v1/x")
    # third client is refused, but a known client still works
    assert rl.check("10.8.0.3", "/api/v1/x")[0] is False
    assert rl.check("10.8.0.1", "/api/v1/x")[0] is True


def test_idle_eviction_frees_capacity_again():
    from services.security.rate_limit import PROFILE_TTL

    rl = RateLimiter(max_buckets=3)
    for i in range(3):
        rl.check(f"10.9.0.{i}", "/api/v1/x")
    assert rl.check("10.9.0.7", "/api/v1/x")[0] is False

    rl._memory = defaultdict(deque, {k: deque([time.time() - PROFILE_TTL - 1]) for k in rl._memory})
    assert rl.check("10.9.0.7", "/api/v1/x")[0] is True


def test_user_buckets_are_capped_too():
    rl = RateLimiter(max_buckets=2)
    rl.check("10.10.0.1", "/api/v1/x", user_id="u1")
    rl.check("10.10.0.2", "/api/v1/x", user_id="u2")
    assert rl.check("10.10.0.3", "/api/v1/x", user_id="u3")[0] is False
    assert len(rl._memory_user) == 2


def test_nlg_works_without_the_optional_legacy_rag_module():
    """services.ai.rag was removed in 5f9aa44; the live index is unified_rag.
    The optional import must not make the NLG path unimportable."""
    from services.ai.nlg import advise

    out = advise("بندسار برای کاهش رواناب", {"spi": -0.812})
    assert out["provider"] == "local-nlg"
    assert out["evidence"]
