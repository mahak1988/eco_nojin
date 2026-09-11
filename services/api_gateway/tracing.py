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
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": "econojin-api"})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry tracing configured")
    except ImportError:
        logger.info("OpenTelemetry not installed, tracing disabled")
    except Exception as exc:
        logger.warning("Tracing setup failed: %s", exc)
