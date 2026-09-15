"""Redis-backed rate limiter with in-memory fallback."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Rate limiter that prefers Redis, falls back to in-memory."""

    def __init__(
        self,
        redis_client: Any | None = None,
        limit: int = 120,
        window: int = 60,
        auth_limit: int = 10,
        user_limit: int = 300,
    ) -> None:
        self._redis = redis_client
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._memory_lock = __import__("threading").Lock()
        self._limit = limit
        self._window = window
        self._auth_limit = auth_limit
        self._user_limit = user_limit

    def check(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        if self._redis is not None:
            try:
                return self._check_redis(ip, path, user_id)
            except Exception as exc:
                logger.warning("Redis rate limit check failed, falling back to memory: %s", exc)
                self._redis = None
        return self._check_memory(ip, path, user_id)

    def _check_redis(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        key = f"rate:{ip}:{path}"
        now = time.time()
        window = self._window
        limit = self._limit
        auth_limit = self._auth_limit
        user_limit = self._user_limit

        pipe = self._redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.expire(key, window + 1)
        results = pipe.execute()
        count = results[2]

        is_credential = path.rstrip('/').endswith(('/login', '/register', '/forgot-password', '/reset-password', '/refresh'))
        if is_credential and count > auth_limit:
            return False, window
        if user_id and count > user_limit:
            return False, window
        if count > limit:
            return False, window
        return True, 0

    def _check_memory(self, ip: str, path: str, user_id: str | None = None) -> tuple[bool, int]:
        with self._memory_lock:
            now = time.time()
            window = self._window
            limit = self._limit
            auth_limit = self._auth_limit
            user_limit = self._user_limit

            # Bucket is keyed by (client, path) so that distinct endpoints
            # (e.g. the ~13 profile reads fired on mount) do not share one
            # global budget and trip each other. Credential endpoints keep a
            # tighter per-path budget to slow brute force.
            bucket_key = f"{ip}:{path}"
            bucket = self._memory[bucket_key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()

            is_credential = path.rstrip('/').endswith(('/login', '/register', '/forgot-password', '/reset-password', '/refresh'))
            if is_credential and len(bucket) >= auth_limit:
                return False, window
            if user_id and len(bucket) >= user_limit:
                return False, window
            if len(bucket) >= limit:
                return False, window

            bucket.append(now)
            return True, 0
