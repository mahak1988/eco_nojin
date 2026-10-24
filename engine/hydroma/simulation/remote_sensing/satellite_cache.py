"""Disk cache for satellite reflectance acquisitions.

Caches ReflectanceTimeSeries objects to disk using JSON serialization.
Cache keys incorporate site coordinates, date range, source product, and
processing level to ensure cache correctness.

Cache entries store raw reflectance values with full metadata so that
downstream NDMI computation can be reproduced without re-fetching from
the satellite API.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from engine.hydroma.simulation.remote_sensing.satellite_source import (
        ReflectanceAcquisition,
        ReflectanceTimeSeries,
    )

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached satellite reflectance time series.

    Attributes:
        key: SHA-256 hash key for this cache entry.
        site_id: Site identifier.
        latitude: Site latitude.
        longitude: Site longitude.
        start_date: Start date of the cached range.
        end_date: End date of the cached range.
        source_product: Satellite product identifier.
        processing_level: Product processing level.
        acquisitions: Cached acquisition data (serializable dicts).
        created_at: ISO timestamp when the entry was cached.
        ttl_seconds: Time-to-live in seconds (None = no expiry).
    """

    key: str
    site_id: str
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    source_product: str
    processing_level: str
    acquisitions: list[dict[str, Any]]
    created_at: str
    ttl_seconds: int | None = None

    def is_expired(self) -> bool:
        """Return True if the cache entry has passed its TTL."""
        if self.ttl_seconds is None:
            return False
        from datetime import UTC, datetime

        created = datetime.fromisoformat(self.created_at)
        now = datetime.now(UTC)
        return (now - created).total_seconds() > self.ttl_seconds


