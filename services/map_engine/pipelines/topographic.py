"""Topographic Map Pipeline (M-TOP) - NumPy 2.x compatible."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from shapely.geometry import LineString

from ..base import MapPipeline, MapRequest, MapResult, MapType


class TopographicPipeline(MapPipeline):
    """
    Produces topographic map with:
    - Elevation (DEM)
    - Slope (%)
    - Aspect (degrees)
    - Hillshade
    - Contour lines (vector)
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_TOP

    def get_required_layers(self) -> list:
        return ["dem"]

    async def execute(
        self,
        base_layers: Dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Generate topographic map."""
        start_time = time.time()

        dem = base_layers["dem"]

        # 1. Calculate slope (degrees -> percent)
        slope = self._calculate_slope(dem)

        # 2. Calculate aspect
        aspect = self._calculate_aspect(dem)

        # 3. Generate hillshade
        hillshade = self._calculate_hillshade(dem)

        # 4. Generate contour lines
        contour_interval = request.parameters.get("contour_interval", 5.0)
        contours = self._generate_contours(dem, contour_interval)

        # 5. Reproject to target CRS
        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        # Save outputs
        map_id = f"M-TOP_{request.request_id[:8]}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Multi-band COG: [elevation, slope, aspect, hillshade]
        cog_path = output_dir / "topographic.tif"
        self._save_multiband_cog(
            dem=dem,
            slope=slope,
            aspect=aspect,
            hillshade=hillshade,
            path=cog_path,
            target_crs=target_crs,
        )

        # Save contour lines as GeoPackage
        contours_path = output_dir / "contours.gpkg"
        if contours is not None and not contours.empty:
            contours.to_file(contours_path, driver="GPKG")
        else:
            contours_path = None

        # Generate metadata (ISO 19115-like)
        metadata = self._generate_metadata(
            request=request,
            dem=dem,
            contour_interval=contour_interval,
            target_crs=target_crs,
        )

        processing_time = time.time() - start_time

        return MapResult(
            map_id=map_id,
            map_type=self.map_type,
            cog_path=cog_path,
            vector_tiles_path=contours_path,
            metadata=metadata,
            processing_time_seconds=processing_time,
            data_sources=["DEM (SRTM/synthetic)"],
            crs=target_crs,
            bounds=dem.rio.bounds(),
            resolution=float(request.resolution),
        )

    # ================================================================
    # Terrain Derivatives - NumPy 2.x Compatible
    # ================================================================

    def _calculate_slope(self, dem: xr.DataArray) -> xr.DataArray:
        """Calculate slope in percent."""
        dy = float(np.abs(dem.y[1] - dem.y[0])) * 111000
        dx = float(np.abs(dem.x[1] - dem.x[0])) * 111000

        # NumPy 2.x: explicit axis specification
        grad_y, grad_x = np.gradient(dem.values, dy, dx, axis=(0, 1))

        # Slope in percent
        slope = np.sqrt(grad_x ** 2 + grad_y ** 2) * 100

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

        slope = np.arctan(np.sqrt(grad_x ** 2 + grad_y ** 2))
        aspect = np.arctan2(-grad_x, grad_y)

        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)

        hillshade = (
            np.sin(altitude_rad) * np.cos(slope)
            + np.cos(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect)
        )

        # Normalize to 0-255
        hillshade = ((hillshade + 1) / 2 * 255).clip(0, 255).astype(np.uint8)

        return xr.DataArray(
            hillshade,
            coords=dem.coords,
            dims=dem.dims,
            attrs={"description": "Hillshade"},
        ).rio.write_crs(dem.rio.crs)

    def _generate_contours(
        self,
        dem: xr.DataArray,
        interval: float,
    ) -> gpd.GeoDataFrame:
        """Generate contour lines as GeoDataFrame - robust marching squares."""
        min_elev = float(dem.min())
        max_elev = float(dem.max())

        if max_elev - min_elev < interval:
            return gpd.GeoDataFrame(
                {"elevation": []}, geometry=[], crs=dem.rio.crs
            )

        elevations = []
        lines = []

        levels = np.arange(
            np.floor(min_elev / interval) * interval + interval,
            np.ceil(max_elev / interval) * interval,
            interval,
        )

        # Marching squares algorithm (no matplotlib dependency)
        data = dem.values
        y_coords = dem.y.values
        x_coords = dem.x.values

        for level in levels:
            above = data >= level

            # Check 4 edges of each cell
            for i in range(data.shape[0] - 1):
                for j in range(data.shape[1] - 1):
                    cell_corners = [
                        (i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)
                    ]

                    states = [above[r, c] for r, c in cell_corners]

                    # Contour edge exists if mixed states
                    if any(states) and not all(states):
                        points = []
                        for k in range(4):
                            r1, c1 = cell_corners[k]
                            r2, c2 = cell_corners[(k + 1) % 4]

                            v1, v2 = data[r1, c1], data[r2, c2]
                            s1, s2 = states[k], states[(k + 1) % 4]

                            if s1 != s2 and v1 != v2:
                                # Linear interpolation
                                t = (level - v1) / (v2 - v1)
                                x = x_coords[c1] + t * (x_coords[c2] - x_coords[c1])
                                y = y_coords[r1] + t * (y_coords[r2] - y_coords[r1])
                                points.append((x, y))

                        if len(points) >= 2:
                            try:
                                line = LineString(points)
                                if line.length > 0:
                                    lines.append(line)
                                    elevations.append(float(level))
                            except Exception:
                                pass

        if not lines:
            return gpd.GeoDataFrame(
                {"elevation": []}, geometry=[], crs=dem.rio.crs
            )

        return gpd.GeoDataFrame(
            {"elevation": elevations},
            geometry=lines,
            crs=dem.rio.crs,
        )

    # ================================================================
    # Output Generation
    # ================================================================

    def _save_multiband_cog(
        self,
        dem: xr.DataArray,
        slope: xr.DataArray,
        aspect: xr.DataArray,
        hillshade: xr.DataArray,
        path: Path,
        target_crs: str,
    ) -> None:
        """Save multi-band COG."""
        # Stack bands
        stack = xr.concat(
            [dem, slope, aspect, hillshade.astype(np.float32)],
            dim="band",
        )
        stack = stack.assign_coords(band=["elevation", "slope", "aspect", "hillshade"])

        # Reproject if needed
        if str(dem.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

        # Write as COG
        stack.rio.to_raster(
            str(path),
            driver="COG",
            compress="DEFLATE",
            overview_resampling="average",
        )

    def _generate_metadata(
        self,
        request: MapRequest,
        dem: xr.DataArray,
        contour_interval: float,
        target_crs: str,
    ) -> dict:
        """Generate ISO 19115-like metadata."""
        return {
            "title": "Topographic Map",
            "abstract": "Multi-band topographic map with elevation, slope, aspect, and hillshade",
            "map_type": self.map_type.value,
            "source_crs": str(dem.rio.crs),
            "target_crs": target_crs,
            "resolution_m": request.resolution,
            "contour_interval_m": contour_interval,
            "elevation_range": {
                "min": float(dem.min()),
                "max": float(dem.max()),
                "mean": float(dem.mean()),
            },
            "bands": ["elevation", "slope", "aspect", "hillshade"],
            "standards": ["ISO 19115", "ISO 19131", "ISO 19157"],
        }
