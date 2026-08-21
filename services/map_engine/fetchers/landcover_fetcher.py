"""Land Cover Fetcher - Synthetic ESA WorldCover-style data."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from shapely.geometry import Polygon

from ..base import MapFetcher


class LandCoverFetcher(MapFetcher):
    """
    Generates synthetic ESA WorldCover-style land cover data.

    Classes (FAO LCCS compatible):
    10: Tree cover
    20: Shrubland
    30: Grassland
    40: Cropland
    50: Built-up
    60: Bare / sparse vegetation
    70: Snow and ice
    80: Permanent water bodies
    90: Herbaceous wetland
    100: Moss and lichen
    """

    CLASSES = {
        10: "Tree cover",
        20: "Shrubland",
        30: "Grassland",
        40: "Cropland",
        50: "Built-up",
        60: "Bare / sparse vegetation",
        70: "Snow and ice",
        80: "Permanent water bodies",
        90: "Herbaceous wetland",
        100: "Moss and lichen",
    }

    def __init__(self, cache_dir: Path = Path("data/maps/landcover_cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def layer_name(self) -> str:
        return "landcover"

    def _cache_key(self, region: Polygon, resolution: float) -> str:
        bounds = region.bounds
        key = f"lc_{bounds[0]:.4f}_{bounds[1]:.4f}_{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}"
        return hashlib.md5(key.encode()).hexdigest()

    async def fetch(
        self,
        region: Polygon,
        resolution: float = 10.0,
        **kwargs,
    ) -> xr.DataArray:
        """Fetch synthetic land cover map."""
        cache_key = self._cache_key(region, resolution)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        if cache_path.exists():
            try:
                da = rioxarray.open_rasterio(str(cache_path), masked=True)
                if "band" in da.dims and da.sizes["band"] == 1:
                    da = da.isel(band=0, drop=True)
                print(f"  [LANDCOVER] Loaded from cache: {da.shape}")
                return da
            except Exception as e:
                print(f"  [LANDCOVER] Cache load failed: {e}")
                cache_path.unlink(missing_ok=True)

        lc = await self._generate_synthetic_lc(region, resolution)
        lc.rio.to_raster(str(cache_path), driver="GTiff", compress="lzw")
        print(f"  [LANDCOVER] Generated: {lc.shape}")
        return lc

    async def _generate_synthetic_lc(
        self,
        region: Polygon,
        resolution: float,
    ) -> xr.DataArray:
        """Generate realistic land cover map with spatial patterns."""
        bounds = region.bounds
        width = max(int((bounds[2] - bounds[0]) / (resolution / 111000)), 100)
        height = max(int((bounds[3] - bounds[1]) / (resolution / 111000)), 100)

        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)
        X, Y = np.meshgrid(x, y)

        # Multi-scale noise for realistic patterns
        noise1 = np.sin(X * 8) * np.cos(Y * 6)  # Large scale
        noise2 = np.sin(X * 20 + Y * 15) * 0.5  # Medium scale
        noise3 = np.random.normal(0, 0.3, (height, width))  # Small scale

        combined = noise1 + noise2 + noise3

        # Iran-typical land cover distribution (semi-arid)
        # High values: cropland, Low values: bare/shrub
        lc = np.full((height, width), 60, dtype=np.uint8)  # Default: bare

        lc[combined > -0.5] = 40  # Cropland
        lc[combined > 0.2] = 30  # Grassland
        lc[combined > 0.6] = 20  # Shrubland
        lc[combined > 1.0] = 10  # Tree cover

        # Add some built-up areas (simple random patches)
        built_up_mask = np.random.random((height, width)) > 0.95
        lc[built_up_mask] = 50

        # Add small water bodies
        water_mask = (np.sin(X * 30) * np.cos(Y * 25)) > 0.95
        lc[water_mask] = 80

        da = xr.DataArray(
            lc,
            dims=["y", "x"],
            coords={"y": y, "x": x},
            attrs={
                "source": "synthetic_esa_worldcover",
                "classes": str(self.CLASSES),
                "units": "class_id",
            },
        )

        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")

        return da