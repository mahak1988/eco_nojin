"""OpenTelemetry and Prometheus observability setup."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Prometheus metrics - will be initialized if opentelemetry is available
ORDER_CREATED = None
PAYMENT_PROCESSED = None
ORDER_LATENCY = None
WALLET_BALANCE = None
OUTBOX_PENDING = None

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from prometheus_client import Counter, Gauge, Histogram, start_http_server

    OTEL_AVAILABLE = True

    # Prometheus metrics
    ORDER_CREATED = Counter(
        "eco_orders_created_total",
        "Total orders created",
        ["status", "payment_method"],
    )

    PAYMENT_PROCESSED = Counter(
        "eco_payments_processed_total",
        "Total payments processed",
        ["provider", "status"],
    )

    ORDER_LATENCY = Histogram(
        "eco_order_duration_seconds",
        "Order processing latency",
        ["operation"],
    )

    WALLET_BALANCE = Gauge(
        "eco_wallet_balance",
        "Current wallet balance",
        ["user_id"],
    )

    OUTBOX_PENDING = Gauge(
        "eco_outbox_pending",
        "Number of unprocessed outbox events",
    )

    OTEL_AVAILABLE = True

except ImportError:
    OTEL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("OpenTelemetry not available, observability features disabled")


def setup_observability(app, service_name: str = "eco-nojin-api"):
    """Setup OpenTelemetry and Prometheus for the application."""
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not installed, skipping observability setup")
        return

    # Resource
    resource = Resource.create({SERVICE_NAME: "eco-nojin-api"})

    # Tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    # If OTLP collector available:
    # trace.get_tracer_provider().add_span_processor(
    #     BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
    # )

    # Metrics
    prom_reader = PrometheusMetricReader()
    otlp_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://otel-collector:4317")
    )
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[prom_reader, otlp_reader])
    )

    # Auto-instrumentation
    # FastAPIInstrumentor.instrument_app(app)  # app passed from main
    SQLAlchemyInstrumentor().instrument(engine=hub.get_sqlalchemy_engine())
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()

    # Start Prometheus metrics server
    start_http_server(port=9464, addr="0.0.0.0")

    logger.info("Observability initialized: OTel + Prometheus on :9464/metrics")


def instrument_app(app):
    """Instrument FastAPI app with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except ImportError:
        logger.warning("OpenTelemetry FastAPI instrumentation not available")
