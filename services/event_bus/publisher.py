"""NATS JetStream event publisher."""

from __future__ import annotations

import inspect
import json
from typing import Any

try:
    import nats
except ImportError:
    nats = None

from .config import EventBusConfig


def _require_nats() -> Any:
    if nats is None:
        raise RuntimeError("NATS support is required; install the eventbus extra")
    return nats


def build_event(
    event_type: str,
    payload: Any,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the stable JSON envelope used on event subjects."""
    event = {"event_type": event_type, "payload": payload}
    if metadata:
        event["metadata"] = metadata
    return event


def encode_event(
    event_type: str,
    payload: Any,
    metadata: dict[str, Any] | None = None,
) -> bytes:
    """Serialize an event envelope for NATS."""
    return json.dumps(
        build_event(event_type, payload, metadata),
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")


def subject_for(event_type: str, config: EventBusConfig | None = None) -> str:
    """Return the configured subject for an event type."""
    return (config or EventBusConfig.from_settings()).subject_for(event_type)


class EventPublisher:
    """Small async JetStream publisher with lazy connection management."""

    def __init__(
        self,
        config: EventBusConfig | None = None,
        *,
        client: Any = None,
        jetstream: Any = None,
        settings: Any = None,
    ) -> None:
        self.config = config or EventBusConfig.from_settings(settings)
        self._client = client
        self._jetstream = jetstream

    @property
    def client(self) -> Any:
        return self._client

    @property
    def jetstream(self) -> Any:
        return self._jetstream

    async def connect(self) -> EventPublisher:
        """Connect to NATS and obtain a JetStream context."""
        if self._client is not None and not bool(getattr(self._client, "is_closed", False)):
            if self._jetstream is None:
                self._jetstream = self._client.jetstream()
            return self

        nats_client = _require_nats()
        options: dict[str, Any] = {
            "servers": list(self.config.servers),
            "name": "econojin-publisher",
            "connect_timeout": self.config.connect_timeout,
        }
        if self.config.token:
            options["token"] = self.config.token
        elif self.config.user:
            options["user"] = self.config.user
            if self.config.password:
                options["password"] = self.config.password

        self._client = await nats_client.connect(**options)
        self._jetstream = self._client.jetstream()
        return self

    async def ensure_stream(self, subjects: list[str] | tuple[str, ...] | None = None) -> None:
        """Ensure the configured stream exists without changing unrelated streams."""
        if self._jetstream is None:
            await self.connect()
        try:
            await self._jetstream.stream_info(self.config.stream)
        except Exception as exc:
            if "NotFound" not in exc.__class__.__name__:
                raise
            await self._jetstream.add_stream(
                name=self.config.stream,
                subjects=list(subjects or (f"{self.config.subject_prefix}.>",)),
            )

    async def publish(
        self,
        event_type: str,
        payload: Any,
        *,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> str:
        """Publish one JSON event and return its subject."""
        if self._jetstream is None:
            await self.connect()
        target_subject = subject or self.config.subject_for(event_type)
        options: dict[str, Any] = {}
        if headers is not None:
            options["headers"] = headers
        if timeout is not None:
            options["timeout"] = timeout
        await self._jetstream.publish(
            target_subject,
            encode_event(event_type, payload, metadata),
            **options,
        )
        return target_subject

    async def close(self) -> None:
        """Drain or close the underlying NATS client."""
        if self._client is None:
            return
        client = self._client
        self._client = None
        self._jetstream = None
        drain = getattr(client, "drain", None)
        close = getattr(client, "close", None)
        operation = drain or close
        if operation is None:
            return
        result = operation()
        if inspect.isawaitable(result):
            await result

    async def __aenter__(self) -> EventPublisher:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self.close()


async def publish_event(
    event_type: str,
    payload: Any,
    *,
    config: EventBusConfig | None = None,
    settings: Any = None,
    **kwargs: Any,
) -> str:
    """Publish one event using a short-lived publisher."""
    async with EventPublisher(config=config, settings=settings) as publisher:
        return await publisher.publish(event_type, payload, **kwargs)


JetStreamPublisher = EventPublisher
NATSJetStreamPublisher = EventPublisher

__all__ = [
    "EventPublisher",
    "JetStreamPublisher",
    "NATSJetStreamPublisher",
    "build_event",
    "encode_event",
    "publish_event",
    "subject_for",
]
