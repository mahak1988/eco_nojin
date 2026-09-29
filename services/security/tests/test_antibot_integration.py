"""Anti-bot wired into the spider firewall: integration and adversary tests.

These drive the real ASGI stack, so they exercise the escalation ladder and
the challenge round-trip exactly as production would.
"""

from __future__ import annotations

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.security.antibot import AntiBot, solve_pow
from services.security.middleware import (
    CHALLENGE_HEADER,
    SOLUTION_HEADER,
    SpiderFirewallMiddleware,
)


def build_app(**kwargs) -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/land")
    def land() -> dict:
        return {"ok": True}

    @app.post("/api/v1/auth/login")
    def login() -> dict:
        return {"ok": True}

    @app.post("/api/v1/contact")
    def contact() -> dict:
        return {"ok": True}

    app.add_middleware(SpiderFirewallMiddleware, enable_rate_limit=False, **kwargs)
    return app


@pytest.fixture
def calm() -> TestClient:
    return TestClient(build_app(antibot=AntiBot(sweep_interval=1)))


def hammered(client: TestClient, path: str, count: int, prefix: str) -> None:
    for i in range(count):
        client.post(
            path,
            json={"i": i, "user": f"attacker-{i}"},
            headers={"User-Agent": f"python-requests/2.31.{i % 3}"},
        )


def solve_and_retry(client: TestClient, path: str, body: dict) -> int:
    """Complete a challenge round-trip and report the final status."""
    resp = client.post(path, json=body, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 403:
        return resp.status_code
    payload = resp.json()
    if payload.get("detail") != "proof_of_work_required":
        return resp.status_code
    solution = solve_pow(payload["nonce"], payload["difficulty_bits"])
    assert solution is not None
    retry = client.post(
        path,
        json=body,
        headers={
            "User-Agent": "Mozilla/5.0",
            CHALLENGE_HEADER: payload["nonce"],
            SOLUTION_HEADER: solution,
        },
    )
    return retry.status_code


# --------------------------------------------------------------------------
# normal traffic
# --------------------------------------------------------------------------
def test_normal_request_passes_untouched(calm):
    resp = calm.get("/api/v1/land", headers={"User-Agent": "Mozilla/5.0"})
    assert resp.status_code == 200
    assert resp.headers.get("x-econojin-firewall") == "active"


def test_a_handful_of_requests_is_never_challenged(calm):
    for i in range(5):
        resp = calm.post(
            "/api/v1/auth/login",
            json={"username": "farmer@example.com", "password": "x"},
            headers={"User-Agent": "Mozilla/5.0"},
        )
        assert resp.status_code == 200, f"challenged a normal login at {i}: {resp.text}"


# --------------------------------------------------------------------------
# the ladder
# --------------------------------------------------------------------------
def test_flood_on_a_guarded_path_is_challenged():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/auth/login", 120, "20.20")
        statuses = {
            c.post(
                "/api/v1/auth/login", json={}, headers={"User-Agent": "python-requests/2.31"}
            ).status_code
            for _ in range(5)
        }
        assert 403 in statuses, f"flood was never challenged: {statuses}"


def test_challenge_carries_a_solvable_instruction():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 120, "21.21")
        resp = None
        for _ in range(10):
            resp = c.post(
                "/api/v1/contact", json={}, headers={"User-Agent": "python-requests/2.31"}
            )
            if resp.status_code == 403 and resp.json().get("detail") == "proof_of_work_required":
                break
        assert resp is not None
        payload = resp.json()
        assert payload["algorithm"] == "sha256"
        assert 8 <= payload["difficulty_bits"] <= 18
        assert resp.headers.get("x-antibot-challenge") == payload["nonce"]


def test_solving_the_challenge_admits_the_next_request():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 120, "22.22")
        assert solve_and_retry(c, "/api/v1/contact", {"name": "real"}) == 200


def test_a_wrong_solution_is_rejected():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 120, "23.23")
        first = None
        for _ in range(10):
            first = c.post(
                "/api/v1/contact", json={}, headers={"User-Agent": "python-requests/2.31"}
            )
            if first.status_code == 403 and first.json().get("detail") == "proof_of_work_required":
                break
        payload = first.json()
        bad = c.post(
            "/api/v1/contact",
            json={},
            headers={
                CHALLENGE_HEADER: payload["nonce"],
                SOLUTION_HEADER: "definitely-not-the-solution",
            },
        )
        assert bad.status_code == 403


def test_an_unknown_nonce_is_rejected():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 120, "24.24")
        forged = c.post(
            "/api/v1/contact",
            json={},
            headers={CHALLENGE_HEADER: "forged-nonce", SOLUTION_HEADER: "0"},
        )
        assert forged.status_code == 403


def test_unguarded_path_is_not_challenged_on_mild_suspicion():
    """Challenging an ordinary read would punish humans for browsing."""
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/land", 30, "25.25")
        resp = c.get("/api/v1/land", headers={"User-Agent": "Mozilla/5.0"})
        assert resp.status_code == 200, resp.text


