"""Tests: DuckDB analytics service + real NDVI alert rules (Phase 4)."""
import pytest

from services.analytics.duckdb_service import summarize_satellite_rows
from services.bots.core.alerts import (
    evaluate_rules,
    ndvi_alert_rules,
    satellite_row_to_metrics,
)


class FakeSatRow:
    """Minimal stand-in for a SQLAlchemy SatelliteAnalysis row."""

    def __init__(self, ndvi, data_source="simulated"):
        self.ndvi = ndvi
        self.evi = 0.3
        self.savi = 0.2
        self.data_source = data_source


# ---------------------------------------------------------------------------
# DuckDB summaries
# ---------------------------------------------------------------------------

def test_duckdb_summary_empty_rows():
    stats = summarize_satellite_rows([])
    assert stats["analyses"] == 0
    assert stats["ndvi_mean"] is None
    assert stats["real_data_count"] == 0


def test_duckdb_summary_with_rows():
    rows = [
        FakeSatRow(0.45, "copernicus"),
        FakeSatRow(0.55, "copernicus"),
        FakeSatRow(0.30, "simulated"),
    ]
    stats = summarize_satellite_rows(rows)
    assert stats["analyses"] == 3
    assert stats["real_data_count"] == 2
    assert stats["ndvi_mean"] == pytest.approx(0.4333, abs=1e-3)
    assert stats["ndvi_min"] == pytest.approx(0.30, abs=1e-3)
    assert stats["ndvi_max"] == pytest.approx(0.55, abs=1e-3)


def test_duckdb_summary_ignores_none_ndvi():
    rows = [FakeSatRow(None, "copernicus")]
    stats = summarize_satellite_rows(rows)
    assert stats["analyses"] == 1
    assert stats["ndvi_mean"] is None


# ---------------------------------------------------------------------------
# Real NDVI alert rules
# ---------------------------------------------------------------------------

def test_ndvi_rules_fire_on_real_data_only():
    rules = ndvi_alert_rules()
    real = satellite_row_to_metrics(FakeSatRow(0.20, "copernicus"))
    assert real is not None
    fired = evaluate_rules(rules, real)
    assert any(r.metric == "ndvi" and r.severity == "critical" for r in fired)


def test_ndvi_rules_never_fire_on_simulated():
    rules = ndvi_alert_rules()
    metrics = satellite_row_to_metrics(FakeSatRow(0.20, "simulated"))
    assert metrics is None  # gate: simulated rows produce no metrics
    assert evaluate_rules(rules, {}) == []


def test_ndvi_rules_healthy_vegetation_info():
    rules = ndvi_alert_rules()
    fired = evaluate_rules(rules, {"ndvi": 0.8})
    assert any(r.severity == "info" for r in fired)
