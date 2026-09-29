"""Spider firewall assembly — pure-ASGI middleware.

Order matters (cheapest checks first):
  1. honeypot trap check (exact path match)
  2. WAF signature scan (the request body is fully buffered, scanned,
     then replayed to the app so the scan sees real payloads)
  3. rate limiter (per-IP / per-user budgets)
  4. anomaly scorer (4xx ratio, entropy, volume)
  5. circuit breaker (repeated WAF blocks -> auto-block)
  6. security headers + HSTS

The middleware never raises: any layer failure degrades to allow + log
(fail-open is documented; the WAF/limiter still hard-block with 403/429).
"""

import asyncio
import contextlib
import ipaddress
import logging

from starlette.responses import JSONResponse

from .anomaly import anomaly_detector
from .antibot import Action as AntiBotAction, AntiBot
from .audit import log_event
from .honeypot import honeypot
from .rate_limit import RateLimiter
from .waf import waf_engine
from .watchdog import circuit_breaker

logger = logging.getLogger(__name__)

MAX_BODY_BYTES = 2_000_000  # scan cap; larger bodies are still forwarded

# Paths worth a proof-of-work challenge on *first* suspicion: sign-in, sign-up,
# password recovery, contact and search. Challenging an ordinary read would
# punish humans for being humans, so everywhere else a challenge requires a
# much higher score.
GUARDED_PREFIXES = (
    "/api/v1/auth",
    "/auth",
    "/api/v1/contact",
    "/api/v1/search",
    "/api/v1/newsletter",
    "/api/v1/support",
)
CHALLENGE_SCORE_ANYWHERE = 55
SOLUTION_HEADER = b"x-antibot-solution"
CHALLENGE_HEADER = b"x-antibot-challenge"


def _parse_networks(raw: str | None) -> list:
    nets = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        with contextlib.suppress(ValueError):
            nets.append(ipaddress.ip_network(part, strict=False))
    return nets


def _client_ip(scope, trusted_networks: list | None = None) -> str:
    """Resolve the client address, honouring X-Forwarded-For only from a
    trusted peer.

    Trusting the header unconditionally lets any caller mint a fresh identity
    per request, which defeats every IP-keyed control downstream (honeypot
    auto-block, circuit breaker, rate limiting, anomaly profiling). The header
    is therefore ignored unless the immediate peer sits in a configured trusted
    proxy network, and the value taken from it must parse as an IP address.
    """
    client = scope.get("client")
    peer = client[0] if client else "unknown"

    networks = trusted_networks or []
    if not networks:
        return peer
    try:
        peer_ip = ipaddress.ip_address(peer)
    except ValueError:
        return peer
    if not any(peer_ip in net for net in networks):
        return peer

    headers = dict(scope.get("headers") or [])
    fwd = headers.get(b"x-forwarded-for")
    if not fwd:
        return peer
    candidate = fwd.decode(errors="ignore").split(",")[0].strip()
    with contextlib.suppress(ValueError):
        return str(ipaddress.ip_address(candidate))
    return peer