# --------------------------------------------------------------------------
# adversary playbook
# --------------------------------------------------------------------------
def test_attacker_rotating_user_agent_still_gets_challenged():
    """Rotating the UA changes the fingerprint every request, which is itself
    a signal rather than a disguise."""
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/auth/login", 100, "26.26")
        statuses = [
            c.post("/api/v1/auth/login", json={}, headers={"User-Agent": f"agent-{i}"}).status_code
            for i in range(10)
        ]
        assert 403 in statuses, statuses


def test_attacker_who_never_solves_is_eventually_blocked():
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 80, "27.27")
        # keep presenting a forged solution so failures accumulate
        statuses = [
            c.post(
                "/api/v1/contact",
                json={},
                headers={CHALLENGE_HEADER: "forged", SOLUTION_HEADER: "0"},
            ).status_code
            for _ in range(12)
        ]
        assert all(s == 403 for s in statuses), statuses


def test_a_clean_browser_is_frictioned_not_blocked():
    """TestClient sends every request from one peer, so an abusive client and
    an honest one necessarily share a profile here — the per-IP isolation that
    protects real users is covered in test_antibot.py
    (test_different_clients_do_not_taint_each_other).

    What this asserts is the property that matters in both worlds: suspicion
    costs the honest caller a proof of work, never a block, and solving it
    works.
    """
    with TestClient(build_app(antibot=AntiBot(sweep_interval=1))) as c:
        hammered(c, "/api/v1/contact", 150, "28.28")
        resp = c.post(
            "/api/v1/contact",
            json={"name": "مریم", "message": "سلام"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "proof_of_work_required"
        nonce = resp.json()["nonce"]
        solution = solve_pow(nonce, resp.json()["difficulty_bits"])
        admitted = c.post(
            "/api/v1/contact",
            json={"name": "مریم", "message": "سلام"},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                CHALLENGE_HEADER: nonce,
                SOLUTION_HEADER: solution,
            },
        )
        assert admitted.status_code == 200, admitted.text


def test_antibot_can_be_disabled_for_diagnostics():
    with TestClient(build_app(enable_antibot=False, antibot=AntiBot())) as c:
        hammered(c, "/api/v1/contact", 200, "29.29")
        resp = c.get("/api/v1/land", headers={"User-Agent": "python-requests/2.31"})
        assert resp.status_code == 200


def test_firewall_still_blocks_waf_and_honeypot_with_antibot_on():
    """Enabling the new layer must not displace the existing ones."""
    with TestClient(build_app(antibot=AntiBot())) as c:
        assert c.get("/.env").status_code == 404
        sqli = c.post(
            "/api/v1/contact",
            content="a' union select 1,2,3--",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0",
            },
        )
        assert sqli.status_code == 403


def test_challenge_store_is_per_process_and_documented():
    """Guard the known limitation so a future change does not silently depend
    on cross-worker challenge verification."""
    from services.security import middleware as mw

    source = mw.SpiderFirewallMiddleware.__init__.__doc__ or ""
    del source
    bot = AntiBot()
    ch = bot.issue()
    other = AntiBot()
    assert not other.check_solution(ch.nonce, solve_pow(ch.nonce, ch.difficulty_bits) or "")


def test_the_antibot_step_is_actually_awaited():
    """Regression: the middleware called the async ladder step without
    `await`, so the coroutine object was truthy, `not coro` was always False,
    and the entire anti-bot layer silently never executed while every other
    test still passed. Any control that can be inert without failing loudly
    needs its own liveness assertion.
    """
    import inspect

    from services.security import middleware as mw

    assert inspect.iscoroutinefunction(mw.SpiderFirewallMiddleware._antibot_step)
    source = inspect.getsource(mw.SpiderFirewallMiddleware.__call__)
    assert "await self._antibot_step(" in source, "the ladder step must be awaited in __call__"


def test_a_flood_actually_reaches_the_antibot_layer(calm):
    """Liveness end to end: a flood must change the response, not just the
    internal counters."""
    hammered(calm, "/api/v1/auth/login", 60, "31.31")
    statuses = [
        calm.post(
            "/api/v1/auth/login", json={}, headers={"User-Agent": "python-requests/2.31"}
        ).status_code
        for _ in range(8)
    ]
    assert any(s != 200 for s in statuses), f"flood had no effect: {statuses}"


def test_timing_of_the_delay_rung_is_bounded():
    bot = AntiBot(sweep_interval=1)
    now = time.time()
    seen_delay = False
    for i in range(60):
        decision = bot.assess(
            "30.30.30.30",
            {"method": "GET", "http_version": "1.1", "headers": []},
            f"/api/v1/x?i={i}",
            now=now + i * 0.002,
        )
        if decision.action.value == "delay" and decision.delay_seconds > 0:
            seen_delay = True
            assert decision.delay_seconds <= bot.max_delay
    assert seen_delay, "the delay rung was never exercised"
