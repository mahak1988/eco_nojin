"""
Hydrometeo-DA (Hydroma) Adapter — bridges the services layer to the
engine's hydroma sub-system for soil, climate, watershed and groundwater
analysis.

The adapter wraps the engine's scientific modules behind a thin, stable
surface used by service-layer integration tests and routers.  Each method
delegates to the canonical engine implementation and returns the engine's
own Pydantic result model.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.climate.et_calculator import (
    ClimateData,
    calc_et0_hargreaves,
)
from engine.hydroma.models.groundwater_model import (
    GroundwaterInput,
    GroundwaterModel,
)
from engine.hydroma.models.results import (
    ClimateAnalysisResult,
    GroundwaterAnalysisResult,
    SoilAnalysisResult,
    WatershedAnalysisResult,
)
from engine.hydroma.soil.salinity import classify_salinity
from engine.hydroma.watershed.calculator import design_check_dam as _design_check_dam

__all__ = ["HydromaAdapter"]


class HydromaAdapter:
    """Adapter over the engine's hydroma analysis sub-systems."""

    def __init__(self):
        self._gw_model = GroundwaterModel()

    # ------------------------------------------------------------------
    # Soil analysis
    # ------------------------------------------------------------------
    def analyze_soil(self, soil_data: dict[str, Any]) -> SoilAnalysisResult:
        """Classify soil salinity from an EC reading.

        Delegates to :func:`engine.hydroma.soil.salinity.classify_salinity`.

        Args:
            soil_data: Dict with at least ``ec`` (dS/m).

        Returns:
            A :class:`~engine.hydroma.models.results.SoilAnalysisResult`.
        """
        ec = float(soil_data.get("ec", 0.0))
        result_dict = classify_salinity(ec)
        return SoilAnalysisResult(
            ec=result_dict["ec"],
            classification=result_dict["classification"],
            description=result_dict["description"],
            crop_recommendations=result_dict.get("crop_recommendations", {}),
            management=result_dict.get("management", {}),
            data_source="modelled",
            model="hydroma.soil.salinity.classify_salinity",
        )

    # ------------------------------------------------------------------
    # Climate analysis
    # ------------------------------------------------------------------
    def analyze_climate(
        self,
        climate_data: dict[str, Any],
    ) -> ClimateAnalysisResult:
        """Estimate reference ET0 via the Hargreaves method.

        Delegates to :func:`engine.hydroma.climate.et_calculator.calc_et0_hargreaves`.

        Args:
            climate_data: Dict with ``temp_mean_c``, ``t_min_c`` and ``t_max_c``.
                ``latitude_deg`` and ``doy`` are optional.

        Returns:
            A :class:`~engine.hydroma.models.results.ClimateAnalysisResult`.
        """
        t_min = float(climate_data.get("t_min_c", 0.0))
        t_max = float(climate_data.get("t_max_c", 0.0))
        float(climate_data.get("temp_mean_c", (t_min + t_max) / 2))
        lat = float(climate_data.get("latitude_deg", 35.0))
        doy = int(climate_data.get("doy", 172))

        et0 = calc_et0_hargreaves(
            data=ClimateData(
                tmin=t_min,
                tmax=t_max,
                latitude=lat,
                doy=doy,
            ),
            dtr_floor=0.1,
        )

        return ClimateAnalysisResult(
            estimated_et0=et0,
            input_data=climate_data,
            method="Hargreaves",
            notes=f"ET0 computed for lat={lat}, doy={doy}",
            data_source="modelled",
            model="hydroma.climate.et_calculator.calc_et0_hargreaves",
        )

    # ------------------------------------------------------------------
    # Watershed analysis
    # ------------------------------------------------------------------
    def analyze_watershed(
        self,
        slope_pct: float,
        area_m2: float,
        rainfall_mm: float,
    ) -> WatershedAnalysisResult:
        """Design a check dam for watershed management.

        Delegates to :func:`engine.hydroma.cycle.design_check_dam`.

        Args:
            slope_pct: Average slope of the area, percent.
            area_m2: Contributing area upstream, square metres.
            rainfall_mm: Design rainfall intensity, mm/hour.

        Returns:
            A :class:`~engine.hydroma.models.results.WatershedAnalysisResult`.
        """
        design = _design_check_dam(
            slope_pct=slope_pct,
            area_m2=area_m2,
            rainfall_mm=rainfall_mm,
        )

        return WatershedAnalysisResult(
            design_proposal=design,
            input_data={
                "slope_pct": slope_pct,
                "area_m2": area_m2,
                "rainfall_mm": rainfall_mm,
            },
            notes="Check dam design via FAO Watershed Management Field Manual",
            data_source="modelled",
            model="hydroma.watershed.calculator.design_check_dam",
        )

    # ------------------------------------------------------------------
    # Groundwater analysis
    # ------------------------------------------------------------------
    def analyze_groundwater(
        self,
        gw_data: dict[str, Any],
    ) -> GroundwaterAnalysisResult:
        """Estimate groundwater water-table depth and quality class.

        When ``estimated_water_table_depth_m`` is supplied in *gw_data* it is
        taken as an observed measurement; otherwise the Theis analytical
        solution is evaluated from the remaining parameters.

        Args:
            gw_data: Dict that may contain ``estimated_water_table_depth_m``
                plus the :class:`~engine.hydroma.models.groundwater_model.GroundwaterInput`
                fields (``transmissivity_m2day``, ``storativity``,
                ``pumping_rate_m3day``, ``observation_distance_m``,
                ``time_days``).

        Returns:
            A :class:`~engine.hydroma.models.results.GroundwaterAnalysisResult`.
        """
        observed_depth = gw_data.get("estimated_water_table_depth_m")
        if observed_depth is not None:
            return GroundwaterAnalysisResult(
                estimated_depth_m=float(observed_depth),
                quality_class="Fresh",
                input_data=gw_data,
                notes="Water-table depth from observed measurement",
                data_source="measured",
                model="HydromaAdapter (measured)",
            )

        # Fall back to the Theis analytical model.
        # ``model_type`` is spelled out because pydantic's synthesized
        # __init__ requires it; the literal is GroundwaterInput's own Field
        # default, so the constructed model is unchanged.
        input_data = GroundwaterInput(
            model_type="analytical",
            transmissivity_m2day=gw_data.get("transmissivity_m2day", 10.0),
            storativity=gw_data.get("storativity", 0.1),
            pumping_rate_m3day=gw_data.get("pumping_rate_m3day", 0.0),
            observation_distance_m=gw_data.get("observation_distance_m", 50.0),
            time_days=gw_data.get("time_days", 1.0),
        )
        output = self._gw_model.execute(input_data)

        return GroundwaterAnalysisResult(
            estimated_depth_m=output.drawdown_m,
            quality_class="Fresh",
            input_data=gw_data,
            notes="Water-table depth from Theis analytical solution",
            data_source="modelled",
            model="hydroma.models.groundwater_model.GroundwaterModel",
        )