def make_cache_key(
    site_id: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    source_product: str,
    processing_level: str,
    bands: list[str] | None = None,
) -> str:
    """Create a deterministic cache key from query parameters.

    The key includes all parameters that affect the result, ensuring that
    different queries never collide.
    """
    payload = {
        "site_id": site_id,
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "start_date": start_date,
        "end_date": end_date,
        "source_product": source_product,
        "processing_level": processing_level,
        "bands": sorted(bands) if bands else [],
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class SatelliteCache:
    """Disk-based cache for satellite reflectance time series.

    Stores each cache entry as a separate JSON file named by its key.
    Entries are never overwritten — a new fetch creates a new entry or
    updates the existing file atomically.
    """

    def __init__(self, cache_dir: str | Path, default_ttl_seconds: int | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_seconds = default_ttl_seconds

    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve a cache entry by key.

        Returns None if the entry does not exist or is expired.
        """
        path = self._entry_path(key)
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            entry = CacheEntry(**data)
            if entry.is_expired():
                path.unlink(missing_ok=True)
                return None
            return entry
        except (json.JSONDecodeError, TypeError, OSError) as exc:
            logger.warning("Cache read failed for key %s: %s", key, exc)
            return None

    def put(self, entry: CacheEntry) -> None:
        """Store a cache entry atomically.

        Writes to a temporary file then renames, so concurrent readers
        never see a partial entry.
        """
        path = self._entry_path(entry.key)
        tmp_path = path.with_suffix(".tmp")

        data = asdict(entry)
        data["acquisitions"] = [
            dict(acq)
            for acq in entry.acquisitions
        ]

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        tmp_path.replace(path)

    def delete(self, key: str) -> bool:
        """Delete a cache entry.  Returns True if the entry existed."""
        path = self._entry_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Remove all cache entries.  Returns the number removed."""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        return count

    def store_timeseries(
        self,
        timeseries: ReflectanceTimeSeries,
        site_id: str,
        key: str | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """Store a ReflectanceTimeSeries in the cache.

        Returns the cache key used.
        """
        from datetime import UTC, datetime

        if key is None:
            key = make_cache_key(
                site_id=site_id,
                latitude=timeseries.acquisitions[0].latitude if timeseries.acquisitions else 0.0,
                longitude=timeseries.acquisitions[0].longitude if timeseries.acquisitions else 0.0,
                start_date=timeseries.dates()[0] if timeseries.dates() else "",
                end_date=timeseries.dates()[-1] if timeseries.dates() else "",
                source_product=timeseries.source_product,
                processing_level=timeseries.processing_level,
            )

        acquisitions_data = []
        for acq in timeseries.acquisitions:
            acquisitions_data.append(
                {
                    "date": acq.date,
                    "latitude": acq.latitude,
                    "longitude": acq.longitude,
                    "bands": {
                        band: {
                            "date": br.date,
                            "band": br.band,
                            "value": br.value,
                            "unit": br.unit,
                            "spatial_resolution_m": br.spatial_resolution_m,
                            "quality_status": br.quality_status.value,
                            "source_product": br.source_product,
                            "source": br.source,
                            "processing_level": br.processing_level,
                            "metadata": br.metadata,
                        }
                        for band, br in acq.bands.items()
                    },
                    "cloud_fraction": acq.cloud_fraction,
                    "cloud_shadow_fraction": acq.cloud_shadow_fraction,
                    "snow_fraction": acq.snow_fraction,
                    "valid_pixel_fraction": acq.valid_pixel_fraction,
                    "valid_observation_count": acq.valid_observation_count,
                    "source_product": acq.source_product,
                    "processing_level": acq.processing_level,
                    "quality_status": acq.quality_status.value,
                }
            )

        entry = CacheEntry(
            key=key,
            site_id=site_id,
            latitude=timeseries.acquisitions[0].latitude if timeseries.acquisitions else 0.0,
            longitude=timeseries.acquisitions[0].longitude if timeseries.acquisitions else 0.0,
            start_date=timeseries.dates()[0] if timeseries.dates() else "",
            end_date=timeseries.dates()[-1] if timeseries.dates() else "",
            source_product=timeseries.source_product,
            processing_level=timeseries.processing_level,
            acquisitions=acquisitions_data,
            created_at=datetime.now(UTC).isoformat(),
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
        )
        self.put(entry)
        return key

    def load_timeseries(self, key: str) -> ReflectanceTimeSeries | None:
        """Load a ReflectanceTimeSeries from the cache by key.

        Returns None if not found or expired.
        """
        entry = self.get(key)
        if entry is None:
            return None

        from .satellite_source import ReflectanceAcquisition

        acquisitions: list[ReflectanceAcquisition] = []
        for acq_data in entry.acquisitions:
            bands: dict[str, Any] = {}
            for band_name, br_data in acq_data.get("bands", {}).items():
                bands[band_name] = type(
                    "BandReflectance",
                    (),
                    {
                        "date": br_data["date"],
                        "band": br_data["band"],
                        "value": br_data["value"],
                        "unit": br_data.get("unit", "reflectance"),
                        "spatial_resolution_m": br_data.get("spatial_resolution_m"),
                        "quality_status": br_data.get("quality_status", "satellite_retrieved"),
                        "source_product": br_data.get("source_product", ""),
                        "source": br_data.get("source", ""),
                        "processing_level": br_data.get("processing_level", ""),
                        "metadata": br_data.get("metadata", {}),
                    },
                )()

            acquisitions.append(
                ReflectanceAcquisition(
                    date=acq_data["date"],
                    latitude=acq_data["latitude"],
                    longitude=acq_data["longitude"],
                    bands=bands,
                    cloud_fraction=acq_data.get("cloud_fraction", 0.0),
                    cloud_shadow_fraction=acq_data.get("cloud_shadow_fraction", 0.0),
                    snow_fraction=acq_data.get("snow_fraction", 0.0),
                    valid_pixel_fraction=acq_data.get("valid_pixel_fraction", 1.0),
                    valid_observation_count=acq_data.get("valid_observation_count", 0),
                    source_product=acq_data.get("source_product", ""),
                    processing_level=acq_data.get("processing_level", ""),
                    quality_status=acq_data.get("quality_status", "satellite_retrieved"),
                )
            )

        from engine.hydroma.simulation.remote_sensing.satellite_source import (
            ReflectanceTimeSeries,
        )

        return ReflectanceTimeSeries(
            site_id=entry.site_id,
            acquisitions=acquisitions,
            source_product=entry.source_product,
            processing_level=entry.processing_level,
            spatial_resolution_m=None,
        )
