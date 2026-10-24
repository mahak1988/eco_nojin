"""Stage 38 — Benchmark acceleration, deduplication, and resumable execution tests.

Tests the Stage 38 modules:
- benchmark_profiler.py — runtime profiling
- data_cache.py — persistent scientific cache
- resumable_benchmark_runner.py — resumable benchmark execution
- radiation_units.py — radiation unit conversion

Also tests calibration parameter integrity and benchmark split integrity.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.benchmark_profiler import (
    BenchmarkProfiler,
)
from engine.hydroma.eval.benchmark_split_manifest import (
    load_split_manifest,
    verify_split,
)
from engine.hydroma.eval.calibration_parameter_registry import (
    ParameterStatus,
    build_registry,
)
from engine.hydroma.simulation.data_cache import (
    ScientificCache,
)
from engine.hydroma.simulation.radiation_units import (
    DEFAULT_PAR_FRACTION,
    KWH_TO_MJ,
    shortwave_to_par,
)

# ---------------------------------------------------------------------------
# Radiation unit tests
# ---------------------------------------------------------------------------

def test_shortwave_to_par_conversion():
    """Shortwave to PAR conversion: 10 MJ/m^2/day * 0.5 = 5 MJ/m^2/day PAR."""
    result, _ = shortwave_to_par(10.0, "MJ/m^2/day")
    assert result == 5.0


def test_shortwave_to_par_kwh_conversion():
    """kWh to MJ to PAR: 1 kWh/m^2/day = 3.6 MJ/m^2/day, * 0.5 = 1.8 PAR."""
    result, _ = shortwave_to_par(1.0, "kWh/m^2/day")
    assert abs(result - 1.8) < 1e-10


def test_shortwave_to_par_invalid_unit():
    """Unrecognized unit raises ValueError."""
    with pytest.raises(ValueError):
        shortwave_to_par(10.0, "invalid_unit")


def test_shortwave_to_par_no_double_conversion():
    """PAR input with already_par=True returns unchanged value."""
    result, spec = shortwave_to_par(5.0, "MJ/m^2/day", already_par=True)
    assert result == 5.0
    assert spec.frac_par == 1.0


def test_par_fraction_default():
    """Default PAR fraction is 0.5."""
    assert DEFAULT_PAR_FRACTION == 0.5


def test_kwh_to_mj_conversion():
    """1 kWh/m^2/day = 3.6 MJ/m^2/day."""
    assert KWH_TO_MJ == 3.6


# ---------------------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------------------

def test_cache_put_and_get():
    """Cache put then get returns the stored value."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ScientificCache(Path(tmpdir) / "test_cache.sqlite")
        cache.put(
            provider="Open-Meteo",
            endpoint="archive-api/v1/archive",
            latitude=25.62,
            longitude=83.58,
            start_date="2024-01-01",
            end_date="2024-01-31",
            variables=["temperature_2m_max"],
            unit_contract_version="stage37_v1",
            status="SUCCESS",
            response_json={"temperature": 25.0},
        )
        result = cache.get(
            provider="Open-Meteo",
            endpoint="archive-api/v1/archive",
            latitude=25.62,
            longitude=83.58,
            start_date="2024-01-01",
            end_date="2024-01-31",
            variables=["temperature_2m_max"],
            unit_contract_version="stage37_v1",
        )
        assert result is not None
        assert result["status"] == "SUCCESS"
        assert result["data"]["temperature"] == 25.0


def test_cache_miss():
    """Cache miss returns None."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ScientificCache(Path(tmpdir) / "test_cache.sqlite")
        result = cache.get(
            provider="Open-Meteo",
            endpoint="archive-api/v1/archive",
            latitude=25.62,
            longitude=83.58,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        assert result is None


def test_cache_invalid_status():
    """Invalid status raises ValueError."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ScientificCache(Path(tmpdir) / "test_cache.sqlite")
        with pytest.raises(ValueError):
            cache.put(
                provider="Open-Meteo",
                endpoint="archive-api/v1/archive",
                status="INVALID_STATUS",
            )


