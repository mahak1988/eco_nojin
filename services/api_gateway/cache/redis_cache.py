"""
Redis Cache Layer with L1/L2, Tags, and Invalidation
=====================================================

Multi-level caching with:
- L1: In-memory (fast, limited size)
- L2: Redis (distributed, persistent)
- Tag-based invalidation
- Pub/sub invalidation across instances
- TTL with jitter
"""

import asyncio
import builtins
import hashlib
import json
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from services.api_gateway.observability.structured_logger import get_logger, log_cache_operation

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache layer."""

    redis_url: str = "redis://localhost:6379/0"
    l1_max_size: int = 1000  # Max entries in L1
    l1_ttl: int = 60  # L1 TTL in seconds
    l2_ttl: int = 3600  # L2 TTL in seconds
    default_ttl: int = 300  # Default TTL
    ttl_jitter: float = 0.1  # 10% jitter
    key_prefix: str = "econojin:"
    tag_separator: str = ":tag:"
    pool_size: int = 10
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    created_at: float
    expires_at: float
    tags: set[str] = field(default_factory=set)
    hits: int = 0


class L1Cache:
    """In-memory L1 cache with LRU eviction."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []  # LRU tracking

    def get(self, key: str) -> CacheEntry | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            self._evict(key)
            return None
        # Update LRU
        self._access_order.remove(key)
        self._access_order.append(key)
        entry.hits += 1
        return entry

    def set(self, key: str, entry: CacheEntry) -> None:
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            self._evict_lru()
        self._cache[key] = entry
        self._access_order.append(key)

    def delete(self, key: str) -> bool:
        if key in self._cache:
            self._evict(key)
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()
        self._access_order.clear()

    def _evict(self, key: str) -> None:
        self._cache.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_lru(self) -> None:
        if self._access_order:
            lru_key = self._access_order.pop(0)
            self._cache.pop(lru_key, None)

    def get_by_tag(self, tag: str) -> list[str]:
        """Get all keys with a specific tag."""
        return [
            key
            for key, entry in self._cache.items()
            if tag in entry.tags and time.time() <= entry.expires_at
        ]


