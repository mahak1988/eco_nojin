"""Soil Erodibility Fetcher - Computes K-factor from soil properties."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import hashlib
from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from shapely.geometry import Polygon

from ..base import MapFetcher


class SoilErodibilityFetcher(MapFetcher):
    """Computes K-factor using Williams (1995) EPIC equation."""

    def __init__(self, cache_dir: Path = Path("data/maps/soil_cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def layer_name(self) -> str:
        return "soil"

    def _cache_key(self, region: Polygon, resolution: float) -> str:
        bounds = region.bounds
        key = f"soil_{bounds[0]:.4f}_{bounds[1]:.4f}_{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def fetch(self, region: Polygon, resolution: float = 30.0, **kwargs) -> xr.DataArray:
        cache_key = self._cache_key(region, resolution)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        if cache_path.exists():
            try:
                da = rioxarray.open_rasterio(str(cache_path), masked=True)
                if "band" in da.dims and da.sizes["band"] == 1:
                    da = da.isel(band=0, drop=True)
                logger.info(f"  [SOIL] Loaded from cache: {da.shape}")
                return da
            except Exception as e:
                logger.info(f"  [SOIL] Cache load failed: {e}")
                cache_path.unlink(missing_ok=True)

        k_factor = await self._generate_synthetic_k(region, resolution)
        k_factor.rio.to_raster(str(cache_path), driver="GTiff", compress="lzw")
        logger.info(f"  [SOIL] Generated K-factor: {k_factor.shape}")
        return k_factor

    async def _generate_synthetic_k(self, region: Polygon, resolution: float) -> xr.DataArray:
        """Generate synthetic soil properties and compute K-factor."""
        bounds = region.bounds
        width = max(int((bounds[2] - bounds[0]) / (resolution / 111000)), 100)
        height = max(int((bounds[3] - bounds[1]) / (resolution / 111000)), 100)

        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)

        # Synthetic soil texture (loam-dominant)
        sand = 35.0 + np.random.normal(0, 8, (height, width)).clip(5, 95)
        silt = 40.0 + np.random.normal(0, 8, (height, width)).clip(5, 95)
        clay = 100.0 - sand - silt
        clay = np.clip(clay, 5, 95)

        total = sand + silt + clay
        sand = sand / total * 100
        silt = silt / total * 100
        clay = clay / total * 100

        oc = 1.5 + np.random.normal(0, 0.3, (height, width)).clip(0.1, 10.0)

        k_factor = self._compute_k_epic(sand, silt, clay, oc)

        da = xr.DataArray(
            k_factor.astype(np.float32),
            dims=["y", "x"],
            coords={"y": y, "x": x},
            attrs={"units": "t*ha*h/ha/MJ/mm", "description": "K-factor (EPIC)"},
        )
        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
        return da

    @staticmethod
    def _compute_k_epic(sand, silt, clay, oc) -> np.ndarray:
        """Compute K-factor using Williams (1995) EPIC equation."""
        eps = 1e-6
        sn1 = 1.0 - sand / 100.0
        silt_frac = silt / 100.0
        clay_silt = (clay + silt) / 100.0 + eps
        oc_frac = oc / 100.0

        term1 = 0.2 + 0.3 * np.exp(-0.0256 * sand * (1 - silt_frac))
        term2 = np.power(silt_frac / clay_silt, 0.3)
        term3 = 1.0 - 0.25 * oc_frac / (oc_frac + np.exp(3.72 - 2.95 * oc_frac) + eps)
        term4 = 1.0 - 0.7 * sn1 / (sn1 + np.exp(-5.51 + 22.9 * sn1) + eps)

        k = term1 * term2 * term3 * term4
        return np.clip(k, 0.005, 0.8)
