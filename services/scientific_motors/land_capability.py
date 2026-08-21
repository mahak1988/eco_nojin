"""
Hydroma Nojin - Land Capability Classification (LCC)
USDA-based land capability classification for sustainable land use planning.
"""
from __future__ import annotations

import time
import numpy as np
import xarray as xr
from typing import Dict, Any, List

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)


class LandCapabilityMotor(AbstractScientificMotor):
    """
    Land Capability Classification Motor (USDA standard)
    
    Classifies land into 8 capability classes based on:
    - Slope gradient
    - Soil depth
    - Soil texture
    - Erosion risk
    - Drainage
    """

    LCC_DESCRIPTIONS = {
        1: "Excellent - No limitations for cultivation",
        2: "Good - Moderate limitations, simple conservation needed",
        3: "Moderate - Severe limitations, special conservation practices",
        4: "Poor - Very severe limitations, restricted crop choice",
        5: "Unsuitable for cultivation - Pasture/range/forest only",
        6: "Severe limitations - Grazing/forest with restrictions",
        7: "Very severe - Forestry/grazing with intensive management",
        8: "Non-arable - Wildlife/recreation/watershed only",
    }

    @property
    def motor_type(self) -> MotorType:
        return MotorType.BIOFERTILIZER  # Reuse until we add LCC enum

    @property
    def display_name(self) -> str:
        return "Land Capability Classification (USDA)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("dem", "raster", True, "Digital Elevation Model"),
            MotorInput("slope", "raster", False, "Slope % (computed from DEM if missing)"),
            MotorInput("soil_depth", "raster", True, "Soil depth (cm)"),
            MotorInput("soil_texture", "raster", True, "Soil texture class (1-12)"),
            MotorInput("erosion_risk", "raster", False, "Erosion risk (0-100)"),
            MotorInput("drainage", "raster", False, "Drainage class (1-7)"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("lcc_class", "raster", "class", "LCC class (1-8)"),
            MotorOutput("lcc_description", "json", "map", "LCC class descriptions"),
            MotorOutput("limiting_factor", "raster", "code", "Primary limiting factor"),
            MotorOutput("suitable_crops", "json", "map", "Recommended crops per class"),
        ]

    async def execute(
        self,
        inputs: Dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute land capability classification."""
        start_time = time.time()
        run_id = f"LCC_{parameters.scenario_name}_{int(time.time())}"

        try:
            dem = inputs.get("dem")
            soil_depth = inputs.get("soil_depth")
            soil_texture = inputs.get("soil_texture")
            erosion_risk = inputs.get("erosion_risk")
            drainage = inputs.get("drainage")

            # Validation
            if any(v is None for v in [dem, soil_depth, soil_texture]):
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required inputs (dem, soil_depth, soil_texture)",
                )

            # Compute slope from DEM if not provided
            slope = inputs.get("slope")
            if slope is None:
                slope = self._compute_slope_from_dem(dem)

            # Align all rasters to DEM grid
            slope = self._align_to_grid(slope, dem)
            soil_depth = self._align_to_grid(soil_depth, dem)
            soil_texture = self._align_to_grid(soil_texture, dem)

            if erosion_risk is not None:
                erosion_risk = self._align_to_grid(erosion_risk, dem)
            else:
                # Estimate from slope
                erosion_risk = np.clip(slope.values * 5, 0, 100)
                erosion_risk = xr.DataArray(
                    erosion_risk, dims=dem.dims, coords=dem.coords
                )

            if drainage is not None:
                drainage = self._align_to_grid(drainage, dem)
            else:
                # Assume moderate drainage
                drainage = xr.DataArray(
                    np.full(dem.shape, 4), dims=dem.dims, coords=dem.coords
                )

            # Classify each pixel
            lcc_class, limiting_factor = self._classify_land(
                slope.values,
                soil_depth.values,
                soil_texture.values,
                erosion_risk.values,
                drainage.values,
            )

            # Build output rasters
            lcc_raster = xr.DataArray(
                lcc_class, dims=dem.dims, coords=dem.coords,
                attrs={"units": "class", "description": "LCC class (1=best, 8=worst)"}
            )

            limiting_raster = xr.DataArray(
                limiting_factor, dims=dem.dims, coords=dem.coords,
                attrs={"units": "code", "description": "Limiting factor code"}
            )

            # Summary statistics
            unique, counts = np.unique(lcc_class, return_counts=True)
            distribution = {
                f"Class {int(c)}": {
                    "pixels": int(n),
                    "percent": float(n / lcc_class.size * 100),
                    "description": self.LCC_DESCRIPTIONS[int(c)],
                }
                for c, n in zip(unique, counts)
            }

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "lcc_class": lcc_raster,
                    "lcc_description": self.LCC_DESCRIPTIONS,
                    "limiting_factor": limiting_raster,
                    "suitable_crops": self._get_suitable_crops(),
                },
                summary={
                    "distribution": distribution,
                    "total_pixels": int(lcc_class.size),
                    "cultivable_percent": float(
                        np.sum(lcc_class <= 4) / lcc_class.size * 100
                    ),
                },
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

    def _compute_slope_from_dem(self, dem: xr.DataArray) -> xr.DataArray:
        """Compute slope percentage from DEM."""
        if 'y' in dem.dims and 'x' in dem.dims:
            y_coord = dem.y.values
            x_coord = dem.x.values
        else:
            y_coord = dem.coords[dem.dims[0]].values
            x_coord = dem.coords[dem.dims[1]].values

        is_latlon = abs(y_coord[0]) <= 90
        if is_latlon and len(y_coord) > 1 and len(x_coord) > 1:
            lat_mean = float(np.mean(y_coord))
            dy_m = float(np.abs(y_coord[1] - y_coord[0])) * 111000
            dx_m = float(np.abs(x_coord[1] - x_coord[0])) * 111000 * np.cos(np.radians(lat_mean))
        else:
            dy_m = float(np.abs(y_coord[1] - y_coord[0])) if len(y_coord) > 1 else 30.0
            dx_m = float(np.abs(x_coord[1] - x_coord[0])) if len(x_coord) > 1 else 30.0

        dy, dx = np.gradient(dem.values, dy_m, dx_m, axis=(0, 1))
        slope_pct = np.sqrt(dx**2 + dy**2) * 100  # Convert to percentage

        return xr.DataArray(
            slope_pct.astype(np.float32),
            dims=dem.dims, coords=dem.coords,
            attrs={"units": "percent", "description": "Slope percentage"}
        )

    def _align_to_grid(self, raster: xr.DataArray, target: xr.DataArray) -> xr.DataArray:
        """Align raster to target grid."""
        if raster is None:
            return None
        if raster.shape == target.shape:
            return raster
        try:
            if hasattr(raster, 'rio') and hasattr(target, 'rio'):
                return raster.rio.reproject_match(target)
        except Exception:
            pass
        from scipy.ndimage import zoom
        zy = target.shape[0] / raster.shape[0]
        zx = target.shape[1] / raster.shape[1]
        resampled = zoom(raster.values, (zy, zx), order=1)
        return xr.DataArray(resampled, dims=target.dims, coords=target.coords)

    def _classify_land(
        self,
        slope: np.ndarray,
        soil_depth: np.ndarray,
        soil_texture: np.ndarray,
        erosion: np.ndarray,
        drainage: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Classify land using USDA LCC criteria.
        
        Limiting factor codes:
        0 = No limitation
        1 = Slope
        2 = Soil depth
        3 = Soil texture
        4 = Erosion
        5 = Drainage
        """
        shape = slope.shape
        lcc = np.ones(shape, dtype=np.int8)
        limiting = np.zeros(shape, dtype=np.int8)

        # Slope-based classification (primary factor)
        # Class I: <2% slope
        # Class II: 2-6%
        # Class III: 6-12%
        # Class IV: 12-20%
        # Class VI: 20-30%
        # Class VII: 30-60%
        # Class VIII: >60%
        slope_class = np.ones(shape, dtype=np.int8)
        slope_class[slope >= 2] = 2
        slope_class[slope >= 6] = 3
        slope_class[slope >= 12] = 4
        slope_class[slope >= 20] = 6
        slope_class[slope >= 30] = 7
        slope_class[slope >= 60] = 8

        # Soil depth limitation
        # >100 cm: no limitation
        # 50-100 cm: class II
        # 25-50 cm: class IV
        # 10-25 cm: class VI
        # <10 cm: class VIII
        depth_class = np.ones(shape, dtype=np.int8)
        depth_class[soil_depth < 100] = 2
        depth_class[soil_depth < 50] = 4
        depth_class[soil_depth < 25] = 6
        depth_class[soil_depth < 10] = 8

        # Texture limitation
        # Assume texture class: 1=sand, 6=loam (best), 12=clay
        # Best classes 4-7 (loam, silt loam, etc)
        texture_class = np.ones(shape, dtype=np.int8)
        texture_class[(soil_texture < 4) | (soil_texture > 8)] = 3
        texture_class[(soil_texture < 3) | (soil_texture > 9)] = 4
        texture_class[(soil_texture < 2) | (soil_texture > 10)] = 6

        # Erosion limitation
        erosion_class = np.ones(shape, dtype=np.int8)
        erosion_class[erosion > 30] = 3
        erosion_class[erosion > 60] = 5
        erosion_class[erosion > 80] = 7

        # Drainage limitation (1=excess, 4=well, 7=very poor)
        drainage_class = np.ones(shape, dtype=np.int8)
        drainage_class[(drainage <= 2) | (drainage >= 6)] = 3
        drainage_class[(drainage <= 1) | (drainage >= 7)] = 5

        # Take the worst (maximum) class
        all_classes = np.stack([
            slope_class, depth_class, texture_class,
            erosion_class, drainage_class
        ], axis=0)
        lcc = np.max(all_classes, axis=0)

        # Determine primary limiting factor
        # Find which factor gave the worst class
        factor_indices = np.argmax(all_classes, axis=0)
        limiting = factor_indices + 1  # 1=slope, 2=depth, 3=texture, 4=erosion, 5=drainage
        limiting[lcc == 1] = 0  # No limitation for class I

        return lcc, limiting

    def _get_suitable_crops(self) -> Dict[int, List[str]]:
        """Recommended crops per LCC class."""
        return {
            1: ["گندم", "جو", "ذرت", "سبزیجات", "حبوبات"],
            2: ["گندم", "جو", "پنبه", "آفتابگردان"],
            3: ["جو", "علوفه", "سیب‌زمینی", "چغندر"],
            4: ["علوفه دائمی", "مراتع"],
            5: ["چراگاه طبیعی", "جنگل‌کاری"],
            6: ["چراگاه محدود", "جنگل‌کاری محدود"],
            7: ["جنگل‌کاری حفاظتی"],
            8: ["حفاظت زیستگاه", "گردشگری"],
        }