class RedisCache:
    """Redis-backed L2 cache with tagging and pub/sub invalidation."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._pool: ConnectionPool | None = None
        self._client: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._tag_channel = f"{config.key_prefix}tags"
        self._invalidation_handlers: list[Callable[[str], Awaitable[None]]] = []

    async def connect(self) -> None:
        """Initialize Redis connection pool and pub/sub."""
        self._pool = ConnectionPool.from_url(
            self.config.redis_url,
            max_connections=self.config.pool_size,
            socket_timeout=self.config.socket_timeout,
            socket_connect_timeout=self.config.socket_connect_timeout,
            decode_responses=True,
        )
        self._client = redis.Redis(connection_pool=self._pool)

        # Setup pub/sub for cross-instance invalidation
        self._pubsub = self._client.pubsub()
        await self._pubsub.subscribe(self._tag_channel)
        asyncio.create_task(self._listen_invalidations())

        logger.info("Redis cache connected", url=self.config.redis_url)

    async def close(self) -> None:
        """Close connections."""
        if self._pubsub:
            await self._pubsub.unsubscribe(self._tag_channel)
            await self._pubsub.close()
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

    async def _listen_invalidations(self) -> None:
        """Listen for invalidation messages from other instances."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    tag = message["data"]
                    await self._handle_invalidation(tag)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Invalidation listener error", error=str(e))

    async def _handle_invalidation(self, tag: str) -> None:
        """Handle invalidation from another instance."""
        for handler in self._invalidation_handlers:
            try:
                await handler(tag)
            except Exception as e:
                logger.error("Invalidation handler error", tag=tag, error=str(e))

    def register_invalidation_handler(self, handler: Callable[[str], Awaitable[None]]) -> None:
        """Register a handler for invalidation events."""
        self._invalidation_handlers.append(handler)

    def _make_key(self, key: str) -> str:
        return f"{self.config.key_prefix}{key}"

    def _make_tag_key(self, tag: str) -> str:
        return f"{self.config.key_prefix}tag:{tag}"

    def _add_jitter(self, ttl: int) -> int:
        jitter = int(ttl * self.config.ttl_jitter * random.uniform(-1, 1))
        return max(1, ttl + jitter)

    async def get(self, key: str) -> CacheEntry | None:
        """Get value from Redis."""
        redis_key = self._make_key(key)
        data = await self._client.get(redis_key)
        if data is None:
            return None

        try:
            entry_data = json.loads(data)
            entry = CacheEntry(
                value=entry_data["value"],
                created_at=entry_data["created_at"],
                expires_at=entry_data["expires_at"],
                tags=set(entry_data.get("tags", [])),
                hits=entry_data.get("hits", 0),
            )
            if time.time() > entry.expires_at:
                await self.delete(key)
                return None
            entry.hits += 1
            # Update hits in Redis (async, fire-and-forget)
            asyncio.create_task(self._increment_hits(key))
            return entry
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None

    async def _increment_hits(self, key: str) -> None:
        """Increment hit counter in Redis."""
        try:
            redis_key = self._make_key(key)
            data = await self._client.get(redis_key)
            if data:
                entry_data = json.loads(data)
                entry_data["hits"] = entry_data.get("hits", 0) + 1
                await self._client.set(redis_key, json.dumps(entry_data))
        except Exception:
            pass  # Best effort

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: set[str] | None = None,
    ) -> None:
        """Set value in Redis with optional tags."""
        ttl = ttl or self.config.default_ttl
        ttl = self._add_jitter(ttl)
        expires_at = time.time() + ttl

        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
            tags=tags or set(),
        )

        redis_key = self._make_key(key)
        entry_data = {
            "value": entry.value,
            "created_at": entry.created_at,
            "expires_at": entry.expires_at,
            "tags": list(entry.tags),
            "hits": entry.hits,
        }

        await self._client.setex(redis_key, ttl, json.dumps(entry_data))

        # Index tags
        if tags:
            for tag in tags:
                tag_key = self._make_tag_key(tag)
                await self._client.sadd(tag_key, key)
                await self._client.expire(tag_key, ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        redis_key = self._make_key(key)
        # Get tags before deletion
        data = await self._client.get(redis_key)
        if data:
            try:
                entry_data = json.loads(data)
                tags = entry_data.get("tags", [])
                for tag in tags:
                    tag_key = self._make_tag_key(tag)
                    await self._client.srem(tag_key, key)
            except Exception:
                pass

        result = await self._client.delete(redis_key)
        return result > 0

    async def invalidate_tag(self, tag: str) -> int:
        """Invalidate all keys with a specific tag."""
        tag_key = self._make_tag_key(tag)
        keys = await self._client.smembers(tag_key)
        if not keys:
            return 0

        # Delete all keys
        redis_keys = [self._make_key(k) for k in keys]
        if redis_keys:
            await self._client.delete(*redis_keys)

        # Clear tag index
        await self._client.delete(tag_key)

        # Publish invalidation to other instances
        await self._client.publish(self._tag_channel, tag)

        logger.info("Tag invalidated", tag=tag, count=len(keys))
        return len(keys)

    async def get_keys_by_tag(self, tag: str) -> builtins.set[str]:
        """Get all keys for a tag."""
        tag_key = self._make_tag_key(tag)
        return await self._client.smembers(tag_key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self._client.exists(self._make_key(key)) > 0

    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        return await self._client.ttl(self._make_key(key))

    async def clear_all(self) -> int:
        """Clear all cache entries (use with caution)."""
        pattern = f"{self.config.key_prefix}*"
        keys = []
        async for key in self._client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self._client.delete(*keys)
        return 0


class MultiLevelCache:
    """Multi-level cache combining L1 (memory) and L2 (Redis)."""

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self.l1 = L1Cache(self.config.l1_max_size)
        self.l2 = RedisCache(self.config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize L2 Redis connection."""
        if not self._initialized:
            await self.l2.connect()
            # Register L1 invalidation handler
            self.l2.register_invalidation_handler(self._on_l2_invalidation)
            self._initialized = True

    async def close(self) -> None:
        await self.l2.close()

    async def _on_l2_invalidation(self, tag: str) -> None:
        """Handle invalidation from L2 (other instances)."""
        keys = self.l1.get_by_tag(tag)
        for key in keys:
            self.l1.delete(key)
        logger.debug("L1 invalidated by tag", tag=tag, count=len(keys))

    def _make_l1_entry(self, value: Any, ttl: int, tags: set[str]) -> CacheEntry:
        return CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=time.time() + ttl,
            tags=tags,
        )

    async def get(self, key: str) -> Any | None:
        """Get value from cache (L1 -> L2)."""
        start_time = time.time()

        # Try L1 first
        l1_entry = self.l1.get(key)
        if l1_entry:
            log_cache_operation(
                logger, "get", key, hit=True, duration_ms=(time.time() - start_time) * 1000
            )
            return l1_entry.value

        # Try L2
        if not self._initialized:
            await self.initialize()

        l2_entry = await self.l2.get(key)
        if l2_entry:
            # Promote to L1
            l1_entry = CacheEntry(
                value=l2_entry.value,
                created_at=l2_entry.created_at,
                expires_at=l2_entry.expires_at,
                tags=l2_entry.tags,
                hits=l2_entry.hits,
            )
            self.l1.set(key, l1_entry)
            log_cache_operation(
                logger, "get", key, hit=True, duration_ms=(time.time() - start_time) * 1000
            )
            return l2_entry.value

        log_cache_operation(
            logger, "get", key, hit=False, duration_ms=(time.time() - start_time) * 1000
        )
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: set[str] | None = None,
    ) -> None:
        """Set value in both L1 and L2."""
        ttl = ttl or self.config.default_ttl
        tags = tags or set()

        l1_entry = self._make_l1_entry(value, self.config.l1_ttl, tags)
        self.l1.set(key, l1_entry)

        if not self._initialized:
            await self.initialize()
        await self.l2.set(key, value, ttl, tags)

    async def delete(self, key: str) -> bool:
        """Delete from both L1 and L2."""
        l1_deleted = self.l1.delete(key)
        if not self._initialized:
            await self.initialize()
        l2_deleted = await self.l2.delete(key)
        return l1_deleted or l2_deleted

    async def invalidate_tag(self, tag: str) -> int:
        """Invalidate all keys with a tag in both L1 and L2."""
        if not self._initialized:
            await self.initialize()

        # Invalidate in L2 (publishes to other instances)
        l2_count = await self.l2.invalidate_tag(tag)

        # Invalidate in local L1
        l1_keys = self.l1.get_by_tag(tag)
        for key in l1_keys:
            self.l1.delete(key)

        logger.info("Tag invalidated", tag=tag, l1_count=len(l1_keys), l2_count=l2_count)
        return len(l1_keys) + l2_count

    async def exists(self, key: str) -> bool:
        if self.l1.get(key):
            return True
        if not self._initialized:
            await self.initialize()
        return await self.l2.exists(key)

    async def clear(self) -> None:
        """Clear all caches."""
        self.l1.clear()
        if self._initialized:
            await self.l2.clear_all()

    # Convenience decorators
    def cached(
        self, ttl: int | None = None, tags: builtins.set[str] | None = None, key_prefix: str = ""
    ):
        """Decorator for caching function results."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()[:32]

                # Try cache
                cached = await self.get(cache_key)
                if cached is not None:
                    return cached

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await self.set(cache_key, result, ttl=ttl, tags=tags)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, run in executor
                import asyncio

                return asyncio.run(async_wrapper(*args, **kwargs))

            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator
