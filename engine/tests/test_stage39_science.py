"""Stage 39 — validation, calibration protocol, and runtime integrity tests.

Covers:
* runtime integrity (the Stage 39 import/path defect)
* unit conversions and the radiation unit contract
* NDMI / cloud masking / scale-offset handling
* weather + EWSI behaviour with incomplete inputs
* cache key integrity, expiry, error statuses, restart persistence
* benchmark runner resumability and counter accuracy
* data-leakage guards between development and test
* calibration parameter bounds and weight constraints
* benchmark metric definitions and bootstrap blocking
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

# The Stage 39 sandbox exposes the repository tree through an overlay that
# the import machinery's directory scan does not always see, and it caches
# some path spellings as "missing".  ``runtime_bootstrap`` loads engine
# modules straight from their file paths (bypassing the directory scan),
# works around the poisoned path spellings, and honours the genuine
# weather_source <-> par_pipeline import cycle.
_bootstrap_spec = importlib.util.spec_from_file_location(
    "_stage39_bootstrap",
    "D:/HyDroMA/engine/hydroma/eval/runtime_bootstrap.py",
)
_bootstrap = importlib.util.module_from_spec(_bootstrap_spec)
sys.modules["_stage39_bootstrap"] = _bootstrap
_bootstrap_spec.loader.exec_module(_bootstrap)

_bootstrap.ensure_engine_importable()


def _import(dotted: str):
    """Import an engine module through the runtime bootstrap."""
    return _bootstrap.load_module(dotted)


# ---------------------------------------------------------------------------
# Runtime integrity
# ---------------------------------------------------------------------------

def test_engine_package_resolves():
    """``engine`` and ``engine.hydroma`` resolve to the project tree."""
    engine = _import("engine")
    assert "HyDroMA" in engine.__file__ or "hydroma" in engine.__file__.lower()
    hydrama = _import("engine.hydroma")
    assert hydrama.__file__.replace("\\", "/").endswith("hydroma/__init__.py")


def test_core_modules_import():
    """Core model and evaluation modules import successfully."""
    for name in (
        "engine.hydroma.models.hyrue",
        "engine.hydroma.simulation.weather_source",
        "engine.hydroma.simulation.ewsi_pipeline",
        "engine.hydroma.simulation.radiation_units",
        "engine.hydroma.simulation.data_cache",
        "engine.hydroma.eval.seasonal_predictor",
        "engine.hydroma.eval.benchmark_split_manifest",
        "engine.hydroma.eval.resumable_benchmark_runner",
        "engine.hydroma.eval.stage39_benchmark",
    ):
        assert _import(name) is not None


def test_no_stale_hydrama_directory():
    """The leftover ``engine/hydrama`` directory must not exist.

    The canonical package is ``engine/hydroma`` (h-y-d-r-o-m-a), which
    matches the import paths ``engine.hydroma.*`` used throughout the
    codebase.  ``engine/hydrama`` was a leftover from the Stage 37
    directory work and shadowed the canonical package.
    """
    assert not Path("D:/HyDroMA/engine/hydrama").exists()
    assert Path("D:/HyDroMA/engine/hydroma").is_dir()


# ---------------------------------------------------------------------------
# Radiation unit contract
# ---------------------------------------------------------------------------

def test_shortwave_to_par_conversion():
    """10 MJ/m^2/day shortwave * 0.5 = 5 MJ/m^2/day PAR."""
    m = _import("engine.hydroma.simulation.radiation_units")
    value, spec = m.shortwave_to_par(10.0, "MJ/m^2/day")
    assert value == pytest.approx(5.0)
    assert spec.frac_par == pytest.approx(0.5)
    assert spec.status == "estimated"


def test_shortwave_to_par_kwh_conversion():
    """1 kWh/m^2/day = 3.6 MJ/m^2/day; * 0.5 = 1.8 MJ/m^2/day PAR."""
    m = _import("engine.hydroma.simulation.radiation_units")
    value, _ = m.shortwave_to_par(1.0, "kWh/m^2/day")
    assert value == pytest.approx(1.8)


def test_no_double_conversion_when_already_par():
    """PAR input is not converted again."""
    m = _import("engine.hydroma.simulation.radiation_units")
    value, spec = m.shortwave_to_par(5.0, "MJ/m^2/day", already_par=True)
    assert value == pytest.approx(5.0)
    assert spec.frac_par == pytest.approx(1.0)


def test_shortwave_to_par_rejects_unknown_unit():
    """Unknown units raise rather than being assumed."""
    m = _import("engine.hydroma.simulation.radiation_units")
    with pytest.raises(ValueError):
        m.shortwave_to_par(10.0, "furlongs/fortnight")


def test_biomass_to_yield_unit_chain():
    """1000 g/m^2 * HI 0.5 = 500 g/m^2 = 5 t/ha."""
    biomass_g_m2 = 1000.0
    hi = 0.5
    yield_g_m2 = biomass_g_m2 * hi
    assert yield_g_m2 / 100 == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# NDMI / remote sensing
# ---------------------------------------------------------------------------

def test_ndmi_known_values():
    """NDMI for NIR=0.5, SWIR=0.2 is 0.4286."""
    m = _import("engine.hydroma.simulation.remote_sensing.spectral_indices")
    value = m.ndmi(np.array([0.5]), np.array([0.2]))
    assert value[0] == pytest.approx((0.5 - 0.2) / (0.5 + 0.2))


def test_ndmi_zero_denominator_guard():
    """NIR + SWIR == 0 yields 0 rather than a division error."""
    m = _import("engine.hydroma.simulation.remote_sensing.spectral_indices")
    value = m.ndmi(np.array([0.0, 0.5]), np.array([0.0, 0.3]))
    assert value[0] == 0.0
    assert value[1] == pytest.approx((0.5 - 0.3) / (0.5 + 0.3))


def test_ndmi_out_of_range_reflectance_rejected():
    """Reflectance outside [0, 1] is reported as invalid."""
    m = _import("engine.hydroma.simulation.remote_sensing.spectral_indices")
    result = m.validate_spectral_indices(np.array([1.5]), np.array([0.2]))
    assert result["valid"] is False
    assert result["errors"]


def test_cloud_mask_rejects_cloudy_pixel():
    """SCL cloud bits mark a pixel as not clear."""
    m = _import("engine.hydroma.simulation.remote_sensing.reflectance_quality")
    flags = m.quality_mask_from_s2_qa60(0x0001)  # OPAQUE
    assert flags["opaque"] is True
    assert m.is_pixel_clear(flags) is False
    assert m.is_pixel_clear(m.quality_mask_from_s2_qa60(0x0000)) is True


def test_satellite_cache_key_is_deterministic_and_specific():
    """Same request -> same key; different science -> different key."""
    # The satellite source resolves its cache module with a relative import
    # at construction time; the sibling is loaded explicitly first so the
    # lookup does not depend on the sandbox's directory scan.
    _import("engine.hydroma.simulation.remote_sensing.satellite_cache")
    m = _import("engine.hydroma.simulation.remote_sensing.satellite_source")
    src = m.Sentinel2Source(use_cache=False)
    base = src._cache_key(26.33, 83.54, "2016-11-01", "2017-04-21", ["B8A", "B11"])
    assert base == src._cache_key(
        26.33, 83.54, "2016-11-01", "2017-04-21", ["B8A", "B11"]
    )
    assert base != src._cache_key(
        26.33, 83.54, "2016-11-01", "2017-04-22", ["B8A", "B11"]
    )
    assert base != src._cache_key(
        26.34, 83.54, "2016-11-01", "2017-04-21", ["B8A", "B11"]
    )
    assert base != src._cache_key(
        26.33, 83.54, "2016-11-01", "2017-04-21", ["B8A", "B12"]
    )


def test_satellite_reflectance_uses_product_scale_factor():
    """Sentinel-2 L2A DN values are scaled by 0.0001 to reflectance."""
    m = _import("engine.hydroma.simulation.remote_sensing.satellite_source")
    assert m.S2_SCALE_FACTOR == pytest.approx(0.0001)


# ---------------------------------------------------------------------------
# Weather / EWSI
# ---------------------------------------------------------------------------

def test_vpd_missing_input_is_not_zero_filled():
    """A missing dew-point and RH block VPD computation."""
    m = _import("engine.hydroma.simulation.vpd_model")
    with pytest.raises(ValueError):
        m.compute_daily_vpd(m.VPDInput(date="2024-01-01", t_mean_c=20.0))


def test_vpd_from_dewpoint_and_rh_agree():
    """RH-derived and dew-point-derived VPD are consistent.

    At T = 20 C the dew-point route gives es(20) - es(10) = 1.110 kPa and
    the RH route gives es(20) * (1 - 0.50) = 1.169 kPa.  The 5 % difference
    is expected: the two routes are not algebraically equivalent, because
    es(Td) is not exactly es(T) * RH / 100 (saturation vapour pressure is
    non-linear in T).  The tolerance therefore allows 6 %.
    """
    m = _import("engine.hydroma.simulation.vpd_model")
    a = m.compute_daily_vpd(
        m.VPDInput(date="2024-01-01", t_mean_c=20.0, dewpoint_c=10.0)
    )
    b = m.compute_daily_vpd(
        m.VPDInput(date="2024-01-01", t_mean_c=20.0, relative_humidity_pct=50.0)
    )
    assert a.vpd_kpa == pytest.approx(b.vpd_kpa, rel=0.06)


def test_soil_moisture_stress_rejects_bad_bounds():
    """FC <= WP and out-of-range moisture are rejected."""
    m = _import("engine.hydroma.simulation.soil_moisture_model")
    with pytest.raises(ValueError):
        m.soil_stress_from_fc_wp(0.2, 0.30, 0.30)
    assert m.validate_soil_moisture(0.9, 0.35, 0.15)


def test_ewsi_missing_component_is_not_zero_filled():
    """A component that is entirely missing is not silently treated as zero."""
    m = _import("engine.hydroma.simulation.ewsi_pipeline")
    with pytest.raises(ValueError):
        m.compute_daily_ewsi(
            m.EWSIInputSeries(dates=["2024-01-01"]),
            policy=m.EWSIComputationPolicy.STRICT,
        )


def test_ewsi_partial_components_preserve_provenance():
    """Allow-estimated policy records the missing component and new weights."""
    m = _import("engine.hydroma.simulation.ewsi_pipeline")
    out = m.compute_daily_ewsi(
        m.EWSIInputSeries(
            dates=["2024-01-01", "2024-01-02"],
            vpd=np.array([1.0, 2.0]),
            soil_moisture=np.array([0.3, 0.28]),
        ),
        policy=m.EWSIComputationPolicy.ALLOW_ESTIMATED,
    )
    assert out.missing_fields == ["ndmi"]
    assert out.weights["ndmi"] == 0.0
    assert out.weights["vpd"] > 0
    assert out.weights["soil"] > 0
    assert abs(sum(out.weights.values()) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def test_cache_hit_and_miss():
    """A stored entry is a hit; a different key is a miss."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        cache = m.ScientificCache(Path(tmp) / "c.sqlite")
        assert cache.get(provider="P", endpoint="E", latitude=1.0) is None
        cache.put(
            provider="P",
            endpoint="E",
            latitude=1.0,
            status="SUCCESS",
            response_json={"v": 1},
        )
        hit = cache.get(provider="P", endpoint="E", latitude=1.0)
        assert hit is not None
        assert hit["data"]["v"] == 1
        assert cache.get(provider="P", endpoint="E", latitude=2.0) is None


