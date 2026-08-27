"""
Satellite Analysis Router (Phase 4)
====================================
Endpoints:
  - GET  /health:            Module health + active data source
  - POST /analyze:           Real Copernicus analysis (or labelled fallback)
  - GET  /history/{farm_id}: Stored analyses for a farm (real DB rows)
  - GET  /weather:           REAL NASA POWER weather + ET0 (no credentials)
  - GET  /stats/{farm_id}:   DuckDB-powered NDVI summary
  - GET  /indices, /providers

Honesty contract (W-001)
------------------------
- ``data_source`` is "copernicus" only when a real scene was sampled;
  otherwise "simulated" with explicit labelling. Weather is always real
  NASA POWER data when the network is reachable, else an error.
"""
import logging
import random
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from database import models
from database.config import get_db
from services.analytics.duckdb_service import summarize_satellite_rows
from services.satellite.copernicus import (
    CopernicusClient,
    CopernicusError,
    health_from_ndvi,
)
from services.satellite.nasa_power import fetch_climate_with_et0
from services.satellite.open_meteo import fetch_era5_summary

# TODO: Refactor to use service layer instead of direct database access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/satellite", tags=["satellite"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SatelliteAnalyzeRequest(BaseModel):
    """Request model for satellite analysis."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude (-90..90)")
    lon: float = Field(..., ge=-180, le=180, description="Longitude (-180..180)")
    analysis_date: str | None = Field(None, description="ISO date (YYYY-MM-DD)")
    farm_id: int | None = Field(None, description="Farm id to attach the stored row")

    @field_validator('analysis_date')
    @classmethod
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('analysis_date must be in ISO format (YYYY-MM-DD)')


class SatelliteAnalyzeResponse(BaseModel):
    """Response model for satellite analysis."""
    lat: float
    lon: float
    ndvi: float = Field(..., ge=-1, le=1)
    evi: float = Field(..., ge=-1, le=1)
    savi: float = Field(..., ge=-1, le=1)
    recommendation: str
    vegetation_health: str
    analysis_date: str | None = None
    data_source: str = "simulated"
    scene_id: str | None = None
    cloud_cover: float | None = None
    sensed_at: str | None = None


class RealLandResponse(BaseModel):
    """Aggregated REAL land intelligence (satellite + climate + soil).

    Every block carries an explicit ``status`` and ``data_source`` label.
    The satellite block may be ``credentials_required`` until free CDSE
    credentials are configured — this endpoint never fabricates data.
    """
    lat: float
    lon: float
    analysis_date: str | None = None
    satellite: dict[str, Any]
    climate: dict[str, Any]
    soil: dict[str, Any]
    summary: dict[str, Any]


class SatelliteHistoryResponse(BaseModel):
    """One stored satellite analysis row."""
    id: int
    farm_id: int
    ndvi: float | None = None
    evi: float | None = None
    savi: float | None = None
    ndwi: float | None = None
    nbr: float | None = None
    satellite: str | None = None
    data_source: str | None = None
    scene_id: str | None = None
    cloud_cover: float | None = None
    analyzed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WeatherResponse(BaseModel):
    """Real weather summary (ERA5 primary, NASA POWER secondary)."""
    status: str
    source: str = "Open-Meteo ERA5"
    lat: float
    lon: float
    days: int = 0
    summary: dict[str, Any] | None = None
    daily: dict[str, dict[str, float]] | None = None
    era5: dict[str, Any] | None = None
    nasa_power: dict[str, Any] | None = None


class StatsResponse(BaseModel):
    """DuckDB NDVI summary for a farm."""
    farm_id: int
    analyses: int
    ndvi_mean: float | None = None
    ndvi_min: float | None = None
    ndvi_max: float | None = None
    ndvi_latest: float | None = None
    real_data_count: int = 0
    engine: str = "duckdb"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "operational"
    module: str = "satellite"
    supported_indices: list[str]
    providers: list[str]
    data_source: str


# ============================================================================
# Constants
# ============================================================================

SUPPORTED_INDICES = [
    "NDVI", "EVI", "SAVI", "MSAVI", "NDWI", "NDBI", "GNDVI",
    "RENDVI", "NDMI", "LAI", "ARVI",
]

PROVIDERS = [
    "Sentinel-2 (Copernicus CDSE)",
    "Landsat-8",
    "Landsat-9",
    "NASA POWER",
    "Planet Labs",
]


def _copernicus_client() -> CopernicusClient:
    return CopernicusClient()


def _simulated_analysis(lat: float, lon: float) -> dict[str, Any]:
    """Deterministic, clearly-labelled simulation (W-001 fallback)."""
    random.seed(int(abs(lat * 1000)) + int(abs(lon * 1000)))
    ndvi = round(random.uniform(0.2, 0.8), 3)
    evi = round(random.uniform(0.1, 0.7), 3)
    savi = round(random.uniform(0.2, 0.6), 3)
    if ndvi < 0.3:
        recommendation = "Low vegetation health. Consider irrigation and soil amendment."
        vegetation_health = "poor"
    elif ndvi < 0.6:
        recommendation = "Moderate vegetation. Monitor crop health and optimize inputs."
        vegetation_health = "moderate"
    else:
        recommendation = "Healthy vegetation. Maintain current management practices."
        vegetation_health = "good"
    return {
        "ndvi": ndvi, "evi": evi, "savi": savi,
        "recommendation": recommendation,
        "vegetation_health": vegetation_health,
        "data_source": "simulated", "scene_id": None,
        "cloud_cover": None, "sensed_at": None,
    }


def _recommendation_for(ndvi: float) -> str:
    if ndvi < 0.3:
        return "Low vegetation health. Consider irrigation and soil amendment."
    if ndvi < 0.6:
        return "Moderate vegetation. Monitor crop health and optimize inputs."
    return "Healthy vegetation. Maintain current management practices."


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/era5/series")
def era5_series(
    lat: float,
    lon: float,
    start: str,
    end: str,
    variables: str | None = None,
):
    """Real ERA5 daily series for a point (CDS). Requires accepted licence."""
    from services.satellite.era5_fetch import Era5Error, fetch_era5_point

    vars_ = variables.split(",") if variables else None
    try:
        return fetch_era5_point(lat, lon, start, end, variables=vars_)
    except Era5Error as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/stores/status", response_model=dict)
def stores_status():
    """All Copernicus data stores (CDS/EWDS/ADS) + SEPAL — honest status."""
    from services.satellite.cds import all_stores_status

    return all_stores_status()


@router.get("/cds/status", response_model=dict)
def cds_status():
    """Honest CDS (Climate Data Store) integration status."""
    from services.satellite.cds import CdsClient

    return CdsClient().status()


@router.get("/health", response_model=HealthResponse)
async def satellite_health():
    """Health check with the active data source honesty flag."""
    client = _copernicus_client()
    return HealthResponse(
        status="operational",
        module="satellite",
        supported_indices=SUPPORTED_INDICES,
        providers=PROVIDERS,
        data_source="copernicus" if client.configured else "simulated",
    )


@router.post("/analyze", response_model=SatelliteAnalyzeResponse)
async def analyze_satellite(request: SatelliteAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze satellite data for a location (real Copernicus when possible)."""
    logger.info(f"Analyzing satellite data for lat={request.lat}, lon={request.lon}")

    client = _copernicus_client()
    analysis = _simulated_analysis(request.lat, request.lon)
    if client.configured:
        try:
            cop = await client.analyze_location(request.lat, request.lon, request.analysis_date)
            if cop["status"] == "ok" and cop.get("ndvi") is not None:
                ndvi = cop["ndvi"]
                analysis = {
                    "ndvi": ndvi,
                    "evi": cop["evi"],
                    "savi": cop["savi"],
                    "recommendation": _recommendation_for(ndvi),
                    "vegetation_health": health_from_ndvi(ndvi),
                    "data_source": "copernicus",
                    "scene_id": cop["scene_id"],
                    "cloud_cover": cop["cloud_cover"],
                    "sensed_at": cop["sensed_at"],
                }
            else:
                logger.warning(
                    "Copernicus path returned %s; labelled fallback",
                    cop.get("status"),
                )
        except CopernicusError as exc:
            logger.warning("Copernicus error, labelled fallback: %s", exc)

    # Persist the analysis when a farm id was provided.
    if request.farm_id is not None:
        farm = db.get(models.Farm, request.farm_id)
        if farm is None:
            raise HTTPException(status_code=404, detail="farm not found")
        row = models.SatelliteAnalysis(
            farm_id=request.farm_id,
            user_id=farm.user_id,
            latitude=request.lat,
            longitude=request.lon,
            ndvi=analysis["ndvi"],
            evi=analysis["evi"],
            savi=analysis["savi"],
            satellite=(
                "Sentinel-2" if analysis["data_source"] == "copernicus" else "simulated"
            ),
            data_source=analysis["data_source"],
            scene_id=analysis.get("scene_id"),
            cloud_cover=analysis.get("cloud_cover"),
        )
        db.add(row)
        db.commit()

    return SatelliteAnalyzeResponse(
        lat=request.lat,
        lon=request.lon,
        ndvi=analysis["ndvi"],
        evi=analysis["evi"],
        savi=analysis["savi"],
        recommendation=analysis["recommendation"],
        vegetation_health=analysis["vegetation_health"],
        analysis_date=request.analysis_date,
        data_source=analysis["data_source"],
        scene_id=analysis.get("scene_id"),
        cloud_cover=analysis.get("cloud_cover"),
        sensed_at=analysis.get("sensed_at"),
    )


