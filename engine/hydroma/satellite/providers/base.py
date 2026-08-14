"""Abstract base class for satellite data providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import numpy as np


@dataclass
class SatelliteTile:
    """Represents a single satellite observation tile."""
    provider: str
    collection: str
    datetime: datetime
    bbox: tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    cloud_cover: float  # 0-100 percentage
    bands: dict[str, np.ndarray]  # band_name -> 2D array
    crs: str = "EPSG:4326"  # Coordinate Reference System
    # Provenance label: "real" for actual observations, "simulated" for
    # synthetic/demo data. Consumers MUST surface this to users (honesty
    # requirement: simulated data must never be presented as real).
    data_source: str = "real"


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
