"""NATS JetStream event consumer."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

try:
    import nats
except ImportError:
    nats = None

from .config import EventBusConfig


logger = logging.getLogger(__name__)
EventHandler = Callable[..., Awaitable[None] | None]


def _require_nats() -> Any:
    if nats is None:
        raise RuntimeError("NATS support is required; install the eventbus extra")
    return nats


def decode_message(message: Any) -> tuple[str, Any]:
    """Decode a NATS message into ``(event_type, payload)``."""
    subject = str(getattr(message, "subject", ""))
    data = getattr(message, "data", message)
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    if isinstance(data, bytearray):
        data = bytes(data).decode("utf-8")
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, dict) and data.get("event_type"):
        return str(data["event_type"]), data.get("payload", data)
    if not subject:
        raise ValueError("message has no event subject")
    event_type = subject.rsplit(".", 1)[-1]
    return event_type, data


def _message_positional_count(handler: EventHandler) -> int | None:
    try:
        parameters = inspect.signature(handler).parameters.values()
    except (TypeError, ValueError):
        return None
    count = 0
    for parameter in parameters:
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            count += 1
        elif parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            return 3
    return count


async def _invoke_handler(
    handler: EventHandler,
    event_type: str,
    payload: Any,
    message: Any,
) -> Any:
    count = _message_positional_count(handler)
    event = {"event_type": event_type, "payload": payload}
    if count == 3:
        result = handler(event_type, payload, message)
    elif count == 2:
        result = handler(event_type, payload)
    elif count == 1:
        result = handler(event)
    elif count == 0:
        result = handler()
    else:
        try:
            result = handler(event_type, payload, message)
        except TypeError:
            try:
                result = handler(event_type, payload)
            except TypeError:
                result = handler(event)
    if inspect.isawaitable(result):
        return await result
    return result


async def _ack(message: Any) -> None:
    ack = getattr(message, "ack", None)
    if ack is None:
        return
    result = ack()
    if inspect.isawaitable(result):
        await result


async def _nak(message: Any, delay: float | None = None) -> None:
    nak = getattr(message, "nak", None)
    if nak is None:
        return
    try:
        result = nak(delay=delay) if delay is not None else nak()
    except TypeError:
        result = nak()
    if inspect.isawaitable(result):
        await result


class EventConsumer:
    """JetStream subscription and message acknowledgement helper."""

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
        self._tasks: set[asyncio.Task[Any]] = set()

    @property
    def client(self) -> Any:
        return self._client

    @property
    def jetstream(self) -> Any:
        return self._jetstream

    async def connect(self) -> "EventConsumer":
        """Connect to NATS and obtain a JetStream context."""
        if self._client is not None and not bool(getattr(self._client, "is_closed", False)):
            if self._jetstream is None:
                self._jetstream = self._client.jetstream()
            return self
        nats_client = _require_nats()
        options: dict[str, Any] = {
            "servers": list(self.config.servers),
            "name": "econojin-consumer",
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

    async def subscribe(
        self,
        subject: str | None = None,
        *,
        durable: str | None = None,
        stream: str | None = None,
        queue: str | None = None,
    ) -> Any:
        """Subscribe to the configured event subject and return the subscription."""
        if self._jetstream is None:
            await self.connect()
        target = subject or f"{self.config.subject_prefix.rstrip('.')}.>"
        options: dict[str, Any] = {"stream": stream or self.config.stream}
        if durable or self.config.durable_consumer:
            options["durable"] = durable or self.config.durable_consumer
        if queue or self.config.consumer_queue:
            options["queue"] = queue or self.config.consumer_queue
        return await self._jetstream.subscribe(target, **options)

    async def start(
        self,
        handler: EventHandler,
        subject: str | None = None,
        *,
        durable: str | None = None,
        stream: str | None = None,
        queue: str | None = None,
    ) -> asyncio.Task[None]:
        """Start consuming messages in a tracked background task."""
        subscription = await self.subscribe(
            subject,
            durable=durable,
            stream=stream,
            queue=queue,
        )
        task = asyncio.create_task(self.consume(subscription, handler))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def consume(
        self,
        subscription: Any,
        handler: EventHandler,
        *,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """Deliver messages to a handler until the subscription or stop event ends."""
        messages = getattr(subscription, "messages", None)
        if messages is not None:
            async for message in messages:
                await self.handle_message(message, handler)
                if stop_event is not None and stop_event.is_set():
                    break
            return

        fetch = getattr(subscription, "fetch", None)
        if fetch is None:
            raise TypeError("subscription supports neither messages nor fetch")
        while stop_event is None or not stop_event.is_set():
            messages_batch = await fetch(batch=1, timeout=1.0)
            if not messages_batch:
                await asyncio.sleep(0.1)
                continue
            for message in messages_batch:
                await self.handle_message(message, handler)

    async def handle_message(self, message: Any, handler: EventHandler) -> None:
        """Decode, dispatch, and acknowledge one message."""
        try:
            event_type, payload = decode_message(message)
            await _invoke_handler(handler, event_type, payload, message)
        except Exception:
            logger.exception("Event consumer failed for %s", getattr(message, "subject", "unknown"))
            await _nak(message)
            return
        await _ack(message)

    async def close(self) -> None:
        """Stop tracked consumers and close the NATS client."""
        tasks = list(self._tasks)
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
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


async def consume_events(
    handler: EventHandler,
    *,
    config: EventBusConfig | None = None,
    settings: Any = None,
    stop_event: asyncio.Event | None = None,
    **kwargs: Any,
) -> None:
    """Consume events until ``stop_event`` is set or the subscription ends."""
    consumer = EventConsumer(config=config, settings=settings)
    subscription = await consumer.subscribe(**kwargs)
    task = asyncio.create_task(consumer.consume(subscription, handler, stop_event=stop_event))
    if stop_event is None:
        await task
    else:
        await stop_event.wait()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    await consumer.close()


JetStreamConsumer = EventConsumer
NATSJetStreamConsumer = EventConsumer

__all__ = [
    "EventConsumer",
    "JetStreamConsumer",
    "NATSJetStreamConsumer",
    "consume_events",
    "decode_message",
]
