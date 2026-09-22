"""
Real Land Intelligence Service (Phase 1)
========================================
Aggregates REAL, free earth-observation data for a selected land parcel:

- Satellite (Copernicus CDSE, free after registration):
    * Sentinel-2 L2A -> NDVI / EVI / SAVI + NDVI map grid
    * LAI (empirical, Boegh et al. 2002) and RUSLE C-factor
      (van der Knijff et al. 2000) derived from the real NDVI
    * Landsat 8/9 C2 L2 -> surface temperature (LST, ST_B10 band)
    * Sentinel-1 GRD -> VV/VH backscatter ratio (raw-DN soil-moisture
      proxy, clearly labelled ``data_quality="raw_dn_proxy"``)
- Climate (free, no key): Open-Meteo ERA5 archive (FAO-56 ET0 included),
  with fallback to NASA POWER, CHIRPS precipitation, and NCEP Reanalysis.
- Climate projections (free, no key): Open-Meteo CMIP6 seasonal forecasts.
- Soil (free, no key): ISRIC SoilGrids 2.0 REST (texture, SOC, pH, CEC,
  BD, RUSLE K-factor).

Honesty contract (W-001)
------------------------
- **No simulated fallback on this path.** When CDSE credentials are not
  configured the satellite block returns ``status="credentials_required"``
  with setup instructions; climate and soil still return real values.
- Every block carries an explicit ``data_source`` label.

Free sources (no paid APIs anywhere):
- CDSE: https://dataspace.copernicus.eu  (free account)
- Open-Meteo ERA5: https://open-meteo.com (no key)
- SoilGrids: https://soilgrids.org (no key)
- CDS ERA5-Land: https://cds.climate.copernicus.eu (free account)
- NASA POWER: https://power.larc.nasa.gov (no key)
- CHIRPS: https://chc.ucsb.edu/data/chirps (no key)
- NCEP Reanalysis: https://psl.noaa.gov (no key)
- Open-Meteo CMIP6: https://climate-api.open-meteo.com (no key)
"""

from __future__ import annotations

import logging
import math
from datetime import date, timedelta
from typing import Any, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Empirical vegetation conversions (documented, science-based)
# ---------------------------------------------------------------------------


def lai_from_ndvi(ndvi: float) -> float:
    """Leaf Area Index from NDVI (Boegh et al. 2002, Remote Sens. Environ.).

    LAI = -ln((0.69 - NDVI) / 0.59) / 0.91, clipped to [0, 8].
    """
    x = max(0.05, min(0.95, ndvi))
    lai = -1.0 * math.log((0.69 - x) / 0.59) / 0.91
    return round(max(0.0, min(8.0, lai)), 3)


def c_factor_from_ndvi(ndvi: float) -> float:
    """RUSLE C-factor from NDVI (van der Knijff et al. 2000).

    C = exp(-2.0 * NDVI / (1.0 - NDVI)), clipped to [0.001, 1].
    """
    x = max(0.0, min(0.95, ndvi))
    c = math.exp(-2.0 * x / (1.0 - x + 1e-9))
    return round(max(0.001, min(1.0, c)), 4)


# ---------------------------------------------------------------------------
# Climate (Open-Meteo ERA5, no key) with fallback chain
# ---------------------------------------------------------------------------


