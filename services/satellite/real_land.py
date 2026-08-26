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
- Climate (free, no key): Open-Meteo ERA5 archive (FAO-56 ET0 included).
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
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Empirical vegetation conversions (documented, science-based)
# ---------------------------------------------------------------------------


def lai_from_ndvi(ndvi: float) -> float:
    """Leaf Area Index from NDVI (Boegh et al. 2002, Remote Sens. Environ.).

    LAI = -ln((0.69 - NDVI) / 0.59) / 0.91, clipped to [0, 8].
    """
    x = max(0.05, min(0.95, ndvi))
    lai = -1.0 * __import__("math").log((0.69 - x) / 0.59) / 0.91
    return round(max(0.0, min(8.0, lai)), 3)


def c_factor_from_ndvi(ndvi: float) -> float:
    """RUSLE C-factor from NDVI (van der Knijff et al. 2000).

    C = exp(-2.0 * NDVI / (1.0 - NDVI)), clipped to [0.001, 1].
    """
    x = max(0.0, min(0.95, ndvi))
    c = __import__("math").exp(-2.0 * x / (1.0 - x + 1e-9))
    return round(max(0.001, min(1.0, c)), 4)


# ---------------------------------------------------------------------------
# Climate (Open-Meteo ERA5, no key)
# ---------------------------------------------------------------------------


async def _climate_block(lat: float, lon: float) -> Dict[str, Any]:
    """Real ERA5 climate series via Open-Meteo (free, no key)."""
    from services.satellite.open_meteo import fetch_era5_daily

    end = date.today()
    start = end - timedelta(days=365)
    try:
        data = await fetch_era5_daily(lat, lon, start, end)
    except Exception as exc:  # defensive: never crash the aggregate
        logger.warning("Open-Meteo fetch failed: %s", exc)
        return {"status": "error", "data_source": "open_meteo_era5", "error": str(exc)}
    if data.get("status") != "success":
        return {
            "status": "error",
            "data_source": "open_meteo_era5",
            "error": data.get("error", "unknown Open-Meteo error"),
        }

    daily = data.get("daily", {})
    precip = [float(v or 0.0) for v in daily.get("precipitation_sum", [])]
    tmax = [float(v or 0.0) for v in daily.get("temperature_2m_max", [])]
    tmin = [float(v or 0.0) for v in daily.get("temperature_2m_min", [])]
    tmean = [float(v or 0.0) for v in daily.get("temperature_2m_mean", [])]
    et0 = [float(v or 0.0) for v in daily.get("et0_fao_evapotranspiration", [])]

    def _avg(vals: list) -> float:
        return round(sum(vals) / len(vals), 1) if vals else 0.0

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
        "latest": {
            "date": daily.get("time", [None])[-1],
            "precipitation_mm": precip[-1] if precip else None,
            "tmax_c": tmax[-1] if tmax else None,
            "tmin_c": tmin[-1] if tmin else None,
            "et0_mm": et0[-1] if et0 else None,
        },
        "reference": "Open-Meteo ERA5 reanalysis (free, no key)",
    }


# ---------------------------------------------------------------------------
# Satellite (CDSE, free account)
# ---------------------------------------------------------------------------


async def _satellite_block(
    lat: float, lon: float, analysis_date: Optional[str]
) -> Dict[str, Any]:
    """Real Copernicus satellite block (Sentinel-2 + Landsat + Sentinel-1)."""
    from services.satellite.copernicus import (
        CopernicusClient,
        CopernicusError,
        CopernicusNotConfigured,
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

    out: Dict[str, Any] = {"data_source": "copernicus"}

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


async def get_real_land(
    lat: float, lon: float, analysis_date: Optional[str] = None
) -> Dict[str, Any]:
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
