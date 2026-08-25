"""Base classes for Map Generation Engine."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import geopandas as gpd
import numpy as np
import rasterio
import xarray as xr
from shapely.geometry import Polygon


class MapType(str, Enum):
    """Supported map types."""
    M_TOP = "topographic"           # Base topographic map
    M_SLP = "slope_aspect"          # Slope and aspect
    M_RUN = "runoff_potential"      # SCS-CN runoff
    M_RCH = "recharge_potential"    # Groundwater recharge
    M_TEX = "soil_texture"          # Soil texture classification
    M_SAL = "salinity"              # Soil salinity (EC)
    M_OMC = "organic_carbon"        # Soil organic carbon
    M_VEG = "vegetation"            # NDVI/EVI time series
    M_ERS = "erosion_rusle"         # RUSLE erosion
    M_HYD = "watershed"             # Watershed delineation
    M_LULC = "land_use_cover"       # Land use/land cover
    M_REG = "regional_context"      # Regional context map
    M_GEO = "geology"               # Geology map
    M_PRI = "priority"              # Implementation priority


@dataclass
class MapRequest:
    """Request to generate a map."""
    map_type: MapType
    region: Polygon  # Bounding polygon in WGS84 (EPSG:4326)
    target_crs: str = "auto"  # "auto" = UTM zone based on centroid
    resolution: float = 10.0  # meters
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class MapResult:
    """Result of map generation."""
    map_id: str
    map_type: MapType
    cog_path: Path
    vector_tiles_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_seconds: float = 0.0
    data_sources: List[str] = field(default_factory=list)
    crs: str = ""
    bounds: tuple = ()
    resolution: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "map_id": self.map_id,
            "map_type": self.map_type.value,
            "cog_path": str(self.cog_path),
            "metadata": self.metadata,
            "processing_time_seconds": self.processing_time_seconds,
            "data_sources": self.data_sources,
            "crs": self.crs,
            "bounds": list(self.bounds),
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
        }


class MapPipeline(ABC):
    """Abstract base class for map generation pipelines."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/maps/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def map_type(self) -> MapType:
        """Map type this pipeline produces."""
        pass

    @abstractmethod
    def get_required_layers(self) -> List[str]:
        """Return list of required base layers (e.g., 'dem', 'sentinel2')."""
        pass

    @abstractmethod
    async def execute(
        self,
        base_layers: Dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Execute the pipeline and return a MapResult."""
        pass

    def detect_utm_zone(self, region: Polygon) -> str:
        """Auto-detect UTM zone from region centroid."""
        centroid = region.centroid
        lon = centroid.x
        lat = centroid.y

        # Calculate UTM zone number
        zone_number = int((lon + 180) / 6) + 1

        # Determine hemisphere
        hemisphere = "N" if lat >= 0 else "S"

        # EPSG codes: 326XX (North), 327XX (South)
        epsg = 32600 + zone_number if hemisphere == "N" else 32700 + zone_number

        return f"EPSG:{epsg}"


class MapFetcher(ABC):
    """Abstract base class for data fetchers."""

    @abstractmethod
    async def fetch(self, region: Polygon, **kwargs) -> xr.DataArray:
        """Fetch data for the given region."""
        pass

    @property
    @abstractmethod
    def layer_name(self) -> str:
        """Name of the layer this fetcher provides."""
        pass
