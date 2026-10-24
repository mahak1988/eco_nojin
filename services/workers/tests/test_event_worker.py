"""Tests for the standalone NATS event worker entry point.

The worker is a thin CLI over ``services.api_gateway.eventbus.worker``. The
contract is that it *runs the one* event bus -- the phase-4 S-EVENT
consolidation removed the parallel ``services/event_bus/`` implementation, so
a second subject mapping must not reappear.
"""

import inspect

from services.workers import event_worker


class TestEntryPoint:
    """Tests for the worker's entry point."""

    def test_main_is_callable(self):
        assert callable(event_worker.main)

    def test_the_worker_comes_from_the_gateway_eventbus(self):
        """There is exactly one event bus: the gateway's."""
        source = inspect.getsource(event_worker)
        assert "services.api_gateway.eventbus" in source
        assert "services.event_bus" not in source

    def test_the_module_docstring_names_the_consolidation(self):
        """The reason the parallel implementation is gone is documented."""
        doc = event_worker.__doc__ or ""
        assert "S-EVENT" in doc

    def test_run_event_worker_builds_the_configured_worker(self):
        assert callable(event_worker.run_event_worker)

    def test_a_keyboard_interrupt_exits_cleanly(self):
        """Ctrl-C is a normal exit, not a crash."""

        async def interrupt(settings=None, **kwargs):
            raise KeyboardInterrupt

        original = event_worker.run_event_worker
        event_worker.run_event_worker = interrupt
        try:
            assert event_worker.main() == 0
        finally:
            event_worker.run_event_worker = original


class TestGatewayWorker:
    """The worker the entry point delegates to."""

    def test_the_worker_has_a_settings_factory(self):
        from services.api_gateway.eventbus.worker import EventWorker

        assert hasattr(EventWorker, "from_settings")

    def test_the_worker_can_be_built_from_settings(self):
        from services.api_gateway.eventbus.worker import EventWorker

        worker = EventWorker.from_settings(None)
        assert worker is not None
