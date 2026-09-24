"""HyDroMa scientific indices API.

Exposes the eight proprietary HyDroMa index models implemented in
``engine.hydroma.models`` (ECSI, EPIA, ESRI, EWSI, HDVI, HLHS, HPheno,
HYRUE) through a uniform, stateless JSON API so the dashboard model pages
can run them live.

Endpoints
---------
GET  /api/v1/hydroma/indices          -> metadata for every index model
GET  /api/v1/hydroma/indices/{id}     -> metadata for one index model
POST /api/v1/hydroma/indices/{id}/run -> execute one model (pure compute)

These endpoints are pure, side-effect-free scientific computations: they
write nothing to the database and accept no personal data. Inputs are
validated by the model's own ``validate_inputs`` and errors are returned
explicitly (no silent fallbacks).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import fields as _fields
from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.models import (
    ECSI,
    EPIA,
    ESRI,
    EWSI,
    HDVI,
    HLHS,
    HYRUE,
    HPheno,
)
from engine.hydroma.models.hlhs import LandscapeMetrics
from services.api_gateway.routers.hydroma_common import (
    build_kwargs as _build_kwargs,
    jsonable as _jsonable,
)

router = APIRouter(prefix="/api/v1/hydroma/indices", tags=["hydroma-indices"])

# ---------------------------------------------------------------------------
# Parameter specs (clean ASCII names; the runner translates to engine names).
# ---------------------------------------------------------------------------

_SPECS: list[dict[str, Any]] = [
    {
        "id": "ecsi",
        "name_en": "ECSI - Carbon Sequestration Index",
        "description": "Soil carbon dynamics: annual interface over the canonical RothC-26.3 kernel (exponential first-order decay, clay-dependent CO2/(BIO+HUM) partition, IOM=0.049*SOC^1.139).",
        "reference": "Coleman & Jenkinson 1996 (RothC-26.3); Rothamsted Broadbalk steady-state anchor. Moisture uses a rainfall/evaporation proxy - use rothc_runner when SMD is available.",
        "params": [
            {
                "name": "initial_soc_t_ha",
                "label": "Initial SOC",
                "unit": "t/ha",
                "kind": "float",
                "default": 40.0,
            },
            {
                "name": "carbon_input_t_ha",
                "label": "Annual carbon input",
                "unit": "t/ha",
                "kind": "float",
                "default": 3.0,
            },
            {
                "name": "t_mean_c",
                "label": "Mean temperature",
                "unit": "C",
                "kind": "float",
                "default": 15.0,
            },
            {
                "name": "rainfall_mm",
                "label": "Rainfall",
                "unit": "mm",
                "kind": "float",
                "default": 500.0,
            },
            {
                "name": "evaporation_mm",
                "label": "Evaporation",
                "unit": "mm",
                "kind": "float",
                "default": 700.0,
            },
            {
                "name": "clay_fraction",
                "label": "Clay fraction",
                "unit": "",
                "kind": "float",
                "default": 0.23,
            },
            {
                "name": "land_use",
                "label": "Land use",
                "unit": "",
                "kind": "select",
                "default": "arable",
                "options": ["arable", "grassland", "forest", "bare", "orchard", "wetland"],
            },
            {
                "name": "dt_years",
                "label": "Time step",
                "unit": "year",
                "kind": "float",
                "default": 1.0,
            },
        ],
    },
    {
        "id": "epia",
        "name_en": "EPIA - Precision Irrigation Advisor",
        "description": "Precision scheduling: ETc = ET0 * Kc * Ks with LAI-derived Kc (FAO-56).",
        "reference": "Allen et al. 1998 (FAO-56)",
        "params": [
            {
                "name": "et0",
                "label": "Reference ET0",
                "unit": "mm/day",
                "kind": "float",
                "default": 5.0,
            },
            {
                "name": "lai",
                "label": "Leaf area index",
                "unit": "",
                "kind": "list_float",
                "default": [2.0],
            },
            {
                "name": "soil_moisture",
                "label": "Soil moisture",
                "unit": "m3/m3",
                "kind": "float",
                "default": 0.3,
            },
            {
                "name": "rainfall_forecast_mm",
                "label": "Forecast rainfall",
                "unit": "mm",
                "kind": "float",
                "default": 20.0,
            },
            {
                "name": "irrigation_efficiency",
                "label": "Irrigation efficiency",
                "unit": "",
                "kind": "float",
                "default": 0.85,
            },
            {
                "name": "taw",
                "label": "Total available water",
                "unit": "mm",
                "kind": "float",
                "default": 50.0,
            },
            {
                "name": "depletion_fraction",
                "label": "Depletion fraction",
                "unit": "",
                "kind": "float",
                "default": 0.5,
            },
        ],
    },
    {
        "id": "esri",
        "name_en": "ESRI - Salinity Risk Index",
        "description": "Spectral salinity index + soil EC + irrigation management (FAO-29).",
        "reference": "Ayers & Westcot 1985 (FAO-29), Richards 1954",
        "params": [
            {
                "name": "blue",
                "label": "Blue reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.05],
            },
            {
                "name": "red",
                "label": "Red reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.08],
            },
            {
                "name": "nir",
                "label": "NIR reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.4],
            },
            {
                "name": "swir",
                "label": "SWIR reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.25],
            },
            {
                "name": "ec_soil_dsm",
                "label": "Soil EC",
                "unit": "dS/m",
                "kind": "float",
                "default": 2.0,
            },
            {
                "name": "ec_irrigation_dsm",
                "label": "Irrigation EC",
                "unit": "dS/m",
                "kind": "float",
                "default": 0.5,
            },
            {
                "name": "actual_leaching_fraction",
                "label": "Actual leaching fraction",
                "unit": "",
                "kind": "float",
                "default": 0.2,
            },
        ],
    },
    {
        "id": "ewsi",
        "name_en": "EWSI - Water Stress Index",
        "description": "Fusion of Sentinel-2 NDMI, atmospheric VPD and root-zone soil moisture.",
        "reference": "Gao 1996, Monteith 1993",
        "params": [
            {
                "name": "nir",
                "label": "NIR reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.4],
            },
            {
                "name": "swir",
                "label": "SWIR reflectance",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.25],
            },
            {
                "name": "vpd",
                "label": "Vapour pressure deficit",
                "unit": "kPa",
                "kind": "float",
                "default": 1.5,
            },
            {
                "name": "soil_moisture",
                "label": "Soil moisture",
                "unit": "m3/m3",
                "kind": "float",
                "default": 0.3,
            },
            {
                "name": "soil_field_capacity",
                "label": "Field capacity",
                "unit": "m3/m3",
                "kind": "float",
                "default": 0.45,
            },
        ],
    },
    {
        "id": "hdvi",
        "name_en": "HDVI - Drought Vulnerability Index",
        "description": "Multi-scale fusion of SPI, SPEI, VHI and SMI.",
        "reference": "McKee 1993, Vicente-Serrano 2010, Kogan 1995",
        "params": [
            {"name": "spi_value", "label": "SPI", "unit": "", "kind": "float", "default": -1.2},
            {"name": "spei_value", "label": "SPEI", "unit": "", "kind": "float", "default": -0.8},
            {
                "name": "vhi_value",
                "label": "VHI",
                "unit": "0-100",
                "kind": "list_float",
                "default": [35.0],
            },
            {
                "name": "smi_value",
                "label": "SMI",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.4],
            },
        ],
    },
    {
        "id": "hlhs",
        "name_en": "HLHS - Landscape Health Score",
        "description": "Composite landscape-fund score: sum(wi * norm(Xi)).",
        "reference": "Shannon 1948, Nagendra 2002",
        "params": [
            {
                "name": "ndvi_mean",
                "label": "Mean NDVI",
                "unit": "0-1",
                "kind": "float",
                "default": 0.5,
            },
            {
                "name": "ewsi_mean",
                "label": "Mean water stress",
                "unit": "0-1",
                "kind": "float",
                "default": 0.4,
            },
            {
                "name": "soc_t_ha",
                "label": "Soil organic carbon",
                "unit": "t/ha",
                "kind": "float",
                "default": 30.0,
            },
            {
                "name": "shdi",
                "label": "Shannon diversity (SHDI)",
                "unit": "",
                "kind": "float",
                "default": 1.5,
            },
            {
                "name": "ecsi_t_co2_ha_yr",
                "label": "Carbon sequestration",
                "unit": "t CO2/ha/yr",
                "kind": "float",
                "default": 1.0,
            },
            {
                "name": "slope_stability",
                "label": "Slope stability",
                "unit": "0-1",
                "kind": "float",
                "default": 0.7,
            },
            {
                "name": "connectivity",
                "label": "Connectivity",
                "unit": "0-1",
                "kind": "float",
                "default": 0.5,
            },
        ],
    },
    {
        "id": "hpheno",
        "name_en": "H-Pheno - Phenology Detection",
        "description": "Savitzky-Golay smoothing + derivatives on an NDVI time series.",
        "reference": "Zhang 2003, White 2009",
        "params": [
            {
                "name": "ndvi_ts",
                "label": "NDVI time series",
                "unit": "-1..1",
                "kind": "list_float",
                "default": [
                    0.1,
                    0.12,
                    0.15,
                    0.2,
                    0.28,
                    0.38,
                    0.5,
                    0.62,
                    0.7,
                    0.72,
                    0.68,
                    0.6,
                    0.5,
                    0.42,
                    0.35,
                    0.3,
                ],
            },
            {
                "name": "dates",
                "label": "Dates (YYYY-MM-DD)",
                "unit": "",
                "kind": "list_str",
                "default": [
                    "2026-01-01",
                    "2026-01-16",
                    "2026-02-01",
                    "2026-02-16",
                    "2026-03-01",
                    "2026-03-16",
                    "2026-04-01",
                    "2026-04-16",
                    "2026-05-01",
                    "2026-05-16",
                    "2026-06-01",
                    "2026-06-16",
                    "2026-07-01",
                    "2026-07-16",
                    "2026-08-01",
                    "2026-08-16",
                ],
            },
            {
                "name": "dt_days",
                "label": "Time step",
                "unit": "day",
                "kind": "float",
                "default": 5.0,
            },
            {
                "name": "ndvi_threshold",
                "label": "NDVI threshold",
                "unit": "",
                "kind": "float",
                "default": 0.15,
            },
        ],
    },
    {
        "id": "hyrue",
        "name_en": "HY-RUE - Radiation Use Efficiency",
        "description": "B = sum(PAR * fIPAR * e * f_stress); Y = B * HI.",
        "reference": "Monteith 1977, Steduto 2009",
        "params": [
            {
                "name": "par",
                "label": "Photosynthetically active radiation",
                "unit": "MJ/m2",
                "kind": "float",
                "default": 10.0,
            },
            {
                "name": "lai",
                "label": "Leaf area index",
                "unit": "",
                "kind": "list_float",
                "default": [2.5],
            },
            {
                "name": "ewsi",
                "label": "Water stress (EWSI)",
                "unit": "0-1",
                "kind": "list_float",
                "default": [0.3],
            },
            {
                "name": "t_mean",
                "label": "Mean temperature",
                "unit": "C",
                "kind": "float",
                "default": 22.0,
            },
            {
                "name": "days",
                "label": "Simulation days",
                "unit": "day",
                "kind": "int",
                "default": 1,
            },
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}

# HLHS dataclass fields use a dotless-i in their names; map clean input names
# to the actual field names by position (dataclass field order is stable).
_HLHS_CLEAN = [
    "ndvi_mean",
    "ewsi_mean",
    "soc_t_ha",
    "shdi",
    "ecsi_t_co2_ha_yr",
    "slope_stability",
    "connectivity",
]
_HLHS_ACTUAL = [f.name for f in _fields(LandscapeMetrics)]
_HLHS_MAP = dict(zip(_HLHS_CLEAN, _HLHS_ACTUAL, strict=False))

# HYRUE.compute accepts the water-stress array under a dotless-i name.
_HYRUE_EWSI_KEY = "ews\u0131"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Runners (explicit per-model translation; no clever dispatch).
# ---------------------------------------------------------------------------


def _run_ecsi(kwargs: dict[str, Any]) -> dict[str, Any]:
    return ECSI().compute(**kwargs)


def _run_epia(kwargs: dict[str, Any]) -> dict[str, Any]:
    return EPIA().compute(**kwargs)


def _run_esri(kwargs: dict[str, Any]) -> dict[str, Any]:
    return ESRI().compute(**kwargs)


def _run_ewsi(kwargs: dict[str, Any]) -> dict[str, Any]:
    result = EWSI().compute(**kwargs)
    return {
        "ewsi": result,
        "classification": EWSI.classify(result),
    }


def _run_hdvi(kwargs: dict[str, Any]) -> dict[str, Any]:
    return HDVI().compute(**kwargs)


def _run_hlhs(kwargs: dict[str, Any]) -> dict[str, Any]:
    metrics = LandscapeMetrics(**{_HLHS_MAP[k]: kwargs[k] for k in _HLHS_CLEAN})
    return HLHS().compute(metrics=metrics)


def _run_hpheno(kwargs: dict[str, Any]) -> dict[str, Any]:
    dates = [_dt.date.fromisoformat(d) for d in kwargs["dates"]]
    result = HPheno().compute(
        ndvi_ts=kwargs["ndvi_ts"],
        dates=dates,
        dt_days=kwargs["dt_days"],
        ndvi_threshold=kwargs["ndvi_threshold"],
    )
    return result


def _run_hyrue(kwargs: dict[str, Any]) -> dict[str, Any]:
    return HYRUE().compute(
        par=kwargs["par"],
        lai=kwargs["lai"],
        **{_HYRUE_EWSI_KEY: kwargs["ewsi"]},
        t_mean=kwargs["t_mean"],
        days=kwargs["days"],
    )


_RUNNERS = {
    "ecsi": _run_ecsi,
    "epia": _run_epia,
    "esri": _run_esri,
    "ewsi": _run_ewsi,
    "hdvi": _run_hdvi,
    "hlhs": _run_hlhs,
    "hpheno": _run_hpheno,
    "hyrue": _run_hyrue,
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
def list_indices() -> dict[str, Any]:
    """List all eight HyDroMa index models with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_index(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa index: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_index(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa index model with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa index: {model_id}")
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    try:
        kwargs = _build_kwargs(spec, params)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid parameters: {exc}") from exc
    try:
        result = _RUNNERS[model_id](kwargs)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=f"model rejected inputs: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"model execution failed: {exc}") from exc
    return {"id": model_id, "result": _jsonable(result)}