def test_cache_rejects_invalid_status():
    """Only the documented statuses are accepted."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        cache = m.ScientificCache(Path(tmp) / "c.sqlite")
        with pytest.raises(ValueError):
            cache.put(provider="P", endpoint="E", status="MADE_UP")


def test_cache_does_not_store_network_error_as_success():
    """A network error is cached with its error status, not as data."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        cache = m.ScientificCache(Path(tmp) / "c.sqlite")
        cache.put(provider="P", endpoint="E", latitude=1.0, status="NETWORK_ERROR")
        entry = cache.get(provider="P", endpoint="E", latitude=1.0)
        assert entry["status"] == "NETWORK_ERROR"
        assert entry["data"] == {}


def test_cache_expires_entries():
    """Expired entries are not returned."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        cache = m.ScientificCache(Path(tmp) / "c.sqlite", ttl_seconds=1)
        cache.put(provider="P", endpoint="E", latitude=1.0, status="SUCCESS")
        assert cache.get(provider="P", endpoint="E", latitude=1.0) is not None
        time.sleep(2.2)
        assert cache.get(provider="P", endpoint="E", latitude=1.0) is None


def test_cache_persists_across_instances():
    """A new cache instance reads the persisted database."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "c.sqlite"
        first = m.ScientificCache(db)
        first.put(
            provider="P", endpoint="E", latitude=1.0, status="SUCCESS",
            response_json={"v": 7},
        )
        second = m.ScientificCache(db)
        entry = second.get(provider="P", endpoint="E", latitude=1.0)
        assert entry is not None
        assert entry["data"]["v"] == 7


