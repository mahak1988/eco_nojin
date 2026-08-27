"""Module for calculating surface runoff."""
from __future__ import annotations

import logging
from enum import Enum
from typing import Literal

import numpy as np
import xarray as xr
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MethodType = Literal["SCS-CN", "Rational"]

class CurveNumberType(str, Enum):
    """Common Curve Number values based on land use and hydrologic soil group."""
    PASTURE_GOOD_CONDITION = 60
    FOREST_MIXED = 65
    CULTIVATED_IRRIGATED = 85
    URBAN_RESIDENTIAL = 85
    # Add more as needed

class RunoffInput(BaseModel):
    """Input parameters for point-scale runoff calculation."""
    precipitation_mm: float = Field(..., gt=0, description="Total precipitation depth in millimeters")
    curve_number: float | CurveNumberType = Field(70, description="Curve Number (CN) or predefined type")
    area_ha: float = Field(..., gt=0, description="Area of the watershed in hectares")
    method: MethodType = Field("SCS-CN", description="Method to use for calculation")
    rational_coefficient: float = Field(0.6, description="Rational coefficient (for Rational method)")


class RunoffOutput(BaseModel):
    """Output results of runoff calculation."""
    volume_m3: float = Field(..., description="Total runoff volume in cubic meters")
    peak_flow_m3s: float | None = Field(None, description="Peak runoff flow rate (if applicable)")


# --- NEW: Spatial Runoff Calculation ---
class SpatialRunoffInput(BaseModel):
    """Input parameters for spatial runoff calculation."""
    dem_path: str = Field(..., description="Path to DEM file")
    land_use_path: str = Field(..., description="Path to Land Use/Land Cover file (GeoTIFF)")
    soil_path: str = Field(..., description="Path to Soil Type file (GeoTIFF)")
    precipitation_mm: float = Field(..., gt=0, description="Precipitation depth in millimeters")
    method: Literal["SCS-CN"] = Field("SCS-CN", description="Currently only SCS-CN is supported for spatial calc") # Extendable
    target_crs: str = Field(default="auto", description="Target coordinate reference system")


class SpatialRunoffOutput(BaseModel):
    """Output results of spatial runoff calculation."""
    runoff_volume_map_path: str | None = Field(None, description="Path to saved runoff volume GeoTIFF (mm)")
    peak_flow_map_path: str | None = Field(None, description="Path to saved peak flow GeoTIFF (m3/s)")


class RunoffCalculator:
    """Calculates point-scale surface runoff volume and peak flow."""
    # ... (existing code for point-scale calculation) ...


class SpatialRunoffCalculator:
    """Calculates spatially distributed surface runoff."""

    def __init__(self):
        pass

    def _load_and_align_layers(self, dem_path: str, lu_path: str, soil_path: str, target_crs: str):
        """Loads and aligns DEM, Land Use, and Soil layers."""
        import rioxarray
        dem = rioxarray.open_rasterio(dem_path, chunks=True).squeeze()
        lu = rioxarray.open_rasterio(lu_path, chunks=True).squeeze()
        soil = rioxarray.open_rasterio(soil_path, chunks=True).squeeze()

        # Reproject if necessary
        if target_crs != "auto":
             dem = dem.rio.reproject(target_crs)
             lu = lu.rio.reproject(target_crs)
             soil = soil.rio.reproject(target_crs)
        else:
            # Assume all are in the same CRS as DEM
            target_crs = dem.rio.crs.to_string()

        # Align layers (e.g., resample LU and Soil to match DEM grid)
        lu_aligned = lu.rio.reproject_match(dem, nodata=lu.rio.nodata)
        soil_aligned = soil.rio.reproject_match(dem, nodata=soil.rio.nodata)

        return dem, lu_aligned, soil_aligned, target_crs

    def _create_cn_map_from_lu_soil(self, lu: xr.DataArray, soil: xr.DataArray) -> xr.DataArray:
        """Creates a CN map based on Land Use and Soil type."""
        # This is a simplified mapping. A real implementation would use a lookup table.
        # Example: CN = f(LU, Soil_Group)
        # For now, assign CN based on LU assuming a default soil group.
        cn_map = xr.where(lu == 1, 60,  # Forest -> CN 60
                          xr.where(lu == 2, 70,  # Pasture -> CN 70
                                   xr.where(lu == 3, 85, # Urban -> CN 85
                                            75))) # Default CN
        # Further refine based on soil group if soil data is detailed enough
        return cn_map

    def execute(self, input_data: SpatialRunoffInput) -> SpatialRunoffOutput:
        """Main execution function for spatial calculation."""
        logger.info(f"Starting spatial runoff calculation using {input_data.method} method.")

        dem, lu, soil, target_crs = self._load_and_align_layers(
            input_data.dem_path, input_data.land_use_path, input_data.soil_path, input_data.target_crs
        )

        cn_map = self._create_cn_map_from_lu_soil(lu, soil)

        # --- SCS-CN Spatial Calculation ---
        if input_data.method == "SCS-CN":
            s = (1000 / cn_map) - 10 # Potential maximum retention
            initial_abstraction = 0.2 * s

            # Precipitation is assumed uniform across the area
            precip_da = xr.full_like(dem, input_data.precipitation_mm, dtype=np.float32)

            runoff_depth = xr.where(precip_da <= initial_abstraction, 0.0,
                                    ((precip_da - initial_abstraction) ** 2) / (precip_da - initial_abstraction + s))

            # Clip negative values
            runoff_depth = xr.where(runoff_depth < 0, 0.0, runoff_depth)

            # Save the resulting runoff depth map
            output_dir = Path("data/spatial_runoff")
            output_dir.mkdir(parents=True, exist_ok=True)
            runoff_map_path = str(output_dir / f"runoff_cn_{input_data.method}_site_{hash(input_data.dem_path)}.tif")

            runoff_depth.rio.write_crs(target_crs, inplace=True)
            runoff_depth.rio.to_raster(runoff_map_path)

            logger.info(f"Spatial runoff map saved to {runoff_map_path}")
            return SpatialRunoffOutput(runoff_volume_map_path=runoff_map_path)

        else:
            raise ValueError(f"Spatial calculation for method '{input_data.method}' is not yet implemented.")

# Note: Need to import Path
from pathlib import Path
