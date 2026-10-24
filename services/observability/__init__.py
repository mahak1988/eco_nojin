"""Observability module - OpenTelemetry and Prometheus setup."""

from __future__ import annotations

from services.observability.setup import instrument_app, setup_observability

__all__ = [
    "instrument_app",
    "setup_observability",
]
