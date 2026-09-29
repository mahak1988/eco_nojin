"""Event worker: dispatch JetStream messages to registered handlers.

Moved here from ``services/event_bus/worker.py`` during the phase 4 S-EVENT
consolidation. ``services/api_gateway/eventbus/`` is the single stack; this
carries the handler-registry behaviour that the standalone worker process needs
and the manager's raw ``subscribe`` callback does not provide.

One behaviour was corrected in the move: an event with **no** registered
handler used to be ``ack``ed and discarded, so the worker silently drained and
threw away anything it did not recognise. S-EVENT requires ``nak`` in that
case — an unhandled event is a deployment mistake, not a message to throw away.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from .nats_client import NATSManager, get_or_create_nats_manager
from .retry import RetryPolicy, retry_or_term

logger = logging.getLogger("econojin.eventbus")

EventHandler = Callable[..., Awaitable[None] | None]
#: Handler for any event type with no specific registration.
CATCH_ALL = "*"


def _positional_count(handler: EventHandler) -> int | None:
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
        elif parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            return 3
    return count


async def _invoke(handler: EventHandler, event_type: str, payload: Any, message: Any) -> Any:
    """Call a handler with as many arguments as it accepts."""
    count = _positional_count(handler)
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
        result = handler(event_type, payload, message)
    if inspect.isawaitable(result):
        return await result
    return result


def _event_type_of(message: Any) -> str:
    """Read the event type, from the subject tail or a message header."""
    headers = getattr(message, "headers", None) or {}
    declared = headers.get("event-type") or headers.get("Event-Type")
    if declared:
        return str(declared)
    subject = getattr(message, "subject", "") or ""
    return subject.rsplit(".", 1)[-1]


class EventWorker:
    """Dispatch JetStream events to registered handlers, with retry and DLQ."""

    def __init__(
        self,
        manager: NATSManager | None = None,
        *,
        retry_policy: RetryPolicy | None = None,
        handlers: Mapping[str, EventHandler] | None = None,
        subject: str = ">",
    ) -> None:
        self._manager = manager
        self.retry_policy = retry_policy
        self.subject = subject
        self._handlers: dict[str, EventHandler] = dict(handlers or {})

    @classmethod
    def from_settings(
        cls,
        settings: Any = None,
        *,
        handlers: Mapping[str, EventHandler] | None = None,
        **kwargs: Any,
    ) -> EventWorker:
        """Build a worker. ``settings`` is accepted for call compatibility."""
        del settings
        return cls(handlers=handlers, **kwargs)

    @property
    def handlers(self) -> Mapping[str, EventHandler]:
        return self._handlers

    def register(self, event_type: str, handler: EventHandler) -> EventWorker:
        self._handlers[event_type] = handler
        return self

    register_handler = register

    def unregister(self, event_type: str) -> None:
        self._handlers.pop(event_type, None)

    def handler_for(self, event_type: str) -> EventHandler | None:
        return self._handlers.get(event_type) or self._handlers.get(CATCH_ALL)

    async def handle_event(self, event_type: str, payload: Any, message: Any = None) -> Any:
        handler = self.handler_for(event_type)
        if handler is None:
            raise KeyError(f"no event handler registered for {event_type}")
        return await _invoke(handler, event_type, payload, message)

    async def process_message(self, message: Any) -> None:
        """Decode and dispatch one JetStream message."""
        policy = self.retry_policy
        if policy is None and self._manager is not None:
            policy = RetryPolicy.from_config(self._manager.config)

        event_type = _event_type_of(message)
        try:
            payload = json.loads(message.data.decode("utf-8"))
        except Exception as exc:
            await retry_or_term(message, exc, policy=policy)
            return

        handler = self.handler_for(event_type)
        if handler is None:
            # nak, not ack: an unhandled event must stay visible instead of
            # being silently drained.
            logger.warning(
                "No handler registered for event %s; leaving it unacked for redelivery",
                event_type,
            )
            nak = getattr(message, "nak", None)
            if nak is not None:
                result = nak()
                if inspect.isawaitable(result):
                    await result
            return

        try:
            await self.handle_event(event_type, payload, message)
        except Exception as exc:
            logger.exception("Event handler failed for %s", event_type)
            publisher = self._manager._dead_letter if self._manager else None
            await retry_or_term(message, exc, policy=policy, publish_dead_letter=publisher)
            return

        ack = getattr(message, "ack", None)
        if ack is not None:
            result = ack()
            if inspect.isawaitable(result):
                await result

    async def run(self, *, stop_event: asyncio.Event | None = None) -> None:
        """Consume until the manager disconnects or ``stop_event`` is set."""
        manager = self._manager
        if manager is None:
            manager = await get_or_create_nats_manager()
            await manager.connect()
            self._manager = manager

        done = asyncio.Event()

        async def dispatch(payload: dict[str, Any], headers: dict[str, str]) -> None:
            message = _SyntheticMessage(headers=headers, payload=payload)
            await self.process_message(message)
            if stop_event is not None and stop_event.is_set():
                done.set()

        await manager.subscribe(self.subject, dispatch)
        await (stop_event.wait() if stop_event is not None else done.wait())

    async def close(self) -> None:
        if self._manager is not None:
            await self._manager.disconnect()


class _SyntheticMessage:
    """A message-shaped object for the callback-style dispatch path.

    ``NATSManager.subscribe`` passes the decoded payload to its callback rather
    than the JetStream message, so the ack/nak decision is made here.
    """

    def __init__(self, headers: dict[str, str], payload: Any) -> None:
        self.headers = headers
        self.payload = payload
        self.subject = headers.get("subject", "")
        self.acked = False
        self.nacked = False
        self.terminated = False

    @property
    def data(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    @property
    def metadata(self) -> Any:
        attempts = int(self.headers.get("Nats-Max-Delivered", "1") or 1)
        return type("Meta", (), {"num_delivered": attempts})()

    async def ack(self) -> None:
        self.acked = True

    async def nak(self, delay: float | None = None) -> None:
        del delay
        self.nacked = True

    async def term(self) -> None:
        self.terminated = True


async def run_worker(
    settings: Any = None,
    *,
    handlers: Mapping[str, EventHandler] | None = None,
    **kwargs: Any,
) -> None:
    """Run a worker with optional handler registrations."""
    worker = EventWorker.from_settings(settings, handlers=handlers)
    await worker.run(**kwargs)


# Historical aliases kept so existing call sites keep working.
EventBusWorker = EventWorker
NATSJetStreamWorker = EventWorker

__all__ = [
    "CATCH_ALL",
    "EventBusWorker",
    "EventHandler",
    "EventWorker",
    "NATSJetStreamWorker",
    "run_worker",
]
