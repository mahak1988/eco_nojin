"""Observability module - OpenTelemetry and Prometheus setup."""

from __future__ import annotations

from services.observability.setup import setup_observability, instrument_app

__all__ = [
    "setup_observability",
    "instrument_app",
]