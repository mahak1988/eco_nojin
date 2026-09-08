"""Abstract interface for the Hydroma Engine functionalities."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from engine.hydroma.models.results import (
    ClimateAnalysisResult,
    GroundwaterAnalysisResult,
    SoilAnalysisResult,
    WatershedAnalysisResult,
)


class IHydromaEngine(ABC):
    """Interface defining the methods the LandService expects from the Hydroma engine components."""

    @abstractmethod
    def analyze_soil(self, soil_data: Dict[str, Any]) -> SoilAnalysisResult:
        """Analyzes soil properties."""
        pass

    @abstractmethod
    def analyze_climate(self, climate_data: Dict[str, Any]) -> ClimateAnalysisResult:
        """Analyzes climate data."""
        pass

    @abstractmethod
    def analyze_watershed(self, slope_pct: float, area_m2: float, rainfall_mm: float) -> WatershedAnalysisResult:
        """Analyzes watershed and proposes structures."""
        pass

    @abstractmethod
    def analyze_groundwater(self, gw_data: Dict[str, Any]) -> GroundwaterAnalysisResult:
        """Analyzes groundwater potential."""
        pass
