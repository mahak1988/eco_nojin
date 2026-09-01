"""Rainfall Fetcher - Computes R-factor from climate data."""
import structlog

logger = structlog.get_logger()
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from shapely.geometry import Polygon

from ..base import MapFetcher


class RainfallFetcher(MapFetcher):
    """Fetches rainfall erosivity (R-factor) data."""

    def __init__(self, cache_dir: Path = Path("data/maps/rainfall_cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def layer_name(self) -> str:
        return "rainfall"

    def _cache_key(self, region: Polygon, resolution: float) -> str:
        bounds = region.bounds
        key = f"rain_{bounds[0]:.4f}_{bounds[1]:.4f}_{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def fetch(self, region: Polygon, resolution: float = 30.0, **kwargs) -> xr.DataArray:
        cache_key = self._cache_key(region, resolution)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        if cache_path.exists():
            try:
                da = rioxarray.open_rasterio(str(cache_path), masked=True)
                if "band" in da.dims and da.sizes["band"] == 1:
                    da = da.isel(band=0, drop=True)
                logger.info(f"  [RAINFALL] Loaded from cache: {da.shape}")
                return da
            except Exception as e:
                logger.info(f"  [RAINFALL] Cache load failed: {e}")
                cache_path.unlink(missing_ok=True)

        r_factor = await self._generate_synthetic_r(region, resolution)
        r_factor.rio.to_raster(str(cache_path), driver="GTiff", compress="lzw")
        logger.info(f"  [RAINFALL] Generated: {r_factor.shape}")
        return r_factor

    async def _generate_synthetic_r(self, region: Polygon, resolution: float) -> xr.DataArray:
        """Generate synthetic R-factor (MJ*mm/ha*h*yr)."""
        bounds = region.bounds
        width = max(int((bounds[2] - bounds[0]) / (resolution / 111000)), 100)
        height = max(int((bounds[3] - bounds[1]) / (resolution / 111000)), 100)

        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)
        X, Y = np.meshgrid(x, y)

        # Semi-arid Iran typical R-factor: 200-500
        r_factor = (
            300.0
            + (Y - bounds[1]) * 2000
            + (X - bounds[0]) * 1000
            + np.random.normal(0, 30, (height, width))
        ).clip(50, 5000)

        da = xr.DataArray(
            r_factor.astype(np.float32),
            dims=["y", "x"],
            coords={"y": y, "x": x},
            attrs={"units": "MJ*mm/ha/h/yr", "description": "R-factor"},
        )
        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
        return da
