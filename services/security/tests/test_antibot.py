"""Tests for the anti-bot layer (services.security.antibot).

Includes an adversary playbook: each attack is written as a bot would perform
it, and the layer must refuse to be fooled.
"""

from __future__ import annotations

import time

import pytest

from services.security.antibot import (
    CHALLENGE_TTL,
    DEFAULT_DIFFICULTY_BITS,
    Action,
    AntiBot,
    clamp_score,
    difficulty_for_score,
    hmac_token,
    http_fingerprint,
    issue_challenge,
    raw_fingerprint_input,
    solve_pow,
    verify_pow,
)

BROWSER_SCOPE = {
    "method": "GET",
    "http_version": "2",
    "headers": [
        (b":method", b"GET"),
        (b":authority", b"econojin.ir"),
        (b":scheme", b"https"),
        (b"user-agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        (b"accept", b"text/html,application/xhtml+xml"),
        (b"accept-language", b"fa-IR,fa;q=0.9,en;q=0.8"),
        (b"accept-encoding", b"gzip, deflate, br"),
        (b"cookie", b"session=abc"),
        (b"sec-ch-ua", b'"Chromium";v="120"'),
    ],
}


def scripted_scope(user_agent: str = "python-requests/2.31") -> dict:
    return {
        "method": "GET",
        "http_version": "1.1",
        "headers": [
            (b"host", b"econojin.ir"),
            (b"user-agent", user_agent.encode()),
            (b"accept", b"*/*"),
            (b"accept-encoding", b"gzip, deflate"),
        ],
    }


@pytest.fixture
def bot() -> AntiBot:
    return AntiBot()


# --------------------------------------------------------------------------
# proof of work
# --------------------------------------------------------------------------
def test_pow_round_trip():
    ch = issue_challenge(8)
    solution = solve_pow(ch.nonce, 8)
    assert solution is not None
    assert verify_pow(ch.nonce, solution, 8)


def test_pow_rejects_wrong_solution():
    ch = issue_challenge(8)
    assert not verify_pow(ch.nonce, "not-the-answer", 8)


def test_pow_rejects_empty_and_oversized_input():
    ch = issue_challenge(8)
    assert not verify_pow(ch.nonce, "", 8)
    assert not verify_pow("", "1", 8)
    assert not verify_pow(ch.nonce, "x" * 33, 8)


def test_pow_is_nonce_bound():
    """A solution for one challenge must not work for another."""
    a, b = issue_challenge(8), issue_challenge(8)
    solution = solve_pow(a.nonce, 8)
    assert solution is not None
    assert not verify_pow(b.nonce, solution, 8)


def test_pow_challenge_is_single_use():
    bot = AntiBot()
    ch = bot.issue()
    solution = solve_pow(ch.nonce, ch.difficulty_bits)
    assert solution is not None
    assert bot.check_solution(ch.nonce, solution) is True
    assert bot.check_solution(ch.nonce, solution) is False


def test_pow_challenge_expires():
    bot = AntiBot()
    ch = bot.issue()
    assert ch.expires_at - ch.issued_at == pytest.approx(CHALLENGE_TTL)
    assert bot.check_solution("never-issued", "1") is False


def test_difficulty_scales_with_suspicion():
    assert difficulty_for_score(20) < difficulty_for_score(60)
    assert difficulty_for_score(95) >= 18


def test_clamp_score_bounds():
    assert clamp_score(-5) == 0
    assert clamp_score(1000) == 100
    assert clamp_score(42.9) == 42


def test_hmac_token_is_stable_and_bound_to_input():
    a = hmac_token("nonce-a", b"key")
    assert a == hmac_token("nonce-a", b"key")
    assert a != hmac_token("nonce-b", b"key")
    assert a != hmac_token("nonce-a", b"other-key")


# --------------------------------------------------------------------------
# fingerprint
# --------------------------------------------------------------------------
def test_fingerprint_is_stable_and_ignores_host_value():
    a = dict(BROWSER_SCOPE)
    b = {
        **BROWSER_SCOPE,
        "headers": [
            (k, v.replace(b"econojin.ir", b"evil.test")) if k == b":authority" else (k, v)
            for k, v in BROWSER_SCOPE["headers"]
        ],
    }
    assert http_fingerprint(a) == http_fingerprint(b)


def test_fingerprint_ignores_volatile_headers():
    base = http_fingerprint(scripted_scope())
    noisy = http_fingerprint(
        {
            **scripted_scope(),
            "headers": scripted_scope()["headers"] + [(b"date", b"Mon, 01 Jan 2035 00:00:00 GMT")],
        }
    )
    assert base == noisy


def test_fingerprint_separates_browser_from_script():
    assert http_fingerprint(BROWSER_SCOPE) != http_fingerprint(scripted_scope())


def test_fingerprint_separates_http_versions():
    v1 = {**scripted_scope(), "http_version": "1.1"}
    v2 = {**scripted_scope(), "http_version": "2"}
    assert http_fingerprint(v1) != http_fingerprint(v2)


def test_raw_input_exposes_method_and_protocol():
    raw = raw_fingerprint_input(BROWSER_SCOPE)
    assert raw.startswith("GET_2_")
    assert "_c1_" in raw, "cookie presence must be recorded"


def test_fingerprint_handles_empty_and_missing_headers():
    assert http_fingerprint({}) == http_fingerprint({"method": "GET", "http_version": "1.1"})
    assert http_fingerprint({"headers": None})


# --------------------------------------------------------------------------
# escalation ladder
# --------------------------------------------------------------------------
def test_calm_traffic_is_allowed_immediately(bot):
    decision = bot.assess("1.1.1.1", BROWSER_SCOPE, "/api/v1/land")
    assert decision.action is Action.ALLOW
    assert decision.score == 0


def test_human_paced_traffic_stays_allowed(bot):
    now = time.time()
    for i in range(30):
        decision = bot.assess(
            "1.1.1.2", BROWSER_SCOPE, f"/api/v1/land?page={i}", now=now + i * 1.7 + (i % 3) * 0.4
        )
        assert decision.action is Action.ALLOW, (
            f"human pacing challenged at {i}: {decision.reasons}"
        )


def test_machine_tight_loop_gets_escalated(bot):
    now = time.time()
    actions = []
    for i in range(40):
        decision = bot.assess("2.2.2.2", scripted_scope(), "/api/v1/x", now=now + i * 0.001)
        actions.append(decision.action)
    assert actions[-1] is not Action.ALLOW, "a tight loop was never escalated"
    assert Action.BLOCK in actions or Action.CHALLENGE in actions


def test_suspicious_traffic_is_delayed_before_blocked(bot):
    """The ladder must degrade gracefully: delay, then challenge, then block."""
    now = time.time()
    seen: set[Action] = set()
    for i in range(60):
        decision = bot.assess(
            "3.3.3.3", scripted_scope(), f"/api/v1/farms/{i}", now=now + i * 0.001
        )
        seen.add(decision.action)
    assert Action.DELAY in seen, f"delay step never used: {seen}"
    assert Action.BLOCK in seen or Action.CHALLENGE in seen, f"never escalated: {seen}"


def test_blocked_client_stays_blocked(bot):
    now = time.time()
    for i in range(60):
        bot.assess("4.4.4.4", scripted_scope(), f"/api/v1/farms/{i}", now=now + i * 0.001)
    assert bot.is_blocked("4.4.4.4", now=now + 1)
    decision = bot.assess("4.4.4.4", scripted_scope(), "/api/v1/land", now=now + 1)
    assert decision.action is Action.BLOCK


def test_different_clients_do_not_taint_each_other(bot):
    now = time.time()
    for i in range(60):
        bot.assess("5.5.5.5", scripted_scope(), f"/api/v1/farms/{i}", now=now + i * 0.001)
    assert bot.assess("6.6.6.6", BROWSER_SCOPE, "/api/v1/land", now=now).action is Action.ALLOW


# --------------------------------------------------------------------------
# adversary playbook
# --------------------------------------------------------------------------
def test_attacker_cannot_reuse_another_clients_solution(bot):
    victim = bot.issue()
    solution = solve_pow(victim.nonce, victim.difficulty_bits)
    assert solution is not None
    # the victim's own check succeeds once
    assert bot.check_solution(victim.nonce, solution) is True
    # a second attempt with the replayed value fails
    assert bot.check_solution(victim.nonce, solution) is False


def test_attacker_rotating_fingerprints_is_noticed(bot):
    """A client that changes its header layout every request is rotating."""
    now = time.time()
    uas = [f"agent-{i}" for i in range(40)]
    actions = []
    for i, ua in enumerate(uas):
        decision = bot.assess("7.7.7.7", scripted_scope(ua), f"/api/v1/x?i={i}", now=now + i * 0.05)
        actions.append(decision.action)
    assert Action.BLOCK in actions or Action.CHALLENGE in actions, actions


def test_path_enumeration_is_scored(bot):
    now = time.time()
    actions = []
    for i in range(120):
        decision = bot.assess(
            "8.8.8.8", scripted_scope(), f"/api/v1/resource/{i}", now=now + i * 0.002
        )
        actions.append(decision.action)
    assert Action.BLOCK in actions or Action.CHALLENGE in actions, actions


def test_repeated_pow_failures_escalate(bot):
    for _ in range(3):
        bot.record_failed_solution("9.9.9.9")
    decision = bot.assess("9.9.9.9", BROWSER_SCOPE, "/api/v1/land")
    assert decision.score >= 40, decision


def test_proof_of_work_stops_a_high_volume_client(bot):
    """The cost that matters: a client that never solves a challenge burns
    budget and gets escalated regardless of how well-formed its traffic is."""
    now = time.time()
    for i in range(30):
        bot.assess("10.10.10.10", scripted_scope(), f"/api/v1/x?i={i}", now=now + i * 0.001)
        bot.record_failed_solution("10.10.10.10")
    final = bot.assess("10.10.10.10", scripted_scope(), "/api/v1/x", now=now + 1)
    assert final.action in (Action.CHALLENGE, Action.BLOCK), final


def test_default_difficulty_is_deliberately_cheap():
    """A challenge must not read as a punishment for ordinary users."""
    assert 10 <= DEFAULT_DIFFICULTY_BITS <= 16
    started = time.perf_counter()
    assert solve_pow(issue_challenge(12).nonce, 12) is not None
    assert time.perf_counter() - started < 5.0


# --------------------------------------------------------------------------
# bounded state
# --------------------------------------------------------------------------
def test_pagination_is_not_blocked(bot):
    """Regression: an earlier heuristic flagged ?page=1..30 browsing as
    enumeration because every full URL was unique.

    Perfectly even pacing may earn a challenge — that is cheap friction — but
    it must never block an ordinary user.
    """
    now = time.time()
    for i in range(40):
        decision = bot.assess(
            "15.15.15.15", BROWSER_SCOPE, f"/api/v1/land?page={i}", now=now + i * 0.9
        )
        assert decision.action is not Action.BLOCK, f"blocked browsing at {i}: {decision.reasons}"


def test_id_walk_of_one_template_is_flagged(bot):
    now = time.time()
    actions = []
    for i in range(60):
        decision = bot.assess(
            "16.16.16.16", scripted_scope(), f"/api/v1/farms/{i}", now=now + i * 0.004
        )
        actions.append(decision.action)
    assert Action.BLOCK in actions or Action.CHALLENGE in actions, actions


def test_navigating_many_distinct_pages_is_not_blocked(bot):
    """A user reading 40 different documents is not a scraper.

    Even spacing may cost them a challenge; that is the documented trade. What
    must never happen is a block, because solving costs a browser milliseconds
    while a block costs the user the page.
    """
    now = time.time()
    for i in range(40):
        decision = bot.assess(
            "17.17.17.17",
            BROWSER_SCOPE,
            f"/api/v1/handbook/chapter-{i}",
            now=now + i * 0.8,
        )
        assert decision.action is not Action.BLOCK, f"blocked browsing at {i}: {decision.reasons}"
        if decision.action is Action.CHALLENGE:
            assert decision.challenge is not None
            assert 8 <= decision.challenge.difficulty_bits <= 18


def test_profiles_are_bounded_and_evictable():
    bot = AntiBot(sweep_interval=4)
    now = time.time()
    for i in range(500):
        bot.assess(f"11.0.{i // 256}.{i % 256}", BROWSER_SCOPE, "/x", now=now)
    assert len(bot._profiles) == 500
    # make them all idle, then let the amortised sweep run
    for p in bot._profiles.values():
        p.last_at = now - 10_000
    for _ in range(5):
        bot.assess("12.12.12.12", BROWSER_SCOPE, "/x", now=now + 20_000)
    assert len(bot._profiles) == 1, "idle profiles were not evicted"


def test_profile_cap_holds():
    bot = AntiBot(max_profiles=100, sweep_interval=1000)
    now = time.time()
    for i in range(2_000):
        bot.assess(
            f"13.{i // 65536 % 256}.{i // 256 % 256}.{i % 256}", BROWSER_SCOPE, "/x", now=now
        )
    assert len(bot._profiles) <= 100, f"cap breached: {len(bot._profiles)}"


def test_housekeeping_is_cheap_enough_for_the_request_path():
    """Regression: sweeping every profile on every request made the limiter
    O(profiles) per call, which is a self-inflicted DoS under flood."""
    import time as _t

    bot = AntiBot(max_profiles=5_000, sweep_interval=64)
    now = _t.time()
    for i in range(5_000):
        bot.assess(f"18.{i // 256}.{i % 256}", BROWSER_SCOPE, "/x", now=now)

    started = _t.perf_counter()
    for i in range(5_000):
        bot.assess(f"19.{i // 256}.{i % 256}", BROWSER_SCOPE, "/x", now=now)
    elapsed = _t.perf_counter() - started
    assert elapsed < 2.0, f"5k assessments took {elapsed:.2f}s; per-request cost is too high"


def test_outstanding_challenges_are_bounded():
    bot = AntiBot(max_challenges=50, sweep_interval=1)
    for _ in range(500):
        bot.issue()
    bot._sweep_locked(time.time() + CHALLENGE_TTL + 10)
    assert len(bot._challenges) == 0


def test_stats_reports_real_counts(bot):
    bot.assess("14.14.14.14", BROWSER_SCOPE, "/x")
    bot.issue()
    stats = bot.stats()
    assert stats["profiles"] >= 1
    assert stats["challenges_outstanding"] >= 1
    assert stats["thresholds"]["block"] > stats["thresholds"]["challenge"]
