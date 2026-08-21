"""HEC-RAS Motor - Simplified Flood Simulation."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

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


class HECRASMOTOR(AbstractScientificMotor):
    """Simplified HEC-RAS hydraulic model for flood simulation."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.HEC_RAS

    @property
    def display_name(self) -> str:
        return "HEC-RAS (Simplified Flood)"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("dem", "raster", True, "Digital Elevation Model"),
            MotorInput("runoff_mm", "raster", True, "Surface runoff from SWAT+"),
            MotorInput("slope", "raster", False, "Slope (computed from DEM if missing)"),
            MotorInput("landcover", "raster", False, "Land cover (optional)"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("peak_discharge_m3s", "raster", "m3/s", "Peak discharge"),
            MotorOutput("flood_depth_m", "raster", "m", "Flood water depth"),
            MotorOutput("flow_velocity_ms", "raster", "m/s", "Flow velocity"),
            MotorOutput("flood_risk_zone", "raster", "class", "Flood risk zone (1-5)"),
        ]

    async def execute(
        self,
        inputs: Dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute HEC-RAS simulation."""
        start_time = time.time()
        run_id = f"HECRAS_{parameters.scenario_name}_{int(time.time())}"

        try:
            dem = inputs.get("dem")
            runoff_mm = inputs.get("runoff_mm")
            slope = inputs.get("slope")
            landcover = inputs.get("landcover")

            if dem is None or runoff_mm is None:
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required inputs: dem or runoff_mm",
                )

            return_period = parameters.custom_params.get("return_period", 100)

            results = await self._simulate_flood(
                dem=dem,
                runoff_mm=runoff_mm,
                slope=slope,
                landcover=landcover,
                return_period=return_period,
                parameters=parameters,
            )

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

    async def _simulate_flood(
        self,
        dem: xr.DataArray,
        runoff_mm: xr.DataArray,
        slope: Optional[xr.DataArray] = None,
        landcover: Optional[xr.DataArray] = None,
        return_period: int = 100,
        **kwargs,
    ) -> Dict[str, xr.DataArray]:
        """Simplified flood simulation using DEM and runoff."""
        # Compute slope from DEM if not provided
        if slope is None:
            slope = self._compute_slope_from_dem(dem)

        # Align runoff to DEM shape if needed
        if runoff_mm.shape != dem.shape:
            runoff_mm = self._align_raster(runoff_mm, dem)

        # Align slope to DEM shape if needed
        if slope.shape != dem.shape:
            slope = self._align_raster(slope, dem)

        # Simplified flood depth calculation
        slope_factor = np.clip(slope.values / 10.0, 0, 2)
        flood_depth = runoff_mm.values * (1.0 - slope_factor * 0.3)
        flood_depth = np.maximum(flood_depth, 0)

        # Peak discharge (simplified)
        pixel_area_m2 = 900.0
        peak_discharge = (runoff_mm.values / 1000.0) * pixel_area_m2 / 3600.0

        # Flow velocity (Manning equation)
        n_manning = 0.03
        slope_rad = np.radians(slope.values)
        flow_velocity = np.where(
            flood_depth > 0,
            (1.0 / n_manning) * (flood_depth ** (2.0 / 3.0)) * (np.sin(slope_rad) ** 0.5),
            0.0,
        )
        flow_velocity = np.clip(flow_velocity, 0, 10)

        # Flood risk zones
        flood_risk = np.ones_like(flood_depth, dtype=np.int32)
        flood_risk[flood_depth > 0.1] = 2
        flood_risk[flood_depth > 0.5] = 3
        flood_risk[flood_depth > 1.0] = 4
        flood_risk[flood_depth > 2.0] = 5

        return {
            "peak_discharge_m3s": xr.DataArray(
                peak_discharge.astype(np.float32),
                dims=dem.dims,
                coords=dem.coords,
                attrs={"units": "m3/s"},
            ).rio.write_crs(dem.rio.crs),
            "flood_depth_m": xr.DataArray(
                flood_depth.astype(np.float32),
                dims=dem.dims,
                coords=dem.coords,
                attrs={"units": "meters"},
            ).rio.write_crs(dem.rio.crs),
            "flow_velocity_ms": xr.DataArray(
                flow_velocity.astype(np.float32),
                dims=dem.dims,
                coords=dem.coords,
                attrs={"units": "m/s"},
            ).rio.write_crs(dem.rio.crs),
            "flood_risk_zone": xr.DataArray(
                flood_risk,
                dims=dem.dims,
                coords=dem.coords,
                attrs={"units": "class"},
            ).rio.write_crs(dem.rio.crs),
        }

    def _compute_slope_from_dem(self, dem: xr.DataArray) -> xr.DataArray:
        """Compute slope from DEM using numpy gradient."""
        # Get coordinates
        if "y" in dem.dims and "x" in dem.dims:
            y_coord = dem.y.values
            x_coord = dem.x.values
        elif "latitude" in dem.dims and "longitude" in dem.dims:
            y_coord = dem.latitude.values
            x_coord = dem.longitude.values
        else:
            y_coord = dem.coords[dem.dims[0]].values
            x_coord = dem.coords[dem.dims[1]].values

        # Calculate cell size in meters
        is_latlon = abs(y_coord[0]) <= 90 and abs(x_coord[0]) <= 180
        if is_latlon and len(y_coord) > 1 and len(x_coord) > 1:
            lat_mean = float(np.mean(y_coord))
            dy_m = float(np.abs(y_coord[1] - y_coord[0])) * 111000
            dx_m = float(np.abs(x_coord[1] - x_coord[0])) * 111000 * float(np.cos(np.radians(lat_mean)))
        else:
            dy_m = float(np.abs(y_coord[1] - y_coord[0])) if len(y_coord) > 1 else 30.0
            dx_m = float(np.abs(x_coord[1] - x_coord[0])) if len(x_coord) > 1 else 30.0

        # Compute gradient
        dy, dx = np.gradient(dem.values, dy_m, dx_m, axis=(0, 1))
        slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

        return xr.DataArray(
            slope_deg.astype(np.float32),
            dims=dem.dims,
            coords=dem.coords,
            attrs={"units": "degrees"},
        ).rio.write_crs(dem.rio.crs)

    def _align_raster(self, source: xr.DataArray, target: xr.DataArray) -> xr.DataArray:
        """Align source raster to target grid."""
        if source.shape == target.shape:
            return source

        try:
            if hasattr(source, "rio") and hasattr(target, "rio"):
                return source.rio.reproject_match(target)
        except Exception:
            pass

        # Fallback: scipy zoom
        from scipy.ndimage import zoom

        zoom_y = target.shape[0] / source.shape[0]
        zoom_x = target.shape[1] / source.shape[1]
        resampled = zoom(source.values, (zoom_y, zoom_x), order=1)

        return xr.DataArray(
            resampled,
            dims=target.dims,
            coords=target.coords,
            attrs=source.attrs,
        ).rio.write_crs(target.rio.crs)

    def _compute_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary statistics."""
        summary = {}
        for key, data in results.items():
            if hasattr(data, "values"):
                values = data.values[~np.isnan(data.values)]
                if len(values) > 0:
                    summary[key] = {
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "mean": float(values.mean()),
                    }
        return summary