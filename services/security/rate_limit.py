"""Layer 2 — smart rate limiting (Redis with in-memory fallback).

Budgets are enforced per client IP, not per (IP, path): a key that includes the
path hands every distinct path a fresh budget, so a caller rotating paths
(`/farms/1`, `/farms/2`, ...) would never hit a ceiling. The Redis key is
therefore `rate:{ip}`.

Budgets, all measured over a 60s sliding window:
  - auth paths  : 10 requests / IP   (brute-force ceiling)
  - general     : 120 requests / IP
  - authenticated: 300 requests / subject, tracked separately as
    `rate:user:{sub}` so a shared NAT egress IP does not make the per-account
    budget unreachable, and an unauthenticated caller cannot inflate it.

The in-memory fallback uses the same two-bucket shape, so degrading to a
single process never *weakens* the limit.
"""

import itertools
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)

_seq = itertools.count()

WINDOW_SECONDS = 60
GENERAL_LIMIT = 120
AUTH_LIMIT = 10
USER_LIMIT = 300
AUTH_PATH_MARKER = "/auth"
PROFILE_TTL = 300.0  # evict a client bucket this long after its last request


class RateLimiter:
    def __init__(self, redis_client: Any | None = None, max_buckets: int = 50_000) -> None:
        self._redis = redis_client
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._memory_user: dict[str, deque[float]] = defaultdict(deque)
        self._memory_lock = threading.Lock()
        self.max_buckets = max_buckets

    def check(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        if self._redis is not None:
            try:
                return self._check_redis(ip, path, user_id)
            except Exception as exc:
                logger.warning("Redis rate limit failed, using memory: %s", exc)
                self._redis = None
        return self._check_memory(ip, path, user_id)

    def _check_redis(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        now = time.time()
        ip_key = f"rate:{ip}"
        count = self._count(ip_key, now)

        if AUTH_PATH_MARKER in path and count >= AUTH_LIMIT:
            return False, WINDOW_SECONDS
        if user_id and self._count(f"rate:user:{user_id}", now) >= USER_LIMIT:
            return False, WINDOW_SECONDS
        if count >= GENERAL_LIMIT:
            return False, WINDOW_SECONDS

        self._touch(ip_key, now)
        if user_id:
            self._touch(f"rate:user:{user_id}", now)
        return True, 0

    def _check_memory(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        with self._memory_lock:
            now = time.time()
            self._evict_idle(now)

            # Fail closed at capacity. Evicting a *live* bucket to make room
            # would hand that caller a fresh budget, so an attacker rotating
            # addresses could buy extra quota simply by rotating — the cap
            # would become the loophole. Refusing to mint an identity we cannot
            # track keeps memory bounded without granting anything.
            if ip not in self._memory and len(self._memory) >= self.max_buckets:
                return False, WINDOW_SECONDS
            if (
                user_id is not None
                and user_id not in self._memory_user
                and len(self._memory_user) >= self.max_buckets
            ):
                return False, WINDOW_SECONDS

            count = self._prune(self._memory[ip], now)

            if AUTH_PATH_MARKER in path and count >= AUTH_LIMIT:
                return False, WINDOW_SECONDS
            if user_id and self._prune(self._memory_user[user_id], now) >= USER_LIMIT:
                return False, WINDOW_SECONDS
            if count >= GENERAL_LIMIT:
                return False, WINDOW_SECONDS

            self._memory[ip].append(now)
            if user_id:
                self._memory_user[user_id].append(now)
            return True, 0

    def _count(self, key: str, now: float) -> int:
        """Requests already recorded for `key` inside the window."""
        assert self._redis is not None
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        pipe.zcard(key)
        return int(pipe.execute()[1])

    def _touch(self, key: str, now: float) -> None:
        # The member must be unique per request while the *score* stays the
        # timestamp that drives the sliding window. Keying the member on the raw
        # clock collapses concurrent requests into one entry: time.time() has
        # only ~15.6ms resolution on Windows, so a burst of requests lands on a
        # single member and the limiter undercounts (a fast caller walks past
        # the ceiling). A monotonic suffix keeps every request distinct.
        member = f"{now!r}:{next(_seq)}"
        assert self._redis is not None
        pipe = self._redis.pipeline()
        pipe.zadd(key, {member: now})
        pipe.expire(key, WINDOW_SECONDS + 1)
        pipe.execute()

    @staticmethod
    def _prune(bucket: deque[float], now: float) -> int:
        while bucket and now - bucket[0] > WINDOW_SECONDS:
            bucket.popleft()
        return len(bucket)

    def _evict_idle(self, now: float) -> None:
        """Drop buckets that have gone quiet.

        Keys are client addresses, so an attacker rotating them would otherwise
        add one permanent deque per address; the resident set must track active
        callers, not lifetime traffic.
        """
        for store in (self._memory, self._memory_user):
            stale = [k for k, dq in store.items() if not dq or now - dq[-1] > PROFILE_TTL]
            for k in stale:
                store.pop(k, None)


rate_limiter = RateLimiter()
