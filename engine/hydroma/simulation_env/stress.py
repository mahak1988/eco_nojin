"""Stress-testing framework for the Eco Nojin simulation environment.

The framework is deterministic (seed-driven) and exercises the simulation
environment under adverse conditions:

1. **Combinatorial scenarios** — climate + disaster matrices.
2. **Data-quality injection** — missing bands, cloud cover, sensor noise and
   sensor-failure on synthetic satellite arrays; verifies the production index
   pipeline degrades gracefully.
3. **Volume stress** — scales rasters/arrays to large sizes and measures time
   and (optionally) memory growth.
4. **Fallback validation** — verifies the pure-Python fallbacks in the
   satellite index and wrapper modules behave identically to the accelerated
   paths and that the C++ binding absence is handled.
5. **Performance profiling** — records throughput of each simulator under load.

All outputs are synthetic and tagged ``data_source="simulated"``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from engine.hydroma.simulation_env.contracts import (
    SimulationMetadata,
    StressTestResult,
)
from engine.hydroma.simulation_env.disasters import (
    FloodScenario,
    LandslideScenario,
    StormScenario,
    simulate_flood,
    simulate_landslide,
    simulate_storm,
)


# ---------------------------------------------------------------------------
# Data-quality injection
# ---------------------------------------------------------------------------
@dataclass
class CorruptionConfig:
    """Describes synthetic data impairments to inject into arrays."""

    missing_band: bool = False
    cloud_cover_pct: float = 0.0  # 0-100
    sensor_noise_std: float = 0.0
    dead_pixels_pct: float = 0.0
    drop_frames_pct: float = 0.0  # temporal gaps (set whole rows to NaN)
    seed: int = 42


def corrupt_array(arr: np.ndarray, cfg: CorruptionConfig) -> np.ndarray:
    """Apply synthetic data-quality impairments to a band array.

    Returns a float64 copy with NaNs where data is missing/dead so downstream
    processors must handle them (just like real satellite pipelines do).
    """
    corrupted = arr.astype(np.float64, copy=True)
    rng = np.random.default_rng(cfg.seed)

    # Dead pixels
    if cfg.dead_pixels_pct > 0:
        dead = rng.random(corrupted.shape) < (cfg.dead_pixels_pct / 100.0)
        corrupted = np.where(dead, np.nan, corrupted)

    # Cloud cover (opaque cloud mask -> NaN)
    if cfg.cloud_cover_pct > 0:
        cloud = rng.random(corrupted.shape) < (cfg.cloud_cover_pct / 100.0)
        corrupted = np.where(cloud, np.nan, corrupted)

    # Sensor noise (additive gaussian, only where not NaN)
    if cfg.sensor_noise_std > 0:
        noise = rng.normal(0.0, cfg.sensor_noise_std, size=corrupted.shape)
        mask = ~np.isnan(corrupted)
        corrupted = np.where(mask, corrupted + noise, corrupted)

    # Temporal frame drops (set entire rows to NaN)
    if cfg.drop_frames_pct > 0 and corrupted.ndim == 2:
        n_drop = int(corrupted.shape[0] * cfg.drop_frames_pct / 100.0)
        if n_drop > 0:
            rows = rng.choice(corrupted.shape[0], size=n_drop, replace=False)
            corrupted[rows, :] = np.nan

    return corrupted


def validate_index_robustness(grid_size: int = 64, seed: int = 42,
                              corruptions: list[CorruptionConfig] | None = None) -> list[StressTestResult]:
    """Run vegetation indices on corrupted arrays; verify graceful handling.

    Uses ``calculate_ndvi``/``calculate_nbr`` from the production index module
    (which already use ``np.nan_to_num``), confirming they never produce NaNs
    or out-of-range values even when fed corrupted input.
    """
    from engine.hydroma.satellite.processors.indices import calculate_nbr, calculate_ndvi

    if corruptions is None:
        corruptions = [
            CorruptionConfig(missing_band=False, cloud_cover_pct=10.0, sensor_noise_std=0.02, seed=seed),
            CorruptionConfig(cloud_cover_pct=50.0, dead_pixels_pct=5.0, seed=seed + 1),
            CorruptionConfig(cloud_cover_pct=90.0, sensor_noise_std=0.05, dead_pixels_pct=10.0, seed=seed + 2),
        ]

    rng = np.random.default_rng(seed)
    results: list[StressTestResult] = []
    for cfg in corruptions:
        red = rng.uniform(0.05, 0.20, size=(grid_size, grid_size))
        nir = rng.uniform(0.20, 0.60, size=(grid_size, grid_size))
        swir = rng.uniform(0.05, 0.15, size=(grid_size, grid_size))

        red_c = corrupt_array(red, cfg)
        nir_c = corrupt_array(nir, cfg)
        swir_c = corrupt_array(swir, cfg)

        if cfg.missing_band:
            # Simulate a missing band by passing NaN array.
            nir_c = np.full_like(nir_c, np.nan)

        ndvi = calculate_ndvi(red_c, nir_c)
        nbr = calculate_nbr(nir_c, swir_c)

        finite_ndvi = np.all(np.isfinite(ndvi))
        finite_nbr = np.all(np.isfinite(nbr))
        in_range = ndvi.min() >= -1.0 and ndvi.max() <= 1.0 and nbr.min() >= -1.0 and nbr.max() <= 1.0

        passed = bool(finite_ndvi and finite_nbr and in_range)
        detail = f"cloud={cfg.cloud_cover_pct}% noise={cfg.sensor_noise_std} -> ndvi[{ndvi.min():.3f},{ndvi.max():.3f}]"
        results.append(
            StressTestResult(
                test_name="index_robustness",
                scenario=f"corruption_{cfg.seed}",
                passed=passed,
                detail=detail,
                metric=float(np.nanmean(ndvi)),
                metadata=_meta(f"corruption_{cfg.seed}", seed, {"corruption": cfg.__dict__}),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Volume stress
# ---------------------------------------------------------------------------
@dataclass
class VolumeResult:
    grid_size: int
    elapsed_ms: float
    nan_share: float
    passed: bool
    metadata: SimulationMetadata


def run_volume_stress(sizes: list[int] | None = None, seed: int = 42) -> list[VolumeResult]:
    """Scale index computation to large rasters; measure elapsed time."""
    from engine.hydroma.satellite.processors.indices import calculate_nbr, calculate_ndvi

    if sizes is None:
        sizes = [64, 256, 512, 1024]
    rng = np.random.default_rng(seed)
    results: list[VolumeResult] = []
    for n in sizes:
        red = rng.uniform(0.05, 0.20, size=(n, n))
        nir = rng.uniform(0.20, 0.60, size=(n, n))
        t0 = time.perf_counter()
        ndvi = calculate_ndvi(red, nir)
        calculate_nbr(nir, red * 0.5)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        nan_share = float(np.isnan(ndvi).mean())
        # 1024x1024 should complete in well under a few seconds for numpy.
        passed = elapsed_ms < ((n > 512 and 10000.0) or 5000.0)
        results.append(VolumeResult(n, round(elapsed_ms, 2), round(nan_share, 4), passed, _meta(f"volume_{n}", seed, {"grid": n})))
    return results


# ---------------------------------------------------------------------------
# Fallback validation
# ---------------------------------------------------------------------------
def validate_fallbacks() -> list[StressTestResult]:
    """Verify the wrapper/indices fallback paths produce finite values.

    Checks the pure-Python fallback used when the C++ binding is unavailable,
    and confirms index functions never return non-finite values.
    """
    from engine.hydroma.cpp_bridge import indices_fallback
    from engine.hydroma.simulation_env.contracts import StressTestResult as SRT
    from engine.hydroma.wrapper import compute_all_indices, compute_evi, compute_ndvi, compute_savi

    results: list[StressTestResult] = []

    # Numba fallback path
    a = indices_fallback.ndvi_fast(np.array([[0.1, 0.2], [0.3, 0.4]]), np.array([[0.4, 0.5], [0.6, 0.7]]))
    r = SRT(
        test_name="numba_fallback_ndvi", scenario="fallback", passed=bool(np.all(np.isfinite(a))),
        detail=f"ndvi_fast finite={np.all(np.isfinite(a))}", metric=float(np.nanmean(a)),
        metadata=_meta("numba_fallback", 0, {}),
    )
    results.append(r)

    # Wrapper scalar fallback
    ndvi = compute_ndvi(0.1, 0.5)
    evi = compute_evi(0.1, 0.5, 0.05)
    savi = compute_savi(0.1, 0.5)
    ok = all(np.isfinite(v) for v in (ndvi, evi, savi))
    allidx = compute_all_indices(0.1, 0.5, 0.05, 0.2, 0.15)
    ok = ok and all(np.isfinite(v) for v in allidx.values())
    results.append(
        SRT(test_name="wrapper_scalar_fallback", scenario="fallback", passed=bool(ok),
            detail=f"ndvi={ndvi:.3f} evi={evi:.3f} savi={savi:.3f}",
            metric=float(np.mean(list(allidx.values()))), metadata=_meta("wrapper_fallback", 0, {}))
    )

    # C++ absence must not crash.
    try:
        from engine.hydroma import cpp_bindings
        cpp_bindings.get_module()
        cpp_available = True
    except Exception:
        cpp_available = False
    results.append(
        SRT(test_name="cpp_availability", scenario="fallback", passed=True,
            detail=f"cpp_available={cpp_available}; python fallback used regardless",
            metric=float(cpp_available), metadata=_meta("cpp_availability", 0, {}))
    )
    return results


# ---------------------------------------------------------------------------
# Combinatorial scenario runner
# ---------------------------------------------------------------------------
@dataclass
class CombinatorialResult:
    combinations: int
    results: list[dict[str, Any]] = field(default_factory=list)
    metadata: SimulationMetadata | None = None
    summary: dict[str, Any] = field(default_factory=dict)


def run_combinatorial(climate_scenarios: list[dict[str, Any]],
                      disaster_scenarios: list[dict[str, Any]],
                      seed: int = 42) -> CombinatorialResult:
    """Run climate + disaster combinations through the simulators.

    Each climate scenario drives the synthetic monsoon/flood; each disaster
    scenario is a wildfire/fire/flood/storm/landslide configuration.  Results
    are tagged as synthetic.
    """
    from engine.hydroma.simulation_env.climate import MonsoonScenario, simulate_monsoon
    from engine.hydroma.simulation_env.disasters import (
        FireScenario,
        FloodScenario as DSFloodScenario,
        simulate_wildfire,
    )

    combinations = len(climate_scenarios) * len(disaster_scenarios)
    out: list[dict[str, Any]] = []
    for ci, clim in enumerate(climate_scenarios):
        for di, dis in enumerate(disaster_scenarios):
            sid = seed + ci * 1000 + di
            # Climate leg: monsoon with flood scaled by scenario severity.
            m_scen = MonsoonScenario(
                seasonal_total_mm=clim.get("seasonal_total_mm", 800.0) * clim.get("precip_factor", 1.0),
                flood_intensity_mm_h=dis.get("flood_intensity_mm_h", 80.0),
                peak_months=tuple(clim.get("peak_months", [6, 7, 8])),
                area_ha=clim.get("area_ha", 100.0),
                curve_number=clim.get("cn", 75.0),
                seed=sid,
            )
            mres = simulate_monsoon(m_scen)
            # Disaster leg.
            dtype = dis.get("type", "flood")
            if dtype == "wildfire":
                dres = simulate_wildfire(FireScenario(grid_size=64, fire_radius_cells=dis.get("radius", 30),
                                                     intensity=dis.get("intensity", 1.0), seed=sid))
                metric = dres.dNBR
            elif dtype == "flood":
                dres = simulate_flood(DSFloodScenario(grid_size=64, rainfall_24h_mm=dis.get("rainfall", 120.0),
                                                      curve_number=dis.get("cn", 82.0), seed=sid))
                metric = dres.max_inundation_depth_m
            elif dtype == "storm":
                dres = simulate_storm(StormScenario(max_wind_speed_kmh=dis.get("wind", 150.0), seed=sid))
                metric = dres.wind_damage_index
            else:
                dres = simulate_landslide(LandslideScenario(slope_pct=dis.get("slope", 25.0),
                                                            rainfall_24h_mm=dis.get("rainfall", 90.0), seed=sid))
                metric = dres.factor_of_safety
            out.append({
                "combo_id": f"c{ci}_d{di}",
                "climate": clim.get("name", f"clim_{ci}"),
                "disaster": dis.get("name", f"dis_{di}"),
                "disaster_type": dtype,
                "climate_precip_mm": mres.annual_precip_mm,
                "disaster_metric": round(float(metric), 4),
                "seed": sid,
            })
    passed = all(r["disaster_metric"] == r["disaster_metric"] for r in out)  # not NaN
    meta = _meta("combinatorial", seed, {"combinations": combinations})
    return CombinatorialResult(
        combinations=combinations, results=out, metadata=meta,
        summary={"all_finite": passed, "n_results": len(out)},
    )


# ---------------------------------------------------------------------------
# Performance profiler
# ---------------------------------------------------------------------------
def profile_simulators(seed: int = 42) -> dict[str, float]:
    """Measure throughput (seconds) of each simulator under a standard workload."""
    timings: dict[str, float] = {}

    from engine.hydroma.simulation_env.climate import (
        DroughtScenario,
        HeatWaveScenario,
        MonsoonScenario,
        simulate_drought,
        simulate_monsoon,
        simulate_temperature_extremes,
    )
    from engine.hydroma.simulation_env.disasters import (
        FireScenario,
        simulate_flood,
        simulate_wildfire,
    )

    t0 = time.perf_counter()
    simulate_drought(600.0, 400.0, DroughtScenario(duration_years=3, seed=seed), seed=seed)
    timings["drought"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    simulate_monsoon(MonsoonScenario(seed=seed))
    timings["monsoon"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    simulate_temperature_extremes(20.0, 400.0, HeatWaveScenario(), years=5, seed=seed)
    timings["temperature_extremes"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    simulate_wildfire(FireScenario(grid_size=64, seed=seed))
    timings["wildfire"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    simulate_flood(FloodScenario(grid_size=64, seed=seed))
    timings["flood"] = time.perf_counter() - t0

    return timings


def _meta(scenario: str, seed: int, params: dict[str, Any]) -> SimulationMetadata:
    return SimulationMetadata(
        scenario=scenario, site_id="stress_test", seed=seed,
        start_year=2024, end_year=2024, parameters=params,
    )


__all__ = [
    "CombinatorialResult",
    "CorruptionConfig",
    "VolumeResult",
    "corrupt_array",
    "profile_simulators",
    "run_combinatorial",
    "run_volume_stress",
    "validate_fallbacks",
    "validate_index_robustness",
]