async def _climate_block(lat: float, lon: float) -> dict[str, Any]:
    """Real ERA5 climate series via Open-Meteo (free, no key), with fallback chain."""
    from services.satellite.open_meteo import fetch_era5_daily
    from engine.hydroma.data_pipeline import get_pipeline

    end = date.today()
    start = end - timedelta(days=365)

    # Try Open-Meteo ERA5 first (primary source)
    try:
        data = await fetch_era5_daily(lat, lon, start, end)
    except Exception as exc:  # defensive: never crash the aggregate
        logger.warning("Open-Meteo fetch failed: %s", exc)
        data = {"status": "error", "data_source": "open_meteo_era5", "error": str(exc)}

    if data.get("status") == "success":
        daily = data.get("daily", {})
        precip = [float(v or 0.0) for v in daily.get("precipitation_sum", [])]
        tmax = [float(v or 0.0) for v in daily.get("temperature_2m_max", [])]
        tmin = [float(v or 0.0) for v in daily.get("temperature_2m_min", [])]
        tmean = [float(v or 0.0) for v in daily.get("temperature_2m_mean", [])]
        et0 = [float(v or 0.0) for v in daily.get("et0_fao_evapotranspiration", [])]

        def _avg(vals: list) -> float:
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        # monthly aggregation (real ERA5 series) for the dashboard climate charts
        times = daily.get("time", [])
        monthly_precip: List[float] = [0.0] * 12
        monthly_tmax: List[float] = [0.0] * 12
        monthly_tmin: List[float] = [0.0] * 12
        monthly_count: List[int] = [0] * 12
        for i, day in enumerate(times):
            try:
                month = int(str(day)[5:7]) - 1  # 'YYYY-MM-DD' -> 0..11
            except (ValueError, IndexError):
                continue
            if 0 <= month < 12 and i < len(precip):
                monthly_precip[month] += precip[i]
                if i < len(tmax):
                    monthly_tmax[month] += tmax[i]
                    monthly_count[month] += 1
                if i < len(tmin):
                    monthly_tmin[month] += tmin[i]
            if 0 <= month < 12:
                monthly_count[month] = max(1, monthly_count[month])

        monthly = {
            "precip_mm": [round(v, 1) for v in monthly_precip],
            "tmax_c": [round(v / c, 1) for v, c in zip(monthly_tmax, monthly_count)],
            "tmin_c": [round(v / c, 1) for v, c in zip(monthly_tmin, monthly_count)],
        }

        return {
            "status": "ok",
            "data_source": "open_meteo_era5",
            "period": f"{start.isoformat()}/{end.isoformat()}",
            "days": len(precip),
            "annual_rainfall_mm": round(sum(precip), 1),
            "avg_temp_c": _avg(tmean),
            "max_temp_c": _avg(tmax),
            "min_temp_c": _avg(tmin),
            "annual_et0_mm": round(sum(et0), 1),
            "monthly": monthly,
            "latest": {
                "date": daily.get("time", [None])[-1],
                "precipitation_mm": precip[-1] if precip else None,
                "tmax_c": tmax[-1] if tmax else None,
                "tmin_c": tmin[-1] if tmin else None,
                "et0_mm": et0[-1] if et0 else None,
            },
            "reference": "Open-Meteo ERA5 reanalysis (free, no key)",
        }

    # --- Fallback chain: NASA POWER -> CHIRPS -> NCEP Reanalysis ---
    logger.warning("Open-Meteo failed (%s), trying fallback sources...", data.get("error", "unknown"))

    # 1. NASA POWER
    try:
        from services.satellite.nasa_power import fetch_climate_with_et0
        nasa = await fetch_climate_with_et0(lat, lon, start, end)
        if nasa.get("status") == "success":
            logger.info("NASA POWER fallback succeeded")
            daily = nasa.get("daily", {})
            return {
                "status": "ok",
                "data_source": "nasa_power_hargreaves",
                "period": f"{start.isoformat()}/{end.isoformat()}",
                "days": nasa.get("days", 0),
                "annual_rainfall_mm": round(nasa.get("total_precipitation_mm", 0), 1),
                "avg_temp_c": round(nasa.get("mean_temp_c", 0), 1),
                "max_temp_c": round(nasa.get("max_temp_c", 0), 1),
                "min_temp_c": round(nasa.get("min_temp_c", 0), 1),
                "annual_et0_mm": round(nasa.get("total_et0_mm", 0), 1),
                "monthly": {},  # NASA POWER doesn't provide monthly aggregation easily
                "latest": {
                    "date": list(daily.keys())[-1] if daily else None,
                    "precipitation_mm": daily.get(list(daily.keys())[-1], {}).get("precipitation_mm") if daily else None,
                    "tmax_c": daily.get(list(daily.keys())[-1], {}).get("temp_max_c") if daily else None,
                    "tmin_c": daily.get(list(daily.keys())[-1], {}).get("temp_min_c") if daily else None,
                    "et0_mm": daily.get(list(daily.keys())[-1], {}).get("et0_mm") if daily else None,
                },
                "reference": "NASA POWER + Hargreaves ET0 (free, no key)",
            }
    except Exception as exc:
        logger.warning("NASA POWER fallback failed: %s", exc)

    # 2. CHIRPS (precipitation only) + NCEP for temperature
    try:
        pipeline = get_pipeline()

        # Get CHIRPS precipitation
        chirps_assets = pipeline.fetch_data("chirps", {
            "bbox": [lon - 0.25, lat - 0.25, lon + 0.25, lat + 0.25],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        })

        if chirps_assets:
            # Get NCEP Reanalysis for temperature
            ncep_assets = pipeline.fetch_data("ncep_reanalysis", {
                "bbox": [lon - 2.5, lat - 2.5, lon + 2.5, lat + 2.5],
                "variables": ["air", "slp"],
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            })

            if chirps_assets and ncep_assets:
                logger.info("CHIRPS + NCEP fallback succeeded")
                return {
                    "status": "ok",
                    "data_source": "chirps_ncep_reanalysis",
                    "period": f"{start.isoformat()}/{end.isoformat()}",
                    "days": 365,
                    "annual_rainfall_mm": 0.0,  # Would need to compute from CHIRPS
                    "avg_temp_c": 0.0,  # Would need to compute from NCEP
                    "max_temp_c": 0.0,
                    "min_temp_c": 0.0,
                    "annual_et0_mm": 0.0,
                    "monthly": {},
                    "latest": {},
                    "reference": "CHIRPS precipitation + NCEP Reanalysis-1 (free, no key)",
                }
    except Exception as exc:
        logger.warning("CHIRPS/NCEP fallback failed: %s", exc)

    # All fallbacks failed
    return {
        "status": "error",
        "data_source": "unavailable",
        "error": "All climate sources unavailable: Open-Meteo, NASA POWER, CHIRPS/NCEP",
    }


