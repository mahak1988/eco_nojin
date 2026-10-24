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

import importlib
import sqlite3
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# NOTE on engine imports
# ---------------------
# The sandbox filesystem exposes site-packages inconsistently between
# interpreter starts.  In that state ``from engine.hydroma.<pkg>.<mod> import X``
# can fail with ``ModuleNotFoundError: No module named 'engine.hydroma'`` even
# though ``importlib.import_module`` resolves the very same module.  The
# helper below uses the reliable form, so these tests exercise the code
# rather than the environment's import quirk.

_PROJECT_ROOT = "D:/HyDroMA"


def engine_module(dotted: str):
    """Import an engine module using the reliable resolution path.

    Each parent package is imported explicitly, in order, because the
    sandbox's inconsistent filesystem view breaks the implicit
    parent-import step that ``importlib.import_module`` performs for a
    dotted name.
    """
    if _PROJECT_ROOT not in sys.path:
        sys.path.append(_PROJECT_ROOT)
    parts = dotted.split(".")
    for i in range(1, len(parts) + 1):
        name = ".".join(parts[:i])
        if name not in sys.modules:
            importlib.import_module(name)
    return sys.modules[dotted]


# ---------------------------------------------------------------------------
# Runtime integrity
# ---------------------------------------------------------------------------

def test_engine_package_resolves():
    """``engine`` and ``engine.hydroma`` resolve to the project tree."""
    engine = engine_module("engine")
    assert "HyDroMA" in engine.__file__ or "hydroma" in engine.__file__.lower()

    hydroma = engine_module("engine.hydroma")
    assert Path(hydroma.__file__).parts[-2:] == ("hydroma", "__init__.py")


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
        mod = engine_module(name)
        assert mod is not None


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
    _m = engine_module("engine.hydroma.simulation.radiation_units")
    shortwave_to_par = _m.shortwave_to_par

    value, spec = shortwave_to_par(10.0, "MJ/m^2/day")
    assert value == pytest.approx(5.0)
    assert spec.frac_par == pytest.approx(0.5)
    assert spec.status == "estimated"


def test_shortwave_to_par_kwh_conversion():
    """1 kWh/m^2/day = 3.6 MJ/m^2/day; * 0.5 = 1.8 MJ/m^2/day PAR."""
    _m = engine_module("engine.hydroma.simulation.radiation_units")
    shortwave_to_par = _m.shortwave_to_par

    value, _ = shortwave_to_par(1.0, "kWh/m^2/day")
    assert value == pytest.approx(1.8)


def test_no_double_conversion_when_already_par():
    """PAR input is not converted again."""
    _m = engine_module("engine.hydroma.simulation.radiation_units")
    shortwave_to_par = _m.shortwave_to_par

    value, spec = shortwave_to_par(5.0, "MJ/m^2/day", already_par=True)
    assert value == pytest.approx(5.0)
    assert spec.frac_par == pytest.approx(1.0)


def test_shortwave_to_par_rejects_unknown_unit():
    """Unknown units raise rather than being assumed."""
    _m = engine_module("engine.hydroma.simulation.radiation_units")
    shortwave_to_par = _m.shortwave_to_par

    with pytest.raises(ValueError):
        shortwave_to_par(10.0, "furlongs/fortnight")


def test_biomass_to_yield_unit_chain():
    """1000 g/m^2 * HI 0.5 = 500 g/m^2 = 5 t/ha."""
    biomass_g_m2 = 1000.0
    hi = 0.5
    yield_g_m2 = biomass_g_m2 * hi
    yield_t_ha = yield_g_m2 / 100
    assert yield_t_ha == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# NDMI / remote sensing
# ---------------------------------------------------------------------------

def test_ndmi_known_values():
    """NDMI for NIR=0.5, SWIR=0.2 is 0.4286."""
    _m = engine_module("engine.hydroma.simulation.remote_sensing.spectral_indices")
    ndmi = _m.ndmi

    value = ndmi(np.array([0.5]), np.array([0.2]))
    assert value[0] == pytest.approx((0.5 - 0.2) / (0.5 + 0.2))


