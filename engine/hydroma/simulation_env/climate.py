"""Climatic profile simulators for the Eco Nojin simulation environment.

Provides deterministic, seed-reproducible simulators for:

* **Drought stress progression** — multi-year droughts with severity
  trajectories and cascading impacts on soil moisture, NDVI and yields.
* **Monsoon / flood cycles** — seasonal precipitation bursts, flood
  inundation depth and erosion under extreme rainfall events.
* **Temperature extremes** — heat-wave and frost-event generators with growing
  season shifts.
* **Climate change projections** — RCP/SSP scenario emulation with
  multi-decadal vegetation shifts (re-uses the existing SSP machinery).

All outputs are synthetic and carry a ``data_source="simulated"`` provenance
block.  No external API is required for the core logic.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from engine.hydroma.climate_adaptation.multi_stress_engine import (
    drought_heat_salinity_stress,
)
from engine.hydroma.scenarios.climate_scenarios import (
    apply_climate_change,
    get_climate_projection,
)
from engine.hydroma.scenarios.crop_scenarios import simulate_crop_yield
from engine.hydroma.scenarios.monte_carlo import monte_carlo_yield
from engine.hydroma.simulation_env.contracts import (
    AnnualImpact,
    Severity,
    SimulationMetadata,
)
from engine.hydroma.simulation_env.weather import (
    WeatherConfig,
    generate_daily_weather,
    hargreaves_et0,
)
from engine.hydroma.soil.physics import available_water_capacity


_BASE_SM = 0.5  # initial soil-moisture fraction of TAW

def _soil_bucket(daily: pd.DataFrame, awc_mm: float, root_depth_mm: float = 600.0) -> pd.DataFrame:
    """Simple two-reservoir soil moisture bucket (mm).

    *taw* = total available water in the root zone (awc [cm3/cm3] x root depth
    [mm] -> mm of water).  Runoff occurs when the bucket exceeds *taw*;
    drainage is lost.  Plant water stress is derived from the depletion
    fraction.
    """
    taw = awc_mm * root_depth_mm  # awc is dimensionless -> mm over root zone
    taw = max(taw, 10.0)
    sm = np.full(len(daily), taw * _BASE_SM)  # start at half-full
    et = np.zeros(len(daily))
    for i in range(len(daily)):
        precip = float(daily["precip"].iloc[i])
        et0 = float(daily["et0"].iloc[i])
        kc = 0.7  # generic herbaceous crop mid-season coefficient
        etc = et0 * kc
        sm[i] += precip
        et[i] = min(sm[i], etc)
        sm[i] -= et[i]
        if sm[i] > taw:
            sm[i] = taw  # drainage
        sm[i] = max(sm[i], 0.0)
    daily = daily.assign(soil_moisture=sm, etc=et)
    daily["sm_fraction"] = daily["soil_moisture"] / taw
    return daily


def _ndvi_from_sm(sm_fraction: float, base_ndvi: float = 0.5) -> float:
    """Empirical NDVI response to soil-moisture stress (linear below 0.5)."""
    stress = 1.0 - sm_fraction
    ndvi = base_ndvi * (1.0 - 0.6 * stress)
    return float(np.clip(ndvi, 0.0, 1.0))


def _base_metadata(scenario: str, seed: int, params: dict[str, Any]) -> SimulationMetadata:
    return SimulationMetadata(
        scenario=scenario,
        site_id=params.get("site_id", "unknown"),
        seed=seed,
        start_year=params.get("start_year", 2024),
        end_year=params.get("end_year", 2024 + params.get("duration_years", 5) - 1),
        parameters=params,
    )


# ---------------------------------------------------------------------------
# Drought stress progression
# ---------------------------------------------------------------------------
@dataclass
class DroughtScenario:
    """Definition of a progressing drought event."""

    severity: str = Severity.MODERATE.value
    duration_years: int = 5
    max_precip_reduction: float = 0.4  # down to 40% of baseline by end
    max_temp_increase_c: float = 3.0
    onset_year_offset: int = 0  # years from start before drought ramps in
    flash_drought: bool = False  # single-year precip collapse

    def trajectory(self) -> Callable[[int], tuple[float, float]]:
        """Return year -> (precip_factor, temp_offset)."""
        severity_map: dict[str, tuple[float, float]] = {
            Severity.MILD.value: (0.75, 1.5),
            Severity.MODERATE.value: (0.5, 2.5),
            Severity.SEVERE.value: (0.3, 3.5),
            Severity.EXTREME.value: (0.15, 5.0),
        }
        target_pref, target_toff = severity_map.get(self.severity, severity_map[Severity.MODERATE.value])
        if self.flash_drought:
            target_pref = max(target_pref, 0.1)

        def traj(year: int) -> tuple[float, float]:
            if self.flash_drought:
                # collapse in year 0, then slow recovery
                if year == 0:
                    return (0.2, 4.0)
                return (0.2 + 0.15 * year, 4.0 - 1.5 * year)
            ramp = 0.0
            if year >= self.onset_year_offset:
                rel = (year - self.onset_year_offset) / max(self.duration_years, 1)
                ramp = min(1.0, rel)
            pf = 1.0 - (1.0 - target_pref) * ramp
            toff = target_toff * ramp
            return (pf, toff)

        return traj


@dataclass
class DroughtResult:
    """Output of a drought stress progression simulation."""

    annual_impacts: list[AnnualImpact]
    daily_weather: pd.DataFrame | None = None
    drought_curve: list[dict[str, float]] = field(default_factory=list)
    metadata: SimulationMetadata | None = None
    summary: dict[str, Any] = field(default_factory=dict)


def simulate_drought(
    baseline_temp_c: float,
    baseline_precip_mm: float,
    scenario: DroughtScenario,
    lat: float = 35.0,
    crop: str = "wheat",
    seed: int = 42,
    soil_texture: str = "loam",
) -> DroughtResult:
    """Run a multi-year drought stress progression simulation.

    Builds on:
      * ``WeatherConfig`` synthetic weather generator
      * Soil moisture bucket model (root-zone water balance)
      * ``simulate_crop_yield`` (FAO AquaCrop water-balance yield)
      * NDVI stress response and the multi-stress engine for combined index.
    """
    awc = available_water_capacity(soil_texture)

    metadata = _base_metadata(
        f"drought_{scenario.severity}",
        seed,
        {
            "site_id": f"synth_drought_{seed}",
            "lat": lat,
            "crop": crop,
            "soil_texture": soil_texture,
            "severity": scenario.severity,
            "duration_years": scenario.duration_years,
            "max_precip_reduction": scenario.max_precip_reduction,
            "max_temp_increase_c": scenario.max_temp_increase_c,
            "flash_drought": scenario.flash_drought,
        },
    )

    traj = scenario.trajectory()
    annual_impacts: list[AnnualImpact] = []
    drought_curve: list[dict[str, float]] = []
    daily_frames: list[pd.DataFrame] = []

    base_ndvi = 0.5

    for yi in range(scenario.duration_years):
        year = 2024 + yi
        pf, toff = traj(yi)
        # Annual aggregate via a 1-year synthetic daily run.
        wcfg = WeatherConfig(
            lat=lat,
            lon=35.0,
            start=date(year, 1, 1),
            end=date(year, 12, 31),
            baseline_temp_c=baseline_temp_c,
            baseline_precip_mm=baseline_precip_mm,
            seed=seed + yi,
            temp_offset_c=toff,
            precip_multiplier=pf,
        )
        daily = generate_daily_weather(wcfg)
        bucket = _soil_bucket(daily, awc)

        growing = bucket[bucket["month"].isin([4, 5, 6, 7, 8, 9])]
        gs_water_avail = float(growing["precip"].sum())
        gs_sm_mean = float(growing["sm_fraction"].mean())
        annual_precip = float(bucket["precip"].sum())
        annual_et0 = float(bucket["et0"].sum())
        annual_sm = float(bucket["soil_moisture"].mean())
        sm_frac = float(gs_sm_mean)

        yield_res = simulate_crop_yield(
            crop_type=crop,
            available_water=gs_water_avail,
            mean_temp=float(bucket["tmax"].mean()),
            irrigation_efficiency=0.6,
        )
        ndvi = _ndvi_from_sm(gs_sm_mean, base_ndvi=base_ndvi)

        stress = drought_heat_salinity_stress(
            temp=float(bucket["tmax"].mean()),
            rain=annual_precip,
            ec=1.0,
        )

        annual_impacts.append(
            AnnualImpact(
                year=year,
                temperature_c=round(float(bucket["tmax"].mean() + bucket["tmin"].mean()) / 2.0, 2),
                precipitation_mm=round(annual_precip, 1),
                et0_mm=round(annual_et0, 1),
                soil_moisture_mm=round(annual_sm, 1),
                soil_moisture_fraction=round(sm_frac, 3),
                ndvi=round(ndvi, 3),
                crop_yield_kg_ha=float(yield_res["actual_yield_kg_ha"]),
                erosion_t_ha=0.0,
                drought_stress=round(stress["drought_stress"], 3),
                severity=_severity_from_sm(sm_frac),
            )
        )
        drought_curve.append({"year": year, "precip_factor": round(pf, 3), "temp_offset_c": round(toff, 3)})
        daily_frames.append(bucket)

    summary = {
        "cumulative_yield_loss_pct": round(
            (1.0 - annual_impacts[-1].crop_yield_kg_ha / max(annual_impacts[0].crop_yield_kg_ha, 0.01)) * 100.0
            if annual_impacts else 0.0,
            2,
        ),
        "ndvi_min": round(min(a.ndvi for a in annual_impacts), 3) if annual_impacts else 0.0,
        "ndvi_max": round(max(a.ndvi for a in annual_impacts), 3) if annual_impacts else 0.0,
        "final_soil_moisture_fraction": annual_impacts[-1].soil_moisture_fraction if annual_impacts else 0.0,
    }

    daily_weather = pd.concat(daily_frames) if daily_frames else None
    metadata.parameters["provenance"] = "simulated"
    return DroughtResult(
        annual_impacts=annual_impacts,
        daily_weather=daily_weather,
        drought_curve=drought_curve,
        metadata=metadata,
        summary=summary,
    )


def _severity_from_sm(sm: float) -> str:
    if sm < 0.15:
        return Severity.SEVERE.value
    if sm < 0.3:
        return Severity.MODERATE.value
    return Severity.MILD.value


# ---------------------------------------------------------------------------
# Monsoon / flood cycles
# ---------------------------------------------------------------------------
@dataclass
class MonsoonScenario:
    """A monsoon season with an embedded extreme-rainfall flood event."""

    peak_months: tuple[int, ...] = (6, 7, 8)
    flood_day: int = 180  # day-of-year of peak flood
    flood_intensity_mm_h: float = 80.0  # 24h equivalent
    flood_duration_h: float = 12.0
    seasonal_total_mm: float = 800.0
    area_ha: float = 100.0
    curve_number: float = 75.0
    slope_pct: float = 3.0
    soil_texture: str = "loam"
    soil_depth_mm: float = 1000.0


@dataclass
class MonsoonResult:
    annual_precip_mm: float
    peak_24h_precip_mm: float
    runoff_volume_m3: float
    flood_depth_mm: float
    sediment_yield_t: float
    daily_weather: pd.DataFrame
    metadata: SimulationMetadata
    summary: dict[str, Any]


def simulate_monsoon(
    scenario: MonsoonScenario,
    lat: float = 25.0,
    seed: int = 42,
) -> MonsoonResult:
    """Simulate a monsoon cycle with an extreme flood event and resulting erosion."""
    rng = np.random.default_rng(seed)
    # Build a 1-year synthetic monsoon season.
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    dates = pd.date_range(start, end, freq="D")
    month = dates.month.to_numpy()
    doy = dates.dayofyear.to_numpy().astype(float)

    # Monsoon-seasonal precip fraction (Gaussian bump in peak months).
    peak = np.array(scenario.peak_months)
    bump = np.zeros_like(doy, dtype=float)
    for pm in peak:
        bump += np.exp(-0.5 * ((doy - (pm * 30.44)) / 25.0) ** 2)
    bump = bump / bump.max() if bump.max() > 0 else bump
    # Distribute seasonal_total across the year using the bump.
    daily_mean = scenario.seasonal_total_mm * bump / bump.sum() if bump.sum() > 0 else np.full_like(doy, scenario.seasonal_total_mm / 365)

    is_wet = rng.random(size=len(dates)) < np.clip(0.4 * bump, 0.0, 0.9)
    raw = rng.exponential(scale=1.0, size=len(dates))
    raw[~is_wet] = 0.0
    ws = float(raw.sum())
    if ws > 0:
        raw = raw * (float(daily_mean.sum()) / ws)

    # Inject the flood event around flood_day.
    flood_days = int(scenario.flood_duration_h / 24.0) or 1
    flood_start = int(scenario.flood_day)
    for d in range(flood_start, min(flood_start + flood_days, len(dates))):
        raw[d] += scenario.flood_intensity_mm_h * scenario.flood_duration_h / max(flood_days, 1)

    precip = np.clip(raw, 0.0, None)
    # Temperature: warm monsoon.
    tmean = 26.0 + 2.0 * np.cos(2 * np.pi * (doy - 200) / 365.0)
    tmin = tmean - 4.0
    tmax = tmean + 8.0
    et0 = np.array([hargreaves_et0(float(tmin[i]), float(tmax[i]), lat, int(doy[i])) for i in range(len(dates))])

    df = pd.DataFrame(
        {"tmin": tmin, "tmax": tmax, "precip": precip, "et0": et0, "month": month, "year": 2024},
        index=pd.DatetimeIndex(dates),
    ).rename_axis("date")

    peak_24h = float(df["precip"].rolling(24, min_periods=1).sum().max())

    # SCS-CN runoff (event scale): Q = (P - 0.2*S)^2 / (P + 0.8*S), S = 1000/CN - 10
    cn = scenario.curve_number
    s = 1000.0 / cn - 10.0
    total_p = float(df["precip"].sum())
    runoff_depth = max(0.0, (total_p - 0.2 * s) ** 2 / (total_p + 0.8 * s)) if total_p > 0.2 * s else 0.0
    area_m2 = scenario.area_ha * 10000.0
    runoff_vol_m3 = runoff_depth * area_m2 / 1000.0

    # Flood inundation depth (rough): assume 30% of runoff volume spreads over flood-prone area.
    flood_prone_area = area_m2 * 0.3
    flood_depth = (runoff_vol_m3 / flood_prone_area) * 1000.0 if flood_prone_area > 0 else 0.0

    # Erosion via simplified RUSLE-like scaling with event rainfall + slope.
    rain_excess_energy = total_p * (0.5 + 0.01 * scenario.slope_pct)
    k_soil = 0.04  # generic silt-loam erodibility t-1
    ls = 1.5 + 0.02 * scenario.slope_pct
    sediment_yield_t = rain_excess_energy * k_soil * ls * cn / 80.0

    metadata = _base_metadata(
        "monsoon_flood",
        seed,
        {
            "site_id": "synth_monsoon",
            "lat": lat,
            "area_ha": scenario.area_ha,
            "curve_number": cn,
            "flood_intensity_mm_h": scenario.flood_intensity_mm_h,
            "peak_months": list(scenario.peak_months),
        },
    )
    metadata.parameters["provenance"] = "simulated"

    summary = {
        "flood_risk": "extreme" if flood_depth > 50 else "moderate" if flood_depth > 20 else "low",
        "erosion_risk": "high" if sediment_yield_t > 5 else "moderate" if sediment_yield_t > 1 else "low",
        "runoff_volume_m3": round(runoff_vol_m3, 2),
    }
    return MonsoonResult(
        annual_precip_mm=round(total_p, 1),
        peak_24h_precip_mm=round(peak_24h, 2),
        runoff_volume_m3=round(runoff_vol_m3, 2),
        flood_depth_mm=round(flood_depth, 2),
        sediment_yield_t=round(sediment_yield_t, 2),
        daily_weather=df,
        metadata=metadata,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Temperature extremes
# ---------------------------------------------------------------------------
@dataclass
class HeatWaveScenario:
    duration_days: int = 5
    intensity_c: float = 6.0  # anomaly above seasonal mean
    timing_doy: int = 200
    frequency_per_year: int = 1


def simulate_temperature_extremes(
    baseline_temp_c: float,
    baseline_precip_mm: float,
    heat_scenario: HeatWaveScenario | None = None,
    frost_days: int = 3,
    frost_min_c: float = -8.0,
    lat: float = 35.0,
    seed: int = 42,
    years: int = 10,
    crop: str = "wheat",
) -> dict[str, Any]:
    """Simulate heat-wave / frost scenarios and growing-season shifts.

    Returns a synthetic time-series of annual extremes plus a Monte-Carlo
    uncertainty envelope around projected crop yield under warming.
    """
    heat_scenario = heat_scenario or HeatWaveScenario()
    rng = np.random.default_rng(seed)
    start = date(2024, 1, 1)
    end = date(2024 + years - 1, 12, 31)
    dates = pd.date_range(start, end, freq="D")
    doy = dates.dayofyear.to_numpy().astype(float)
    year = dates.year.to_numpy()
    base_year = 2024

    phase = 2 * np.pi * (doy - 172) / 365.0
    seasonal = 7.0 * np.cos(phase)
    trend_c = 1.5 * (year - base_year) / max(years, 1)
    tmean = baseline_temp_c + seasonal + trend_c + rng.normal(0, 1.0, size=len(dates))

    # Inject heat waves.
    for _ in range(heat_scenario.frequency_per_year * years):
        yd = int(rng.integers(0, len(dates)))
        centre = yd
        half = heat_scenario.duration_days // 2
        lo = max(0, centre - half)
        hi = min(len(dates), centre + half)
        tmean[lo:hi] += heat_scenario.intensity_c

    tmin = tmean - 5.0
    tmax = tmean + 5.0

    # Inject frost events near start of year.
    frost_mask = rng.random(size=len(dates)) < (frost_days / 365.0)
    tmin = np.where(frost_mask, frost_min_c, tmin)

    annual = pd.DataFrame({"tmean": tmean, "tmin": tmin, "tmax": tmax, "year": year},
                          index=pd.DatetimeIndex(dates)).rename_axis("date")
    agg = annual.groupby("year").agg(
        mean_temp=("tmean", "mean"),
        max_temp=("tmax", "max"),
        min_temp=("tmin", "min"),
    )

    heat_wave_days = (annual["tmax"] > (baseline_temp_c + seasonal + heat_scenario.intensity_c + 5.0)).sum()
    frost_events = (annual["tmin"] < -5.0).sum()

    growing_window = baseline_precip_mm * 0.55  # ~55% of annual in growing season
    yield_mc = monte_carlo_yield(
        crop_type=crop,
        mean_water=growing_window,
        water_std=growing_window * 0.2,
        mean_temp=float(agg["mean_temp"].mean()) + 2.0,
        temp_std=2.0,
        n_simulations=200,
        seed=seed,
    )

    metadata = _base_metadata(
        "temperature_extremes",
        seed,
        {
            "site_id": "synth_temperature",
            "lat": lat,
            "years": years,
            "heat_intensity_c": heat_scenario.intensity_c,
            "frost_min_c": frost_min_c,
        },
    )
    metadata.parameters["provenance"] = "simulated"

    return {
        "heat_wave_days_total": int(heat_wave_days),
        "frost_events_total": int(frost_events),
        "annual_summary": agg.round(2).to_dict(orient="index"),
        "yield_uncertainty": yield_mc,
        "metadata": metadata.model_dump(),
        "summary": {
            "growing_season_shift_days": round((heat_scenario.intensity_c / 1.5) * 6),
            "frost_risk": "high" if frost_events > 10 else "moderate" if frost_events > 0 else "low",
        },
    }


# ---------------------------------------------------------------------------
# Climate change projections (RCP/SSP emulation)
# ---------------------------------------------------------------------------
def simulate_climate_change(
    baseline_temp_c: float,
    baseline_precip_mm: float,
    ssp: str,
    target_year: int,
    lat: float = 35.0,
    crop: str = "wheat",
    seed: int = 42,
    n_ensembles: int = 50,
) -> dict[str, Any]:
    """Emulate an RCP/SSP scenario and project multi-decadal vegetation shifts.

    Re-uses the existing SSP projection tables and Monte-Carlo yield engine so
    results stay consistent with the platform's scientific stack.
    """
    projection = get_climate_projection(ssp, target_year, baseline_temp_c, baseline_precip_mm, 1500.0)
    projected = apply_climate_change(baseline_temp_c, baseline_precip_mm, 1500.0, projection)

    # Multi-decadal vegetation shift: project yield under the new climate.
    baseline_yield = simulate_crop_yield(
        crop_type=crop,
        available_water=baseline_precip_mm * 0.55,
        mean_temp=baseline_temp_c,
    )
    projected_yield = simulate_crop_yield(
        crop_type=crop,
        available_water=projected["precipitation"] * 0.55,
        mean_temp=projected["temperature"],
    )

    # Uncertainty envelope.
    yield_mc = monte_carlo_yield(
        crop_type=crop,
        mean_water=projected["precipitation"] * 0.55,
        water_std=baseline_precip_mm * 0.55 * 0.2,
        mean_temp=projected["temperature"],
        temp_std=1.5,
        n_simulations=n_ensembles,
        seed=seed,
    )

    # Vegetation shift proxy: compare baseline vs projected NDVI-equivalent.
    ndvi_baseline = 0.5
    ndvi_projected = _ndvi_from_sm(max(0.3, 1.0 - projection.delta_precip / 100.0), ndvi_baseline)

    metadata = _base_metadata(
        f"climate_change_{ssp}_{target_year}",
        seed,
        {
            "site_id": "synth_climate_change",
            "lat": lat,
            "ssp": ssp,
            "target_year": target_year,
            "crop": crop,
            "n_ensembles": n_ensembles,
        },
    )
    metadata.parameters["provenance"] = "simulated"

    return {
        "projection": projection.model_dump(),
        "projected_climate": projected,
        "baseline_yield_kg_ha": baseline_yield["actual_yield_kg_ha"],
        "projected_yield_kg_ha": projected_yield["actual_yield_kg_ha"],
        "yield_change_pct": round(
            (projected_yield["actual_yield_kg_ha"] - baseline_yield["actual_yield_kg_ha"])
            / max(baseline_yield["actual_yield_kg_ha"], 1.0) * 100.0, 2
        ),
        "ndvi_baseline": ndvi_baseline,
        "ndvi_projected": round(ndvi_projected, 3),
        "yield_uncertainty": yield_mc,
        "metadata": metadata.model_dump(),
        "summary": {
            "confidence": projection.confidence,
            "vegetation_shift": "declining" if ndvi_projected < ndvi_baseline else "stable",
        },
    }


__all__ = [
    "DroughtResult",
    "DroughtScenario",
    "HeatWaveScenario",
    "MonsoonResult",
    "MonsoonScenario",
    "simulate_climate_change",
    "simulate_drought",
    "simulate_monsoon",
    "simulate_temperature_extremes",
]