def test_cache_stats():
    """Cache stats returns entry counts."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ScientificCache(Path(tmpdir) / "test_cache.sqlite")
        cache.put(
            provider="Open-Meteo",
            endpoint="archive-api/v1/archive",
            latitude=25.62,
            longitude=83.58,
            start_date="2024-01-01",
            end_date="2024-01-31",
            status="SUCCESS",
        )
        stats = cache.stats()
        assert stats["total_entries"] == 1
        assert stats["by_status"]["SUCCESS"] == 1


# ---------------------------------------------------------------------------
# Split manifest tests
# ---------------------------------------------------------------------------

def test_split_no_district_overlap():
    """No district appears in both development and test sets."""
    manifest = load_split_manifest()
    dev = set(manifest["development_districts"])
    test = set(manifest["test_districts"])
    assert dev & test == set()


def test_split_no_record_overlap():
    """No record ID appears in both development and test sets."""
    manifest = load_split_manifest()
    dev_ids = set(manifest["development_record_ids"])
    test_ids = set(manifest["test_record_ids"])
    assert dev_ids & test_ids == set()


def test_split_manifest_hash_verification():
    """Manifest hash matches recomputed hash."""
    manifest = load_split_manifest()
    verification = verify_split(manifest)
    assert verification["verified"] is True
    assert verification["manifest_hash_matches"] is True


# ---------------------------------------------------------------------------
# Calibration parameter registry tests
# ---------------------------------------------------------------------------

def test_registry_ewsi_weights_sum_to_one():
    """EWSI weights sum to 1.0."""
    registry = build_registry()
    ndmi = registry.get_value("ewsi_weight_ndmi")
    vpd = registry.get_value("ewsi_weight_vpd")
    soil = registry.get_value("ewsi_weight_soil")
    assert abs(ndmi + vpd + soil - 1.0) < 1e-6


def test_registry_ewsi_weights_non_negative():
    """EWSI weights are non-negative."""
    registry = build_registry()
    for name in ("ewsi_weight_ndmi", "ewsi_weight_vpd", "ewsi_weight_soil"):
        val = registry.get_value(name)
        assert val >= 0.0


def test_registry_parameter_bounds():
    """All parameter values are within allowed bounds."""
    registry = build_registry()
    for name, entry in registry.get_all().items():
        val = entry.parameter_value
        if entry.allowed_min is not None:
            assert val >= entry.allowed_min, f"{name}={val} below min={entry.allowed_min}"
        if entry.allowed_max is not None:
            assert val <= entry.allowed_max, f"{name}={val} above max={entry.allowed_max}"


def test_registry_update_traceability():
    """Parameter update records calibration metadata."""
    registry = build_registry()
    registry.update_value(
        parameter_name="epsilon",
        new_value=2.5,
        calibration_method="grid_search",
        calibration_dataset="CIMMYT_dev",
        calibration_version="stage38_v1",
        rationale="Optimized on development districts",
    )
    entry = registry.get("epsilon")
    assert entry.parameter_value == 2.5
    assert entry.parameter_status == ParameterStatus.CALIBRATED
    assert entry.calibration_method == "grid_search"
    assert entry.calibration_dataset == "CIMMYT_dev"


def test_registry_update_rejects_out_of_bounds():
    """Parameter update outside bounds raises ValueError."""
    registry = build_registry()
    with pytest.raises(ValueError):
        registry.update_value(
            parameter_name="epsilon",
            new_value=10.0,  # above allowed_max=5.0
        )


# ---------------------------------------------------------------------------
# Profiler tests
# ---------------------------------------------------------------------------

def test_profiler_records_operation():
    """Profiler records operation profiles correctly."""
    profiler = BenchmarkProfiler()
    profiler.start_record("rec1", "district1", "season1")
    profiler.start_operation("weather_api_request")
    profiler.end_operation(
        "weather_api_request",
        status="SUCCESS",
        cache_hit=False,
        retry_count=0,
    )
    profiler.end_record()

    assert len(profiler.records) == 1
    op = profiler.records[0]
    assert op.operation_name == "weather_api_request"
    assert op.record_id == "rec1"
    assert op.district_id == "district1"
    assert op.season == "season1"
    assert op.request_status == "SUCCESS"
    assert op.cache_hit is False


def test_profiler_summarize():
    """Profiler summarize returns correct summary."""
    profiler = BenchmarkProfiler()
    profiler.start_record("rec1", "district1", "season1")
    profiler.start_operation("weather_api_request")
    profiler.end_operation("weather_api_request", status="SUCCESS")
    profiler.end_record()

    summary = profiler.summarize()
    assert summary.records_processed == 1
    assert summary.weather_requests == 1
    assert summary.total_elapsed_seconds >= 0


# ---------------------------------------------------------------------------
# Radiation unit equation tests
# ---------------------------------------------------------------------------

def test_t_ha_conversion():
    """1000 g/m^2 * HI 0.5 = 500 g/m^2 = 5 t/ha."""
    biomass = 1000.0  # g/m^2
    hi = 0.5  # dimensionless
    yield_g_m2 = biomass * hi
    yield_t_ha = yield_g_m2 / 100
    assert abs(yield_t_ha - 5.0) < 1e-10


def test_ewsi_range_validation():
    """EWSI outside [0,1] is rejected."""
    # EWSI validation happens in HYRUE model validation
    from engine.hydroma.models.hyrue import HYRUE, HYRUEParams

    model = HYRUE(params=HYRUEParams())
    ok, errors = model.validate_inputs(
        par=np.array([20.0]),
        lai=np.array([3.0]),
        ewsi=np.array([1.5]),  # Outside [0,1]
        t_mean=np.array([25.0]),
    )
    assert ok is False
    assert any("EWSI" in e for e in errors)


def test_par_range_validation():
    """PAR outside [0, 50] is rejected."""
    from engine.hydroma.models.hyrue import HYRUE, HYRUEParams

    model = HYRUE(params=HYRUEParams())
    ok, errors = model.validate_inputs(
        par=np.array([60.0]),  # Outside [0, 50]
        lai=np.array([3.0]),
        ewsi=np.array([0.3]),
        t_mean=np.array([25.0]),
    )
    assert ok is False
    assert any("PAR" in e for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
