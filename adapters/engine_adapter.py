"""
Engine Adapter — bridges the services layer to the engine layer.

This adapter wraps the engine's land-analysis components behind a small,
stable surface that services depend on.  It translates between the
service-side call signatures (see ``services/land/service.py``) and the
engine-side analyser classes (``terrain_analysis.TerrainAnalyzer``,
``drainage.DrainageAnalyzer``, ``capability.assess_land_capability``).

The adapter exists so the service layer can depend on an interface rather
than on concrete engine module paths, which keeps the engine's internal
refactor surface free of import-time coupling from services.
"""

from __future__ import annotations

from typing import Any

from engine.land.capability import assess_land_capability
from engine.land.drainage import DrainageAnalyzer
from engine.land.models import (
    CapabilityAssessment,
    DrainageAnalysis,
    TerrainAnalysis,
)
from engine.land.terrain_analysis import TerrainAnalyzer

__all__ = ["EngineAdapter"]


class EngineAdapter:
    """Adapter over the engine's land-analysis sub-systems."""

    def __init__(self, resolution: float = 30.0):
        self._default_resolution = resolution

    # ------------------------------------------------------------------
    # Terrain analysis
    # ------------------------------------------------------------------
    def analyze_terrain(
        self,
        dem_array: Any,
        profile_id: str | None = None,
        resolution: float | None = None,
    ) -> TerrainAnalysis:
        """Analyse terrain topography from a DEM.

        Args:
            dem_array: 2-D elevation array.
            profile_id: Optional profile identifier attached to the result.
            resolution: Cell size in metres. Falls back to the adapter's
                default.

        Returns:
            A :class:`~engine.land.models.TerrainAnalysis` instance.
        """
        res = resolution if resolution is not None else self._default_resolution
        analyzer = TerrainAnalyzer(resolution=res)
        return analyzer.analyze(dem_array, profile_id=profile_id)

    # ------------------------------------------------------------------
    # Drainage analysis
    # ------------------------------------------------------------------
    def analyze_drainage(
        self,
        dem_array: Any,
        profile_id: str | None = None,
        resolution: float | None = None,
        area_km2: float = 1.0,
    ) -> DrainageAnalysis:
        """Analyse drainage network from a DEM.

        Args:
            dem_array: 2-D elevation array.
            profile_id: Optional profile identifier attached to the result.
            resolution: Cell size in metres. Falls back to the adapter's
                default.
            area_km2: Catchment area in km² (used as a fall-back when the DEM
                does not cover enough cells to estimate area).

        Returns:
            A :class:`~engine.land.models.DrainageAnalysis` instance.
        """
        res = resolution if resolution is not None else self._default_resolution
        analyzer = DrainageAnalyzer(resolution=res)
        return analyzer.analyze(dem_array, profile_id=profile_id, area_km2=area_km2)

    # ------------------------------------------------------------------
    # Land-capability assessment
    # ------------------------------------------------------------------
    def assess_capability(
        self,
        profile_id: str | None = None,
        slope_degrees: float = 0.0,
        soil_depth_m: float | None = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam",
    ) -> CapabilityAssessment:
        """Assess land capability using USDA rules.

        Delegates to :func:`engine.land.capability.assess_land_capability`.
        """
        return assess_land_capability(
            profile_id=profile_id,
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture,
        )
