"""Manual reference dataset API — feeds the 3D simulator & dashboards.

Read-only access to data/manual/eco_manual_v1.sqlite via
services.data_manual (the shared loader used by every model).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.data_manual import manual

router = APIRouter(prefix="/api/v1/manual", tags=["manual-data"])


class ManualStatusResponse(BaseModel):
    """Existence, size and table inventory of the reference SQLite file.

    `exists` is a deployment state, not a claim about data quality: the frontend
    reports a missing file as missing rather than as an error.
    """

    exists: bool
    path: str | None = None
    size_mb: float | None = None
    tables: dict[str, int] = Field(default_factory=dict)


class ManualDatasetPage(BaseModel):
    """The part every dataset page shares: a row count.

    The list itself is deliberately *not* a field of this base. The key the
    records arrive under is the dataset's own name — `rows`, `crops`, `regions`,
    `months` — and a subclass that inherits one key while its handler builds
    another is filtered down to that inherited key, so the page asks for
    `crops` and reads a 200 carrying only an empty `rows`.
    """

    count: int


class ManualRowsResponse(ManualDatasetPage):
    """Weather-daily and crop-calendar records, under the key `rows`.

    The records hold the dataframe exactly as stored, so the record type is the
    dataset's own column names. The manual tables are not homogeneous and the
    published contract therefore describes the envelope precisely while leaving
    the cell shape to the payload, which is what the client reads back.
    """

    rows: list[dict[str, Any]] = Field(default_factory=list)


class ManualSite(BaseModel):
    """One climate site.

    Every field is selected explicitly by `manual_sites`, so this model states
    the columns the route actually returns instead of accepting any object.
    """

    site_id: Any
    country: Any = None
    admin1_city: Any = None
    province: Any = None
    lat: Any = None
    lon: Any = None
    elevation_m: Any = None
    koppen: Any = None
    annual_rain_normal_mm: Any = None


class ManualSitesResponse(BaseModel):
    count: int
    sites: list[ManualSite] = Field(default_factory=list)


class ManualRegionsResponse(ManualDatasetPage):
    """Soil hydraulic regions, under the key `regions` that `manual_soil` builds."""

    regions: list[dict[str, Any]] = Field(default_factory=list)


class ManualCropsResponse(ManualDatasetPage):
    """Crop water parameters, under the key `crops` that `manual_crop_params` builds."""

    crops: list[dict[str, Any]] = Field(default_factory=list)


class ManualMonthsResponse(ManualDatasetPage):
    """Monthly climate normals, under the key `months` that `manual_normals` builds."""

    months: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/status", response_model=ManualStatusResponse)
def manual_status() -> dict[str, Any]:
    return manual.status()


@router.get("/sites", response_model=ManualSitesResponse)
def manual_sites(
    q: str | None = Query(None, description="search in site_id/country/province"),
) -> dict[str, Any]:
    df = manual.sites()
    if q:
        ql = q.lower()
        mask = df["site_id"].astype(str).str.lower().str.contains(ql) | df.get(
            "country", df["site_id"]
        ).astype(str).str.lower().str.contains(ql)
        if "province" in df.columns:
            mask = mask | df["province"].astype(str).str.lower().str.contains(ql)
        df = df[mask]
    cols = [
        c
        for c in (
            "site_id",
            "country",
            "admin1_city",
            "province",
            "lat",
            "lon",
            "elevation_m",
            "koppen",
            "annual_rain_normal_mm",
        )
        if c in df.columns
    ]
    return {"count": len(df), "sites": df[cols].to_dict("records")}


@router.get("/sites/{site_id}", response_model=ManualSite)
def manual_site(site_id: str) -> dict[str, Any]:
    df = manual.site(site_id)
    if df.empty:
        raise HTTPException(404, f"site '{site_id}' not found")
    return df.iloc[0].to_dict()


@router.get("/weather-daily/{site_id}", response_model=ManualRowsResponse)
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


@router.get("/climate-normals/{site_id}", response_model=ManualMonthsResponse)
def manual_normals(site_id: str) -> dict[str, Any]:
    df = manual.climate_normals(site_id)
    if df.empty:
        raise HTTPException(404, f"no normals for '{site_id}'")
    return {"count": len(df), "months": df.to_dict("records")}


@router.get("/crop-params", response_model=ManualCropsResponse)
def manual_crop_params(species_id: str | None = None) -> dict[str, Any]:
    df = manual.crop_water_params(species_id=species_id)
    return {"count": len(df), "crops": df.to_dict("records")}


@router.get("/soil-regions", response_model=ManualRegionsResponse)
def manual_soil(province: str | None = None) -> dict[str, Any]:
    df = manual.soil_regions(province=province)
    return {"count": len(df), "regions": df.to_dict("records")}


@router.get("/crop-calendar", response_model=ManualRowsResponse)
def manual_calendar(province: str | None = None, crop_fa: str | None = None) -> dict[str, Any]:
    df = manual.crop_calendar(province=province, crop_fa=crop_fa)
    return {"count": len(df), "rows": df.to_dict("records")}
