"""Retry policy and JetStream redelivery for the event bus.

Moved here from ``services/event_bus/retry.py`` during the phase 4 S-EVENT
consolidation, because this is the only implementation of the behaviour that
matters and the gateway stack was the one missing it.

The defect this fixes: ``NATSManager.subscribe`` used a bare
``await msg.nak()`` with no delay and no attempt cap, so a poison message was
redelivered at full speed until the consumer's ``max_deliver`` ran out. The
DLQ in ``dlq.py`` was never called from anywhere, so nothing was ever routed
to a dead letter. ``retry_or_term`` does the three things that are actually
required: back off, publish to the dead-letter subject once the attempts are
exhausted, then terminate the message so it stops being redelivered.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

logger = logging.getLogger("econojin.eventbus")

T = TypeVar("T")
Operation = Callable[..., T | Awaitable[T]]

#: Subject suffix for messages that exhausted their delivery attempts.
DEAD_LETTER_SUFFIX = "dead_letter"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential-backoff policy for JetStream message delivery."""

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError("retry delays cannot be negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay cannot be lower than base_delay")

    @classmethod
    def from_config(cls, config: Any) -> RetryPolicy:
        return cls(
            max_retries=config.max_retries,
            base_delay=config.retry_base_delay,
            max_delay=config.retry_max_delay,
            # Google SRE ch.22 and the AWS architecture blog both say
            # un-jittered exponential backoff is the clear loser: every
            # redelivery in a tight loop retries in lockstep and re-creates
            # the thundering herd the backoff was meant to break. There is no
            # reason to ship a retry loop that is measurably worse, so this
            # is on unless a caller explicitly turns it off.
            jitter=bool(getattr(config, "retry_jitter", True)),
        )

    def delay_for(self, retry_number: int) -> float:
        """Delay in seconds for a one-based retry number."""
        exponent = max(0, int(retry_number) - 1)
        delay = min(self.max_delay, self.base_delay * (2**exponent))
        if self.jitter and delay > 0:
            return random.uniform(delay / 2, delay)
        return delay

    def should_retry(self, attempt: int) -> bool:
        """Whether a one-based delivery attempt may be retried."""
        return max(0, int(attempt) - 1) < self.max_retries


def delivery_attempt(message: Any) -> int:
    """Read NATS's one-based delivery count from a message.

    Falls back to the headers nats-py sets, because a plain ``Msg`` (as used
    in tests and by the core API) exposes no ``metadata``.
    """
    metadata = getattr(message, "metadata", None)
    value = getattr(metadata, "num_delivered", None)
    if value is None:
        headers = getattr(message, "headers", None) or {}
        value = headers.get("Nats-Max-Delivered") or headers.get("Nats-Delivered")
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


def decode_payload(message: Any) -> Any:
    """Best-effort decode of a JetStream message body."""
    data = getattr(message, "data", message)
    if isinstance(data, (bytes, bytearray)):
        return json.loads(bytes(data).decode("utf-8"))
    return data


async def _nak(message: Any, delay: float | None = None) -> None:
    nak = getattr(message, "nak", None)
    if nak is None:
        return
    try:
        result = nak(delay=delay) if delay is not None else nak()
    except TypeError:
        # Older nats-py has no delay kwarg.
        result = nak()
    if inspect.isawaitable(result):
        await result


async def _term(message: Any) -> None:
    """Stop redelivery: ``term()`` where available, else ``ack()``."""
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
    publish_dead_letter: Callable[[str, dict[str, Any]], Any] | None = None,
    dead_letter_subject: str | None = None,
) -> None:
    """Back off and retry, or dead-letter then terminate.

    Args:
        message: The JetStream message that failed.
        error: The exception that caused the failure.
        policy: Attempt cap and backoff curve.
        publish_dead_letter: Coroutine taking ``(subject, payload)``. When
            omitted the message is still terminated, so it stops being
            redelivered, but the reason is only logged.
        dead_letter_subject: Overrides the derived subject.
    """
    retry_policy = policy or RetryPolicy()
    attempt = delivery_attempt(message)

    if retry_policy.should_retry(attempt):
        delay = retry_policy.delay_for(attempt)
        logger.warning(
            "Event delivery attempt %d/%d failed (%s); retrying in %.1fs",
            attempt,
            retry_policy.max_retries + 1,
            error,
            delay,
        )
        await _nak(message, delay)
        return

    payload: Any
    try:
        payload = decode_payload(message)
    except Exception:
        payload = {"raw": "<undecodable>"}

    subject = dead_letter_subject or DEAD_LETTER_SUFFIX
    if publish_dead_letter is not None:
        try:
            result = publish_dead_letter(
                subject,
                {
                    "original_subject": getattr(message, "subject", ""),
                    "error": str(error),
                    "delivery_attempt": attempt,
                    "payload": payload,
                },
            )
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("Failed to publish to the dead-letter subject")
    else:
        logger.error(
            "Dead-lettering %s after %d attempts with no publisher configured: %s",
            getattr(message, "subject", "<unknown>"),
            attempt,
            error,
        )

    await _term(message)


async def execute_with_retry[T](
    operation: Operation[T],
    *args: Any,
    policy: RetryPolicy | None = None,
    on_error: Callable[[Exception, int], Any] | None = None,
    sleep: Callable[[float], Any] = asyncio.sleep,
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
            sleep_result = sleep(retry_policy.delay_for(attempt + 1))
            if inspect.isawaitable(sleep_result):
                await sleep_result
    raise RuntimeError("retry loop exited unexpectedly")


__all__ = [
    "DEAD_LETTER_SUFFIX",
    "RetryPolicy",
    "decode_payload",
    "delivery_attempt",
    "execute_with_retry",
    "retry_or_term",
]
