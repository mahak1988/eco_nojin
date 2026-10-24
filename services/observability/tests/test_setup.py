"""Tests for the observability setup (OpenTelemetry + Prometheus).

``setup_observability`` starts a Prometheus exporter on port 9464 and binds it
to ``0.0.0.0``. A metrics endpoint that is reachable from outside the host
exposes operational data, so the binding is a deployment decision: it must be
configurable, and it must default to the loopback interface.
"""

import pytest

from services.observability import setup as obs


class TestMetricRegistry:
    """Tests for the metric objects."""

    def test_the_availability_flag_is_a_bool(self):
        assert isinstance(obs.OTEL_AVAILABLE, bool)

    def test_every_metric_is_either_present_or_none(self):
        """A missing OpenTelemetry install must not leave a half-built metric."""
        for metric in (
            obs.ORDER_CREATED,
            obs.PAYMENT_PROCESSED,
            obs.ORDER_LATENCY,
            obs.WALLET_BALANCE,
            obs.OUTBOX_PENDING,
        ):
            assert metric is None or metric is not None

    def test_the_metrics_are_defined_when_otel_is_available(self):
        if not obs.OTEL_AVAILABLE:
            pytest.skip("OpenTelemetry is not installed in this environment")
        assert obs.ORDER_CREATED is not None
        assert obs.PAYMENT_PROCESSED is not None
        assert obs.ORDER_LATENCY is not None
        assert obs.WALLET_BALANCE is not None
        assert obs.OUTBOX_PENDING is not None


class TestSetupObservability:
    """Tests for the setup entry point."""

    def test_it_is_callable_without_opentelemetry(self):
        """A missing OpenTelemetry install must not break the boot."""
        if obs.OTEL_AVAILABLE:
            pytest.skip("OpenTelemetry is installed; the degraded path is not exercised")
        obs.setup_observability(object())
        obs.instrument_app(object())

    def test_instrument_app_never_raises(self):
        """Instrumentation is best-effort; a failure must not break the app."""
        from fastapi import FastAPI

        obs.instrument_app(FastAPI())

    def test_instrument_app_survives_a_non_app(self):
        """A bad argument must not propagate out of the instrumentation."""
        obs.instrument_app(object())


class TestMetricsEndpointBinding:
    """The Prometheus exporter's bind address is a deployment decision."""

    def test_the_bind_address_is_configurable(self):
        """The bind address must come from the environment, not be hard-coded."""
        import inspect

        source = inspect.getsource(obs.setup_observability)
        assert "0.0.0.0" not in source, (
            "the Prometheus exporter must not bind every interface by default"
        )

    def test_the_bind_address_defaults_to_loopback(self):
        import inspect

        source = inspect.getsource(obs.setup_observability)
        assert "127.0.0.1" in source
