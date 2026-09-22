"""Slope-Aspect Pipeline (M-SLP) - Slope and Aspect Derivatives.

Produces a single-band slope map and a single-band aspect map from a DEM.
Complements the TopographicPipeline (M-TOP) by providing a focused
slope/aspect output suitable for specialized terrain analysis.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import xarray as xr

from ..base import MapPipeline, MapRequest, MapResult, MapType


class SlopeAspectPipeline(MapPipeline):
    """
    Produces slope and aspect derivatives from a DEM.

    Output bands:
    1. slope_pct - Slope in percent (0-100)
    2. aspect_deg - Aspect in degrees (0-360, North=0)
    3. hillshade - Hillshade (0-255) for visualization
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_SLP

    def get_required_layers(self) -> list:
        return ["dem"]

    async def execute(
        self,
        base_layers: dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Generate slope/aspect map."""
        start_time = time.time()

        dem = base_layers["dem"]

        # 1. Calculate slope
        slope = self._calculate_slope(dem)

        # 2. Calculate aspect
        aspect = self._calculate_aspect(dem)

        # 3. Hillshade
        hillshade = self._calculate_hillshade(dem)

        # 4. Reproject to target CRS
        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        # Stack output bands
        stack = xr.concat(
            [slope, aspect, hillshade.astype(np.float32)],
            dim="band",
        ).assign_coords(band=["slope_pct", "aspect_deg", "hillshade"])

        if str(dem.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

        # Save COG
        map_id = f"M-SLP_{request.request_id[:8]}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cog_path = output_dir / "slope_aspect.tif"

        stack.rio.to_raster(
            str(cog_path),
            driver="COG",
            compress="DEFLATE",
            overview_resampling="average",
        )

        processing_time = time.time() - start_time

        return MapResult(
            map_id=map_id,
            map_type=self.map_type,
            cog_path=cog_path,
            metadata={
                "title": "Slope and Aspect Map",
                "abstract": "Slope (percent), aspect (degrees), and hillshade from DEM",
                "bands": ["slope_pct", "aspect_deg", "hillshade"],
                "slope_stats": {
                    "min": float(slope.min()),
                    "max": float(slope.max()),
                    "mean": float(slope.mean()),
                },
                "aspect_stats": {
                    "min": float(aspect.min()),
                    "max": float(aspect.max()),
                    "mean": float(aspect.mean()),
                },
                "standards": ["ISO 19115"],
            },
            processing_time_seconds=processing_time,
            data_sources=["DEM (SRTM/synthetic)"],
            crs=target_crs,
            bounds=dem.rio.bounds(),
            resolution=float(request.resolution),
        )

    def _calculate_slope(self, dem: xr.DataArray) -> xr.DataArray:
        """Calculate slope in percent."""
        dy = float(np.abs(dem.y[1] - dem.y[0])) * 111000
        dx = float(np.abs(dem.x[1] - dem.x[0])) * 111000

        grad_y, grad_x = np.gradient(dem.values, dy, dx, axis=(0, 1))

        slope = np.sqrt(grad_x**2 + grad_y**2) * 100

        return xr.DataArray(
            slope.astype(np.float32),
            coords=dem.coords,
            dims=dem.dims,
            attrs={"units": "percent", "description": "Slope"},
        ).rio.write_crs(dem.rio.crs)

    def _calculate_aspect(self, dem: xr.DataArray) -> xr.DataArray:
        """Calculate aspect in degrees (0-360, North=0)."""
        dy = float(np.abs(dem.y[1] - dem.y[0])) * 111000
        dx = float(np.abs(dem.x[1] - dem.x[0])) * 111000

        grad_y, grad_x = np.gradient(dem.values, dy, dx, axis=(0, 1))

        aspect = np.arctan2(-grad_x, grad_y) * 180 / np.pi
        aspect = np.where(aspect < 0, aspect + 360, aspect)

        return xr.DataArray(
            aspect.astype(np.float32),
            coords=dem.coords,
            dims=dem.dims,
            attrs={"units": "degrees", "description": "Aspect"},
        ).rio.write_crs(dem.rio.crs)

    def _calculate_hillshade(
        self,
        dem: xr.DataArray,
        azimuth: float = 315,
        altitude: float = 45,
    ) -> xr.DataArray:
        """Calculate hillshade (0-255)."""
        dy = float(np.abs(dem.y[1] - dem.y[0])) * 111000
        dx = float(np.abs(dem.x[1] - dem.x[0])) * 111000

        grad_y, grad_x = np.gradient(dem.values, dy, dx, axis=(0, 1))

        slope = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
        aspect = np.arctan2(-grad_x, grad_y)

        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)

        hillshade = np.sin(altitude_rad) * np.cos(slope) + np.cos(altitude_rad) * np.sin(
            slope
        ) * np.cos(azimuth_rad - aspect)

        hillshade = ((hillshade + 1) / 2 * 255).clip(0, 255).astype(np.uint8)

        return xr.DataArray(
            hillshade,
            coords=dem.coords,
            dims=dem.dims,
            attrs={"description": "Hillshade"},
        ).rio.write_crs(dem.rio.crs)
