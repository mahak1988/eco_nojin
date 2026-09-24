"""Adapter implementing IHydromaEngine interface to wrap engine/hydroma functionality."""

import structlog

logger = structlog.get_logger()
from typing import Any

from engine.hydroma.models.results import (
    ClimateAnalysisResult,
    GroundwaterAnalysisResult,
    SoilAnalysisResult,
    WatershedAnalysisResult,
)
from interfaces.hydroma_engine_interface import IHydromaEngine

try:
    from engine.hydroma.climate.et_calculator import calc_et0_hargreaves
    from engine.hydroma.soil.salinity import classify_salinity as hydroma_classify_salinity
    from engine.hydroma.watershed.watershed_calculator import (
        design_check_dam as hydroma_design_check_dam,
    )
except ImportError as e:
    logger.warning(f"Warning: Could not import from engine.hydroma: {e}")

    def hydroma_classify_salinity(x):
        return {
            "classification": "unknown",
            "description": "",
            "crop_recommendations": {},
            "management": {},
        }

    def calc_et0_hargreaves(t_min, t_max, t_mean, ra_mj):
        return 0.0

    def hydroma_design_check_dam(slope_pct, area_m2, rainfall_mm):
        return {"type": "not_implemented"}


class HydromaAdapter(IHydromaEngine):
    """Concrete adapter that uses the existing engine/hydroma modules."""

    def analyze_soil(self, soil_data: dict[str, Any]) -> SoilAnalysisResult:
        """Implements soil analysis by delegating to engine/hydroma."""
        ec = soil_data.get("ec", 0.0)
        result = hydroma_classify_salinity(ec)
        return SoilAnalysisResult(
            ec=result.get("ec", ec),
            unit=result.get("unit", "dS/m"),
            classification=result.get("classification", "unknown"),
            description=result.get("description", ""),
            crop_recommendations=result.get("crop_recommendations", {}),
            management=result.get("management", {}),
        )

    def analyze_climate(self, climate_data: dict[str, Any]) -> ClimateAnalysisResult:
        """Implements climate analysis by delegating to engine/hydroma."""
        temp_mean = climate_data.get("temp_mean_c", 20.0)
        t_min = climate_data.get("t_min_c", temp_mean - 5)
        t_max = climate_data.get("t_max_c", temp_mean + 5)
        ra_mj = climate_data.get("ra_mj", 15.0)
        et0_est = calc_et0_hargreaves(t_min=t_min, t_max=t_max, t_mean=temp_mean, ra_mj=ra_mj)
        return ClimateAnalysisResult(
            estimated_et0=et0_est,
            input_data=climate_data,
            method="Hargreaves",
        )

    def analyze_watershed(
        self, slope_pct: float, area_m2: float, rainfall_mm: float
    ) -> WatershedAnalysisResult:
        """Implements watershed analysis by delegating to engine/hydroma."""
        design_result = hydroma_design_check_dam(slope_pct, area_m2, rainfall_mm)
        return WatershedAnalysisResult(
            design_proposal=design_result,
            input_data={"slope_pct": slope_pct, "area_m2": area_m2, "rainfall_mm": rainfall_mm},
        )

    def analyze_groundwater(self, gw_data: dict[str, Any]) -> GroundwaterAnalysisResult:
        """Implements groundwater analysis (placeholder)."""
        estimated_depth = gw_data.get("estimated_water_table_depth_m", 10.0)
        quality_class = "Fresh"
        return GroundwaterAnalysisResult(
            estimated_depth_m=estimated_depth,
            quality_class=quality_class,
            input_data=gw_data,
        )
