"""Bridge: manual reference dataset → scientific motors (local-first feeding).

Converts the normalized tables of data/manual/eco_manual_v1.sqlite into the
exact input contracts of the scientific motors, so they run fully offline:

    from services.data_manual import motor_feed
    from services.scientific_motors.aquacrop_real import RealAquaCropMotor

    bundle = motor_feed.aquacrop_bundle(
        site_id="SITE103", crop_name="wheat",
        planting_date="2022-11-05",
        sim_start="2022-11-01", sim_end="2023-06-30",
    )
    result = await RealAquaCropMotor().execute(bundle["inputs"], bundle["parameters"])

Every bundle also carries `site` (profile) and `provenance` (where each piece
came from) so callers can log/audit the data source.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np

from services.data_manual import loader as manual
from services.scientific_motors.base import MotorParameters

# Persian USDA texture classes (soil_hydraulic_regions) → SoilGrids keys
_FA_TEXTURE_TO_SOILGRIDS = {
    "لوم رسی": "ClayLoam",
    "لوم شنی": "SandyLoam",
    "لوم": "Loam",
    "رسی": "Clay",
    "لوم سیلتی رسی": "SiltyClayLoam",
    "شنی": "Sand",
    "شنی لومی": "LoamySand",
    "سیلت": "Silt",
    "سیلتی لوم": "SiltLoam",
    "شنی رسی": "SandyClay",
    "سیلتی رسی": "SiltyClay",
    "شنی رسی لومی": "SandyClayLoam",
}

_DEFAULT_SOIL = "loam"


class _Series:
    """Minimal shim: motors read `.values` from raster-like inputs."""

    def __init__(self, values: list[float] | np.ndarray, units: str = "mm/day") -> None:
        self.values = np.asarray(values, dtype=float)
        self.units = units


def site_profile(site_id: str) -> dict[str, Any]:
    row = manual.site(site_id)
    if row.empty:
        raise ValueError(f"unknown site_id '{site_id}' (see manual.sites())")
    rec = row.iloc[0].to_dict()
    return {
        "site_id": rec.get("site_id"),
        "country": rec.get("country"),
        "province": rec.get("province") or rec.get("admin1_city"),
        "lat": rec.get("lat"),
        "lon": rec.get("lon"),
        "elevation_m": rec.get("elevation_m"),
        "koppen": rec.get("koppen"),
    }


def _texture_for_province(province: str | None) -> tuple[str | None, dict[str, Any]]:
    if not province:
        return None, {}
    soil = manual.soil_regions(province=province)
    if soil.empty:
        return None, {}
    rec = soil.iloc[0].to_dict()
    fa = (rec.get("texture_class_fa") or "").strip()
    return _FA_TEXTURE_TO_SOILGRIDS.get(fa, _DEFAULT_SOIL), rec


def aquacrop_bundle(
    site_id: str,
    crop_name: str,
    planting_date: str,
    sim_start: str,
    sim_end: str,
    irrigation_threshold_mm: float | None = None,
    soil_province: str | None = None,
) -> dict[str, Any]:
    """Build the exact inputs of RealAquaCropMotor from the manual dataset."""
    profile = site_profile(site_id)
    province = soil_province or profile.get("province")
    daily = manual.weather_daily(site_id, start=sim_start, end=sim_end)
    if daily.empty:
        raise ValueError(
            f"no daily weather for site '{site_id}' in {sim_start}..{sim_end} "
            "(daily coverage: 2020-2024, 32 sites)"
        )
    weather_rows = [
        {
            "datetime": str(r["date"]),
            "tmin": float(r["tmin_c"]),
            "tmax": float(r["tmax_c"]),
            "precip": float(r["precip_mm"]),
            "et0": float(r["et0_mm"]),
        }
        for _, r in daily.iterrows()
    ]
    soil_texture, soil_rec = _texture_for_province(province)
    inputs = {
        "weather_rows": weather_rows,
        "soil_texture": soil_texture or _DEFAULT_SOIL,
        "crop_name": crop_name,
        "planting_date": planting_date,
    }
    parameters = MotorParameters(
        start_date=sim_start,
        end_date=sim_end,
        custom_params={
            "sim_start": sim_start,
            "sim_end": sim_end,
            "irrigation_threshold_mm": irrigation_threshold_mm,
        },
    )
    return {
        "inputs": inputs,
        "parameters": parameters,
        "site": profile,
        "provenance": {
            "weather": "weather_daily (manual dataset)",
            "soil_texture": f"soil_hydraulic_regions:{province}" if soil_rec else "default",
            "rows": len(weather_rows),
        },
    }


def irrigation_bundle(
    site_id: str,
    crop: str = "wheat",
    species_id: str | None = None,
    season_days: int = 120,
    season_start: str | None = None,
    soil_province: str | None = None,
) -> dict[str, Any]:
    """Build IrrigationSchedulerMotor inputs: ET0 shim + real soil + root depth."""
    profile = site_profile(site_id)
    province = soil_province or profile.get("province")

    daily = manual.weather_daily(site_id)
    if not daily.empty:
        if season_start:
            daily = daily[daily["date"] >= season_start]
        et0_values = daily["et0_mm"].tail(season_days).tolist()
    else:
        et0_values = []

    if len(et0_values) < season_days:
        # fall back to monthly normals expanded to daily means
        normals = manual.climate_normals(site_id)
        if not normals.empty:
            cycle = normals.set_index("month")["et0_mm"].to_dict()
            et0_values = [cycle.get(((i % 12) + 1), 3.0) for i in range(season_days)]

    if not et0_values:
        raise ValueError(f"no ET0 data available for site '{site_id}'")

    et0_values = (et0_values * (season_days // len(et0_values) + 1))[:season_days]
    et0 = _Series(et0_values)

    field_capacity, wilting_point = 0.30, 0.15
    soil_rec: dict[str, Any] = {}
    texture = None
    if province:
        texture, soil_rec = _texture_for_province(province)
        if soil_rec:
            if soil_rec.get("theta_fc_cm3cm3") is not None:
                field_capacity = float(soil_rec["theta_fc_cm3cm3"])
            if soil_rec.get("theta_wp_cm3cm3") is not None:
                wilting_point = float(soil_rec["theta_wp_cm3cm3"])

    root_depth = 0.8
    if species_id:
        params = manual.crop_water_params(species_id=species_id)
        if not params.empty and params.iloc[0].get("root_depth_m") is not None:
            root_depth = float(params.iloc[0]["root_depth_m"])

    inputs = {
        "et0_mm_day": et0,
        "soil_moisture": None,
    }
    parameters = MotorParameters(
        start_date=season_start or date.today().isoformat(),
        end_date=date.today().isoformat(),
        custom_params={
            "field_capacity": field_capacity,
            "wilting_point": wilting_point,
            "root_depth_m": root_depth,
            "crop": crop,
            "season_days": season_days,
        },
    )
    return {
        "inputs": inputs,
        "parameters": parameters,
        "site": profile,
        "provenance": {
            "et0_days": len(et0_values),
            "soil_texture": texture,
            "field_capacity": field_capacity,
            "wilting_point": wilting_point,
            "root_depth_m": root_depth,
        },
    }


def planting_bundle(site_id: str, crops: list[str]) -> dict[str, Any]:
    """Build PlantingCalendarMotor inputs from the site profile (lat/koppen)."""
    profile = site_profile(site_id)
    inputs = {
        "latitude": profile.get("lat"),
        "koppen_climate": profile.get("koppen"),
        "crops": crops,
    }
    parameters = MotorParameters(
        start_date=date.today().isoformat(),
        end_date=date.today().isoformat(),
        custom_params={
            "latitude": profile.get("lat"),
            "koppen_climate": profile.get("koppen"),
            "crops": crops,
        },
    )
    return {
        "inputs": inputs,
        "parameters": parameters,
        "site": profile,
        "provenance": {"latitude": profile.get("lat"), "koppen": profile.get("koppen")},
    }


# ============================================================================
# Manual-dataset bundles: crop_advisor (full) + rusle (pending DEM layer)
# ============================================================================

# USDA texture index 1-12 (NRCS order) used by CropAdvisorMotor
_FA_TEXTURE_TO_USDA_INDEX = {
    "ط´ظ†غŒ": 1, "ط´ظ†غŒ ظ„ظˆظ…غŒ": 2, "ظ„ظˆظ… ط´ظ†غŒ": 3, "ط³غŒظ„طھغŒ ظ„ظˆظ…": 4, "ظ„ظˆظ… ط³غŒظ„طھغŒ": 4,
    "ط³غŒظ„طھ": 5, "ط´ظ†غŒ ط±ط³غŒ ظ„ظˆظ…غŒ": 6, "ظ„ظˆظ… ط±ط³غŒ": 7, "ظ„ظˆظ… ط³غŒظ„طھغŒ ط±ط³غŒ": 8,
    "ط´ظ†غŒ ط±ط³غŒ": 9, "ط³غŒظ„طھغŒ ط±ط³غŒ": 10, "ط±ط³غŒ": 11, "ظ„ظˆظ…": 3,
}


def crop_advisor_bundle(
    site_id: str,
    soil_province: str | None = None,
    total_water_mm: float | None = None,
) -> dict[str, Any]:
    """Build CropAdvisorMotor inputs. Real: altitude, koppen, water, texture.
    Defaults (declared in provenance): pH 7.0, slope 5%, LCC 3."""
    profile = site_profile(site_id)
    province = soil_province or profile.get("province")
    texture_fa = None
    if province:
        soil = manual.soil_regions(province=province)
        if not soil.empty:
            texture_fa = (soil.iloc[0].get("texture_class_fa") or "").strip()
    usda_index = _FA_TEXTURE_TO_USDA_INDEX.get(texture_fa, 5)

    if total_water_mm is None:
        ann = manual.weather_annual(site_id)
        if not ann.empty:
            total_water_mm = float(ann["precip_mm"].mean())

    inputs = {
        "soil_ph": None,       # motor default 7.0 (no pH in manual dataset yet)
        "soil_texture": usda_index,
        "slope": None,         # motor default 5.0
        "lcc_class": None,     # motor default 3
    }
    parameters = MotorParameters(
        start_date=date.today().isoformat(),
        end_date=date.today().isoformat(),
        custom_params={
            "koppen_climate": profile.get("koppen"),
            "altitude_m": profile.get("elevation_m"),
            "total_water_mm": total_water_mm or 600,
        },
    )
    return {
        "inputs": inputs,
        "parameters": parameters,
        "site": profile,
        "provenance": {
            "texture_fa": texture_fa,
            "usda_index": usda_index,
            "altitude_m": profile.get("elevation_m"),
            "koppen": profile.get("koppen"),
            "total_water_mm": total_water_mm,
            "defaults_used": ["soil_ph=7.0", "slope=5.0", "lcc_class=3"],
        },
    }


def rusle_bundle(site_id: str, soil_province: str | None = None) -> dict[str, Any]:
    """RUSLE is DEM-gated: everything the manual dataset can supply is here,
    but `dem` itself must come from a raster layer (SRTM/satellite)."""
    profile = site_profile(site_id)
    province = soil_province or profile.get("province")
    ann = manual.weather_annual(site_id)
    annual_rainfall = float(ann["precip_mm"].mean()) if not ann.empty else None
    texture_fa = None
    om_pct = None
    if province:
        soil = manual.soil_regions(province=province)
        if not soil.empty:
            texture_fa = (soil.iloc[0].get("texture_class_fa") or "").strip()
            om_pct = soil.iloc[0].get("organic_carbon_pct")
    return {
        "status": "pending_dem",
        "reason": "RUSLE needs a DEM raster (SRTM/satellite) â€” not part of the manual dataset",
        "site": profile,
        "provenance": {
            "annual_rainfall_mm": annual_rainfall,
            "texture_fa": texture_fa,
            "organic_carbon_pct": om_pct,
        },
        "inputs": {"dem": None, "soil_texture": texture_fa, "soil_organic_matter": om_pct},
        "parameters": MotorParameters(
            start_date=date.today().isoformat(),
            end_date=date.today().isoformat(),
            custom_params={"annual_rainfall_mm": annual_rainfall or 300},
        ),
    }

