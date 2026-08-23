"""Abstract interface for the Land Analysis Engine."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np


class ILandEngine(ABC):
    """Interface defining the methods the LandService expects from the analysis engine."""

    @abstractmethod
    def analyze_terrain(self, dem_array: np.ndarray, profile_id: str = "") -> Dict[str, Any]:
        """Performs comprehensive terrain analysis."""
        pass

    @abstractmethod
    def analyze_drainage(self, dem_array: np.ndarray, profile_id: str = "") -> Dict[str, Any]:
        """Performs drainage analysis."""
        pass

    @abstractmethod
    def assess_capability(
        self,
        slope_degrees: float,
        soil_depth_m: Optional[float] = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam"
    ) -> Dict[str, Any]:
        """Assesses land capability."""
        pass

    @abstractmethod
    def analyze_surface_water(self, dem_file_path: str) -> Dict[str, Any]:
        """Analyzes surface water potential using DEM."""
        pass