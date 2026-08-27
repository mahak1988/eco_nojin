"""OGC endpoints: OGC API — Features + WaterML 2.0 (subset)."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from services.ogc import features as ogc_features
from services.ogc.waterml import build_timeseries
from services.scientific_motors.drought_motor import run_drought

router = APIRouter(prefix="/ogc", tags=["ogc"])


@router.get("/features/v1/")
async def landing():
    return JSONResponse(ogc_features._LANDING, media_type="application/json")


@router.get("/features/v1/conformance")
async def conformance():
    return JSONResponse(ogc_features._CONFORMANCE, media_type="application/json")


@router.get("/features/v1/collections")
async def collections():
    return JSONResponse(ogc_features._COLLECTIONS, media_type="application/json")


@router.get("/features/v1/collections/{collection_id}/items")
async def items(collection_id: str, limit: int = Query(100, ge=1, le=500), bbox: str | None = None):
    if collection_id != ogc_features.COLLECTION_ID:
        return JSONResponse({"code": "NotFound", "detail": f"unknown collection: {collection_id}"}, status_code=404)
    result = ogc_features.items(limit=limit, bbox=bbox)
    if result.get("status") == "error":
        return JSONResponse(result, status_code=503)
    return JSONResponse(result, media_type="application/geo+json")


@router.get("/waterml/1.0/timeseries", response_class=Response)
async def waterml_timeseries(
    lat: float = 35.7,
    lon: float = 51.4,
    timescale: int = Query(6, ge=1, le=24),
    index: str = Query("spi", pattern="^(spi|spei)$"),
):
    """Real SPI/SPEI series (ERA5) as WaterML 2.0 MeasurementTimeseries XML."""
    result = run_drought(lat=lat, lon=lon, timescale_months=timescale)
    if result.get("status") != "ok":
        return PlainTextResponse(f"Error: {result.get('error', 'unknown')}", status_code=502)
    xml = build_timeseries(result.get("series", []), index=index, title=index.upper())
    return Response(content=xml, media_type="application/xml;charset=utf-8")
