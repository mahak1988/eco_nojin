"""Layer 2 — smart rate limiting (free, in-memory sliding window).

Per-IP: general API budget (default 120 req/min) and a stricter
auth-endpoint budget (10 req/min) against credential brute force.
Per-user: 300 req/min when a JWT subject is present.

Upgrade path (honest note): single-process in-memory store; for multi-worker
deployments swap the store for Redis / Upstash (paid) or a Postgres table.
"""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ip: dict[str, deque[float]] = defaultdict(deque)
        self._user: dict[str, deque[float]] = defaultdict(deque)
        self._auth_ip: dict[str, deque[float]] = defaultdict(deque)

    def _sweep(self, bucket: dict[str, deque[float]], key: str, window: float) -> None:
        now = time.time()
        dq = bucket[key]
        while dq and now - dq[0] > window:
            dq.popleft()

    def check(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        with self._lock:
            now = time.time()
            auth_route = "/auth" in path
            self._sweep(self._ip, ip, 60)
            self._ip[ip].append(now)
            if len(self._ip[ip]) > 120:
                return False, 60

            if auth_route:
                self._sweep(self._auth_ip, ip, 60)
                self._auth_ip[ip].append(now)
                if len(self._auth_ip[ip]) > 10:
                    return False, 60

            if user_id:
                self._sweep(self._user, user_id, 60)
                self._user[user_id].append(now)
                if len(self._user[user_id]) > 300:
                    return False, 60
        return True, 0


rate_limiter = RateLimiter()
