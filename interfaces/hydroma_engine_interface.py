"""Abstract interface for the Hydroma Engine functionalities."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IHydromaEngine(ABC):
    """Interface defining the methods the LandService expects from the Hydroma engine components."""

    @abstractmethod
    def analyze_soil(self, soil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes soil properties."""
        pass

    @abstractmethod
    def analyze_climate(self, climate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes climate data."""
        pass

    @abstractmethod
    def analyze_watershed(self, slope_pct: float, area_m2: float, rainfall_mm: float) -> Dict[str, Any]:
        """Analyzes watershed and proposes structures."""
        pass

    @abstractmethod
    def analyze_groundwater(self, gw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes groundwater potential."""
        pass