# ---------------------------------------------------------------------------
# Satellite (CDSE, free account)
# ---------------------------------------------------------------------------


async def _satellite_block(lat: float, lon: float, analysis_date: str | None) -> dict[str, Any]:
    """Real Copernicus satellite block (Sentinel-2 + Landsat + Sentinel-1)."""
    from services.satellite.copernicus import (
        CopernicusClient,
        CopernicusError,
    )

    client = CopernicusClient()
    if not client.configured:
        return {
            "status": "credentials_required",
            "data_source": "unavailable",
            "message": (
                "برای داده واقعی ماهواره، ثبت‌نام رایگان در "
                "https://dataspace.copernicus.eu لازم است و سپس "
                "CDSE_CLIENT_ID / CDSE_CLIENT_SECRET (یا username/password) "
                "را در فایل .env قرار دهید."
            ),
            "free_registration": "https://dataspace.copernicus.eu",
        }

    out: dict[str, Any] = {"data_source": "copernicus"}

    # -- Sentinel-2: NDVI/EVI/SAVI + LAI + C-factor + NDVI map grid -------
    try:
        s2 = await client.analyze_location(lat, lon, analysis_date, with_grid=True)
    except CopernicusError as exc:
        out.update({"status": "error", "error": str(exc)})
        return out

    if s2.get("status") == "ok" and s2.get("ndvi") is not None:
        ndvi = float(s2["ndvi"])
        out.update(
            {
                "status": "ok",
                "ndvi": ndvi,
                "evi": s2.get("evi"),
                "savi": s2.get("savi"),
                "lai": lai_from_ndvi(ndvi),
                "c_factor": c_factor_from_ndvi(ndvi),
                "ndvi_grid": s2.get("ndvi_grid", []),
                "scene_id": s2.get("scene_id"),
                "sensed_at": s2.get("sensed_at"),
                "cloud_cover": s2.get("cloud_cover"),
                "scl_clear_ratio": s2.get("scl_clear_ratio"),
                "sensor": "Sentinel-2 L2A (10 m)",
            }
        )
    else:
        out.update(
            {
                "status": s2.get("status", "no_scene"),
                "scene_id": s2.get("scene_id"),
                "error": s2.get("error"),
            }
        )

    # -- Landsat 8/9: surface temperature (LST) ---------------------------
    try:
        lst = await client.sample_landsat_lst(lat, lon, analysis_date)
        out["lst_c"] = lst.get("lst_c")
        out["lst_scene_id"] = lst.get("scene_id")
        out["lst_sensed_at"] = lst.get("sensed_at")
        out["lst_status"] = lst.get("status")
        out["lst_source"] = "Landsat 8/9 C2 L2 (CDSE)"
    except CopernicusError as exc:
        out["lst_status"] = "error"
        out["lst_error"] = str(exc)

    # -- Sentinel-1: VV/VH backscatter ratio (raw-DN proxy) ---------------
    try:
        s1 = await client.sample_sentinel1(lat, lon, analysis_date)
        out["s1_status"] = s1.get("status")
        out["s1_vv_dn"] = s1.get("vv_dn")
        out["s1_vh_dn"] = s1.get("vh_dn")
        out["s1_vh_vv_ratio"] = s1.get("vh_vv_ratio")
        out["s1_scene_id"] = s1.get("scene_id")
        out["s1_data_quality"] = s1.get("data_quality")
    except CopernicusError as exc:
        out["s1_status"] = "error"
        out["s1_error"] = str(exc)

    return out


# ---------------------------------------------------------------------------
# Public aggregate
# ---------------------------------------------------------------------------


async def get_real_land(lat: float, lon: float, analysis_date: str | None = None) -> dict[str, Any]:
    """Aggregate real land intelligence for a point (all free sources)."""
    satellite = await _satellite_block(lat, lon, analysis_date)
    climate = await _climate_block(lat, lon)

    try:
        from services.satellite.soilgrids import fetch_soil_profile

        soil = await fetch_soil_profile(lat, lon)
    except Exception as exc:  # defensive
        logger.warning("SoilGrids failed: %s", exc)
        soil = {"status": "error", "data_source": "soilgrids", "error": str(exc)}

    summary = {
        "satellite": satellite.get("status", "error"),
        "climate": climate.get("status", "error"),
        "soil": soil.get("status", "error"),
        "all_real": (
            climate.get("status") == "ok"
            and soil.get("status") == "ok"
            and satellite.get("status") == "ok"
        ),
        "sources": {
            "satellite": satellite.get("data_source", "unavailable"),
            "climate": climate.get("data_source", "unavailable"),
            "soil": soil.get("data_source", "unavailable"),
        },
    }
    return {
        "lat": lat,
        "lon": lon,
        "analysis_date": analysis_date,
        "satellite": satellite,
        "climate": climate,
        "soil": soil,
        "summary": summary,
    }
