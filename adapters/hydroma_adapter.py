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
    from engine.hydroma.watershed.calculator import (
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
        # Raised rather than returned as 0.0. The previous stub returned a
        # zero reference evapotranspiration, and the caller labelled the result
        # as a Hargreaves FAO-56 computation. A zero ET0 is also a physical
        # claim, not a neutral one: it says the crop transpires nothing, which
        # is never a correct answer.
        raise RuntimeError(
            "engine.hydroma.evapotranspiration could not be imported; no FAO-56 "
            "reference evapotranspiration is available"
        )

    def hydroma_design_check_dam(slope_pct, area_m2, rainfall_mm):
        # Raised rather than returned as a payload. The previous stub returned
        # {"type": "not_implemented"} with no flag, so a caller could not tell
        # an absent engine from a computed design, and the result was shaped like
        # a successful answer.
        raise RuntimeError(
            "engine.hydroma.watershed.calculator could not be imported; no check-dam "
            "design is available"
        )


class HydromaAdapter(IHydromaEngine):
    """Concrete adapter that uses the existing engine/hydroma modules."""

    def analyze_soil(self, soil_data: dict[str, Any]) -> SoilAnalysisResult:
        """Implements soil analysis by delegating to engine/hydroma."""
        ec = soil_data.get("ec", 0.0)
        result = hydroma_classify_salinity(ec)
        return SoilAnalysisResult(
            data_source="modelled",
            model="soil salinity classification (engine.hydroma.soil.salinity)",
            ec=result.get("ec", ec),
            unit=result.get("unit", "dS/m"),
            classification=result.get("classification", "unknown"),
            description=result.get("description", ""),
            crop_recommendations=result.get("crop_recommendations", {}),
            management=result.get("management", {}),
        )

    def analyze_climate(self, climate_data: dict[str, Any]) -> ClimateAnalysisResult:
        """Implements climate analysis by delegating to engine/hydroma.

        When the engine cannot be imported, the fallback raises rather than
        returning a number, so this method reports ``unavailable`` instead of
        a reference evapotranspiration that was never computed.
        """
        temp_mean = climate_data.get("temp_mean_c", 20.0)
        t_min = climate_data.get("t_min_c", temp_mean - 5)
        t_max = climate_data.get("t_max_c", temp_mean + 5)
        ra_mj = climate_data.get("ra_mj", 15.0)
        try:
            et0_est = calc_et0_hargreaves(t_min=t_min, t_max=t_max, t_mean=temp_mean, ra_mj=ra_mj)
        except RuntimeError as exc:
            return ClimateAnalysisResult(
                data_source="unavailable",
                model="unavailable",
                estimated_et0=None,
                input_data=climate_data,
                method="Hargreaves",
                notes=str(exc),
            )
        return ClimateAnalysisResult(
            data_source="modelled",
            model="FAO-56 reference ET0 (et_calculator.calc_et0_hargreaves)",
            estimated_et0=et0_est,
            input_data=climate_data,
            method="Hargreaves",
        )

    def analyze_watershed(
        self, slope_pct: float, area_m2: float, rainfall_mm: float
    ) -> WatershedAnalysisResult:
        """Implements watershed analysis by delegating to engine/hydroma.

        The fallback raises, so an engine that could not be imported is
        reported as unavailable rather than as a check-dam design.
        """
        try:
            design_result = hydroma_design_check_dam(slope_pct, area_m2, rainfall_mm)
        except RuntimeError as exc:
            return WatershedAnalysisResult(
                data_source="unavailable",
                model="unavailable",
                design_proposal={},
                input_data={
                    "slope_pct": slope_pct,
                    "area_m2": area_m2,
                    "rainfall_mm": rainfall_mm,
                },
                notes=str(exc),
            )
        return WatershedAnalysisResult(
            data_source="modelled",
            model="check-dam design (engine.hydroma.watershed.calculator)",
            design_proposal=design_result,
            input_data={"slope_pct": slope_pct, "area_m2": area_m2, "rainfall_mm": rainfall_mm},
        )

    def analyze_groundwater(self, gw_data: dict[str, Any]) -> GroundwaterAnalysisResult:
        """Groundwater depth and quality.

        The previous version returned a default depth of 10.0 m and the class
        "Fresh" for every call, labelled ``data_source="modelled"`` with a
        model string that said "placeholder". A depth is the number a farmer
        uses to decide whether to drill, and "Fresh" is a potability claim;
        supplying both as constants is worse than supplying nothing.

        Both fields are now optional. A caller that supplies neither gets
        ``unavailable`` and must decide what to do with that, which is the
        outcome the data deserves.
        """
        depth = gw_data.get("estimated_water_table_depth_m")
        quality = gw_data.get("quality_class")

        if depth is None and quality is None:
            return GroundwaterAnalysisResult(
                data_source="unavailable",
                model="none: no groundwater solver is wired into this adapter",
                estimated_depth_m=None,
                quality_class="unknown",
                input_data=gw_data,
                notes=(
                    "no depth and no quality class were supplied, and no solver "
                    "is available to derive them. No groundwater figure was "
                    "invented."
                ),
            )

        return GroundwaterAnalysisResult(
            # Partial data: a depth alone is measured, a class alone is
            # measured, neither is modelled.
            data_source="measured" if (depth is not None or quality is not None) else "unavailable",
            model="supplied measurement",
            estimated_depth_m=depth,
            quality_class=quality or "unknown",
            input_data=gw_data,
        )