@router.post("/real-land", response_model=RealLandResponse)
async def real_land_analysis(request: SatelliteAnalyzeRequest):
    """REAL land intelligence for a point (all sources free):

    - satellite: Sentinel-2 L2A (NDVI/EVI/SAVI/LAI/C-factor + NDVI grid),
      Landsat 8/9 LST, Sentinel-1 VV/VH proxy — via Copernicus CDSE.
    - climate: ERA5 daily series + FAO-56 ET0 via Open-Meteo (no key).
    - soil: SoilGrids v2.0 REST profile (texture, SOC, pH, CEC, BD, K).

    Honesty (W-001): no simulated fallback. Without CDSE credentials the
    satellite block reports ``credentials_required`` with free sign-up
    instructions (climate + soil still return real values).
    """
    from services.satellite.real_land import get_real_land

    return await get_real_land(request.lat, request.lon, request.analysis_date)


@router.get("/history/{farm_id}", response_model=list[SatelliteHistoryResponse])
def get_satellite_history(farm_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Return stored satellite analyses for a farm (newest first)."""
    rows = (
        db.query(models.SatelliteAnalysis)
        .filter(models.SatelliteAnalysis.farm_id == farm_id)
        .order_by(models.SatelliteAnalysis.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    return rows


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=30),
):
    """REAL weather for a location (no credentials): ERA5 FAO ET0 primary,
    NASA POWER + Hargreaves secondary. Both sources are labelled."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    era5 = await fetch_era5_summary(lat, lon, start, end)
    nasa = await fetch_climate_with_et0(lat, lon, start, end)

    if era5.get("status") == "success":
        return WeatherResponse(
            status="success",
            lat=lat,
            lon=lon,
            days=era5["days"],
            summary=era5["summary"],
            daily=era5["daily"],
            era5=era5,
            nasa_power=nasa if nasa.get("status") == "success" else None,
        )
    if nasa.get("status") == "success":
        return WeatherResponse(
            status="success",
            source="NASA POWER + Hargreaves ET0",
            lat=lat,
            lon=lon,
            days=nasa["days"],
            summary=nasa["summary"],
            daily=nasa["daily"],
            era5=None,
            nasa_power=nasa,
        )
    raise HTTPException(
        status_code=502,
        detail="Both weather sources unavailable (Open-Meteo ERA5 and NASA POWER)",
    )


@router.get("/stats/{farm_id}", response_model=StatsResponse)
def get_satellite_stats(farm_id: int, db: Session = Depends(get_db)):
    """DuckDB-powered NDVI summary for a farm (real stored rows only)."""
    rows = (
        db.query(models.SatelliteAnalysis)
        .filter(models.SatelliteAnalysis.farm_id == farm_id)
        .all()
    )
    stats = summarize_satellite_rows(rows)
    return StatsResponse(farm_id=farm_id, **stats)


@router.get("/indices")
async def list_supported_indices():
    """List supported spectral indices."""
    return {"indices": SUPPORTED_INDICES}


@router.get("/providers")
async def list_providers():
    """List data providers."""
    return {"providers": PROVIDERS}