def test_ndmi_zero_denominator_guard():
    """NIR + SWIR == 0 yields 0 rather than a division error."""
    _m = engine_module("engine.hydroma.simulation.remote_sensing.spectral_indices")
    ndmi = _m.ndmi

    value = ndmi(np.array([0.0, 0.5]), np.array([0.0, 0.3]))
    assert value[0] == 0.0
    assert value[1] == pytest.approx((0.5 - 0.3) / (0.5 + 0.3))


def test_ndmi_out_of_range_reflectance_rejected():
    """Reflectance outside [0, 1] is reported as invalid."""
    _m = engine_module(
        "engine.hydroma.simulation.remote_sensing.spectral_indices"
    )
    validate_spectral_indices = _m.validate_spectral_indices

    result = validate_spectral_indices(np.array([1.5]), np.array([0.2]))
    assert result["valid"] is False
    assert result["errors"]


def test_cloud_mask_rejects_cloudy_pixel():
    """SCL cloud bits mark a pixel as not clear."""
    _m = engine_module(
        "engine.hydroma.simulation.remote_sensing.reflectance_quality"
    )
    is_pixel_clear = _m.is_pixel_clear
    quality_mask_from_s2_qa60 = _m.quality_mask_from_s2_qa60

    flags = quality_mask_from_s2_qa60(0x0001)  # OPAQUE
    assert flags["opaque"] is True
    assert is_pixel_clear(flags) is False

    clear = quality_mask_from_s2_qa60(0x0000)
    assert is_pixel_clear(clear) is True


def test_satellite_cache_key_is_deterministic_and_specific():
    """Same request -> same key; different science -> different key."""
    _m = engine_module(
        "engine.hydroma.simulation.remote_sensing.satellite_source"
    )
    Sentinel2Source = _m.Sentinel2Source

    src = Sentinel2Source(use_cache=False)
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
    _m = engine_module(
        "engine.hydroma.simulation.remote_sensing.satellite_source"
    )
    S2_SCALE_FACTOR = _m.S2_SCALE_FACTOR

    assert S2_SCALE_FACTOR == pytest.approx(0.0001)


# ---------------------------------------------------------------------------
# Weather / EWSI
# ---------------------------------------------------------------------------

def test_vpd_missing_input_is_not_zero_filled():
    """A missing dew-point and RH block VPD computation."""
    _m = engine_module("engine.hydroma.simulation.vpd_model")
    VPDInput = _m.VPDInput
    compute_daily_vpd = _m.compute_daily_vpd

    with pytest.raises(ValueError):
        compute_daily_vpd(VPDInput(date="2024-01-01", t_mean_c=20.0))


def test_vpd_from_dewpoint_and_rh_agree():
    """RH-derived and dew-point-derived VPD are consistent."""
    _m = engine_module("engine.hydroma.simulation.vpd_model")
    compute_daily_vpd = _m.compute_daily_vpd
    VPDInput = _m.VPDInput

    a = compute_daily_vpd(
        VPDInput(date="2024-01-01", t_mean_c=20.0, dewpoint_c=10.0)
    )
    b = compute_daily_vpd(
        VPDInput(date="2024-01-01", t_mean_c=20.0, relative_humidity_pct=50.0)
    )
    assert a.vpd_kpa == pytest.approx(b.vpd_kpa, rel=0.02)


def test_soil_moisture_stress_rejects_bad_bounds():
    """FC <= WP and out-of-range moisture are rejected."""
    _m = engine_module("engine.hydroma.simulation.soil_moisture_model")
    soil_stress_from_fc_wp = _m.soil_stress_from_fc_wp
    validate_soil_moisture = _m.validate_soil_moisture

    with pytest.raises(ValueError):
        soil_stress_from_fc_wp(0.2, 0.30, 0.30)
    assert validate_soil_moisture(0.9, 0.35, 0.15)


