"""Slope & Aspect Pipeline (M-SLP) - NumPy 2.x compatible."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import xarray as xr

from ..base import MapPipeline, MapRequest, MapResult, MapType


class SlopeAspectPipeline(MapPipeline):
    """
    Produces detailed slope and aspect classification map.

    Bands:
    1. slope_deg     - Slope in degrees (0-90)
    2. slope_class   - Slope class (1-5)
    3. aspect_deg    - Aspect in degrees (0-360, North=0)
    4. aspect_class  - Aspect class (1-9)
    5. curvature     - Profile curvature
    6. twi           - Topographic Wetness Index
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_SLP

    def get_required_layers(self) -> list:
        return ["dem"]

    async def execute(
        self,
        base_layers: Dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Generate slope & aspect map."""
        start_time = time.time()
        dem = base_layers["dem"]

        # Validate DEM
        if dem.sizes.get("y", 0) < 3 or dem.sizes.get("x", 0) < 3:
            raise ValueError(f"DEM too small: {dem.shape}")

        # Compute derivatives (shared computations)
        dy, dx = self._get_resolution(dem)
        grad_y, grad_x = self._compute_gradients(dem.values, dy, dx)

        slope_deg = self._build_dataarray(
            np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2))),
            dem,
            {"units": "degrees", "description": "Slope"},
        )

        aspect_deg = self._build_dataarray(
            self._compute_aspect_from_gradients(grad_x, grad_y),
            dem,
            {"units": "degrees", "description": "Aspect"},
        )

        # Classifications
        slope_class = self._classify_slope_from_degrees(slope_deg)
        aspect_class = self._classify_aspect_from_degrees(aspect_deg)

        # Higher-order derivatives
        curvature = self._compute_curvature(dem.values, dy, dx, dem)
        twi = self._compute_twi(slope_deg, dem, dx)

        # Stack all bands
        stack = xr.concat(
            [slope_deg, slope_class, aspect_deg, aspect_class, curvature, twi],
            dim="band",
        ).assign_coords(
            band=["slope_deg", "slope_class", "aspect_deg",
                  "aspect_class", "curvature", "twi"]
        )

        # Save COG
        map_id = f"M-SLP_{request.request_id[:8]}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cog_path = output_dir / "slope_aspect.tif"

        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        if str(dem.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

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
                "title": "Slope & Aspect Classification",
                "abstract": "Multi-band slope, aspect, curvature, and TWI map",
                "bands": [str(b) for b in stack.band.values],
                "slope_classes": {
                    "1": "flat (0-2%)",
                    "2": "gentle (2-5%)",
                    "3": "moderate (5-10%)",
                    "4": "steep (10-20%)",
                    "5": "very steep (>20%)",
                },
                "aspect_classes": {
                    "1": "N (337.5-22.5)",
                    "2": "NE (22.5-67.5)",
                    "3": "E (67.5-112.5)",
                    "4": "SE (112.5-157.5)",
                    "5": "S (157.5-202.5)",
                    "6": "SW (202.5-247.5)",
                    "7": "W (247.5-292.5)",
                    "8": "NW (292.5-337.5)",
                },
                "resolution_m": request.resolution,
            },
            processing_time_seconds=processing_time,
            data_sources=["DEM"],
            crs=target_crs,
            bounds=dem.rio.bounds(),
            resolution=float(request.resolution),
        )

    # ================================================================
    # Private helpers - NumPy 2.x compatible
    # ================================================================

    def _get_resolution(self, dem: xr.DataArray) -> Tuple[float, float]:
        """Get pixel resolution in meters."""
        y_vals = dem.y.values
        x_vals = dem.x.values

        # Check if in geographic CRS (degrees) or projected (meters)
        crs_str = str(dem.rio.crs).lower()
        is_geographic = "4326" in crs_str or "geographic" in crs_str

        dy = float(abs(y_vals[1] - y_vals[0]))
        dx = float(abs(x_vals[1] - x_vals[0]))

        if is_geographic:
            # Convert degrees to meters (approximate)
            dy *= 111000
            dx *= 111000 * np.cos(np.radians(float(np.mean(y_vals))))

        if dy <= 0 or dx <= 0:
            raise ValueError(f"Invalid resolution: dy={dy}, dx={dx}")

        return dy, dx

    def _compute_gradients(
        self,
        data: np.ndarray,
        dy: float,
        dx: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute gradients - NumPy 2.x compatible."""
        # Explicit axis specification required in NumPy 2.x
        grad_y, grad_x = np.gradient(data, dy, dx, axis=(0, 1))
        return grad_y, grad_x

    def _compute_aspect_from_gradients(
        self,
        grad_x: np.ndarray,
        grad_y: np.ndarray,
    ) -> np.ndarray:
        """Compute aspect from pre-computed gradients."""
        aspect_rad = np.arctan2(-grad_x, grad_y)
        aspect_deg = np.degrees(aspect_rad)
        # Normalize to 0-360
        aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360, aspect_deg)
        return aspect_deg.astype(np.float32)

    def _build_dataarray(
        self,
        data: np.ndarray,
        template: xr.DataArray,
        attrs: dict,
    ) -> xr.DataArray:
        """Build a DataArray with same coords/crs as template."""
        return xr.DataArray(
            data.astype(np.float32),
            coords=template.coords,
            dims=template.dims,
            attrs=attrs,
        ).rio.write_crs(template.rio.crs)

    def _classify_slope_from_degrees(self, slope_deg: xr.DataArray) -> xr.DataArray:
        """Classify slope into 5 classes (based on percent)."""
        slope_pct = np.tan(slope_deg.values * np.pi / 180) * 100

        classified = np.ones_like(slope_pct, dtype=np.uint8)
        classified = np.where(slope_pct >= 2, 2, classified)
        classified = np.where(slope_pct >= 5, 3, classified)
        classified = np.where(slope_pct >= 10, 4, classified)
        classified = np.where(slope_pct >= 20, 5, classified)

        return xr.DataArray(
            classified,
            coords=slope_deg.coords,
            dims=slope_deg.dims,
            attrs={"description": "Slope class (1=flat, 5=very steep)"},
        ).rio.write_crs(slope_deg.rio.crs)

    def _classify_aspect_from_degrees(self, aspect_deg: xr.DataArray) -> xr.DataArray:
        """Classify aspect into 8 cardinal directions."""
        values = aspect_deg.values
        classified = np.zeros_like(values, dtype=np.uint8)

        classified = np.where((values >= 337.5) | (values < 22.5), 1, classified)  # N
        classified = np.where((values >= 22.5) & (values < 67.5), 2, classified)   # NE
        classified = np.where((values >= 67.5) & (values < 112.5), 3, classified)  # E
        classified = np.where((values >= 112.5) & (values < 157.5), 4, classified) # SE
        classified = np.where((values >= 157.5) & (values < 202.5), 5, classified) # S
        classified = np.where((values >= 202.5) & (values < 247.5), 6, classified) # SW
        classified = np.where((values >= 247.5) & (values < 292.5), 7, classified) # W
        classified = np.where((values >= 292.5) & (values < 337.5), 8, classified) # NW

        return xr.DataArray(
            classified,
            coords=aspect_deg.coords,
            dims=aspect_deg.dims,
            attrs={"description": "Aspect class (1=N, 8=NW)"},
        ).rio.write_crs(aspect_deg.rio.crs)

    def _compute_curvature(
        self,
        data: np.ndarray,
        dy: float,
        dx: float,
        template: xr.DataArray,
    ) -> xr.DataArray:
        """Profile curvature (convex/concave)."""
        # Second derivatives with explicit axes
        dxx = np.gradient(np.gradient(data, dx, axis=1), dx, axis=1)
        dyy = np.gradient(np.gradient(data, dy, axis=0), dy, axis=0)

        # Laplacian (negative = convex, positive = concave)
        curvature = -(dxx + dyy)

        return xr.DataArray(
            curvature.astype(np.float32),
            coords=template.coords,
            dims=template.dims,
            attrs={"description": "Profile curvature"},
        ).rio.write_crs(template.rio.crs)

    def _compute_twi(
        self,
        slope_deg: xr.DataArray,
        template: xr.DataArray,
        dx: float,
    ) -> xr.DataArray:
        """Topographic Wetness Index (simplified)."""
        slope_rad = slope_deg.values * np.pi / 180
        tan_slope = np.tan(slope_rad)

        # Avoid division by zero in flat areas
        tan_slope = np.where(tan_slope < 0.01, 0.01, tan_slope)

        # Simplified: assume uniform contributing area
        # Real implementation needs flow accumulation
        approx_flow_acc = np.full_like(template.values, 100.0, dtype=np.float32)

        twi = np.log((approx_flow_acc * dx) / tan_slope)

        return xr.DataArray(
            twi.astype(np.float32),
            coords=template.coords,
            dims=template.dims,
            attrs={"description": "Topographic Wetness Index"},
        ).rio.write_crs(template.rio.crs)
