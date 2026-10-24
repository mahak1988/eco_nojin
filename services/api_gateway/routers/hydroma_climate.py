"""HyDroMa climate-tools API (FAO-56 ET0 + irrigation scheduling).

Endpoints
---------
GET  /api/v1/hydroma/climate          -> metadata
GET  /api/v1/hydroma/climate/{id}     -> one tool's metadata
POST /api/v1/hydroma/climate/{id}/run -> execute (pure compute)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from services._gateway_facade import (
    calc_et0_hargreaves,
    calc_et0_penman_monteith,
    fetch_daily_weather,
    hargreaves_et0,
)
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/climate", tags=["hydroma-climate"])

_SPECS: list[dict[str, Any]] = [
    {
        "id": "et-fao56",
        "name_en": "FAO-56 reference ET0",
        "description": "Full Penman-Monteith when humidity/wind/radiation are provided, "
        "Hargreaves-Samani (temperature-only) otherwise.",
        "reference": "Allen et al. 1998 (FAO-56)",
        "params": [
            {"name": "tmin", "label": "T min", "unit": "C", "kind": "float", "default": 12.0},
            {"name": "tmax", "label": "T max", "unit": "C", "kind": "float", "default": 28.0},
            {
                "name": "rh_min",
                "label": "RH min",
                "unit": "%",
                "kind": "float",
                "default": 30.0,
                "optional": True,
            },
            {
                "name": "rh_max",
                "label": "RH max",
                "unit": "%",
                "kind": "float",
                "default": 80.0,
                "optional": True,
            },
            {
                "name": "wind_speed",
                "label": "Wind speed",
                "unit": "m/s",
                "kind": "float",
                "default": 2.0,
                "optional": True,
            },
            {
                "name": "solar_radiation",
                "label": "Solar radiation",
                "unit": "MJ/m2/day",
                "kind": "float",
                "default": 20.0,
                "optional": True,
            },
            {
                "name": "elevation",
                "label": "Elevation",
                "unit": "m",
                "kind": "float",
                "default": 1200.0,
            },
            {
                "name": "latitude",
                "label": "Latitude",
                "unit": "deg",
                "kind": "float",
                "default": 35.7,
            },
            {"name": "doy", "label": "Day of year", "unit": "", "kind": "int", "default": 180},
        ],
    },
    {
        "id": "irrigation-scheduler",
        "name_en": "Irrigation scheduler",
        "description": "Irrigation interval from ETc and readily available water + gross application depth.",
        "reference": "FAO-56; Keller & Bliesner 1990",
        "params": [
            {
                "name": "etc_mm_per_day",
                "label": "ETc",
                "unit": "mm/day",
                "kind": "float",
                "default": 5.0,
            },
            {
                "name": "raw_mm",
                "label": "Readily available water",
                "unit": "mm",
                "kind": "float",
                "default": 25.0,
            },
            {
                "name": "allowable_depletion",
                "label": "Allowable depletion",
                "unit": "",
                "kind": "float",
                "default": 0.5,
            },
            {
                "name": "efficiency",
                "label": "Irrigation efficiency",
                "unit": "",
                "kind": "float",
                "default": 0.85,
            },
            {
                "name": "effective_rain_mm",
                "label": "Effective rain",
                "unit": "mm",
                "kind": "float",
                "default": 0.0,
            },
        ],
    },
    {
        "id": "weather-source",
        "name_en": "Real weather source",
        "description": "Daily historical weather (Open-Meteo ERA5) with FAO-56 Hargreaves ET0 per day.",
        "reference": "Open-Meteo ERA5 + FAO-56 Hargreaves",
        "params": [
            {
                "name": "latitude",
                "label": "Latitude",
                "unit": "deg",
                "kind": "float",
                "default": 35.7,
            },
            {
                "name": "longitude",
                "label": "Longitude",
                "unit": "deg",
                "kind": "float",
                "default": 51.4,
            },
            {"name": "days", "label": "History days", "unit": "day", "kind": "int", "default": 30},
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


def _run_et_fao56(kw: dict[str, Any]) -> dict[str, Any]:
    try:
        result = calc_et0_penman_monteith(
            temp_max=kw["tmax"],
            temp_min=kw["tmin"],
            temp_mean=(kw["tmin"] + kw["tmax"]) / 2,
            rh_max=kw.get("rh_max", 80.0),
            rh_min=kw.get("rh_min", 30.0),
            rh_mean=(kw.get("rh_min", 30.0) + kw.get("rh_max", 80.0)) / 2,
            wind_speed=kw.get("wind_speed", 2.0),
            solar_radiation=kw.get("solar_radiation", 20.0),
            elevation=kw["elevation"],
            latitude=kw["latitude"],
            doy=int(kw["doy"]),
        )
        et0 = result["data"]["et0_mm_day"]
        method = "penman_monteith"
    except (ValueError, RuntimeError):
        result = calc_et0_hargreaves(
            temp_max=kw["tmax"],
            temp_min=kw["tmin"],
            elevation=kw["elevation"],
            latitude=kw["latitude"],
            doy=int(kw["doy"]),
        )
        et0 = result["data"]["et0_mm_day"]
        method = "hargreaves"
    return {"et0_mm_day": et0, "method": method}


def _run_irrigation_scheduler(kw: dict[str, Any]) -> dict[str, Any]:
    etc = kw["etc_mm_per_day"]
    raw = kw["raw_mm"]
    depletion = kw["allowable_depletion"]
    efficiency = kw["efficiency"]
    effective_rain = kw.get("effective_rain_mm", 0.0)
    allowable_extract = raw * depletion
    interval_days = max(1, round(allowable_extract / max(etc, 0.001)))
    net_depth = etc * interval_days
    gross_depth = net_depth / max(efficiency, 0.001)
    application_depth = max(0.0, gross_depth - effective_rain)
    return {
        "interval_days": interval_days,
        "application_depth_mm": application_depth,
        "gross_per_interval_mm": gross_depth,
    }


def _run_weather_source(kw: dict[str, Any]) -> dict[str, Any]:
    import datetime as _dt

    latitude = kw["latitude"]
    longitude = kw["longitude"]
    days = int(kw["days"])
    end = _dt.date.today()
    start = end - _dt.timedelta(days=days - 1)
    try:
        df = fetch_daily_weather(latitude, longitude, start.isoformat(), end.isoformat())
        cols = {c.lower(): c for c in df.columns}
        tmin_c = next((cols[c] for c in cols if "min" in c and "temp" in c), None)
        tmax_c = next((cols[c] for c in cols if "max" in c and "temp" in c), None)
        doy = start
        et0_values = []
        if tmin_c and tmax_c:
            for tmin, tmax in zip(df[tmin_c].tolist(), df[tmax_c].tolist(), strict=False):
                try:
                    et0_values.append(
                        round(
                            hargreaves_et0(float(tmin), float(tmax), latitude, doy.timetuple().tm_yday),
                            3,
                        )
                    )
                except (TypeError, ValueError):
                    et0_values.append(None)
                doy = doy + _dt.timedelta(days=1)
        et0_mean = (
            round(
                sum(v for v in et0_values if v is not None)
                / max(1, len([v for v in et0_values if v is not None])),
                3,
            )
            if et0_values
            else None
        )
        return {
            "source": "Open-Meteo ERA5",
            "latitude": latitude,
            "longitude": longitude,
            "days": days,
            "et0_hargreaves_mm_day_mean": et0_mean,
            "et0_series_mm_day": et0_values,
            "columns": list(df.columns),
        }
    except NotImplementedError:
        return {
            "source": "Open-Meteo ERA5",
            "latitude": latitude,
            "longitude": longitude,
            "days": days,
            "error": "fetch_daily_weather requires external API configuration",
            "et0_hargreaves_mm_day_mean": None,
            "et0_series_mm_day": [],
        }


_RUNNERS = {
    "weather-source": _run_weather_source,
    "et-fao56": _run_et_fao56,
    "irrigation-scheduler": _run_irrigation_scheduler,
}


@router.get("")
def list_climate_tools() -> dict[str, Any]:
    """List all HyDroMa climate tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_climate_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa climate tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_climate_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa climate tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa climate tool: {model_id}")
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    try:
        kwargs = build_kwargs(spec, params)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid parameters: {exc}") from exc
    try:
        result = _RUNNERS[model_id](kwargs)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=f"tool rejected inputs: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"tool execution failed: {exc}") from exc
    return {"id": model_id, "result": jsonable(result)}
