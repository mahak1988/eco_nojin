"""DEM Fetcher - Downloads/caches DEM data (NumPy 2.x & rioxarray compatible)."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import numpy as np
import rioxarray  # CRITICAL: Must be at module level to register .rio accessor
import xarray as xr
from shapely.geometry import Polygon

from ..base import MapFetcher


class DEMFetcher(MapFetcher):
    """Fetches DEM data with proper caching."""

    def __init__(
        self,
        cache_dir: Path = Path("data/maps/dem_cache"),
        source: str = "srtm",
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.source = source.lower()

    @property
    def layer_name(self) -> str:
        return "dem"

    def _generate_cache_key(self, region: Polygon, resolution: float) -> str:
        """Generate unique cache key based on region and resolution."""
        bounds = region.bounds
        key_str = (
            f"{self.source}_{bounds[0]:.4f}_{bounds[1]:.4f}_"
            f"{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}"
        )
        return hashlib.md5(key_str.encode()).hexdigest()

    async def fetch(
        self,
        region: Polygon,
        resolution: float = 30.0,
        **kwargs,
    ) -> xr.DataArray:
        """Fetch DEM for the given region."""
        cache_key = self._generate_cache_key(region, resolution)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        # Check cache first
        if cache_path.exists():
            try:
                dem = self._load_from_cache(cache_path)
                # Validate shape
                if dem.ndim >= 2 and dem.shape[0] >= 3 and dem.shape[1] >= 3:
                    print(f"  [DEMFETCHER] Loaded from cache: {dem.shape}")
                    return dem
                else:
                    print(f"  [DEMFETCHER] Cache invalid shape: {dem.shape}, regenerating")
                    cache_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"  [DEMFETCHER] Cache load failed: {e}, regenerating")
                cache_path.unlink(missing_ok=True)

        # Generate synthetic DEM
        dem = await self._generate_synthetic_dem(region, resolution)

        # Save to cache
        self._save_to_cache(dem, cache_path)

        print(f"  [DEMFETCHER] Generated: {dem.shape}")
        return dem

    async def _generate_synthetic_dem(
        self,
        region: Polygon,
        resolution: float,
    ) -> xr.DataArray:
        """Generate synthetic DEM for development."""
        bounds = region.bounds  # (minx, miny, maxx, maxy)

        # Calculate dimensions (degrees to approximate pixels)
        width = int((bounds[2] - bounds[0]) / (resolution / 111000))
        height = int((bounds[3] - bounds[1]) / (resolution / 111000))

        # Ensure minimum size
        width = max(width, 100)
        height = max(height, 100)

        # Generate coordinates
        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)

        # Generate synthetic elevation
        X, Y = np.meshgrid(x, y)
        elevation = (
            1000.0
            + (X - bounds[0]) * 100
            + (Y - bounds[1]) * 50
            + np.random.normal(0, 5, (height, width))
        )

        # Create 2D DataArray (NOT 3D - no band dimension)
        dem = xr.DataArray(
            elevation.astype(np.float32),
            dims=["y", "x"],
            coords={"y": y, "x": x},
            attrs={
                "source": "synthetic",
                "resolution_m": resolution,
                "units": "meters",
            },
        )

        # Set CRS (WGS84) - rioxarray accessor now available
        dem = dem.rio.write_crs("EPSG:4326")
        dem = dem.rio.set_spatial_dims(x_dim="x", y_dim="y")

        return dem

    def _load_from_cache(self, path: Path) -> xr.DataArray:
        """Load DEM from cached GeoTIFF - handles band dimension correctly."""
        # rioxarray accessor is already registered via module-level import
        da = rioxarray.open_rasterio(str(path), masked=True)

        # Remove band dimension if present (rasterio adds it)
        if "band" in da.dims:
            if da.sizes["band"] == 1:
                da = da.isel(band=0, drop=True)
            else:
                # Multi-band: take first band
                da = da.isel(band=0, drop=True)

        # Ensure 2D shape
        if da.ndim > 2:
            # Squeeze extra dimensions
            da = da.squeeze()

        # Validate
        if da.ndim != 2:
            raise ValueError(
                f"DEM has unexpected shape after load: {da.shape}, dims: {da.dims}"
            )

        # Ensure proper spatial dimensions
        if "y" not in da.dims or "x" not in da.dims:
            # Try to identify spatial dims
            for dim in da.dims:
                if "y" in str(dim).lower():
                    da = da.rename({dim: "y"})
                elif "x" in str(dim).lower():
                    da = da.rename({dim: "x"})

        # Ensure CRS is set
        try:
            _ = da.rio.crs
        except Exception:
            da = da.rio.write_crs("EPSG:4326")

        return da

    def _save_to_cache(self, dem: xr.DataArray, path: Path) -> None:
        """Save DEM to cache as GeoTIFF."""
        # Ensure 2D before saving
        if dem.ndim > 2:
            dem = dem.squeeze()

        # Ensure spatial dims are set
        try:
            dem.rio.set_spatial_dims(x_dim="x", y_dim="y")
        except Exception:
            pass

        # Save
        dem.rio.to_raster(str(path), driver="GTiff", compress="lzw")