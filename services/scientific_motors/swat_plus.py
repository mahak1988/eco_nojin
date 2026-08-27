"""SWAT+ Simplified Water Balance Model."""
from __future__ import annotations

import time
from typing import Any

import numpy as np
import xarray as xr

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)


class SWATPlusMotor(AbstractScientificMotor):
    """
    Simplified SWAT+ water balance model.

    Computes:
    - Surface runoff (SCS-CN)
    - Evapotranspiration (Penman-Monteith simplified)
    - Soil water storage
    - Groundwater recharge
    - Streamflow (aggregated)
    """

    @property
    def motor_type(self) -> MotorType:
        return MotorType.SWAT_PLUS

    @property
    def display_name(self) -> str:
        return "SWAT+ (Simplified Water Balance)"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("dem", "raster", True, "Digital Elevation Model"),
            MotorInput("soil", "raster", True, "Soil properties (K-factor)"),
            MotorInput("landcover", "raster", True, "Land cover classes"),
            MotorInput("rainfall", "timeseries", True, "Daily precipitation"),
            MotorInput("temperature", "timeseries", False, "Daily temperature"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("runoff_mm", "raster", "mm", "Surface runoff"),
            MotorOutput("et_mm", "raster", "mm", "Evapotranspiration"),
            MotorOutput("soil_water_mm", "raster", "mm", "Soil water storage"),
            MotorOutput("recharge_mm", "raster", "mm", "Groundwater recharge"),
            MotorOutput("water_yield_mm", "raster", "mm", "Total water yield"),
        ]

    async def execute(
        self,
        inputs: dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute SWAT+ water balance simulation."""
        start_time = time.time()
        run_id = f"SWAT_{parameters.scenario_name}_{int(time.time())}"

        try:
            # Validate inputs
            if not self.validate_inputs(inputs):
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required inputs",
                )

            # Extract inputs
            dem = inputs.get("dem")
            soil = inputs.get("soil")
            landcover = inputs.get("landcover")
            rainfall_ts = inputs.get("rainfall")  # time series

            # Simulate water balance
            results = await self._simulate_water_balance(
                dem=dem,
                soil=soil,
                landcover=landcover,
                rainfall=rainfall_ts,
                parameters=parameters,
            )

            # Compute summary statistics
            summary = self._compute_summary(results)

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs=results,
                summary=summary,
                execution_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    async def _simulate_water_balance(
        self,
        dem: xr.DataArray,
        soil: xr.DataArray,
        landcover: xr.DataArray,
        rainfall: xr.DataArray,
        parameters: MotorParameters,
    ) -> dict[str, Any]:
        """Simulate daily water balance."""
        # Align all rasters to DEM grid
        soil_aligned = self._align_raster(soil, dem)
        lc_aligned = self._align_raster(landcover, dem)

        # Get CN from land cover + soil
        cn = self._compute_cn(lc_aligned, soil_aligned)

        # Simplified ET (Hargreaves method)
        # ET0 = 0.0023 * Ra * (Tavg + 17.8) * (Tmax - Tmin)^0.5
        # For simplicity, assume ET0 = 3-5 mm/day
        et_potential = xr.full_like(dem, 4.0, dtype=np.float32)

        # Total precipitation (sum over time period)
        if hasattr(rainfall, "time"):
            p_total = rainfall.sum(dim="time")
        else:
            p_total = rainfall  # assume single value

        # SCS-CN runoff
        s = (1000.0 / cn - 10.0) * 25.4  # retention
        ia = 0.2 * s  # initial abstraction
        runoff = xr.where(
            p_total > ia,
            (p_total - ia) ** 2 / (p_total - ia + s),
            0.0,
        )

        # Actual ET (limited by available water)
        available_water = p_total - runoff
        et_actual = xr.where(
            available_water > et_potential,
            et_potential,
            available_water,
        )

        # Soil water storage
        soil_water = available_water - et_actual
        soil_water = soil_water.clip(0, 300)  # max 300mm

        # Groundwater recharge (10% of excess)
        recharge = (soil_water * 0.1).clip(0, 50)

        # Water yield (runoff + baseflow)
        baseflow = recharge * 0.5  # 50% becomes baseflow
        water_yield = runoff + baseflow

        return {
            "runoff_mm": runoff,
            "et_mm": et_actual,
            "soil_water_mm": soil_water,
            "recharge_mm": recharge,
            "water_yield_mm": water_yield,
        }

    def _align_raster(self, source: xr.DataArray, target: xr.DataArray) -> xr.DataArray:
        """Align source raster to target grid."""
        try:
            if source.shape == target.shape:
                return source
            return source.rio.reproject_match(target)
        except Exception:
            return source

    def _compute_cn(
        self,
        landcover: xr.DataArray,
        soil: xr.DataArray,
    ) -> xr.DataArray:
        """Compute Curve Number from land cover and soil."""
        # Simplified CN lookup
        cn_table = {
            10: 60,  # Forest
            20: 66,  # Shrub
            30: 61,  # Grass
            40: 76,  # Cropland
            50: 98,  # Built-up
            60: 86,  # Bare
            80: 100, # Water
        }

        lc_values = landcover.values
        cn = np.full_like(lc_values, 75, dtype=np.float32)

        for lc_class, cn_value in cn_table.items():
            mask = lc_values == lc_class
            cn[mask] = cn_value

        return xr.DataArray(
            cn,
            coords=landcover.coords,
            dims=landcover.dims,
        ).rio.write_crs(landcover.rio.crs)

    def _compute_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Compute summary statistics."""
        summary = {}
        for key, data in results.items():
            if isinstance(data, xr.DataArray):
                values = data.values[~np.isnan(data.values)]
                if len(values) > 0:
                    summary[key] = {
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "mean": float(values.mean()),
                        "sum": float(values.sum()),
                    }
        return summary
