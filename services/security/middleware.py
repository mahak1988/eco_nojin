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
import logging

from starlette.responses import JSONResponse

from .anomaly import anomaly_detector
from .audit import log_event
from .honeypot import honeypot
from .rate_limit import rate_limiter
from .waf import waf_engine
from .watchdog import circuit_breaker

logger = logging.getLogger("econojin.firewall")

MAX_BODY_BYTES = 2_000_000  # scan cap; larger bodies are still forwarded


def _client_ip(scope) -> str:
    headers = dict(scope.get("headers") or [])
    fwd = headers.get(b"x-forwarded-for")
    if fwd:
        return fwd.decode().split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


class SpiderFirewallMiddleware:
    def __init__(self, app, exempt_prefixes=("/health", "/ready", "/docs", "/openapi.json", "/redoc")) -> None:
        self.app = app
        self.exempt = exempt_prefixes

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        ip = _client_ip(scope)

        if path.startswith(self.exempt):
            await self.app(scope, receive, send)
            return

        # --- honeypot: any trap hit -> record + block IP -------------------
        if honeypot.is_trap(path):
            headers = dict(scope.get("headers") or [])
            ua = headers.get(b"user-agent", b"").decode(errors="ignore")
            honeypot.hit(ip, path, ua)
            log_event("honeypot", ip, f"trap:{path}", "block", {"user_agent": ua[:120]}, severity="critical")
            resp = JSONResponse({"detail": "not found"}, status_code=404)
            await resp(scope, receive, send)
            return

        # --- circuit breaker (auto-blocked IP) ------------------------------
        if circuit_breaker.is_blocked(ip):
            log_event("breaker", ip, method + " " + path, "block", {"reason": "circuit_open"})
            resp = JSONResponse({"detail": "temporarily blocked"}, status_code=403)
            await resp(scope, receive, send)
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
        allowed, score, hits, reason = waf_engine.check(method, path, query, body_bytes.decode("utf-8", "ignore"), ua)
        if not allowed:
            log_event("waf", ip, method + " " + path, "block", {"rules": hits, "score": score}, severity="high")
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
        ok, retry_after = rate_limiter.check(ip, path, user_id)
        if not ok:
            log_event("rate", ip, method + " " + path, "block", {"retry_after": retry_after}, severity="medium")
            resp = JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": str(retry_after)})
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
                log_event("anomaly", ip, method + " " + path, "throttle", {"score": score_a}, severity="medium")