class SpiderFirewallMiddleware:
    def __init__(
        self,
        app,
        exempt_prefixes=("/health", "/ready", "/docs", "/openapi.json", "/redoc"),
        redis_client=None,
        enable_rate_limit=True,
        trusted_proxies: str | None = None,
        antibot: AntiBot | None = None,
        enable_antibot: bool = True,
    ) -> None:
        self.app = app
        self.exempt = exempt_prefixes
        self._rate_limiter = RateLimiter(redis_client=redis_client)
        # The gateway already mounts a per-IP RateLimitMiddleware driven by
        # ECONOJIN_RATELIMIT_PER_MINUTE. Mounting a second, stricter limiter
        # here would silently override that configured budget, so the gateway
        # passes enable_rate_limit=False and keeps a single source of truth.
        self._rate_limit_enabled = enable_rate_limit
        self._trusted_networks = _parse_networks(trusted_proxies)
        # NOTE: the challenge store is per-process. Behind multiple workers a
        # nonce issued by one worker will not be verifiable by another, so a
        # challenge can be retried rather than solved once. That is a liveness
        # cost, not a security hole; move the store to Redis before relying on
        # challenges for anything stronger than friction.
        self._antibot = antibot or AntiBot()
        self._antibot_enabled = enable_antibot

    async def _antibot_step(self, scope, ip, path, method, receive, send) -> bool:
        """Run one rung of the anti-bot ladder. Returns True to continue.

        A client retrying with a valid proof-of-work solution is let through
        without re-scoring, so solving once is enough.
        """
        headers = dict(scope.get("headers") or [])
        solution = headers.get(SOLUTION_HEADER)
        if solution is not None:
            if self._antibot.check_solution(
                headers.get(CHALLENGE_HEADER, b"").decode(errors="ignore"),
                solution.decode(errors="ignore"),
            ):
                return True
            self._antibot.record_failed_solution(ip)
            log_event(
                "antibot",
                ip,
                method + " " + path,
                "block",
                {"reason": "pow_invalid"},
                severity="medium",
            )

        decision = self._antibot.assess(ip, scope, path)
        target = path

        if decision.action is AntiBotAction.ALLOW:
            return True

        if decision.action is AntiBotAction.DELAY:
            if decision.delay_seconds > 0:
                await asyncio.sleep(decision.delay_seconds)
            return True

        if decision.action is AntiBotAction.BLOCK:
            log_event(
                "antibot",
                ip,
                method + " " + path,
                "block",
                {"reason": "score", "score": decision.score, "signals": list(decision.reasons)},
                severity="high",
            )
            resp = JSONResponse(
                {"detail": "blocked", "signals": list(decision.reasons)},
                status_code=403,
            )
            await resp(scope, receive, send)
            return False

        # CHALLENGE: only where abuse actually hurts, or once the score is high
        # enough that any endpoint is fair game.
        if not target.startswith(GUARDED_PREFIXES) and decision.score < CHALLENGE_SCORE_ANYWHERE:
            if decision.delay_seconds > 0:
                await asyncio.sleep(decision.delay_seconds)
            return True

        challenge = decision.challenge
        assert challenge is not None
        log_event(
            "antibot",
            ip,
            method + " " + path,
            "challenge",
            {
                "score": decision.score,
                "signals": list(decision.reasons),
                "difficulty_bits": challenge.difficulty_bits,
            },
            severity="medium",
        )
        resp = JSONResponse(
            {
                "detail": "proof_of_work_required",
                "nonce": challenge.nonce,
                "difficulty_bits": challenge.difficulty_bits,
                "algorithm": "sha256",
                "instruction": (
                    "find solution such that sha256(f'{nonce}:{solution}') "
                    f"starts with {challenge.difficulty_bits} zero bits, then retry "
                    f"with the {SOLUTION_HEADER.decode()}"
                    f" and {CHALLENGE_HEADER.decode()} headers"
                ),
            },
            status_code=403,
            headers={
                CHALLENGE_HEADER.decode(): challenge.nonce,
                "Retry-After": "1",
            },
        )
        await resp(scope, receive, send)
        return False

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        ip = _client_ip(scope, self._trusted_networks)

        if path.startswith(self.exempt):
            await self.app(scope, receive, send)
            return

        # --- honeypot: any trap hit -> record + block IP -------------------
        if honeypot.is_trap(path):
            headers = dict(scope.get("headers") or [])
            ua = headers.get(b"user-agent", b"").decode(errors="ignore")
            honeypot.hit(ip, path, ua)
            log_event(
                "honeypot",
                ip,
                f"trap:{path}",
                "block",
                {"user_agent": ua[:120]},
                severity="critical",
            )
            resp = JSONResponse({"detail": "not found"}, status_code=404)
            await resp(scope, receive, send)
            return

        # --- circuit breaker / honeypot auto-block (previously blocked IP) -----
        # The honeypot's 15-minute IP ban is recorded by `hit()` but was never
        # consulted here, so a scanner that tripped one trap could walk straight
        # back onto the real endpoints.
        if circuit_breaker.is_blocked(ip) or honeypot.is_blocked(ip):
            log_event("breaker", ip, method + " " + path, "block", {"reason": "circuit_open"})
            resp = JSONResponse({"detail": "temporarily blocked"}, status_code=403)
            await resp(scope, receive, send)
            return

        # --- anti-bot ladder: allow -> delay -> challenge -> block ------------
        # NOTE: the await is load-bearing. A bare `self._antibot_step(...)`
        # yields a coroutine object, which is always truthy, so `not coro` is
        # always False and the whole ladder silently never runs.
        if self._antibot_enabled and not await self._antibot_step(
            scope, ip, path, method, receive, send
        ):
            return

        # --- buffer the full request body so WAF can scan it ----------------
        body = bytearray()
        while True:
            msg = await receive()
            if msg["type"] == "http.request":
                body.extend(msg.get("body", b""))
                if not msg.get("more_body", False) or len(body) > MAX_BODY_BYTES:
                    break
            elif msg["type"] == "http.disconnect":
                break
        body_bytes = bytes(body)

        headers = dict(scope.get("headers") or [])
        ua = headers.get(b"user-agent", b"").decode(errors="ignore")
        query = scope.get("query_string", b"").decode(errors="ignore")

        # --- WAF -------------------------------------------------------------
        allowed, score, hits, reason = waf_engine.check(
            method, path, query, body_bytes.decode("utf-8", "ignore"), ua
        )
        if not allowed:
            log_event(
                "waf",
                ip,
                method + " " + path,
                "block",
                {"rules": hits, "score": score},
                severity="high",
            )
            circuit_breaker.report_block(ip)
            resp = JSONResponse({"detail": "blocked by WAF", "reason": reason}, status_code=403)
            await resp(scope, receive, send)
            return

        # --- rate limit -------------------------------------------------------
        user_id = None
        auth_header = headers.get(b"authorization", b"").decode(errors="ignore")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                import base64
                import json as _json

                payload_b64 = token.split(".")[1] + "=="
                payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                user_id = payload.get("sub")
            except Exception:
                user_id = None
        ok, retry_after = self._rate_limiter.check(ip, path, user_id)
        if self._rate_limit_enabled and not ok:
            log_event(
                "rate",
                ip,
                method + " " + path,
                "block",
                {"retry_after": retry_after},
                severity="medium",
            )
            resp = JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
            await resp(scope, receive, send)
            return

        # --- anomaly scoring (post-response) ----------------------------------
        status_holder = {"code": 200}

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-econojin-firewall", b"active"))
                message["headers"] = headers
            await send(message)

        # replay the buffered body to the inner app
        replayed = [False]

        async def replay_receive():
            if not replayed[0]:
                replayed[0] = True
                return {"type": "http.request", "body": body_bytes, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        try:
            await self.app(scope, replay_receive, send_wrapper)
        finally:
            score_a = anomaly_detector.score(ip, status_holder["code"], query, len(body_bytes))
            if score_a >= 80:
                log_event(
                    "anomaly",
                    ip,
                    method + " " + path,
                    "throttle",
                    {"score": score_a},
                    severity="medium",
                )
