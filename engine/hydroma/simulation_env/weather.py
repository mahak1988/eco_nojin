"""Deterministic synthetic weather generator (no external API dependency).

Generates daily temperature / precipitation / reference-ET time-series using a
seasonal sinusoid plus seeded stochastic noise.  All data produced here is
explicitly synthetic and labelled as such by callers.

The generator is intentionally pure (no network) so that every simulator is
fully reproducible from a seed, which is a hard requirement for the stress
 testing framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from engine.hydroma.climate.et_calculator import calc_extraterrestrial_radiation
from engine.hydroma.simulation_env.contracts import (
    DEFAULT_MONTHLY_PRECT_FRAC,
    Provenance,
)


def hargreaves_et0(tmin: float, tmax: float, lat: float, doy: int) -> float:
    """FAO-56 Hargreaves-Samani ET0 (mm/day) from daily min/max temperature."""
    ra_mj = calc_extraterrestrial_radiation(lat, doy)
    ra_mm = ra_mj * 0.408  # MJ/m2/day -> mm/day
    tmean = (tmin + tmax) / 2.0
    dtr = max(tmax - tmin, 0.1)
    return max(0.0, 0.0023 * (tmean + 17.8) * (dtr**0.5) * ra_mm)


@dataclass
class WeatherConfig:
    """Configuration for a synthetic daily weather run."""

    lat: float
    lon: float
    start: date
    end: date
    baseline_temp_c: float
    baseline_precip_mm: float
    seed: int | None = None
    # Seasonal/trend perturbations
    temp_offset_c: float = 0.0
    precip_multiplier: float = 1.0
    temp_trend_c_per_yr: float = 0.0
    precip_trend_pct_per_yr: float = 0.0
    # Seasonal shape
    monthly_prect_frac: list[float] | None = None
    temp_seasonal_amp_c: float | None = None
    diurnal_range_c: float = 10.0
    wet_day_prob: float = 0.45
    summer_day_of_year: int = 172  # NH mid-summer
    # Drought trajectory: year -> (precip_factor, temp_offset) applied per calendar year.
    drought_trajectory: object | None = None


def generate_daily_weather(cfg: WeatherConfig) -> pd.DataFrame:
    """Generate a synthetic daily weather DataFrame.

    Returns a DataFrame indexed by date with columns ``tmin``, ``tmax``,
    ``precip`` and ``et0``.  Fully deterministic given ``cfg.seed``.
    """
    rng = np.random.default_rng(cfg.seed)
    dates = pd.date_range(cfg.start, cfg.end, freq="D")

    doy = dates.dayofyear.to_numpy().astype(float)
    year = dates.year.to_numpy().astype(int)
    base_year = int(cfg.start.year)

    monthly = cfg.monthly_prect_frac or DEFAULT_MONTHLY_PRECT_FRAC
    monthly = np.asarray(monthly, dtype=float)
    monthly = monthly / monthly.sum()

    # Seasonal temperature anomaly (cosine peak at summer_day).
    phase = 2.0 * np.pi * (doy - cfg.summer_day_of_year) / 365.0
    amp = cfg.temp_seasonal_amp_c if cfg.temp_seasonal_amp_c is not None else 6.0
    seasonal_temp = amp * np.cos(phase)

    tmean = cfg.baseline_temp_c + seasonal_temp + cfg.temp_offset_c
    tmean = tmean + cfg.temp_trend_c_per_yr * (year - base_year)

    # Drought trajectory: per-year (precip_factor, temp_offset).
    if cfg.drought_trajectory is not None:
        traj = np.array(
            [cfg.drought_trajectory(int(y)) for y in year], dtype=object
        )
        year_pmult = np.array([t[0] for t in traj], dtype=float)
        year_temp_off = np.array([t[1] for t in traj], dtype=float)
        tmean = tmean + year_temp_off
    else:
        year_pmult = np.full(doy.shape, cfg.precip_multiplier)

    tmin = tmean - cfg.diurnal_range_c / 2.0
    tmax = tmean + cfg.diurnal_range_c / 2.0

    tmin = tmin + rng.normal(0.0, 1.2, size=tmin.shape)
    tmax = tmax + rng.normal(0.0, 1.2, size=tmax.shape)
    bad = tmax < tmin
    tmax[bad] = tmin[bad] + 0.5

    # --- Precipitation -------------------------------------------------
    # Annual total decays/grows with trend + trajectory multiplier.
    annual_target = cfg.baseline_precip_mm * (
        (1.0 + cfg.precip_trend_pct_per_yr / 100.0) ** (year - base_year)
    ) * year_pmult

    month_idx = dates.month.to_numpy()
    monthly_frac_per_day = np.array([monthly[m - 1] for m in month_idx])
    daily_mean = annual_target * monthly_frac_per_day / 30.44

    # Seasonal wet-day probability.
    season_wet = 0.5 + 0.3 * np.cos(2.0 * np.pi * (month_idx - 1) / 12.0)
    p_wet = np.clip(cfg.wet_day_prob * season_wet, 0.05, 0.95)

    is_wet = rng.random(size=len(dates)) < p_wet
    raw = rng.exponential(scale=1.0, size=len(dates))
    raw[~is_wet] = 0.0
    wet_sum = float(raw.sum())
    if wet_sum > 0:
        raw = raw * (float(daily_mean.sum()) / wet_sum)
    precip = np.clip(raw, 0.0, None)

    et0 = np.array(
        [hargreaves_et0(float(tmin[i]), float(tmax[i]), cfg.lat, int(doy[i])) for i in range(len(dates))]
    )

    return pd.DataFrame(
        {
            "tmin": tmin,
            "tmax": tmax,
            "precip": precip,
            "et0": et0,
            "month": month_idx,
            "year": year,
        },
        index=pd.DatetimeIndex(dates),
    ).rename_axis("date")


def provenance(seed: int | None) -> Provenance:
    """Build a provenance block for weather-based outputs."""
    return Provenance(seed=seed)
