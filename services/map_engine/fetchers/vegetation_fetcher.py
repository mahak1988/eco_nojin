"""Vegetation Fetcher - Synthetic Sentinel-2 spectral data with phenology."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
from shapely.geometry import Polygon

from ..base import MapFetcher


class VegetationFetcher(MapFetcher):
    """
    Generates synthetic Sentinel-2-like spectral data.

    Bands (reflectance, 0-10000 scaled):
    - B02 (Blue, 490nm)
    - B03 (Green, 560nm)
    - B04 (Red, 665nm)
    - B08 (NIR, 842nm)
    - B11 (SWIR, 1610nm)
    - SCL (Scene Classification Layer)
    """

    # Typical reflectance ranges (scaled 0-10000)
    BAND_PROFILES = {
        "B02": {"vegetation": (400, 800), "soil": (1500, 2500), "water": (200, 500)},
        "B03": {"vegetation": (600, 1200), "soil": (1800, 2800), "water": (150, 400)},
        "B04": {"vegetation": (300, 900), "soil": (2000, 3200), "water": (100, 300)},
        "B08": {"vegetation": (3500, 6500), "soil": (2200, 3200), "water": (50, 200)},
        "B11": {"vegetation": (1500, 3500), "soil": (2500, 3800), "water": (30, 150)},
    }

    # Phenology: NDVI by season for different land covers
    PHENOLOGY = {
        "cropland": {"spring": 0.65, "summer": 0.55, "autumn": 0.30, "winter": 0.15},
        "forest":   {"spring": 0.75, "summer": 0.80, "autumn": 0.60, "winter": 0.55},
        "grass":    {"spring": 0.60, "summer": 0.45, "autumn": 0.25, "winter": 0.10},
        "shrub":    {"spring": 0.50, "summer": 0.40, "autumn": 0.30, "winter": 0.25},
        "bare":     {"spring": 0.10, "summer": 0.08, "autumn": 0.08, "winter": 0.05},
    }

    def __init__(self, cache_dir: Path = Path("data/maps/vegetation_cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def layer_name(self) -> str:
        return "vegetation"

    def _cache_key(self, region: Polygon, resolution: float, season: str) -> str:
        bounds = region.bounds
        key = f"veg_{bounds[0]:.4f}_{bounds[1]:.4f}_{bounds[2]:.4f}_{bounds[3]:.4f}_{resolution}_{season}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def fetch(
        self,
        region: Polygon,
        resolution: float = 10.0,
        season: str = "summer",
        cloud_cover_pct: float = 10.0,
        **kwargs,
    ) -> xr.DataArray:
        """Fetch synthetic Sentinel-2 multi-band data."""
        cache_key = self._cache_key(region, resolution, season)
        cache_path = self.cache_dir / f"{cache_key}.tif"

        if cache_path.exists():
            try:
                da = rioxarray.open_rasterio(str(cache_path), masked=True)
                print(f"  [VEGETATION] Loaded from cache: {da.shape}")
                return da
            except Exception as e:
                print(f"  [VEGETATION] Cache load failed: {e}")
                cache_path.unlink(missing_ok=True)

        # Generate synthetic Sentinel-2
        s2_data = await self._generate_synthetic_s2(
            region, resolution, season, cloud_cover_pct
        )

        # Save to cache
        s2_data.rio.to_raster(str(cache_path), driver="GTiff", compress="lzw")
        print(f"  [VEGETATION] Generated: {s2_data.shape}")
        return s2_data

    async def _generate_synthetic_s2(
        self,
        region: Polygon,
        resolution: float,
        season: str,
        cloud_cover_pct: float,
    ) -> xr.DataArray:
        """Generate synthetic Sentinel-2 data with realistic spectral signatures."""
        bounds = region.bounds
        width = max(int((bounds[2] - bounds[0]) / (resolution / 111000)), 100)
        height = max(int((bounds[3] - bounds[1]) / (resolution / 111000)), 100)

        y = np.linspace(bounds[3], bounds[1], height)
        x = np.linspace(bounds[0], bounds[2], width)

        # Generate land cover mix (simple spatial pattern)
        land_cover = self._generate_land_cover_mix(height, width)

        # Generate each band
        bands_data = []
        band_names = ["B02", "B03", "B04", "B08", "B11", "SCL"]

        for band in band_names:
            if band == "SCL":
                band_data = self._generate_scl(height, width, cloud_cover_pct)
            else:
                band_data = self._generate_spectral_band(
                    band, land_cover, season, height, width
                )
            bands_data.append(band_data)

        # Stack into 3D array (band, y, x)
        stack = np.stack(bands_data, axis=0).astype(np.uint16)

        # Create DataArray with band dimension
        da = xr.DataArray(
            stack,
            dims=["band", "y", "x"],
            coords={
                "band": band_names,
                "y": y,
                "x": x,
            },
            attrs={
                "source": "synthetic_sentinel2",
                "season": season,
                "cloud_cover_pct": cloud_cover_pct,
                "units": "reflectance_0_10000",
            },
        )

        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")

        return da

    def _generate_land_cover_mix(self, height: int, width: int) -> np.ndarray:
        """Generate a land cover map with realistic spatial patterns."""
        # Create spatial zones using smooth noise
        y = np.linspace(0, 1, height)
        x = np.linspace(0, 1, width)
        X, Y = np.meshgrid(x, y)

        # Smooth noise for natural-looking boundaries
        noise = (
            np.sin(X * 10) * 0.3
            + np.cos(Y * 8) * 0.3
            + np.sin(X * 5 + Y * 7) * 0.2
            + np.random.normal(0, 0.1, (height, width))
        )

        # Classify into land cover types
        land_cover = np.full((height, width), "cropland", dtype=object)
        land_cover[noise > 0.3] = "forest"
        land_cover[noise > 0.5] = "shrub"
        land_cover[noise < -0.3] = "grass"
        land_cover[noise < -0.5] = "bare"

        return land_cover

    def _generate_spectral_band(
        self,
        band: str,
        land_cover: np.ndarray,
        season: str,
        height: int,
        width: int,
    ) -> np.ndarray:
        """Generate a spectral band based on land cover and phenology."""
        result = np.zeros((height, width), dtype=np.float32)

        for lc_type, target_ndvi in self.PHENOLOGY.items():
            mask = land_cover == lc_type
            if not np.any(mask):
                continue

            # Get seasonal NDVI
            ndvi = target_ndvi.get(season, target_ndvi["summer"])

            # Get band-specific reflectance range
            band_range = self.BAND_PROFILES[band]

            # Blend vegetation and soil signatures based on NDVI
            veg_low, veg_high = band_range["vegetation"]
            soil_low, soil_high = band_range["soil"]

            # Higher NDVI = more vegetation contribution
            veg_fraction = ndvi
            base_reflectance = (
                veg_fraction * np.random.uniform(veg_low, veg_high, (height, width))
                + (1 - veg_fraction) * np.random.uniform(soil_low, soil_high, (height, width))
            )

            # Add noise
            noise = np.random.normal(0, 100, (height, width))
            reflectance = base_reflectance + noise

            # Apply to mask
            result[mask] = reflectance[mask]

        # Clip to valid range and convert to uint16
        return np.clip(result, 0, 10000).astype(np.uint16)

    def _generate_scl(
        self,
        height: int,
        width: int,
        cloud_cover_pct: float,
    ) -> np.ndarray:
        """
        Generate Scene Classification Layer.

        SCL classes:
        0: No data
        1: Saturated or defective
        2: Dark area pixels
        3: Cloud shadows
        4: Vegetation
        5: Bare soils
        6: Water
        7: Unclassified
        8: Cloud medium probability
        9: Cloud high probability
        10: Thin cirrus
        11: Snow
        """
        # Start with vegetation as default
        scl = np.full((height, width), 4, dtype=np.uint8)

        # Add some bare soil areas
        soil_mask = np.random.random((height, width)) > 0.85
        scl[soil_mask] = 5

        # Add water bodies (small patches)
        water_mask = np.random.random((height, width)) > 0.95
        scl[water_mask] = 6

        # Add clouds
        cloud_fraction = cloud_cover_pct / 100.0
        cloud_mask = np.random.random((height, width)) < cloud_fraction
        scl[cloud_mask] = 9  # High probability cloud

        # Add cloud shadows near clouds
        if np.any(cloud_mask):
            # Simple: shadow slightly offset from clouds
            shadow_mask = np.roll(cloud_mask, 2, axis=0) & ~cloud_mask
            scl[shadow_mask] = 3

        return scl