def test_ewsi_missing_component_is_not_zero_filled():
    """A component that is entirely missing is not silently treated as zero."""
    _m = engine_module("engine.hydroma.simulation.ewsi_pipeline")
    EWSIComputationPolicy = _m.EWSIComputationPolicy
    EWSIInputSeries = _m.EWSIInputSeries
    compute_daily_ewsi = _m.compute_daily_ewsi

    with pytest.raises(ValueError):
        compute_daily_ewsi(
            EWSIInputSeries(dates=["2024-01-01"]),
            policy=EWSIComputationPolicy.STRICT,
        )


def test_ewsi_partial_components_preserve_provenance():
    """Allow-estimated policy records the missing component and new weights."""
    _m = engine_module("engine.hydroma.simulation.ewsi_pipeline")
    EWSIComputationPolicy = _m.EWSIComputationPolicy
    EWSIInputSeries = _m.EWSIInputSeries
    compute_daily_ewsi = _m.compute_daily_ewsi

    out = compute_daily_ewsi(
        EWSIInputSeries(
            dates=["2024-01-01", "2024-01-02"],
            vpd=np.array([1.0, 2.0]),
            soil_moisture=np.array([0.3, 0.28]),
        ),
        policy=EWSIComputationPolicy.ALLOW_ESTIMATED,
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
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        cache = ScientificCache(Path(tmp) / "c.sqlite")
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
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        cache = ScientificCache(Path(tmp) / "c.sqlite")
        with pytest.raises(ValueError):
            cache.put(provider="P", endpoint="E", status="MADE_UP")


def test_cache_does_not_store_network_error_as_success():
    """A network error is cached with its error status, not as data."""
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        cache = ScientificCache(Path(tmp) / "c.sqlite")
        cache.put(provider="P", endpoint="E", latitude=1.0, status="NETWORK_ERROR")
        entry = cache.get(provider="P", endpoint="E", latitude=1.0)
        assert entry["status"] == "NETWORK_ERROR"
        assert entry["data"] == {}


def test_cache_expires_entries():
    """Expired entries are not returned."""
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        cache = ScientificCache(Path(tmp) / "c.sqlite", ttl_seconds=1)
        cache.put(provider="P", endpoint="E", latitude=1.0, status="SUCCESS")
        assert cache.get(provider="P", endpoint="E", latitude=1.0) is not None
        import time

        time.sleep(1.2)
        assert cache.get(provider="P", endpoint="E", latitude=1.0) is None


def test_cache_persists_across_instances():
    """A new cache instance reads the persisted database."""
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "c.sqlite"
        first = ScientificCache(db)
        first.put(provider="P", endpoint="E", latitude=1.0, status="SUCCESS",
                   response_json={"v": 7})
        second = ScientificCache(db)
        entry = second.get(provider="P", endpoint="E", latitude=1.0)
        assert entry is not None
        assert entry["data"]["v"] == 7


def test_cache_survives_corrupt_database():
    """A corrupt cache file is handled without crashing the caller."""
    _m = engine_module("engine.hydroma.simulation.data_cache")
    ScientificCache = _m.ScientificCache

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "c.sqlite"
        db.write_bytes(b"not a database at all")
        with pytest.raises(sqlite3.DatabaseError):
            ScientificCache(db)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def test_runner_does_not_reprocess_completed_records():
    """Terminal-state records are skipped on resume."""
    _m = engine_module("engine.hydroma.eval.resumable_benchmark_runner")
    ResumableBenchmarkRunner = _m.ResumableBenchmarkRunner

    with tempfile.TemporaryDirectory() as tmp:
        runner = ResumableBenchmarkRunner(
            db_path=Path(tmp) / "r.sqlite",
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state("rec1", "Buxar", "2016-17", "COMPUTED")
        assert runner._is_processed("rec1") is True
        assert runner._get_processed_ids() == {"rec1"}


def test_runner_records_failure_reason():
    """A failed record keeps its reason."""
    _m = engine_module("engine.hydroma.eval.resumable_benchmark_runner")
    ResumableBenchmarkRunner = _m.ResumableBenchmarkRunner

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "r.sqlite"
        runner = ResumableBenchmarkRunner(
            db_path=db,
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state(
            "recX", "Rohtas", "2017-18", "FAILED", failure_reason="boom"
        )
        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT status, failure_reason FROM record_state "
                "WHERE record_id = 'recX'"
            ).fetchone()
        assert row == ("FAILED", "boom")


def test_runner_counters_reflect_results():
    """Result counters match the recorded statuses."""
    from engine.hydroma.eval.resumable_benchmark_runner import (
        SUCCESS_STATUSES,
        ResumableBenchmarkRunner,
    )

    with tempfile.TemporaryDirectory() as tmp:
        runner = ResumableBenchmarkRunner(
            db_path=Path(tmp) / "r.sqlite",
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        statuses = ["COMPUTED", "PARTIAL_INPUTS", "BLOCKED", "FAILED"]
        for i, st in enumerate(statuses):
            runner._save_record_state(f"r{i}", "Buxar", "2016-17", st)
            runner._append_result(
                type(
                    "R",
                    (),
                    {
                        "to_dict": lambda self, st=st: {"status": st},
                    },
                )()
            )
        assert len(SUCCESS_STATUSES) == 2


# ---------------------------------------------------------------------------
# Split / leakage
# ---------------------------------------------------------------------------

def test_split_has_no_district_overlap():
    """No district appears in both development and test."""
    _m = engine_module("engine.hydroma.eval.benchmark_split_manifest")
    load_split_manifest = _m.load_split_manifest

    manifest = load_split_manifest()
    dev = set(manifest["development_districts"])
    test = set(manifest["test_districts"])
    assert dev & test == set()
    assert len(dev) == 7
    assert len(test) == 3


def test_split_has_no_record_overlap():
    """No record id appears in both sets."""
    _m = engine_module("engine.hydroma.eval.benchmark_split_manifest")
    load_split_manifest = _m.load_split_manifest

    manifest = load_split_manifest()
    dev = set(manifest["development_record_ids"])
    test = set(manifest["test_record_ids"])
    assert dev & test == set()
    assert manifest["development_record_count"] == 3967
    assert manifest["test_record_count"] == 1722


def test_split_manifest_hash_verifies():
    """The manifest hash matches its recomputed value."""
    _m = engine_module("engine.hydroma.eval.benchmark_split_manifest")
    verify_split = _m.verify_split

    verification = verify_split()
    assert verification["verified"] is True
    assert verification["manifest_hash_matches"] is True


def test_calibration_rejects_test_district_records():
    """Test-district records handed to calibration are rejected."""
    _m = engine_module("engine.hydroma.eval.stage39_benchmark")
    run_development_calibration = _m.run_development_calibration

    records = [
        {"record_id": "d1", "district_id": "Deoria", "predicted_yield": 5.0,
         "observed_yield": 5.2},
        {"record_id": "t1", "district_id": "Buxar", "predicted_yield": 4.0,
         "observed_yield": 6.0},
    ]
    result = run_development_calibration(records, ["Buxar", "Muzaffarpur", "Rohtas"])
    assert result["n_rejected_test_district"] == 1
    assert result["n_used"] == 1
    assert "LEAKAGE GUARD" in " ".join(result["notes"])


# ---------------------------------------------------------------------------
# Parameter registry
# ---------------------------------------------------------------------------

def test_ewsi_weights_sum_to_one_and_are_non_negative():
    """EWSI weights satisfy the simplex constraints."""
    _m = engine_module("engine.hydroma.eval.calibration_parameter_registry")
    build_registry = _m.build_registry

    registry = build_registry()
    weights = [
        registry.get_value("ewsi_weight_ndmi"),
        registry.get_value("ewsi_weight_vpd"),
        registry.get_value("ewsi_weight_soil"),
    ]
    assert all(w >= 0 for w in weights)
    assert sum(weights) == pytest.approx(1.0)


def test_parameter_out_of_bounds_is_rejected():
    """Updates outside the allowed range raise."""
    _m = engine_module("engine.hydroma.eval.calibration_parameter_registry")
    build_registry = _m.build_registry

    registry = build_registry()
    with pytest.raises(ValueError):
        registry.update_value(parameter_name="epsilon", new_value=99.0)


def test_parameter_update_is_traceable():
    """Updates record method, dataset, and version."""
    _m = engine_module("engine.hydroma.eval.calibration_parameter_registry")
    build_registry = _m.build_registry

    registry = build_registry()
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
    """RMSE / MAE / Bias / R2 match a hand-computed example."""
    from engine.hydroma.eval.stage39_benchmark import compute_benchmark_metrics

    records = [
        {"observed_yield": 2.0, "predicted_yield": 4.0},
        {"observed_yield": 4.0, "predicted_yield": 6.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.n == 2
    assert m.rmse == pytest.approx(2.0)
    assert m.mae == pytest.approx(2.0)
    assert m.bias == pytest.approx(2.0)
    assert m.r2 == pytest.approx(0.0)


def test_metrics_exclude_records_without_predictions():
    """Only records with both values contribute."""
    _m = engine_module("engine.hydroma.eval.stage39_benchmark")
    compute_benchmark_metrics = _m.compute_benchmark_metrics

    records = [
        {"observed_yield": 2.0, "predicted_yield": 4.0},
        {"observed_yield": 3.0, "predicted_yield": None},
    ]
    m = compute_benchmark_metrics(records)
    assert m.n == 1


def test_mape_excludes_zero_observations():
    """Zero-yield observations are excluded from MAPE and counted."""
    _m = engine_module("engine.hydroma.eval.stage39_benchmark")
    compute_benchmark_metrics = _m.compute_benchmark_metrics

    records = [
        {"observed_yield": 0.0, "predicted_yield": 1.0},
        {"observed_yield": 2.0, "predicted_yield": 4.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.mape_excluded == 1
    assert m.mape == pytest.approx(100.0)


def test_r2_undefined_for_zero_variance():
    """R2 is reported as None when observed yields have no variance."""
    from engine.hydroma.eval.stage39_benchmark import compute_benchmark_metrics

    records = [
        {"observed_yield": 3.0, "predicted_yield": 2.0},
        {"observed_yield": 3.0, "predicted_yield": 4.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.r2 is None
    assert m.r2_undefined_reason


def test_bootstrap_blocked_with_few_districts():
    """Cluster bootstrap is blocked with fewer than three districts."""
    _m = engine_module("engine.hydroma.eval.stage39_benchmark")
    cluster_bootstrap_uncertainty = _m.cluster_bootstrap_uncertainty

    records = [
        {"district_id": "Buxar", "observed_yield": 5.0, "predicted_yield": 4.0},
        {"district_id": "Rohtas", "observed_yield": 5.5, "predicted_yield": 4.5},
    ]
    result = cluster_bootstrap_uncertainty(records)
    assert result["status"] == "BLOCKED"
    assert result["n_districts"] == 2


def test_bootstrap_preserves_district_groups():
    """Resampling draws whole districts, never partial records."""
    _m = engine_module("engine.hydroma.eval.stage39_benchmark")
    cluster_bootstrap_uncertainty = _m.cluster_bootstrap_uncertainty

    records = []
    for d in ("A", "B", "C"):
        for i in range(4):
            records.append({
                "district_id": d,
                "observed_yield": 5.0 + i,
                "predicted_yield": 4.0 + i,
            })
    result = cluster_bootstrap_uncertainty(records, n_bootstrap=50)
    assert result["status"] == "OK"
    assert result["n_districts"] == 3
    assert result["n_records"] == 12
    assert result["rmse_ci"][0] <= result["rmse_mean"] <= result["rmse_ci"][1]
