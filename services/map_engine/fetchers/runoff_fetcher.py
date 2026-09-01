"""Runoff Fetcher - Computes Curve Number from Land Cover and Soil."""
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


class RunoffFetcher(MapFetcher):
    """
    Computes SCS Curve Number (CN) from Land Cover and Soil.

    Hydrologic Soil Groups (HSG):
    A: Low runoff potential (sand, loamy sand)
    B: Moderate (sandy loam)
    C: Moderately high (loam, silt loam)
    D: High runoff potential (clay, silty clay)
    """

    # CN values for AMC-II (normal conditions)
    # Source: USDA TR-55
    CN_TABLE = {
        10: {"A": 36, "B": 60, "C": 73, "D": 79},   # Tree cover
        20: {"A": 45, "B": 66, "C": 77, "D": 83},   # Shrubland
        30: {"A": 39, "B": 61, "C": 74, "D": 80},   # Grassland
        40: {"A": 64, "B": 76, "C": 84, "D": 88},   # Cropland
        50: {"A": 98, "B": 98, "C": 98, "D": 98},   # Built-up
        60: {"A": 77, "B": 86, "C": 91, "D": 94},   # Bare soil
        70: {"A": 0,  "B": 0,  "C": 0,  "D": 0},    # Snow/ice
        80: {"A": 100,"B": 100,"C": 100,"D": 100},  # Water
        90: {"A": 100,"B": 100,"C": 100,"D": 100},  # Wetland
        100: {"A": 63, "B": 77, "C": 85, "D": 89},  # Moss/lichen
    }

    def __init__(self, cache_dir: Path = Path("data/maps/runoff_cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def layer_name(self) -> str:
        return "runoff"

    def _cache_key(self, region: Polygon, resolution: float) -> str:
        bounds = region.bounds
        key = f"cn_{bounds[0]:.4f}_{bounds[1]:.4f}_{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def fetch(
        self,
        region: Polygon,
        resolution: float = 30.0,
        landcover: xr.DataArray = None,
        soil: xr.DataArray = None,
        **kwargs,
    ) -> xr.DataArray:
        """Compute CN from land cover and soil texture."""
        cache_key = self._cache_key(region, resolution)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        if cache_path.exists():
            try:
                da = rioxarray.open_rasterio(str(cache_path), masked=True)
                if "band" in da.dims and da.sizes["band"] == 1:
                    da = da.isel(band=0, drop=True)
                logger.info(f"  [RUNOFF] Loaded from cache: {da.shape}")
                return da
            except Exception as e:
                logger.info(f"  [RUNOFF] Cache load failed: {e}")
                cache_path.unlink(missing_ok=True)

        cn = await self._compute_cn(region, resolution, landcover, soil)
        cn.rio.to_raster(str(cache_path), driver="GTiff", compress="lzw")
        logger.info(f"  [RUNOFF] Generated CN: {cn.shape}")
        return cn

    async def _compute_cn(
        self,
        region: Polygon,
        resolution: float,
        landcover: xr.DataArray,
        soil: xr.DataArray,
    ) -> xr.DataArray:
        """Compute CN using lookup table."""
        bounds = region.bounds
        width = max(int((bounds[2] - bounds[0]) / (resolution / 111000)), 100)
        height = max(int((bounds[3] - bounds[1]) / (resolution / 111000)), 100)

        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)

        # Generate synthetic land cover if not provided
        if landcover is None:
            lc = self._generate_synthetic_lc(height, width)
        else:
            lc = landcover.values if hasattr(landcover, 'values') else landcover

        # Generate synthetic soil texture if not provided
        if soil is None:
            hsg = self._generate_synthetic_hsg(height, width)
        else:
            # Derive HSG from soil K-factor (approximate)
            hsg = self._soil_to_hsg(soil)

        # CN lookup
        cn = np.full((height, width), 75, dtype=np.float32)  # default

        for lc_class, hsg_cns in self.CN_TABLE.items():
            mask = lc == lc_class
            if not np.any(mask):
                continue

            # Map HSG to CN
            for hsg_class, cn_value in hsg_cns.items():
                hsg_mask = hsg == hsg_class
                combined_mask = mask & hsg_mask
                if np.any(combined_mask):
                    cn[combined_mask] = cn_value

        da = xr.DataArray(
            cn,
            dims=["y", "x"],
            coords={"y": y, "x": x},
            attrs={
                "description": "SCS Curve Number (AMC-II)",
                "units": "dimensionless (0-100)",
                "source": "USDA TR-55",
            },
        )
        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")

        return da

    def _soil_to_hsg(self, soil_k: xr.DataArray) -> np.ndarray:
        """Convert K-factor to Hydrologic Soil Group (approximate)."""
        k = soil_k.values if hasattr(soil_k, 'values') else soil_k
        hsg = np.full_like(k, "B", dtype=object)
        hsg[k < 0.15] = "A"      # Sandy, low erodibility
        hsg[(k >= 0.15) & (k < 0.25)] = "B"
        hsg[(k >= 0.25) & (k < 0.40)] = "C"
        hsg[k >= 0.40] = "D"     # Clay, high erodibility
        return hsg

    def _generate_synthetic_lc(self, height: int, width: int) -> np.ndarray:
        """Generate synthetic land cover classes."""
        y = np.linspace(0, 1, height)
        x = np.linspace(0, 1, width)
        X, Y = np.meshgrid(x, y)

        noise = np.sin(X * 8) * np.cos(Y * 6) + np.random.normal(0, 0.2, (height, width))

        lc = np.full((height, width), 60, dtype=np.uint8)  # bare
        lc[noise > -0.5] = 40  # cropland
        lc[noise > 0.2] = 30  # grass
        lc[noise > 0.6] = 20  # shrub
        lc[noise > 1.0] = 10  # tree

        # Small built-up patches
        built_up = np.random.random((height, width)) > 0.95
        lc[built_up] = 50

        return lc

    def _generate_synthetic_hsg(self, height: int, width: int) -> np.ndarray:
        """Generate synthetic HSG classes."""
        noise = np.random.random((height, width))
        hsg = np.full((height, width), "B", dtype=object)
        hsg[noise < 0.2] = "A"
        hsg[(noise >= 0.2) & (noise < 0.5)] = "B"
        hsg[(noise >= 0.5) & (noise < 0.8)] = "C"
        hsg[noise >= 0.8] = "D"
        return hsg