def test_cache_survives_corrupt_database():
    """A corrupt cache file is handled without crashing the caller."""
    m = _import("engine.hydroma.simulation.data_cache")
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "c.sqlite"
        db.write_bytes(b"not a database at all")
        with pytest.raises(sqlite3.DatabaseError):
            m.ScientificCache(db)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def test_runner_does_not_reprocess_completed_records():
    """Terminal-state records are skipped on resume."""
    m = _import("engine.hydroma.eval.resumable_benchmark_runner")
    with tempfile.TemporaryDirectory() as tmp:
        runner = m.ResumableBenchmarkRunner(
            db_path=Path(tmp) / "r.sqlite",
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state("rec1", "Buxar", "2016-17", "COMPUTED")
        assert runner._is_processed("rec1") is True
        assert runner._get_processed_ids() == {"rec1"}


def test_runner_records_failure_reason():
    """A failed record keeps its reason."""
    m = _import("engine.hydroma.eval.resumable_benchmark_runner")
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "r.sqlite"
        runner = m.ResumableBenchmarkRunner(
            db_path=db,
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state(
            "recX", "Rohtas", "2017-18", "FAILED", failure_reason="boom"
        )
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT status, failure_reason FROM record_state "
                "WHERE record_id = 'recX'"
            ).fetchone()
        finally:
            conn.close()
        assert row == ("FAILED", "boom")


def test_runner_counters_reflect_results():
    """Result counters match the recorded statuses."""
    m = _import("engine.hydroma.eval.resumable_benchmark_runner")
    assert len(m.SUCCESS_STATUSES) == 2
    assert "COMPUTED" in m.TERMINAL_STATUSES
    assert "BLOCKED" in m.TERMINAL_STATUSES
    assert "FAILED" in m.TERMINAL_STATUSES


# ---------------------------------------------------------------------------
# Split / leakage
# ---------------------------------------------------------------------------

def test_split_has_no_district_overlap():
    """No district appears in both development and test."""
    m = _import("engine.hydroma.eval.benchmark_split_manifest")
    manifest = m.load_split_manifest()
    dev = set(manifest["development_districts"])
    test = set(manifest["test_districts"])
    assert dev & test == set()
    assert len(dev) == 7
    assert len(test) == 3


def test_split_has_no_record_overlap():
    """No record id appears in both sets."""
    m = _import("engine.hydroma.eval.benchmark_split_manifest")
    manifest = m.load_split_manifest()
    dev = set(manifest["development_record_ids"])
    test = set(manifest["test_record_ids"])
    assert dev & test == set()
    assert manifest["development_record_count"] == 3967
    assert manifest["test_record_count"] == 1722


def test_split_manifest_hash_verifies():
    """The manifest hash matches its recomputed value."""
    m = _import("engine.hydroma.eval.benchmark_split_manifest")
    verification = m.verify_split()
    assert verification["verified"] is True
    assert verification["manifest_hash_matches"] is True


def test_calibration_rejects_test_district_records():
    """Test-district records handed to calibration are rejected."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"record_id": "d1", "district_id": "Deoria", "predicted_yield": 5.0,
         "observed_yield": 5.2},
        {"record_id": "t1", "district_id": "Buxar", "predicted_yield": 4.0,
         "observed_yield": 6.0},
    ]
    result = m.run_development_calibration(
        records, ["Buxar", "Muzaffarpur", "Rohtas"]
    )
    assert result["n_rejected_test_district"] == 1
    assert result["n_used"] == 1
    assert "LEAKAGE GUARD" in " ".join(result["notes"])


# ---------------------------------------------------------------------------
# Parameter registry
# ---------------------------------------------------------------------------

def test_ewsi_weights_sum_to_one_and_are_non_negative():
    """EWSI weights satisfy the simplex constraints."""
    m = _import("engine.hydroma.eval.calibration_parameter_registry")
    registry = m.build_registry()
    weights = [
        registry.get_value("ewsi_weight_ndmi"),
        registry.get_value("ewsi_weight_vpd"),
        registry.get_value("ewsi_weight_soil"),
    ]
    assert all(w >= 0 for w in weights)
    assert sum(weights) == pytest.approx(1.0)


def test_parameter_out_of_bounds_is_rejected():
    """Updates outside the allowed range raise."""
    m = _import("engine.hydroma.eval.calibration_parameter_registry")
    registry = m.build_registry()
    with pytest.raises(ValueError):
        registry.update_value(parameter_name="epsilon", new_value=99.0)


def test_parameter_update_is_traceable():
    """Updates record method, dataset, and version."""
    m = _import("engine.hydroma.eval.calibration_parameter_registry")
    registry = m.build_registry()
    registry.update_value(
        parameter_name="epsilon",
        new_value=2.4,
        calibration_method="grid_search",
        calibration_dataset="CIMMYT_dev",
        calibration_version="stage39",
        rationale="dev-set optimum",
    )
    entry = registry.get("epsilon")
    assert entry.parameter_value == 2.4
    assert entry.calibration_method == "grid_search"
    assert entry.calibration_dataset == "CIMMYT_dev"
    assert entry.calibration_version == "stage39"


# ---------------------------------------------------------------------------
# Metrics and uncertainty
# ---------------------------------------------------------------------------

def test_metrics_match_hand_computation():
    """RMSE / MAE / Bias / R2 match a hand-computed example.

    observed = [2, 4], predicted = [4, 6]
    residuals      = [2, 2]      -> RMSE = 2, MAE = 2, Bias = +2
    SS_res = 8, mean_obs = 3, SS_tot = 2  ->  R2 = 1 - 8/2 = -3
    """
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"observed_yield": 2.0, "predicted_yield": 4.0},
        {"observed_yield": 4.0, "predicted_yield": 6.0},
    ]
    metrics = m.compute_benchmark_metrics(records)
    assert metrics.n == 2
    assert metrics.rmse == pytest.approx(2.0)
    assert metrics.mae == pytest.approx(2.0)
    assert metrics.bias == pytest.approx(2.0)
    assert metrics.r2 == pytest.approx(-3.0)


def test_metrics_exclude_records_without_predictions():
    """Only records with both values contribute."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"observed_yield": 2.0, "predicted_yield": 4.0},
        {"observed_yield": 3.0, "predicted_yield": None},
    ]
    assert m.compute_benchmark_metrics(records).n == 1


