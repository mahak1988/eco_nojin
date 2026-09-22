"""Retry policy and JetStream redelivery helpers."""

from __future__ import annotations

import asyncio
import inspect
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from .config import EventBusConfig
from .consumer import decode_message


T = TypeVar("T")
Operation = Callable[..., T | Awaitable[T]]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential-backoff policy for JetStream message delivery."""

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = False

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError("retry delays cannot be negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay cannot be lower than base_delay")

    @classmethod
    def from_settings(cls, settings: Any = None) -> "RetryPolicy":
        config = EventBusConfig.from_settings(settings)
        return cls(
            max_retries=config.max_retries,
            base_delay=config.retry_base_delay,
            max_delay=config.retry_max_delay,
        )

    def delay_for(self, retry_number: int) -> float:
        """Return delay in seconds for a one-based retry number."""
        exponent = max(0, int(retry_number) - 1)
        delay = min(self.max_delay, self.base_delay * (2**exponent))
        if self.jitter and delay > 0:
            return random.uniform(delay / 2, delay)
        return delay

    def should_retry(self, delivery_attempt: int) -> bool:
        """Return whether a one-based delivery attempt may be retried."""
        return max(0, int(delivery_attempt) - 1) < self.max_retries


async def execute_with_retry(
    operation: Operation[T],
    *,
    policy: RetryPolicy | None = None,
    on_error: Callable[[Exception, int], Any] | None = None,
    sleep: Callable[[float], Any] = asyncio.sleep,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute an operation with exponential backoff."""
    retry_policy = policy or RetryPolicy()
    for attempt in range(retry_policy.max_retries + 1):
        try:
            result = operation(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except Exception as exc:
            if attempt >= retry_policy.max_retries:
                raise
            if on_error is not None:
                callback = on_error(exc, attempt + 1)
                if inspect.isawaitable(callback):
                    await callback
            delay = retry_policy.delay_for(attempt + 1)
            sleep_result = sleep(delay)
            if inspect.isawaitable(sleep_result):
                await sleep_result
    raise RuntimeError("retry loop exited unexpectedly")


def retry_async(
    policy: RetryPolicy | None = None,
    *,
    max_retries: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    jitter: bool = False,
) -> Callable[[Operation[T]], Operation[T]]:
    """Decorator form of :func:`execute_with_retry`."""
    retry_policy = policy or RetryPolicy(
        max_retries=5 if max_retries is None else max_retries,
        base_delay=1.0 if base_delay is None else base_delay,
        max_delay=60.0 if max_delay is None else max_delay,
        jitter=jitter,
    )

    def decorator(operation: Operation[T]) -> Operation[T]:
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            return await execute_with_retry(operation, policy=retry_policy, *args, **kwargs)

        return wrapped

    return decorator


def delivery_attempt(message: Any) -> int:
    """Read NATS's one-based delivery count from a message."""
    metadata = getattr(message, "metadata", None)
    value = getattr(metadata, "num_delivered", None)
    if value is None:
        headers = getattr(message, "headers", None) or {}
        value = headers.get("Nats-Max-Delivered") or headers.get("Nats-Delivered")
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


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


async def _term(message: Any) -> None:
    term = getattr(message, "term", None)
    if term is not None:
        result = term()
        if inspect.isawaitable(result):
            await result
        return
    ack = getattr(message, "ack", None)
    if ack is not None:
        result = ack()
        if inspect.isawaitable(result):
            await result


async def retry_or_term(
    message: Any,
    error: Exception,
    *,
    policy: RetryPolicy | None = None,
    publisher: Any = None,
    dead_letter_subject: str | None = None,
) -> None:
    """Nak for a retryable failure or terminate/publish a poison message."""
    retry_policy = policy or RetryPolicy.from_settings()
    attempt = delivery_attempt(message)
    if retry_policy.should_retry(attempt):
        await _nak(message, retry_policy.delay_for(attempt))
        return

    if publisher is not None:
        try:
            event_type, payload = decode_message(message)
        except Exception:
            event_type, payload = "event_bus.dead_letter", {
                "subject": getattr(message, "subject", ""),
                "error": str(error),
            }
        publisher_config = getattr(publisher, "config", None)
        prefix = getattr(publisher_config, "subject_prefix", "econojin.events")
        target = dead_letter_subject or f"{prefix}.dead_letter"
        await publisher.publish(
            event_type,
            payload,
            subject=target,
            metadata={"error": str(error), "delivery_attempt": attempt},
        )
    await _term(message)


RetryConfig = RetryPolicy

__all__ = [
    "RetryConfig",
    "RetryPolicy",
    "delivery_attempt",
    "execute_with_retry",
    "retry_async",
    "retry_or_term",
]
