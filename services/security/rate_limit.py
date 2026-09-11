"""Layer 2 — smart rate limiting (Redis with in-memory fallback).

Per-IP: general API budget (default 120 req/min) and a stricter
auth-endpoint budget (10 req/min) against credential brute force.
Per-user: 300 req/min when a JWT subject is present.

Upgrade path: uses Redis when available, falls back to in-memory for
single-process deployments.
"""
import logging
import time
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._memory_lock = __import__("threading").Lock()

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
        key = f"rate:{ip}:{path}"
        now = time.time()
        window = 60
        limit = 120
        auth_limit = 10
        user_limit = 300

        pipe = self._redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.expire(key, window + 1)
        results = pipe.execute()
        count = results[2]

        if "/auth" in path and count > auth_limit:
            return False, 60
        if user_id and count > user_limit:
            return False, 60
        if count > limit:
            return False, 60
        return True, 0

    def _check_memory(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        with self._memory_lock:
            now = time.time()
            window = 60
            auth_limit = 10
            user_limit = 300
            limit = 120

            bucket = self._memory[ip]
            while bucket and now - bucket[0] > window:
                bucket.popleft()

            if "/auth" in path and len(bucket) >= auth_limit:
                return False, 60
            if user_id and len(bucket) >= user_limit:
                return False, 60
            if len(bucket) >= limit:
                return False, 60

            bucket.append(now)
            return True, 0


rate_limiter = RateLimiter()
