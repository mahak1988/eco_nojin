"""Abstract base class for satellite data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime as _datetime
from typing import Any

import numpy as np


@dataclass
class SatelliteTile:
    """Represents a single satellite observation tile."""

    provider: str | None = None
    collection: str | None = None
    # The field is named `datetime`, which shadows the type of the same name
    # inside this class body. Without `from __future__ import annotations` the
    # annotation is evaluated at class creation, so `datetime | None` resolved
    # `datetime` to the field being defined -- None -- and raised
    # "unsupported operand type(s) for |: 'NoneType' and 'NoneType'" on import.
    # The postponed-annotations import above fixes that; the aliased import
    # keeps the type correct for any runtime introspection.
    datetime: _datetime | None = None
    bbox: tuple[float, float, float, float] | None = None
    cloud_cover: float | None = None
    bands: dict[str, np.ndarray] | None = None
    crs: str = "EPSG:4326"  # Coordinate Reference System
    # Provenance label: "real" for actual observations, "simulated" for
    # synthetic/demo data. Consumers MUST surface this to users (honesty
    # requirement: simulated data must never be presented as real).
    data_source: str = "real"
    # Per-tile provenance metadata. Keys are intentionally generic so
    # different providers can record different diagnostics without changing
    # the dataclass signature.
    quality_flags: dict[str, Any] | None = None


class SatelliteProvider(ABC):
    """Abstract base for satellite data sources."""

    @abstractmethod
    def search(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ) -> list[dict]:
        """Search for available tiles at a location."""
        pass

    @abstractmethod
    def fetch_tile(self, item_id: str) -> SatelliteTile:
        """Download and decode a specific tile."""
        pass

    @property
    @abstractmethod
    def available_bands(self) -> list[str]:
        """List of band names this provider supports."""
        pass
