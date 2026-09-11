"""Natural disaster simulators for the Eco Nojin simulation environment.

Deterministic, seed-reproducible simulators for:

* **Wildfire** — pre/post NBR imagery -> dNBR burn-severity mapping and
  post-fire NDVI recovery tracking (Key & Benson 2006).
* **Flood / inundation** — synthetic DEM raster + SCS-CN runoff -> flood
  depth raster, inundation mask and sediment deposition (McCuen & Ewell).
* **Storm / hurricane** — wind-damage index, coastal erosion via wind-wave
  energy and infrastructure fragility curves.
* **Landslide / erosion** — infinite-slope stability, topographic change and
  watershed sediment-yield impact.

All outputs are synthetic (raster data is generated procedurally) and tagged
``data_source="simulated"``.  No external API or measured raster is required.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from engine.hydroma.simulation_env.contracts import (
    Severity,
    SimulationMetadata,
)


def _metadata(scenario: str, seed: int, params: dict[str, Any]) -> SimulationMetadata:
    return SimulationMetadata(
        scenario=scenario,
        site_id=params.get("site_id", "unknown"),
        seed=seed,
        start_year=params.get("start_year", 2024),
        end_year=params.get("end_year", 2024),
        parameters=params,
    )


def _severity_band(value: float, thresholds: dict[str, float]) -> str:
    if value >= thresholds["extreme"]:
        return Severity.EXTREME.value
    if value >= thresholds["severe"]:
        return Severity.SEVERE.value
    if value >= thresholds["moderate"]:
        return Severity.MODERATE.value
    return Severity.MILD.value


# ---------------------------------------------------------------------------
# Wildfire
# ---------------------------------------------------------------------------
@dataclass
class FireScenario:
    grid_size: int = 128
    fire_center: tuple[int, int] | None = None  # row, col; if None random
    fire_radius_cells: int = 40
    intensity: float = 1.0  # 0.0-1.0
    severity_dNBR_thresholds: dict[str, float] | None = None
    recovery_years: int = 10
    seed: int = 42


@dataclass
class FireResult:
    pre_nbr: float
    post_nbr: float
    dNBR: float
    burn_severity: str
    burned_area_ha: float
    economic_loss_usd: float
    recovery_curve: list[float]
    post_fire_ndvi: float
    metadata: SimulationMetadata
    raster: dict[str, np.ndarray]


# dNBR burn-severity thresholds (Key & Benson 2006, scaled).
DEFAULT_FIRE_THRESHOLDS = {
    "low": 0.10,
    "moderate": 0.27,
    "high": 0.44,
    "extreme": 0.66,
}


def _synthetic_bands(grid: int, rng: np.random.Generator, ndvi_base: float) -> dict[str, np.ndarray]:
    """Generate synthetic pre-fire NIR/Red/Green bands (0-1 reflectance)."""
    nir = rng.uniform(0.35, 0.65, size=(grid, grid)) + ndvi_base * 0.15
    red = rng.uniform(0.05, 0.12, size=(grid, grid))
    green = rng.uniform(0.06, 0.14, size=(grid, grid))
    nir = np.clip(nir, 0.0, 1.0)
    return {"nir": nir, "red": red, "green": green}


def simulate_wildfire(scenario: FireScenario) -> FireResult:
    """Simulate a wildfire: burn-severity mapping from dNBR + recovery track.

    Reuses ``calculate_nbr`` / ``calculate_ndvi`` from the satellite processor
    so the severity classification is consistent with the production stack.
    """
    from engine.hydroma.satellite.processors.indices import calculate_nbr, calculate_ndvi

    rng = np.random.default_rng(scenario.seed)
    grid = scenario.grid_size
    if scenario.fire_center is None:
        cy, cx = int(rng.integers(grid // 4, 3 * grid // 4)), int(rng.integers(grid // 4, 3 * grid // 4))
    else:
        cy, cx = scenario.fire_center

    pre = _synthetic_bands(grid, rng, ndvi_base=0.5)
    post = _synthetic_bands(grid, rng, ndvi_base=0.5)

    # Impose fire damage in a disk around the fire centre.
    yy, xx = np.ogrid[:grid, :grid]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    mask = dist <= scenario.fire_radius_cells
    damage = np.clip(1.0 - dist / (scenario.fire_radius_cells + 1.0), 0.0, 1.0) * scenario.intensity
    # NIR drops, Red slightly drops (ash), SWIR concept: increase NIR reflectance post-fire
    post["nir"] = np.clip(post["nir"] * (1.0 - 0.7 * damage), 0.0, 1.0)
    post["red"] = np.clip(post["red"] * (1.0 - 0.3 * damage), 0.0, 1.0)
    # Add a SWIR-like band (post-fire increases SWIR via bare soil).
    swir_pre = rng.uniform(0.05, 0.12, size=(grid, grid))
    swir_post = np.clip(swir_pre + 0.25 * damage, 0.0, 1.0)

    pre_nbr = float(np.median(calculate_nbr(pre["nir"], swir_pre)))
    post_nbr = float(np.median(calculate_nbr(post["nir"], swir_post)))
    dnbr = pre_nbr - post_nbr

    th = scenario.severity_dNBR_thresholds or DEFAULT_FIRE_THRESHOLDS
    if dnbr < th["low"]:
        burn_severity = "unburned"
    elif dnbr < th["moderate"]:
        burn_severity = "low"
    elif dnbr < th["high"]:
        burn_severity = "moderate"
    elif dnbr < th["extreme"]:
        burn_severity = "high"
    else:
        burn_severity = "extreme"

    burned_pixels = int(np.count_nonzero(mask))
    burned_area_ha = burned_pixels / (grid * grid) * 10000.0  # ~1 ha per pixel at 100m resolution

    # Post-fire recovery (logistic NDVI over years).
    post_ndvi = float(np.median(calculate_ndvi(post["red"], post["nir"])))
    K = 0.5
    r = 1.0 / max(scenario.recovery_years / 3.0, 1.0)
    recovery_curve = [
        round(post_ndvi + (K - post_ndvi) * (1 - math.exp(-r * y)), 4)
        for y in range(scenario.recovery_years + 1)
    ]

    metadata = _metadata("wildfire", scenario.seed, {
        "site_id": "synth_wildfire",
        "grid_size": grid,
        "fire_radius_cells": scenario.fire_radius_cells,
        "intensity": scenario.intensity,
    })
    metadata.parameters["provenance"] = "simulated"

    economic_loss_usd = burned_area_ha * 350.0 * {"low": 0.1, "moderate": 0.4, "high": 0.7, "extreme": 1.0, "unburned": 0.0}.get(burn_severity, 0.0)

    return FireResult(
        pre_nbr=round(pre_nbr, 4),
        post_nbr=round(post_nbr, 4),
        dNBR=round(dnbr, 4),
        burn_severity=burn_severity,
        burned_area_ha=round(burned_area_ha, 2),
        economic_loss_usd=round(economic_loss_usd, 2),
        recovery_curve=recovery_curve,
        post_fire_ndvi=round(post_ndvi, 4),
        metadata=metadata,
        raster={"pre_nir": pre["nir"], "post_nir": post["nir"], "damage": damage, "burned_mask": mask.astype(np.uint8)},
    )


# ---------------------------------------------------------------------------
# Flood / inundation
# ---------------------------------------------------------------------------
@dataclass
class FloodScenario:
    grid_size: int = 64
    dem_mean_m: float = 50.0
    valley_depth_m: float = 8.0
    rainfall_24h_mm: float = 120.0
    area_ha: float = 100.0
    curve_number: float = 82.0
    soil_texture: str = "clay_loam"
    seed: int = 42


@dataclass
class FloodResult:
    peak_runoff_m3s: float
    flood_volume_m3: float
    max_inundation_depth_m: float
    inundation_fraction: float
    sediment_deposition_t: float
    metadata: SimulationMetadata
    raster: dict[str, np.ndarray]


def _synthetic_dem(grid: int, rng: np.random.Generator, mean_m: float, valley_depth: float) -> np.ndarray:
    """Procedurally generate a DEM with a central valley (Gaussian basin)."""
    yy, xx = np.mgrid[0:grid, 0:grid]
    center = grid / 2.0
    radius = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
    valley = valley_depth * np.exp(-((radius / (grid * 0.35)) ** 2))
    terrain = np.sin(xx * 0.3) * 0.5 + np.cos(yy * 0.2) * 0.5
    dem = mean_m - valley + terrain + rng.normal(0, 0.5, size=(grid, grid))
    return np.clip(dem, 0.1, None)


def simulate_flood(scenario: FloodScenario) -> FloodResult:
    """Simulate flash-flood inundation over a synthetic DEM using SCS-CN."""
    rng = np.random.default_rng(scenario.seed)
    grid = scenario.grid_size
    dem = _synthetic_dem(grid, rng, scenario.dem_mean_m, scenario.valley_depth_m)

    # Slope and flow direction (simple D8 steepest descent).
    gx, gy = np.gradient(dem)
    slope = np.sqrt(gx**2 + gy**2)
    slope_pct = np.degrees(np.arctan(slope)) * 100.0

    # SCS-CN runoff depth for the event.
    cn = scenario.curve_number
    s = 1000.0 / cn - 10.0
    p = scenario.rainfall_24h_mm
    runoff_depth = max(0.0, (p - 0.2 * s) ** 2 / (p + 0.8 * s)) if p > 0.2 * s else 0.0
    cell_area_ha = scenario.area_ha / (grid * grid)
    runoff_vol_m3 = runoff_depth * cell_area_ha * 10.0  # mm -> m3

    # Flow accumulation proxy: distance to the lowest neighbour valley.
    # Lower cells accumulate more flow; inundation depth decays with distance
    # from the depression minimum.
    depress = dem - dem.min()
    depth = np.where(depress < runoff_depth * 1.5, runoff_depth - depress, 0.0)
    depth = np.clip(depth, 0.0, None)
    inundated = depth > 0.0
    inundation_fraction = float(inundated.mean())
    max_depth = float(depth.max()) if depth.size else 0.0

    # Sediment deposition (mg/m3 ~ t on the deposited area); scale with slope & discharge.
    sediment_deposition_t = runoff_vol_m3 * 0.05 * (slope_pct.mean() / 5.0) * cn / 80.0

    peak_flow_m3s = runoff_vol_m3 / (24.0 * 3600.0) if runoff_vol_m3 > 0 else 0.0

    metadata = _metadata("flood_inundation", scenario.seed, {
        "site_id": "synth_flood",
        "grid_size": grid,
        "rainfall_24h_mm": scenario.rainfall_24h_mm,
        "curve_number": cn,
        "area_ha": scenario.area_ha,
    })
    metadata.parameters["provenance"] = "simulated"
    metadata.parameters["flood_severity"] = _severity_band(
        inundation_fraction, {"moderate": 0.05, "severe": 0.20, "extreme": 0.50}
    )

    return FloodResult(
        peak_runoff_m3s=round(peak_flow_m3s, 4),
        flood_volume_m3=round(runoff_vol_m3, 2),
        max_inundation_depth_m=round(max_depth, 3),
        inundation_fraction=round(inundation_fraction, 4),
        sediment_deposition_t=round(sediment_deposition_t, 3),
        metadata=metadata,
        raster={"dem": dem, "depth": depth, "inundated": inundated.astype(np.uint8), "slope_pct": slope_pct},
    )


# ---------------------------------------------------------------------------
# Storm / hurricane
# ---------------------------------------------------------------------------
@dataclass
class StormScenario:
    max_wind_speed_kmh: float = 180.0
    radius_km: float = 80.0
    duration_h: float = 12.0
    fetch_km: float = 100.0
    coastal: bool = True
    vegetation_height_m: float = 2.0
    infrastructure_exposure: float = 0.6  # 0-1 fraction of assets in path
    seed: int = 42


@dataclass
class StormResult:
    wind_damage_index: float
    coastal_eroding_m: float
    structures_destroyed: int
    affected_area_ha: float
    total_loss_usd: float
    metadata: SimulationMetadata


def simulate_storm(scenario: StormScenario) -> StormResult:
    """Simulate hurricane/storm impact: wind damage, coastal erosion, losses."""
    # Wind damage index ( normalised 0-1; exponential damage law )
    # V = wind speed; damage ~ 1 - exp(-((V - V_thresh)/scale))
    v_thresh = 120.0
    scale = 45.0
    wind_damage_index = float(np.clip(1.0 - math.exp(-(max(scenario.max_wind_speed_kmh - v_thresh, 0.0)) / scale), 0.0, 1.0))

    # Coastal erosion via wind-wave setup ( Kamphuis 2010 simplified ).
    if scenario.coastal:
        g = 9.81
        # Significant wave height (wind-sea)
        u10 = scenario.max_wind_speed_kmh / 3.6
        hs = 0.22 * (u10**2 / g) * (1.0 - math.exp(-0.0016 * (u10**2 / g)))
        # Wave energy flux -> erosion (empirical m/MJ*m)
        ho = hs * 0.5
        coastal_eroding_m = float(0.05 * ho * scenario.duration_h * wind_damage_index)
    else:
        coastal_eroding_m = 0.0

    # Vegetation wind damage probability (depends on wind vs vegetation drag).
    veg_damage_prob = float(np.clip((scenario.max_wind_speed_kmh - 90.0) / 90.0, 0.0, 1.0))
    affected_area_ha = scenario.radius_km * scenario.radius_km * 3.14159 * 100.0 * veg_damage_prob

    # Infrastructure fragility (log-normal style).
    fragility = float(np.clip(1.0 - math.exp(-((scenario.max_wind_speed_kmh - 100.0) / 35.0)), 0.0, 1.0))
    structures_destroyed = int(scenario.infrastructure_exposure * 1000.0 * fragility)
    crop_loss = affected_area_ha * 400.0
    struct_loss = structures_destroyed * 12000.0
    coastal_loss = coastal_eroding_m * 5000.0 if scenario.coastal else 0.0
    total_loss_usd = crop_loss + struct_loss + coastal_loss

    metadata = _metadata("storm_hurricane", scenario.seed, {
        "site_id": "synth_storm",
        "max_wind_speed_kmh": scenario.max_wind_speed_kmh,
        "coastal": scenario.coastal,
        "radius_km": scenario.radius_km,
        "duration_h": scenario.duration_h,
    })
    metadata.parameters["provenance"] = "simulated"

    return StormResult(
        wind_damage_index=round(wind_damage_index, 3),
        coastal_eroding_m=round(coastal_eroding_m, 3),
        structures_destroyed=structures_destroyed,
        affected_area_ha=round(affected_area_ha, 2),
        total_loss_usd=round(total_loss_usd, 0),
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Landslide / erosion
# ---------------------------------------------------------------------------
@dataclass
class LandslideScenario:
    grid_size: int = 48
    slope_pct: float = 25.0
    cohesion_kpa: float = 15.0
    phi_deg: float = 30.0
    soil_depth_m: float = 1.5
    rainfall_24h_mm: float = 90.0
    vegetation_reduction: float = 0.7  # root reinforcement factor
    area_ha: float = 50.0
    seed: int = 42


@dataclass
class LandslideResult:
    factor_of_safety: float
    failure_probability: float
    displaced_volume_m3: float
    sediment_yield_t: float
    affected_area_fraction: float
    metadata: SimulationMetadata
    raster: dict[str, np.ndarray]


def _infinite_slope_fs(slope_pct: float, cohesion_kpa: float, phi_deg: float,
                       soil_depth_m: float, vegetation_reduction: float,
                       rainfall_mm: float, gamma_sat: float = 18.0,
                       gamma_w: float = 9.81) -> tuple[float, float]:
    """Infinite-slope factor of safety after rainfall infiltration.

    FS = [c' + (gamma_sat - m*gamma_w) * z * cos(B) * tan(phi')] /
         [gamma_sat * z * sin(B)]
    where m = rain_saturation_factor * (1 - vegetation_reduction).
    """
    beta = math.radians(slope_pct / 100.0)
    phi = math.radians(phi_deg)
    c = cohesion_kpa  # kPa
    z = soil_depth_m  # m
    # Rain infiltration raises pore pressure: m approximates saturation fraction.
    sat_frac = float(np.clip(rainfall_mm / 150.0, 0.0, 1.0))
    m = sat_frac * (1.0 - vegetation_reduction)
    effective_unit_weight = gamma_sat - m * gamma_w
    shear_strength = c + effective_unit_weight * z * math.cos(beta) * math.tan(phi)
    driving = gamma_sat * z * math.sin(beta) * math.cos(beta)
    fs = shear_strength / max(driving, 1e-6)
    return fs, m


def simulate_landslide(scenario: LandslideScenario) -> LandslideResult:
    """Simulate slope-stability failure, topographic change and sediment yield."""
    rng = np.random.default_rng(scenario.seed)
    grid = scenario.grid_size

    fs, _m = _infinite_slope_fs(
        scenario.slope_pct, scenario.cohesion_kpa, scenario.phi_deg,
        scenario.soil_depth_m, scenario.vegetation_reduction, scenario.rainfall_24h_mm,
    )
    # Spatial variability: perturb cohesion across the slope.
    cohesion_field = scenario.cohesion_kpa * (0.7 + 0.6 * rng.random(size=(grid, grid)))
    slope_field = scenario.slope_pct * (0.85 + 0.3 * rng.random(size=(grid, grid)))

    fs_arr = np.empty((grid, grid), dtype=float)
    for i in range(grid):
        for j in range(grid):
            fsi, _ = _infinite_slope_fs(
                float(slope_field[i, j]), float(cohesion_field[i, j]),
                scenario.phi_deg, scenario.soil_depth_m,
                scenario.vegetation_reduction, scenario.rainfall_24h_mm,
            )
            fs_arr[i, j] = fsi
    fs = float(np.nanmedian(fs_arr))

    failure_probability = float(np.clip(1.0 - fs, 0.0, 1.0))
    failure_mask = fs_arr < 1.0
    affected_fraction = float(failure_mask.mean())

    displaced_volume_m3 = float(np.count_nonzero(failure_mask)) * scenario.soil_depth_m * 25.0  # ~25 m2 per cell
    # Sediment yield (t) = displaced volume * bulk density * affected fraction * erosion factor.
    bulk_density = 1.4
    sediment_yield_t = displaced_volume_m3 * bulk_density * 0.8 * (scenario.rainfall_24h_mm / 100.0)

    metadata = _metadata("landslide_erosion", scenario.seed, {
        "site_id": "synth_landslide",
        "grid_size": grid,
        "slope_pct": scenario.slope_pct,
        "cohesion_kpa": scenario.cohesion_kpa,
        "phi_deg": scenario.phi_deg,
        "rainfall_24h_mm": scenario.rainfall_24h_mm,
        "vegetation_reduction": scenario.vegetation_reduction,
    })
    metadata.parameters["provenance"] = "simulated"
    metadata.parameters["landslide_severity"] = _severity_band(fs, {"moderate": 1.3, "severe": 1.0, "extreme": 0.7})

    return LandslideResult(
        factor_of_safety=round(fs, 3),
        failure_probability=round(failure_probability, 3),
        displaced_volume_m3=round(displaced_volume_m3, 2),
        sediment_yield_t=round(sediment_yield_t, 2),
        affected_area_fraction=round(affected_fraction, 4),
        metadata=metadata,
        raster={"fs": fs_arr, "slope": slope_field, "cohesion": cohesion_field, "failure": failure_mask.astype(np.uint8)},
    )


# Re-exported helper for completeness.
__all__ = [
    "FireResult",
    "FireScenario",
    "FloodResult",
    "FloodScenario",
    "LandslideResult",
    "LandslideScenario",
    "StormResult",
    "StormScenario",
    "simulate_flood",
    "simulate_landslide",
    "simulate_storm",
    "simulate_wildfire",
]
