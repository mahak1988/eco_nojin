"""
NATS JetStream Client for Eco Nojin Event Bus
=============================================
Provides connection management, publish/subscribe helpers, and reconnection logic.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Optional

# NATS is an optional dependency (eventbus extra). The gateway must import
# cleanly without it; the failure is raised at connection time, never at import
# time.
try:
    import nats
    from nats.aio.client import Client as NATSClient
    from nats.js import JetStreamContext
    from nats.js.api import ConsumerConfig, StreamConfig
    from nats.js.errors import NotFoundError

    NATS_AVAILABLE = True
    _NATS_IMPORT_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - environment dependent
    NATS_AVAILABLE = False
    _NATS_IMPORT_ERROR = str(exc)
    nats = None  # type: ignore[assignment]
    NATSClient = Any  # type: ignore[misc,assignment]
    JetStreamContext = Any  # type: ignore[misc,assignment]
    ConsumerConfig = StreamConfig = Any  # type: ignore[misc,assignment]
    NotFoundError = Exception  # type: ignore[misc,assignment]


def _require_nats() -> Any:
    """Fail loudly (with remediation) instead of silently degrading."""
    if not NATS_AVAILABLE:
        raise RuntimeError(
            "NATS support is required for the event bus but the nats-py package "
            "is not installed ("
            + str(_NATS_IMPORT_ERROR)
            + "). Install the eventbus extra (pip install nats-py) or disable the event bus."
        )
    return nats

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.eventbus")


@dataclass
class NATSConfig:
    """NATS connection configuration from settings."""
    url: str
    servers: str
    user: str
    password: str
    token: str
    stream: str
    subject_prefix: str
    durable_consumer: str
    consumer_queue: str
    max_retries: int
    retry_base_delay: float
    retry_max_delay: float
    connect_timeout: float

    @classmethod
    def from_settings(cls) -> "NATSConfig":
        settings = get_settings()
        return cls(
            url=settings.nats_url,
            servers=settings.nats_servers,
            user=settings.nats_user,
            password=settings.nats_password,
            token=settings.nats_token,
            stream=settings.nats_stream,
            subject_prefix=settings.nats_subject_prefix,
            durable_consumer=settings.nats_durable_consumer,
            consumer_queue=settings.nats_consumer_queue,
            max_retries=settings.nats_max_retries,
            retry_base_delay=settings.nats_retry_base_delay,
            retry_max_delay=settings.nats_retry_max_delay,
            connect_timeout=settings.nats_connect_timeout,
        )


class NATSManager:
    """Manages NATS connection, JetStream context, and stream/consumer setup."""

    def __init__(self, config: Optional[NATSConfig] = None):
        self.config = config or NATSConfig.from_settings()
        self._nc: Optional[NATSClient] = None
        self._js: Optional[JetStreamContext] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._subscriptions: list = []

    @property
    def nc(self) -> Optional[NATSClient]:
        return self._nc

    @property
    def js(self) -> Optional[JetStreamContext]:
        return self._js

    @property
    def is_connected(self) -> bool:
        return self._connected and self._nc is not None and not self._nc.is_closed

    async def connect(self) -> None:
        """Establish NATS connection with JetStream."""
        if self.is_connected:
            return

        try:
            servers = [self.config.url]
            if self.config.servers:
                servers = [s.strip() for s in self.config.servers.split(",")]

            connect_options = {
                "servers": servers,
                "connect_timeout": self.config.connect_timeout,
                "max_reconnect_attempts": self.config.max_retries,
                "reconnect_time_wait": self.config.retry_base_delay,
            }

            if self.config.user and self.config.password:
                connect_options["user"] = self.config.user
                connect_options["password"] = self.config.password
            elif self.config.token:
                connect_options["token"] = self.config.token

            self._nc = await nats.connect(**connect_options)
            self._js = self._nc.jetstream()
            self._connected = True

            logger.info(f"✅ NATS connected to {servers}, stream: {self.config.stream}")

            # Setup stream and consumer
            await self._ensure_stream()
            await self._ensure_consumer()

        except Exception as e:
            self._connected = False
            logger.error(f"❌ NATS connection failed: {e}")
            raise

    async def _ensure_stream(self) -> None:
        """Create or update the JetStream stream."""
        try:
            await self._js.add_stream(
                StreamConfig(
                    name=self.config.stream,
                    subjects=[f"{self.config.subject_prefix}.>"],
                    retention="limits",
                    max_age=86400 * 7,  # 7 days
                    max_msgs=10_000_000,
                    max_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
                    storage="file",
                    replicas=1,
                )
            )
            logger.info(f"✅ JetStream stream '{self.config.stream}' ready")
        except NotFoundError:
            # Stream doesn't exist, create it
            await self._js.add_stream(
                StreamConfig(
                    name=self.config.stream,
                    subjects=[f"{self.config.subject_prefix}.>"],
                    retention="limits",
                    max_age=86400 * 7,
                    max_msgs=10_000_000,
                    max_bytes=10 * 1024 * 1024 * 1024,
                    storage="file",
                    replicas=1,
                )
            )
            logger.info(f"✅ JetStream stream '{self.config.stream}' created")
        except Exception as e:
            # Stream might already exist with different config
            logger.warning(f"Stream config check: {e}")

    async def _ensure_consumer(self) -> None:
        """Create or update the durable consumer."""
        try:
            await self._js.add_consumer(
                self.config.stream,
                ConsumerConfig(
                    durable_name=self.config.durable_consumer,
                    filter_subject=f"{self.config.subject_prefix}.>",
                    ack_policy="explicit",
                    ack_wait=30,
                    max_deliver=self.config.max_retries,
                    replay_policy="instant",
                    deliver_policy="all",
                ),
            )
            logger.info(f"✅ Durable consumer '{self.config.durable_consumer}' ready")
        except NotFoundError:
            await self._js.add_consumer(
                self.config.stream,
                ConsumerConfig(
                    durable_name=self.config.durable_consumer,
                    filter_subject=f"{self.config.subject_prefix}.>",
                    ack_policy="explicit",
                    ack_wait=30,
                    max_deliver=self.config.max_retries,
                    replay_policy="instant",
                    deliver_policy="all",
                )
            )
            logger.info(f"✅ Durable consumer '{self.config.durable_consumer}' created")
        except Exception as e:
            logger.warning(f"Consumer config check: {e}")

    async def disconnect(self) -> None:
        """Gracefully disconnect from NATS."""
        self._connected = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        self._subscriptions.clear()

        if self._nc and not self._nc.is_closed:
            await self._nc.drain()
            logger.info("✅ NATS disconnected gracefully")

    async def publish(
        self,
        subject: str,
        payload: dict[str, Any],
        headers: Optional[dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish a message to JetStream with acknowledgment."""
        if not self.is_connected:
            logger.warning("NATS not connected, cannot publish")
            return False

        full_subject = f"{self.config.subject_prefix}.{subject}"

        message_headers = {
            "content-type": "application/json",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if correlation_id:
            message_headers["correlation-id"] = correlation_id
        if headers:
            message_headers.update(headers)

        try:
            ack = await self._js.publish(
                full_subject,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers=message_headers,
            )
            logger.debug(
                f"Published to {full_subject}: stream={ack.stream}, seq={ack.seq}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {full_subject}: {e}")
            return False

    async def publish_with_retry(
        self,
        subject: str,
        payload: dict[str, Any],
        headers: Optional[dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        """Publish with exponential backoff retry."""
        last_error = None
        for attempt in range(max_retries):
            if await self.publish(subject, payload, headers, correlation_id):
                return True
            last_error = f"Attempt {attempt + 1} failed"
            if attempt < max_retries - 1:
                delay = min(
                    self.config.retry_base_delay * (2**attempt),
                    self.config.retry_max_delay,
                )
                logger.warning(f"Publish retry {attempt + 1}/{max_retries} after {delay}s: {last_error}")
                await asyncio.sleep(delay)
        logger.error(f"Publish failed after {max_retries} attempts: {last_error}")
        return False

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[dict[str, Any], dict[str, str]], None],
        durable_name: Optional[str] = None,
        queue: Optional[str] = None,
    ) -> None:
        """Subscribe to a subject with a callback."""
        if not self.is_connected:
            raise RuntimeError("NATS not connected")

        full_subject = f"{self.config.subject_prefix}.{subject}"

        async def message_handler(msg):
            try:
                payload = json.loads(msg.data.decode("utf-8"))
                headers = dict(msg.headers) if msg.headers else {}
                await callback(payload, headers)
                await msg.ack()
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                await msg.nak()

        try:
            if durable_name:
                sub = await self._js.subscribe(
                    full_subject,
                    cb=message_handler,
                    durable=durable_name,
                    queue=queue or self.config.consumer_queue,
                )
            else:
                sub = await self._js.subscribe(
                    full_subject,
                    cb=message_handler,
                    queue=queue or self.config.consumer_queue,
                )
            self._subscriptions.append(sub)
            logger.info(f"✅ Subscribed to {full_subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {full_subject}: {e}")
            raise

    async def request(
        self,
        subject: str,
        payload: dict[str, Any],
        timeout: float = 5.0,
    ) -> Optional[dict[str, Any]]:
        """Send a request and wait for response (request-reply pattern)."""
        if not self.is_connected:
            raise RuntimeError("NATS not connected")

        full_subject = f"{self.config.subject_prefix}.{subject}"

        try:
            msg = await self._nc.request(
                full_subject,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=timeout,
            )
            return json.loads(msg.data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Request to {full_subject} failed: {e}")
            return None


# Global NATS manager instance
_nats_manager: Optional[NATSManager] = None


def get_nats_manager() -> NATSManager:
    """Get or create the global NATS manager."""
    global _nats_manager
    if _nats_manager is None:
        _nats_manager = NATSManager()
    return _nats_manager


async def init_nats() -> NATSManager:
    """Initialize NATS connection (call during app startup)."""
    manager = get_nats_manager()
    await manager.connect()
    return manager


async def shutdown_nats() -> None:
    """Shutdown NATS connection (call during app shutdown)."""
    global _nats_manager
    if _nats_manager:
        await _nats_manager.disconnect()
        _nats_manager = None


@asynccontextmanager
async def nats_lifespan():
    """Async context manager for NATS lifecycle."""
    manager = await init_nats()
    try:
        yield manager
    finally:
        await shutdown_nats()