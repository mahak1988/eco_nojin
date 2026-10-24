"""OpenTelemetry tracing setup for Eco Nojin."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def setup_tracing(app: Any) -> None:
    """Configure OpenTelemetry tracing for the FastAPI app."""
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        # Only attach the OTLP exporter when a collector endpoint is configured
        # explicitly. A hard-coded localhost fallback made the exporter retry
        # forever on machines without a collector, flooding logs (and breaking
        # test runs whose capture stream is closed while the worker thread logs).
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
        if not endpoint:
            try:
                from engine.hydroma.config.settings import get_settings

                endpoint = (
                    getattr(get_settings(), "otel_exporter_otlp_endpoint", "") or ""
                ).strip()
            except Exception:  # settings unavailable -> stay disabled
                endpoint = ""

        resource = Resource.create({"service.name": "econojin-api"})
        provider = TracerProvider(resource=resource)
        if endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            logger.info("OpenTelemetry tracing configured (endpoint=%s)", endpoint)
        else:
            logger.info("OpenTelemetry tracing disabled: no OTLP endpoint configured")

        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        logger.info("OpenTelemetry not installed, tracing disabled")
    except Exception as exc:
        logger.warning("Tracing setup failed: %s", exc)
