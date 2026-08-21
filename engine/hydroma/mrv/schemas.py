"""Pydantic schemas for the three-level MRV module (EM-01).

Levels:
- Level 1: satellite indices (Sentinel-2/Landsat/Sentinel-1 derived).
- Level 2: IoT field sensor readings (soil moisture, temperature, EC, flow).
- Level 3: citizen field reports (offline-first observations).

Provenance discipline: satellite inputs are explicitly tagged
``real`` or ``simulated`` and are never silently upgraded.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class IoTReading(BaseModel):
    """Single reading from an IoT field sensor (MRV level 2)."""

    site_id: str = Field(..., min_length=1, max_length=200, description="Site/parcel identifier")
    sensor_type: Literal["soil_moisture", "temp", "ec", "flow"] = Field(
        ..., description="Physical quantity measured by the sensor"
    )
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of the value")
    ts: datetime = Field(
        default_factory=datetime.utcnow, description="Observation timestamp (UTC)"
    )


class CitizenReport(BaseModel):
    """Offline citizen field observation (MRV level 3)."""

    site_id: str = Field(..., min_length=1, max_length=200)
    observer: str = Field(..., min_length=1, max_length=200, description="Observer name/ID")
    category: Literal["pest", "disease", "plant_growth", "structure_damage"] = Field(...)
    note: str = Field(..., min_length=1, max_length=4000, description="Free-text observation")
    lat: float | None = Field(None, ge=-90, le=90, description="Optional geotag latitude")
    lon: float | None = Field(None, ge=-180, le=180, description="Optional geotag longitude")
    photos_urls: list[str] = Field(
        default_factory=list, description="URLs of field photos (KoboToolbox attachments)"
    )

    @field_validator("lat", "lon", mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        """Coerce empty strings from simple forms into None."""
        return None if value == "" else value


class CitizenBatch(BaseModel):
    """Offline queue sync: many citizen reports in one request."""

    reports: list[CitizenReport] = Field(..., min_length=1, max_length=500)


class SatelliteIndex(BaseModel):
    """Satellite-derived vegetation/soil index (MRV level 1)."""

    site_id: str = Field(..., min_length=1, max_length=200)
    index: Literal["NDVI", "LAI", "C-factor", "LST", "soil_moisture_sar"] = Field(...)
    value: float = Field(...)
    ts: datetime = Field(default_factory=datetime.utcnow)
    data_source: Literal["real", "simulated"] = Field(
        "simulated",
        description="Provenance: real satellite retrieval or simulation. "
        "Simulated values are always labeled as such.",
    )


class SatelliteRefreshRequest(BaseModel):
    """Request a live Sentinel-2 NDVI retrieval from CDSE for a site."""

    site_id: str = Field(..., min_length=1, max_length=200)
    lat: float = Field(..., ge=-90, le=90, description="Site centroid latitude")
    lon: float = Field(..., ge=-180, le=180, description="Site centroid longitude")
    start: str = Field(..., description="Search start, ISO-8601, e.g. 2026-07-01T00:00:00Z")
    end: str = Field(..., description="Search end, ISO-8601, e.g. 2026-08-01T00:00:00Z")
    half_side_km: float = Field(0.5, gt=0, le=10, description="Half-side of the search box in km")