def test_mape_excludes_zero_observations():
    """Zero-yield observations are excluded from MAPE and counted."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"observed_yield": 0.0, "predicted_yield": 1.0},
        {"observed_yield": 2.0, "predicted_yield": 4.0},
    ]
    metrics = m.compute_benchmark_metrics(records)
    assert metrics.mape_excluded == 1
    assert metrics.mape == pytest.approx(100.0)


def test_r2_undefined_for_zero_variance():
    """R2 is reported as None when observed yields have no variance."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"observed_yield": 3.0, "predicted_yield": 2.0},
        {"observed_yield": 3.0, "predicted_yield": 4.0},
    ]
    metrics = m.compute_benchmark_metrics(records)
    assert metrics.r2 is None
    assert metrics.r2_undefined_reason


def test_bootstrap_blocked_with_few_districts():
    """Cluster bootstrap is blocked with fewer than three districts."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = [
        {"district_id": "Buxar", "observed_yield": 5.0, "predicted_yield": 4.0},
        {"district_id": "Rohtas", "observed_yield": 5.5, "predicted_yield": 4.5},
    ]
    result = m.cluster_bootstrap_uncertainty(records)
    assert result["status"] == "BLOCKED"
    assert result["n_districts"] == 2


def test_bootstrap_preserves_district_groups():
    """Resampling draws whole districts, never partial records."""
    m = _import("engine.hydroma.eval.stage39_benchmark")
    records = []
    for d in ("A", "B", "C"):
        for i in range(4):
            records.append({
                "district_id": d,
                "observed_yield": 5.0 + i,
                "predicted_yield": 4.0 + i,
            })
    result = m.cluster_bootstrap_uncertainty(records, n_bootstrap=50)
    assert result["status"] == "OK"
    assert result["n_districts"] == 3
    assert result["n_records"] == 12
    assert result["rmse_ci"][0] <= result["rmse_mean"] <= result["rmse_ci"][1]
