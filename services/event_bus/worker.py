"""Reusable NATS JetStream event worker."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from .config import EventBusConfig
from .consumer import EventConsumer
from .publisher import EventPublisher
from .retry import RetryPolicy, retry_or_term

logger = logging.getLogger(__name__)
EventHandler = Callable[..., Awaitable[None] | None]


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


class EventWorker:
    """Dispatch JetStream events to registered handlers with redelivery retries."""

    def __init__(
        self,
        config: EventBusConfig | None = None,
        *,
        consumer: EventConsumer | None = None,
        publisher: EventPublisher | None = None,
        retry_policy: RetryPolicy | None = None,
        handlers: Mapping[str, EventHandler] | None = None,
        settings: Any = None,
    ) -> None:
        self.config = config or EventBusConfig.from_settings(settings)
        self.retry_policy = retry_policy or RetryPolicy(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_base_delay,
            max_delay=self.config.retry_max_delay,
        )
        self.consumer = consumer
        self.publisher = publisher
        self._owns_consumer = consumer is None
        self._owns_publisher = publisher is None
        self._handlers: dict[str, EventHandler] = dict(handlers or {})
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    @classmethod
    def from_settings(
        cls,
        settings: Any = None,
        *,
        handlers: Mapping[str, EventHandler] | None = None,
        **kwargs: Any,
    ) -> EventWorker:
        config = EventBusConfig.from_settings(settings)
        return cls(
            config=config,
            retry_policy=RetryPolicy.from_settings(settings),
            handlers=handlers,
            **kwargs,
        )

    def register(self, event_type: str, handler: EventHandler) -> EventWorker:
        """Register a handler for an exact event type."""
        self._handlers[event_type] = handler
        return self

    register_handler = register

    def unregister(self, event_type: str) -> None:
        self._handlers.pop(event_type, None)

    @property
    def handlers(self) -> Mapping[str, EventHandler]:
        return self._handlers

    async def handle_event(
        self,
        event_type: str,
        payload: Any,
        message: Any = None,
    ) -> Any:
        """Invoke the handler registered for an event type."""
        handler = self._handlers.get(event_type) or self._handlers.get("*")
        if handler is None:
            raise KeyError(f"no event handler registered for {event_type}")
        return await _invoke_handler(handler, event_type, payload, message)

    async def process_message(self, message: Any) -> None:
        """Decode and process one JetStream message."""
        from .consumer import decode_message

        try:
            event_type, payload = decode_message(message)
        except Exception as exc:
            logger.exception("Unable to decode event message")
            await retry_or_term(
                message,
                exc,
                policy=self.retry_policy,
                publisher=self.publisher,
            )
            return

        handler = self._handlers.get(event_type) or self._handlers.get("*")
        if handler is None:
            logger.warning("No handler registered for event %s", event_type)
            await _ack(message)
            return

        try:
            await self.handle_event(event_type, payload, message)
        except Exception as exc:
            logger.exception("Event handler failed for %s", event_type)
            await retry_or_term(
                message,
                exc,
                policy=self.retry_policy,
                publisher=self.publisher,
            )
            return
        await _ack(message)

    async def run(
        self,
        *,
        subject: str | None = None,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """Consume events until the subscription ends or stop_event is set."""
        if self.consumer is None:
            self.consumer = EventConsumer(config=self.config)
        subscription = await self.consumer.subscribe(
            subject or f"{self.config.subject_prefix.rstrip('.')}.>",
            durable=self.config.durable_consumer,
            stream=self.config.stream,
            queue=self.config.consumer_queue,
        )
        messages = getattr(subscription, "messages", None)
        if messages is None:
            raise TypeError("JetStream subscription does not expose a messages iterator")
        async for message in messages:
            await self.process_message(message)
            if stop_event is not None and stop_event.is_set():
                break

    async def start(self) -> asyncio.Task[None]:
        """Start the worker loop in the current event loop."""
        if self._task is not None and not self._task.done():
            return self._task
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self.run(stop_event=self._stop_event))
        return self._task

    async def stop(self) -> None:
        """Request worker shutdown and wait for its loop to stop."""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        self._task = None

    async def close(self) -> None:
        """Stop the loop and close clients owned by this worker."""
        await self.stop()
        if self._owns_consumer and self.consumer is not None:
            await self.consumer.close()
        if self._owns_publisher and self.publisher is not None:
            await self.publisher.close()

    run_forever = run


async def run_worker(
    settings: Any = None,
    *,
    handlers: Mapping[str, EventHandler] | None = None,
    **kwargs: Any,
) -> None:
    """Run a configured worker with optional handler registrations."""
    worker = EventWorker.from_settings(settings, handlers=handlers)
    await worker.run(**kwargs)


EventBusWorker = EventWorker
NATSJetStreamWorker = EventWorker

__all__ = [
    "EventBusWorker",
    "EventWorker",
    "NATSJetStreamWorker",
    "run_worker",
]
