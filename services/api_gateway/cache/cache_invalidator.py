"""
Cache Invalidator via Redis Pub/Sub
=====================================

Cross-instance cache invalidation using Redis pub/sub.
Supports tag-based, pattern-based, and key-based invalidation.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Set, Callable, Awaitable, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from services.api_gateway.cache.redis_cache import CacheConfig, RedisCache
from services.api_gateway.observability.structured_logger import get_logger

logger = get_logger(__name__)


class InvalidationType(Enum):
    """Types of invalidation."""

    KEY = "key"  # Single key
    TAG = "tag"  # By tag
    PATTERN = "pattern"  # By key pattern
    ALL = "all"  # Clear all


@dataclass
class InvalidationMessage:
    """Invalidation message for pub/sub."""

    type: InvalidationType
    payload: str  # key, tag, or pattern
    source_instance: str  # Instance ID that originated invalidation
    timestamp: float


class CacheInvalidator:
    """
    Cross-instance cache invalidator using Redis pub/sub.

    Features:
    - Tag-based invalidation (most common)
    - Pattern-based invalidation (prefix matching)
    - Key-based invalidation
    - Cross-instance propagation via Redis pub/sub
    - Local L1 cache coordination
    """

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        instance_id: Optional[str] = None,
    ):
        self.config = config or CacheConfig()
        self.instance_id = instance_id or f"instance-{id(self)}"
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._channel = f"{self.config.key_prefix}invalidation"
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._handlers: Dict[InvalidationType, List[Callable[[str], Awaitable[None]]]] = {
            InvalidationType.KEY: [],
            InvalidationType.TAG: [],
            InvalidationType.PATTERN: [],
            InvalidationType.ALL: [],
        }
        self._l1_caches: List[Any] = []  # Registered L1 caches

    @property
    def client(self) -> redis.Redis | None:
        return self._client

    async def start(self) -> None:
        """Start the invalidator."""
        if self._running:
            return
        if not self.config.redis_url:
            logger.info("Cache invalidator disabled: redis_url is empty")
            return

        try:
            self._pool = ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=5,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            self._pubsub = self._client.pubsub()
            await self._pubsub.subscribe(self._channel)
            self._running = True
            self._listener_task = asyncio.create_task(self._listen())
            logger.info("Cache invalidator started", instance=self.instance_id, channel=self._channel)
        except Exception as exc:
            logger.warning("Cache invalidator start failed, continuing without Redis", error=str(exc))
            await self._close_connections()

    async def _close_connections(self) -> None:
        if self._pubsub:
            try:
                await self._pubsub.close()
            except Exception:
                pass
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
        if self._pool:
            try:
                await self._pool.disconnect()
            except Exception:
                pass
        self._pubsub = None
        self._client = None
        self._pool = None

    async def stop(self) -> None:
        """Stop the invalidator."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        await self._close_connections()
        logger.info("Cache invalidator stopped", instance=self.instance_id)

    def register_l1_cache(self, l1_cache: Any) -> None:
        """Register an L1 cache for invalidation."""
        self._l1_caches.append(l1_cache)

    def register_handler(
        self,
        invalidation_type: InvalidationType,
        handler: Callable[[str], Awaitable[None]],
    ) -> None:
        """Register a handler for specific invalidation type."""
        self._handlers[invalidation_type].append(handler)

    async def _listen(self) -> None:
        """Listen for invalidation messages."""
        try:
            async for message in self._pubsub.listen():
                if not self._running:
                    break
                if message["type"] == "message":
                    await self._handle_message(message["data"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Invalidation listener error", error=str(e))

    async def _handle_message(self, data: str) -> None:
        """Handle incoming invalidation message."""
        try:
            msg_data = json.loads(data)
            msg = InvalidationMessage(
                type=InvalidationType(msg_data["type"]),
                payload=msg_data["payload"],
                source_instance=msg_data["source_instance"],
                timestamp=msg_data["timestamp"],
            )

            # Ignore messages from ourselves
            if msg.source_instance == self.instance_id:
                return

            logger.debug(
                "Received invalidation",
                type=msg.type.value,
                payload=msg.payload,
                source=msg.source_instance,
            )

            # Execute handlers
            handlers = self._handlers.get(msg.type, [])
            for handler in handlers:
                try:
                    await handler(msg.payload)
                except Exception as e:
                    logger.error("Handler error", type=msg.type.value, error=str(e))

            # Invalidate local L1 caches
            await self._invalidate_local_l1(msg.type, msg.payload)

        except Exception as e:
            logger.error("Invalidation message handling error", error=str(e))

    async def _invalidate_local_l1(self, inv_type: InvalidationType, payload: str) -> int:
        """Invalidate local L1 caches."""
        invalidated = 0
        for l1_cache in self._l1_caches:
            try:
                if inv_type == InvalidationType.KEY:
                    invalidated += int(l1_cache.delete(payload))
                elif inv_type == InvalidationType.TAG:
                    keys = list(l1_cache.get_by_tag(payload))
                    for key in keys:
                        l1_cache.delete(key)
                    invalidated += len(keys)
                elif inv_type == InvalidationType.PATTERN:
                    import fnmatch

                    keys = list(getattr(l1_cache, "keys", lambda: l1_cache._cache.keys())())
                    for key in keys:
                        if fnmatch.fnmatch(key, payload):
                            l1_cache.delete(key)
                            invalidated += 1
                elif inv_type == InvalidationType.ALL:
                    before = len(getattr(l1_cache, "_cache", {}))
                    l1_cache.clear()
                    invalidated += before
            except Exception as exc:
                logger.error("L1 invalidation error", error=str(exc))
        return invalidated

    # --- Public Invalidation Methods ---

    async def invalidate_key(self, key: str) -> bool:
        """Invalidate a single key across all instances."""
        await self._invalidate_local_l1(InvalidationType.KEY, key)
        message = InvalidationMessage(
            type=InvalidationType.KEY,
            payload=key,
            source_instance=self.instance_id,
            timestamp=time.time(),
        )
        await self._publish(message)
        return True

    async def invalidate_tag(self, tag: str) -> int:
        """Invalidate all keys with a tag across all instances."""
        local_count = await self._invalidate_local_l1(InvalidationType.TAG, tag)
        message = InvalidationMessage(
            type=InvalidationType.TAG,
            payload=tag,
            source_instance=self.instance_id,
            timestamp=time.time(),
        )
        await self._publish(message)
        return local_count + 1

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern across all instances."""
        local_count = await self._invalidate_local_l1(InvalidationType.PATTERN, pattern)
        message = InvalidationMessage(
            type=InvalidationType.PATTERN,
            payload=pattern,
            source_instance=self.instance_id,
            timestamp=time.time(),
        )
        await self._publish(message)
        return local_count + 1

    async def invalidate_all(self) -> bool:
        """Invalidate all cache entries across all instances."""
        await self._invalidate_local_l1(InvalidationType.ALL, "*")
        message = InvalidationMessage(
            type=InvalidationType.ALL,
            payload="*",
            source_instance=self.instance_id,
            timestamp=time.time(),
        )
        await self._publish(message)
        return True

    async def _publish(self, message: InvalidationMessage) -> None:
        """Publish invalidation message to Redis channel."""
        if not self._client:
            return
        data = json.dumps(
            {
                "type": message.type.value,
                "payload": message.payload,
                "source_instance": message.source_instance,
                "timestamp": message.timestamp,
            }
        )
        await self._client.publish(self._channel, data)

    # --- Utility Methods ---

    async def get_stats(self) -> Dict[str, Any]:
        """Get invalidator statistics."""
        return {
            "instance_id": self.instance_id,
            "channel": self._channel,
            "running": self._running,
            "registered_l1_caches": len(self._l1_caches),
            "handlers": {t.value: len(h) for t, h in self._handlers.items()},
        }


class CacheWarmer:
    """
    Cache warming utility for pre-populating cache.

    Usage:
        warmer = CacheWarmer(cache)
        await warmer.warm(
            keys=["key1", "key2"],
            loader=lambda k: fetch_data(k),
            concurrency=10
        )
    """

    def __init__(self, cache: Any, max_concurrency: int = 10):
        self.cache = cache
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def warm(
        self,
        keys: List[str],
        loader: Callable[[str], Awaitable[Any]],
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        skip_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Warm cache for multiple keys concurrently.

        Args:
            keys: List of cache keys to warm
            loader: Async function to load data for a key
            ttl: TTL for cached entries
            tags: Tags for cache entries
            skip_existing: Skip keys that already exist

        Returns:
            Dict with results: {"warmed": int, "skipped": int, "errors": int}
        """
        results = {"warmed": 0, "skipped": 0, "errors": 0}

        async def warm_key(key: str):
            async with self.semaphore:
                try:
                    if skip_existing and await self.cache.exists(key):
                        results["skipped"] += 1
                        return
                    value = await loader(key)
                    await self.cache.set(key, value, ttl=ttl, tags=tags)
                    results["warmed"] += 1
                except Exception as e:
                    logger.error("Cache warming error", key=key, error=str(e))
                    results["errors"] += 1

        await asyncio.gather(*[warm_key(k) for k in keys])
        logger.info("Cache warming completed", **results)
        return results


class CacheHealthChecker:
    """Health checker for cache system."""

    def __init__(self, cache: Any, invalidator: Optional[CacheInvalidator] = None):
        self.cache = cache
        self.invalidator = invalidator

    async def check_health(self) -> Dict[str, Any]:
        """Check health of cache system."""
        results = {
            "healthy": True,
            "checks": {},
        }

        # Check L2 connectivity
        try:
            start = time.time()
            await self.cache.l2.client.ping()
            latency = (time.time() - start) * 1000
            results["checks"]["redis"] = {
                "healthy": True,
                "latency_ms": round(latency, 2),
            }
        except Exception as e:
            results["healthy"] = False
            results["checks"]["redis"] = {
                "healthy": False,
                "error": str(e),
            }

        # Check L1 cache
        try:
            test_key = "__health_check__"
            await self.cache.set(test_key, "ok", ttl=10)
            value = await self.cache.get(test_key)
            await self.cache.delete(test_key)
            results["checks"]["l1_l2"] = {
                "healthy": value == "ok",
            }
        except Exception as e:
            results["healthy"] = False
            results["checks"]["l1_l2"] = {
                "healthy": False,
                "error": str(e),
            }

        # Check invalidator
        if self.invalidator:
            try:
                stats = await self.invalidator.get_stats()
                results["checks"]["invalidator"] = {
                    "healthy": stats["running"],
                    "stats": stats,
                }
            except Exception as e:
                results["healthy"] = False
                results["checks"]["invalidator"] = {
                    "healthy": False,
                    "error": str(e),
                }

        return results
