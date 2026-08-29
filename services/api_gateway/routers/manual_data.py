"""Manual reference dataset API — feeds the 3D simulator & dashboards.

Read-only access to data/manual/eco_manual_v1.sqlite via
services.data_manual (the shared loader used by every model).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from services.data_manual import manual

router = APIRouter(prefix="/api/v1/manual", tags=["manual-data"])


@router.get("/status")
def manual_status() -> dict[str, Any]:
    return manual.status()


@router.get("/sites")
def manual_sites(
    q: str | None = Query(None, description="search in site_id/country/province"),
) -> dict[str, Any]:
    df = manual.sites()
    if q:
        ql = q.lower()
        mask = (
            df["site_id"].astype(str).str.lower().str.contains(ql)
            | df.get("country", df["site_id"]).astype(str).str.lower().str.contains(ql)
        )
        if "province" in df.columns:
            mask = mask | df["province"].astype(str).str.lower().str.contains(ql)
        df = df[mask]
    cols = [c for c in ("site_id", "country", "admin1_city", "province", "lat", "lon", "elevation_m", "koppen", "annual_rain_normal_mm") if c in df.columns]
    return {"count": len(df), "sites": df[cols].to_dict("records")}


@router.get("/sites/{site_id}")
def manual_site(site_id: str) -> dict[str, Any]:
    df = manual.site(site_id)
    if df.empty:
        raise HTTPException(404, f"site '{site_id}' not found")
    return df.iloc[0].to_dict()


@router.get("/weather-daily/{site_id}")
def manual_weather_daily(
    site_id: str,
    start: str | None = Query(None),
    end: str | None = Query(None),
    limit: int = Query(400, ge=1, le=1000),
) -> dict[str, Any]:
    df = manual.weather_daily(site_id, start=start, end=end)
    if df.empty:
        raise HTTPException(404, f"no daily weather for '{site_id}'")
    return {"count": len(df), "rows": df.head(limit).to_dict("records")}


@router.get("/climate-normals/{site_id}")
def manual_normals(site_id: str) -> dict[str, Any]:
    df = manual.climate_normals(site_id)
    if df.empty:
        raise HTTPException(404, f"no normals for '{site_id}'")
    return {"count": len(df), "months": df.to_dict("records")}


@router.get("/crop-params")
def manual_crop_params(species_id: str | None = None) -> dict[str, Any]:
    df = manual.crop_water_params(species_id=species_id)
    return {"count": len(df), "crops": df.to_dict("records")}


@router.get("/soil-regions")
def manual_soil(province: str | None = None) -> dict[str, Any]:
    df = manual.soil_regions(province=province)
    return {"count": len(df), "regions": df.to_dict("records")}


@router.get("/crop-calendar")
def manual_calendar(province: str | None = None, crop_fa: str | None = None) -> dict[str, Any]:
    df = manual.crop_calendar(province=province, crop_fa=crop_fa)
    return {"count": len(df), "rows": df.to_dict("records")}
