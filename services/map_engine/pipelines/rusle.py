"""RUSLE Pipeline (M-ERS) - Soil Erosion Risk."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import time
from pathlib import Path

import numpy as np
import xarray as xr

from ..base import MapPipeline, MapRequest, MapResult, MapType


class RUSLEPipeline(MapPipeline):
    """
    Computes soil erosion using Revised Universal Soil Loss Equation:
    A = R * K * LS * C * P
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_ERS

    def get_required_layers(self) -> list:
        return ["dem", "rainfall", "soil"]

    async def execute(
        self,
        base_layers: dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        start_time = time.time()

        dem = base_layers["dem"]
        rainfall = base_layers["rainfall"]
        soil = base_layers["soil"]

        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        # Align layers to DEM grid
        r = self._align_to_grid(rainfall, dem)
        k = self._align_to_grid(soil, dem)

        # Compute LS-factor from DEM
        ls = self._compute_ls(dem)

        # C-factor and P-factor from parameters
        c_value = request.parameters.get("c_factor", 0.3)
        p_value = request.parameters.get("p_factor", 1.0)
        c = xr.full_like(dem, c_value, dtype=np.float32)
        p = xr.full_like(dem, p_value, dtype=np.float32)

        # RUSLE: A = R * K * LS * C * P
        erosion = r * k * ls * c * p
        erosion_class = self._classify_erosion(erosion)

        # Stack output bands
        stack = xr.concat(
            [erosion, erosion_class, ls, r, k],
            dim="band",
        ).assign_coords(band=["erosion", "erosion_class", "ls_factor", "r_factor", "k_factor"])

        if str(dem.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

        # Save COG
        map_id = f"M-ERS_{request.request_id[:8]}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cog_path = output_dir / "erosion_rusle.tif"

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
                "title": "RUSLE Soil Erosion Map",
                "abstract": "Annual soil loss estimated using RUSLE: A = R*K*LS*C*P",
                "equation": "A = R * K * LS * C * P",
                "bands": [str(b) for b in stack.band.values],
                "erosion_range_t_ha_yr": {
                    "min": float(erosion.min()),
                    "max": float(erosion.max()),
                    "mean": float(erosion.mean()),
                },
                "erosion_classes": {
                    "1": "very low (<5 t/ha/yr)",
                    "2": "low (5-10)",
                    "3": "moderate (10-20)",
                    "4": "high (20-40)",
                    "5": "very high (>40)",
                },
                "c_factor_used": c_value,
                "p_factor_used": p_value,
                "standards": ["RUSLE (Renard et al., 1997)", "ISO 19115"],
            },
            processing_time_seconds=processing_time,
            data_sources=["DEM", "Rainfall (synthetic)", "Soil (synthetic)"],
            crs=target_crs,
            bounds=dem.rio.bounds(),
            resolution=float(request.resolution),
        )

    def _align_to_grid(self, source: xr.DataArray, target: xr.DataArray) -> xr.DataArray:
        """Resample source to match target grid."""
        try:
            if source.shape == target.shape:
                return source
            resampled = source.rio.reproject_match(target)
            if "band" in resampled.dims and resampled.sizes["band"] == 1:
                resampled = resampled.isel(band=0, drop=True)
            return resampled
        except Exception as e:
            logger.warning(f"  [WARN] Reproject failed: {e}")
            return source

    def _compute_ls(self, dem: xr.DataArray) -> xr.DataArray:
        """Compute LS-factor (Slope Length & Steepness)."""
        dy = float(np.abs(dem.y[1] - dem.y[0])) * 111000
        dx = float(np.abs(dem.x[1] - dem.x[0])) * 111000

        grad_y, grad_x = np.gradient(dem.values, dy, dx, axis=(0, 1))
        slope_rad = np.arctan(np.sqrt(grad_x ** 2 + grad_y ** 2))
        slope_pct = np.tan(slope_rad) * 100

        slope_length = 100.0  # typical field length in meters

        m = np.where(slope_pct < 1, 0.2,
            np.where(slope_pct < 3, 0.3,
            np.where(slope_pct < 5, 0.4, 0.5)))

        sin_b = np.sin(slope_rad)
        ls = (
            np.power(slope_length / 22.13, m)
            * (65.41 * sin_b ** 2 + 4.56 * sin_b + 0.065)
        )
        ls = np.clip(ls, 0.1, 50.0)

        return xr.DataArray(
            ls.astype(np.float32),
            coords=dem.coords,
            dims=dem.dims,
            attrs={"description": "LS-factor"},
        ).rio.write_crs(dem.rio.crs)

    def _classify_erosion(self, erosion: xr.DataArray) -> xr.DataArray:
        """Classify erosion into 5 risk classes."""
        values = erosion.values
        classified = np.ones_like(values, dtype=np.uint8)
        classified = np.where(values >= 5, 2, classified)
        classified = np.where(values >= 10, 3, classified)
        classified = np.where(values >= 20, 4, classified)
        classified = np.where(values >= 40, 5, classified)

        return xr.DataArray(
            classified,
            coords=erosion.coords,
            dims=erosion.dims,
            attrs={"description": "Erosion risk class"},
        ).rio.write_crs(erosion.rio.crs)
