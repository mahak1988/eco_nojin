"""S-EVENT contract tests: one stack, one subject rule, real dead-lettering.

The consolidation in phase 4 removed a second NATS stack and a dead DLQ
module. These tests pin the three properties that justified the deletion, so a
second stack or a bare ``nak`` cannot quietly come back.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from services.api_gateway.eventbus import (
    DEAD_LETTER_SUFFIX,
    NATSConfig,
    RetryPolicy,
    delivery_attempt,
    retry_or_term,
)

ROOT = Path(__file__).resolve().parents[2]


class TestSingleStack:
    def test_the_duplicate_stack_is_gone(self):
        assert not (ROOT / "services" / "event_bus").exists(), (
            "services/event_bus was removed in the S-EVENT consolidation; a second "
            "subject-naming implementation is exactly what it duplicated"
        )

    def test_the_dead_dlq_module_is_gone(self):
        assert not (ROOT / "services" / "api_gateway" / "eventbus" / "dlq.py").exists(), (
            "dlq.py implemented a dead-letter store nothing called; dead-lettering "
            "now happens in retry.retry_or_term"
        )

    def test_nothing_imports_the_old_package(self):
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "event_bus" in path.parts and "__pycache__" not in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "services.event_bus" in text:
                offenders.append(str(path.relative_to(ROOT)))
        assert not offenders, f"still importing the deleted stack: {offenders}"


class TestSingleSubjectRule:
    def test_subject_naming_is_a_method_not_an_inline_fstring(self):
        manager = object.__new__(type(ROOT))  # unused; keep the import graph honest
        del manager
        from services.api_gateway.eventbus.nats_client import NATSManager

        config = NATSConfig(
            url="nats://localhost:4222",
            servers="",
            user="",
            password="",
            token="",
            stream="ECONOJIN",
            subject_prefix="econojin.events",
            durable_consumer="econojin-workers",
            consumer_queue="",
            max_retries=5,
            retry_base_delay=1.0,
            retry_max_delay=60.0,
            max_deliver=5,
            connect_timeout=2.0,
        )
        nats_manager = NATSManager(config)
        assert nats_manager.subject_for("order.created") == "econojin.events.order.created"

    def test_subject_for_rejects_wildcards(self):
        from services.api_gateway.eventbus.nats_client import NATSManager

        config = NATSConfig(
            url="nats://x",
            servers="",
            user="",
            password="",
            token="",
            stream="S",
            subject_prefix="p",
            durable_consumer="d",
            consumer_queue="",
            max_retries=1,
            retry_base_delay=1.0,
            retry_max_delay=1.0,
            max_deliver=1,
            connect_timeout=1.0,
        )
        nats_manager = NATSManager(config)
        for bad in ("", "has space", "wild*", "gt>"):
            with pytest.raises(ValueError, match="non-empty NATS subject segment"):
                nats_manager.subject_for(bad)

    def test_publish_subscribe_request_all_use_the_method(self):
        source = (ROOT / "services" / "api_gateway" / "eventbus" / "nats_client.py").read_text(
            encoding="utf-8"
        )
        assert source.count("self.subject_for(") >= 3, (
            "publish, subscribe and request must all go through subject_for(); "
            "inlining the f-string is what allowed two naming rules to coexist"
        )
        assert 'f"{self.config.subject_prefix}.{subject}"' not in source


class TestRedeliveryIsNotBareNak:
    class _Msg:
        def __init__(self, attempt: int = 1) -> None:
            self.attempt = attempt
            self.nak_delay: float | None = "unset"
            self.acked = False
            self.terminated = False
            self.metadata = type("M", (), {"num_delivered": attempt})()

        async def nak(self, delay=None) -> None:
            self.nak_delay = delay

        async def ack(self) -> None:
            self.acked = True

        async def term(self) -> None:
            self.terminated = True

    @pytest.mark.asyncio
    async def test_a_retryable_failure_naks_with_backoff(self):
        msg = self._Msg(attempt=1)
        await retry_or_term(
            msg, ValueError("boom"), policy=RetryPolicy(max_retries=5, base_delay=2.0)
        )
        assert msg.nak_delay == 2.0
        assert not msg.terminated

    @pytest.mark.asyncio
    async def test_backoff_grows_then_saturates(self):
        policy = RetryPolicy(max_retries=10, base_delay=1.0, max_delay=8.0)
        assert [policy.delay_for(n) for n in range(1, 6)] == [1.0, 2.0, 4.0, 8.0, 8.0]

    @pytest.mark.asyncio
    async def test_an_exhausted_message_is_dead_lettered_then_terminated(self):
        """The behaviour the bare nak() never had."""
        msg = self._Msg(attempt=5)
        seen: list[tuple[str, dict]] = []

        async def publish(subject, payload):
            seen.append((subject, payload))

        await retry_or_term(
            msg,
            RuntimeError("poison"),
            policy=RetryPolicy(max_retries=3, base_delay=1.0),
            publish_dead_letter=publish,
        )
        assert seen, "an exhausted message must be published to the dead letter"
        subject, payload = seen[0]
        assert subject == DEAD_LETTER_SUFFIX
        assert payload["error"] == "poison"
        assert payload["delivery_attempt"] == 5
        assert msg.terminated
        assert msg.nak_delay == "unset"

    @pytest.mark.asyncio
    async def test_an_exhausted_message_is_terminated_even_without_a_publisher(self):
        msg = self._Msg(attempt=9)
        await retry_or_term(msg, RuntimeError("x"), policy=RetryPolicy(max_retries=1))
        assert msg.terminated

    def test_delivery_attempt_defaults_to_one(self):
        class Bare:
            pass

        assert delivery_attempt(Bare()) == 1

    def test_delivery_attempt_reads_the_header_fallback(self):
        class WithHeaders:
            headers: ClassVar[dict[str, str]] = {"Nats-Max-Delivered": "4"}

        assert delivery_attempt(WithHeaders()) == 4


class TestRedeliveryCeilingIsItsOwnKnob:
    def test_max_deliver_is_independent_of_publish_retries(self):
        """Previously ``max_deliver`` was wired to ``max_retries``."""
        from services.api_gateway.eventbus.nats_client import NATSConfig

        fields = set(NATSConfig.__dataclass_fields__)
        assert "max_deliver" in fields
        assert "max_retries" in fields

    def test_no_consumer_uses_the_publish_retry_knob(self):
        source = (ROOT / "services" / "api_gateway" / "eventbus" / "nats_client.py").read_text(
            encoding="utf-8"
        )
        consumer_block = source.split("async def _ensure_consumer", 1)[-1].split(
            "async def disconnect", 1
        )[0]
        assert "max_deliver=self.config.max_retries" not in consumer_block, (
            "consumer redelivery ceiling must come from max_deliver, not the publish retry count"
        )


class TestWorkerDoesNotDrainUnrecognisedEvents:
    @pytest.mark.asyncio
    async def test_an_unhandled_event_is_nacked_not_acked(self):
        from services.api_gateway.eventbus.worker import EventWorker, _SyntheticMessage

        worker = EventWorker()
        message = _SyntheticMessage(headers={"event-type": "nobody.listens"}, payload={"x": 1})
        await worker.process_message(message)
        assert message.nacked, (
            "an event with no handler used to be ack'd and discarded, so the worker "
            "silently drained anything it did not recognise"
        )
        assert not message.acked

    @pytest.mark.asyncio
    async def test_a_handled_event_is_acked(self):
        from services.api_gateway.eventbus.worker import EventWorker, _SyntheticMessage

        seen: list = []
        worker = EventWorker()
        # A one-argument handler receives the event envelope, per the
        # worker's documented arity contract.
        worker.register("order.created", lambda event: seen.append(event))
        message = _SyntheticMessage(headers={"event-type": "order.created"}, payload={"id": 7})
        await worker.process_message(message)
        assert message.acked
        assert seen == [{"event_type": "order.created", "payload": {"id": 7}}]

    @pytest.mark.asyncio
    async def test_a_two_argument_handler_receives_type_and_payload(self):
        from services.api_gateway.eventbus.worker import EventWorker, _SyntheticMessage

        seen: list = []
        worker = EventWorker()
        worker.register(
            "order.created", lambda event_type, payload: seen.append((event_type, payload))
        )
        message = _SyntheticMessage(headers={"event-type": "order.created"}, payload={"id": 8})
        await worker.process_message(message)
        assert seen == [("order.created", {"id": 8})]

    @pytest.mark.asyncio
    async def test_a_failing_handler_dead_letters_instead_of_acking(self):
        from services.api_gateway.eventbus.worker import EventWorker, _SyntheticMessage

        def boom(_payload):
            raise RuntimeError("handler failed")

        worker = EventWorker()
        worker.register("order.created", boom)
        message = _SyntheticMessage(
            headers={"event-type": "order.created", "Nats-Max-Delivered": "9"}, payload={}
        )
        await worker.process_message(message)
        assert not message.acked
        assert message.terminated, "a repeatedly failing handler must stop being redelivered"

    @pytest.mark.asyncio
    async def test_undecodable_payload_is_not_acked(self):
        from services.api_gateway.eventbus.worker import EventWorker

        class Broken:
            data = b"not json"
            headers: ClassVar[dict[str, str]] = {"event-type": "x"}

        message = Broken()
        await EventWorker().process_message(message)
        assert not getattr(message, "acked", False)
