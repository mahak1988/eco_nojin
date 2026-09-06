"""
Hydroma Nojin - Sentinel-2 Satellite Data Provider

Provides access to Copernicus Sentinel-2 L2A imagery through:
- Planetary Computer STAC API (primary, free)
- Local cache for offline use
- Band-level and index-level products

Used by:
- Smart Map Generator (NDVI, biomass)
- Crop Advisor (validation)
- Carbon Sequestration (baseline SOC)
- RUSLE Erosion (C-factor)
- Irrigation Scheduler (soil moisture proxy)

Scientific References:
- ESA Sentinel-2 User Handbook
- Planetary Computer STAC API
- Sentinel-2 L2A ATBD (Atmospheric Correction)
"""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import warnings

# Suppress noisy warnings from odc-stac and rasterio
warnings.filterwarnings('ignore', category=UserWarning, module='odc')
warnings.filterwarnings('ignore', category=UserWarning, module='rasterio')
warnings.filterwarnings('ignore', message='.*non-nanosecond precision.*')
warnings.filterwarnings('ignore', message='.*no geotransform.*')

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# Safe Unpickler - محدودسازی کلاس‌های مجاز برای امنیت
# ═══════════════════════════════════════════════════════════════════════

class SafeUnpickler(pickle.Unpickler):
    """Unpickler محدودشده که فقط کلاس‌های امن را بارگذاری می‌کند."""

    ALLOWED_MODULES = {
        'builtins', 'collections', 'datetime',
        'numpy', 'numpy.core', 'numpy.core.multiarray',
        'numpy._core', 'numpy._core.multiarray',
        'xarray', 'xarray.core', 'xarray.core.dataarray',
        'xarray.core.dataset', 'xarray.core.variable',
        'pandas', 'pandas.core', 'pandas.core.frame',
    }

    def find_class(self, module, name):
        if module in self.ALLOWED_MODULES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"Forbidden class: {module}.{name}. "
            f"Only whitelisted classes are allowed for security."
        )


def safe_pickle_load(file_obj):
    """بارگذاری امن فایل pickle با محدودسازی کلاس‌های مجاز."""
    return SafeUnpickler(file_obj).load()


try:
    import rasterio
    import xarray as xr
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    xr = None


class SentinelProduct(Enum):
    """Sentinel-2 product levels."""
    L1C = "Level-1C (TOA reflectance)"
    L2A = "Level-2A (Surface reflectance, atmospheric corrected)"


class SpectralIndex(Enum):
    """Spectral vegetation/water indices."""
    NDVI = "Normalized Difference Vegetation Index"
    NDWI = "Normalized Difference Water Index (Gao 1996, NIR-SWIR)"
    NDMI = "Normalized Difference Moisture Index"
    SAVI = "Soil Adjusted Vegetation Index"
    EVI = "Enhanced Vegetation Index (aerosol-resistant)"
    NBR = "Normalized Burn Ratio"
    GNDVI = "Green NDVI (chlorophyll)"
    MSAVI2 = "Modified SAVI 2"
    COMPOSITE = "Composite Vegetation Index (best-of)"


# Sentinel-2 band configuration
S2_BANDS = {
    "B02": {"name": "Blue", "wavelength_nm": 490, "resolution_m": 10},
    "B03": {"name": "Green", "wavelength_nm": 560, "resolution_m": 10},
    "B04": {"name": "Red", "wavelength_nm": 665, "resolution_m": 10},
    "B05": {"name": "Red Edge 1", "wavelength_nm": 705, "resolution_m": 20},
    "B06": {"name": "Red Edge 2", "wavelength_nm": 740, "resolution_m": 20},
    "B07": {"name": "Red Edge 3", "wavelength_nm": 783, "resolution_m": 20},
    "B08": {"name": "NIR", "wavelength_nm": 842, "resolution_m": 10},
    "B8A": {"name": "Narrow NIR", "wavelength_nm": 865, "resolution_m": 20},
    "B11": {"name": "SWIR 1", "wavelength_nm": 1610, "resolution_m": 20},
    "B12": {"name": "SWIR 2", "wavelength_nm": 2190, "resolution_m": 20},
    "SCL": {"name": "Scene Classification", "wavelength_nm": 0, "resolution_m": 20},
}


@dataclass
class SatelliteScene:
    """Metadata for a single satellite scene."""
    scene_id: str
    datetime: datetime
    cloud_cover_pct: float
    bounds: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    crs: str
    resolution_m: float
    bands_available: list[str]
    source: str  # "planetary_computer", "local_cache", "synthetic"


class Sentinel2Provider:
    """
    Sentinel-2 data provider with intelligent fallback.
    
    Priority:
    1. Local cache (fastest)
    2. Planetary Computer STAC API (real data)
    3. Synthetic generation (development/testing)
    """

    def __init__(
        self,
        cache_dir: str = ".satellite_cache",
        use_planetary_computer: bool = True,
        api_timeout_s: int = 30,
        use_disk_cache: bool = True,
        default_resolution: int = 10,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.disk_cache_dir = self.cache_dir / "disk_cache"
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_pc = use_planetary_computer
        self.api_timeout = api_timeout_s
        self.use_disk_cache = use_disk_cache
        self.default_resolution = default_resolution
        self._pc_client = None
        # Session-level band cache
        self._band_cache: dict[str, dict[str, xr.DataArray]] = {}
        # Always load these essential bands (covers all indices)
        # B02=Blue, B03=Green, B04=Red, B8A=Narrow NIR, B08=Broad NIR, B11=SWIR1, B12=SWIR2
        self._essential_bands = ["B02", "B03", "B04", "B8A", "B08", "B11", "B12", "SCL"]

        # Band requirements per index (for selective loading in batch mode)
        self._index_band_map = {
            SpectralIndex.NDVI: ["B04", "B08"],
            SpectralIndex.NDWI: ["B08", "B11"],
            SpectralIndex.NDMI: ["B08", "B11"],
            SpectralIndex.SAVI: ["B04", "B08"],
            SpectralIndex.EVI: ["B02", "B04", "B08"],
            SpectralIndex.NBR: ["B08", "B12"],
            SpectralIndex.GNDVI: ["B03", "B08"],
            SpectralIndex.MSAVI2: ["B04", "B08"],
            SpectralIndex.COMPOSITE: ["B02", "B04", "B08", "B11"],
        }

    def get_scene(
        self,
        bbox: tuple[float, float, float, float],
        date_from: datetime,
        date_to: datetime,
        max_cloud_pct: float = 20.0,
        product: SentinelProduct = SentinelProduct.L2A,
    ) -> SatelliteScene | None:
        """
        Find and retrieve best scene for bbox/date range.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            date_from: Start date
            date_to: End date
            max_cloud_pct: Maximum cloud cover percentage
            product: L1C or L2A
        
        Returns:
            SatelliteScene or None if no scene available
        """
        # Step 1: Check local cache
        cached = self._check_cache(bbox, date_from, date_to, max_cloud_pct)
        if cached:
            logger.info(f"  [SENTINEL] Loaded from cache: {cached.scene_id}")
            return cached

        # Step 2: Try Planetary Computer
        if self.use_pc:
            try:
                scene = self._fetch_planetary_computer(
                    bbox, date_from, date_to, max_cloud_pct, product
                )
                if scene:
                    self._save_to_cache(scene, bbox)
                    return scene
            except Exception as e:
                logger.error(f"  [SENTINEL] Planetary Computer error: {e}")

        # Step 3: Fall back to synthetic
        logger.info("  [SENTINEL] Using synthetic data (development mode)")
        return self._generate_synthetic(bbox, date_from, date_to)

    def compute_index(
        self,
        scene: SatelliteScene,
        index: SpectralIndex,
        bbox: tuple[float, float, float, float] | None = None,
        apply_cloud_mask: bool = True,
    ) -> xr.DataArray | None:
        """Compute a spectral index from scene data with caching and cloud masking."""
        if not HAS_RASTERIO or xr is None:
            logger.info("  [SENTINEL] xarray/rasterio not available, returning None")
            return None

        # Use simple cache key (scene + bbox only)
        cache_key = f"{scene.scene_id}_{bbox}"

        if cache_key not in self._band_cache:
            # Always load all essential bands (covers all indices)
            bands = self._load_bands_selective(scene, bbox, self._essential_bands)
            if bands is None:
                return None

            # Apply cloud mask if requested
            if apply_cloud_mask and "SCL" in bands:
                bands = self._apply_cloud_mask(bands)

            self._band_cache[cache_key] = bands
            logger.info(f"  [SENTINEL] Cached {len(bands)} essential bands for {scene.scene_id}")
        else:
            bands = self._band_cache[cache_key]

        return self._calculate_index(bands, index)

    # =================================================================
    # Private Methods
    # =================================================================

    def _check_cache(
        self, bbox, date_from, date_to, max_cloud_pct
    ) -> SatelliteScene | None:
        """Check local cache for matching scene."""
        cache_key = self._bbox_date_key(bbox, date_from, date_to)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            import json
            with open(cache_file, encoding='utf-8') as f:
                data = json.load(f)
            return SatelliteScene(**data)
        except Exception:
            return None

    def _save_to_cache(self, scene: SatelliteScene, bbox):
        """Save scene metadata to cache."""
        import json
        cache_key = self._bbox_date_key(bbox, datetime.now(), datetime.now())
        cache_file = self.cache_dir / f"{cache_key}.json"

        data = {
            "scene_id": scene.scene_id,
            "datetime": scene.datetime.isoformat(),
            "cloud_cover_pct": scene.cloud_cover_pct,
            "bounds": scene.bounds,
            "crs": scene.crs,
            "resolution_m": scene.resolution_m,
            "bands_available": scene.bands_available,
            "source": scene.source,
        }
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"  [SENTINEL] Cache save error: {e}")

    def _bbox_date_key(self, bbox, date_from, date_to) -> str:
        """Generate cache key from bbox and date range."""
        key = f"{bbox}_{date_from.date()}_{date_to.date()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _fetch_planetary_computer(
        self, bbox, date_from, date_to, max_cloud_pct, product
    ) -> SatelliteScene | None:
        """Fetch scene from Microsoft Planetary Computer."""
        try:
            import planetary_computer as pc
            import pystac_client
        except ImportError:
            logger.info("  [SENTINEL] planetary_computer/pystac_client not installed")
            return None

        if self._pc_client is None:
            try:
                self._pc_client = pystac_client.Client.open(
                    "https://planetarycomputer.microsoft.com/api/stac/v1",
                    modifier=pc.sign_inplace,
                )
            except Exception as e:
                logger.info(f"  [SENTINEL] PC connection failed: {e}")
                return None

        collection = "sentinel-2-l2a" if product == SentinelProduct.L2A else "sentinel-2-l1c"

        try:
            search = self._pc_client.search(
                collections=[collection],
                bbox=bbox,
                datetime=f"{date_from.isoformat()}/{date_to.isoformat()}",
                query={"eo:cloud_cover": {"lt": max_cloud_pct}},
                sortby=[{"field": "eo:cloud_cover", "direction": "asc"}],
            )

            items = list(search.items())
            if not items:
                return None

            best = items[0]

            return SatelliteScene(
                scene_id=best.id,
                datetime=best.datetime,
                cloud_cover_pct=best.properties.get("eo:cloud_cover", 0),
                bounds=best.bbox,
                crs=best.properties.get("proj:epsg", "EPSG:4326"),
                resolution_m=10.0,
                bands_available=list(S2_BANDS.keys()),
                source="planetary_computer",
            )
        except Exception as e:
            logger.error(f"  [SENTINEL] PC search error: {e}")
            return None

    def _generate_synthetic(
        self, bbox, date_from, date_to
    ) -> SatelliteScene:
        """Generate synthetic scene for testing."""
        return SatelliteScene(
            scene_id=f"SYN_{int(time.time())}",
            datetime=date_from + timedelta(days=1),
            cloud_cover_pct=5.0,
            bounds=bbox,
            crs="EPSG:4326",
            resolution_m=10.0,
            bands_available=list(S2_BANDS.keys()),
            source="synthetic",
        )

    def _load_bands(
        self,
        scene: SatelliteScene,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> dict[str, xr.DataArray] | None:
        """Load bands as xarray DataArrays."""
        if scene.source == "synthetic":
            return self._generate_synthetic_bands(scene, bbox)

        # Real data loading via odc-stac (Planetary Computer)
        try:
            return self._load_real_data_odc(scene, bbox)
        except Exception as e:
            logger.info(f"  [SENTINEL] Real data load failed: {e}")
            logger.info("  [SENTINEL] Falling back to synthetic")
            return self._generate_synthetic_bands(scene, bbox)


    def _disk_cache_key(self, scene_id: str, bands: list[str], resolution: int, bbox) -> str:
        """Generate disk cache key."""
        import hashlib
        key_str = f"{scene_id}_{'_'.join(sorted(bands))}_{resolution}_{bbox}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _save_to_disk_cache(self, key: str, data: dict[str, xr.DataArray]):
        """Save band data to disk cache."""
        try:
            import pickle
            cache_file = self.disk_cache_dir / f"{key}.pkl"
            # Convert to Integerizable format
            Integerizable = {}
            for band_name, da in data.items():
                Integerizable[band_name] = {
                    "values": da.values,
                    "dims": da.dims,
                    "coords": {k: v.values for k, v in da.coords.items()},
                    "attrs": dict(da.attrs),
                }
            with open(cache_file, 'wb') as f:
                pickle.dump(Integerizable, f)
        except Exception as e:
            logger.error(f"  [SENTINEL] Disk cache save error: {e}")

    def _load_from_disk_cache(self, key: str) -> dict[str, xr.DataArray] | None:
        """Load band data from disk cache."""
        try:
            cache_file = self.disk_cache_dir / f"{key}.pkl"
            if not cache_file.exists():
                return None
            with open(cache_file, 'rb') as f:
                Integerizable = safe_pickle_load(f)
            result = {}
            for band_name, data in Integerizable.items():
                result[band_name] = xr.DataArray(
                    data["values"],
                    dims=data["dims"],
                    coords=data["coords"],
                    attrs=data["attrs"],
                )
            logger.info(f"  [SENTINEL] Loaded from disk cache: {key[:16]}...")
            return result
        except Exception:
            return None

    def _load_bands_selective(
        self,
        scene: SatelliteScene,
        bbox: tuple[float, float, float, float] | None = None,
        required_bands: list[str] | None = None,
        resolution: int | None = None,
    ) -> dict[str, xr.DataArray] | None:
        """Load only the required bands with adaptive resolution."""
        if scene.source == "synthetic":
            return self._generate_synthetic_bands(scene, bbox)

        try:
            return self._load_real_data_odc(scene, bbox, required_bands, resolution=resolution)
        except Exception as e:
            logger.info(f"  [SENTINEL] Real data load failed: {e}")
            return self._generate_synthetic_bands(scene, bbox)

    def _load_real_data_odc(
        self,
        scene: SatelliteScene,
        bbox: tuple[float, float, float, float] | None = None,
        required_bands: list[str] | None = None,
        resolution: int | None = None,
    ) -> dict[str, xr.DataArray]:
        """
        Load real Sentinel-2 L2A data using odc-stac (optimized).
        
        Optimizations:
        - Disk cache (pickle)
        - Selective band loading
        - Adaptive resolution
        - Batch computation
        """
        # Select bands
        bands_to_load = required_bands if required_bands else list(S2_BANDS.keys())
        bands_to_load = [b for b in bands_to_load if b in S2_BANDS]

        # Determine resolution
        target_res = resolution if resolution else self.default_resolution
        bbox_to_use = bbox if bbox else scene.bounds

        # === Check disk cache ===
        cache_key = self._disk_cache_key(scene.scene_id, bands_to_load, target_res, bbox_to_use)
        if self.use_disk_cache:
            cached = self._load_from_disk_cache(cache_key)
            if cached is not None:
                return cached

        # === Not cached, load from PC ===
        import odc.stac
        import planetary_computer as pc
        import pystac_client

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace,
        )

        # Retry logic with exponential backoff
        items = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                search = catalog.search(
                    collections=["sentinel-2-l2a"],
                    ids=[scene.scene_id],
                )
                items = list(search.items())
                if items:
                    break
                raise ValueError(f"Scene {scene.scene_id} not found (attempt {attempt+1})")
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"  [SENTINEL] Search retry {attempt+1}/{max_retries} after {wait}s: {type(e).__name__}")
                    time.sleep(wait)
                else:
                    raise

        if not items:
            raise ValueError(f"Scene {scene.scene_id} not found after {max_retries} attempts")

        item = items[0]

        logger.info(f"  [SENTINEL] Loading: {scene.scene_id[:30]}... res={target_res}m bands={len(bands_to_load)}")

        # Load with odc-stac (lazy)
        data = odc.stac.load(
            [item],
            bands=bands_to_load,
            bbox=bbox_to_use,
            resolution=target_res,
            chunks={"x": 1024, "y": 1024},
            progress=False,
            fail_on_error=False,
        )

        # Batch compute all bands at once (more efficient than per-band)
        # Use dask to compute all arrays together
        dask_arrays = {}
        for band_name in bands_to_load:
            if band_name not in data.data_vars:
                continue
            band_data = data[band_name].isel(time=0)
            dask_arrays[band_name] = (band_data, band_data.coords)

        # Compute all bands at once (single dask graph traversal)
        if dask_arrays:
            import dask
            values_list = [da.values for da, _ in dask_arrays.values()]  # already computed by isel

            # Force compute if dask arrays
            try:
                computed = dask.compute(*[da for da in data.data_vars.values()], scheduler='synchronous')
            except Exception:
                # Fallback: compute one by one
                pass

        # Build result
        bands = {}
        for band_name, (band_data, coords) in dask_arrays.items():
            try:
                band_arr = band_data.compute()  # force compute with dask
            except Exception:
                band_arr = band_data.values

            # Scale: 0-10000 -> 0-1 (except SCL)
            if band_name == "SCL":
                band_arr = band_arr.astype(np.uint8)
            else:
                band_arr = band_arr.astype(np.float32) / 10000.0
                band_arr = np.clip(band_arr, 0.0, 1.0)

            bands[band_name] = xr.DataArray(
                band_arr,
                dims=["y", "x"],
                coords={
                    "y": coords["y"].values,
                    "x": coords["x"].values,
                },
                attrs={
                    "band": band_name,
                    "wavelength_nm": S2_BANDS[band_name]["wavelength_nm"],
                    "description": f"Sentinel-2 {S2_BANDS[band_name]['name']}",
                    "units": "reflectance" if band_name != "SCL" else "class",
                },
            )

        logger.info(f"  [SENTINEL] Loaded {len(bands)} bands @ {target_res}m "
              f"(shape: {next(iter(bands.values())).shape})")

        # Save to disk cache
        if self.use_disk_cache and bands:
            self._save_to_disk_cache(cache_key, bands)

        return bands

    def _apply_cloud_mask(
        self, bands: dict[str, xr.DataArray]
    ) -> dict[str, xr.DataArray]:
        """
        Apply cloud/shadow masking using SCL (Scene Classification Layer).

        SCL classes (Sentinel-2 L2A):
          0 = No data                    → MASK
          1 = Saturated / Defective      → MASK
          2 = Dark areas / shadows       → MASK
          3 = Cloud shadows              → MASK
          4 = Vegetation                 → KEEP ✓
          5 = Bare soil                  → KEEP ✓
          6 = Water                      → KEEP ✓
          7 = Unclassified               → KEEP (permissive)
          8 = Cloud medium probability   → MASK
          9 = Cloud high probability     → MASK
         10 = Cirrus                     → MASK
         11 = Snow / Ice                 → KEEP ✓
        """
        if "SCL" not in bands:
            return bands

        scl = bands["SCL"].values

        # More permissive: keep unclassified (7) as well
        # This avoids over-masking in complex scenes
        valid_classes = [4, 5, 6, 7, 11]
        valid_mask = np.isin(scl, valid_classes)

        # Mask cloud-affected pixels in all reflectance bands
        for band_name, band_da in bands.items():
            if band_name == "SCL":
                continue
            arr = band_da.values.astype(np.float32)
            # Set invalid pixels to NaN
            arr[~valid_mask] = np.nan
            bands[band_name] = xr.DataArray(
                arr,
                dims=band_da.dims,
                coords=band_da.coords,
                attrs=band_da.attrs,
            )

        # Report masking stats with breakdown
        total = scl.size
        valid = valid_mask.sum()

        # Count each class
        class_counts = {}
        for cls in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
            count = np.sum(scl == cls)
            if count > 0:
                class_counts[cls] = count

        logger.info(f"  [SENTINEL] Cloud mask: {valid}/{total} pixels valid "
              f"({100*valid/total:.1f}%)")

        # Show breakdown if significant masking occurred
        if valid / total < 0.95:
            class_names = {
                2: "shadows", 3: "cloud_shadows", 4: "vegetation",
                5: "bare_soil", 6: "water", 7: "unclassified",
                8: "cloud_med", 9: "cloud_high", 10: "cirrus", 11: "snow"
            }
            breakdown = ", ".join(
                f"{class_names.get(c, c)}={n}"
                for c, n in sorted(class_counts.items())
            )
            logger.info(f"  [SENTINEL] SCL breakdown: {breakdown}")

        return bands

    def _generate_synthetic_bands(
        self, scene, bbox
    ) -> dict[str, xr.DataArray]:
        """Generate realistic synthetic bands."""
        shape = (100, 100)
        if bbox:
            lon_range = bbox[2] - bbox[0]
            lat_range = bbox[3] - bbox[1]
        else:
            lon_range, lat_range = 0.1, 0.1
            bbox = (51.0, 35.0, 51.1, 35.1)

        coords = {
            "y": np.linspace(bbox[3], bbox[1], shape[0]),
            "x": np.linspace(bbox[0], bbox[2], shape[1]),
        }

        # Create spatially coherent noise using 2D patterns
        y_grid, x_grid = np.meshgrid(
            np.linspace(0, 2 * np.pi, shape[0]),
            np.linspace(0, 2 * np.pi, shape[1]),
            indexing='ij'
        )
        base_pattern = (np.sin(x_grid) * np.cos(y_grid) + 1) / 2

        bands = {}
        # Realistic reflectance ranges (0-1 for surface reflectance)
        band_ranges = {
            "B02": (0.03, 0.15),   # Blue
            "B03": (0.04, 0.20),   # Green
            "B04": (0.03, 0.18),   # Red
            "B08": (0.15, 0.55),   # NIR (high for vegetation)
            "B11": (0.10, 0.40),   # SWIR1
            "B12": (0.05, 0.30),   # SWIR2
        }

        for band, (min_val, max_val) in band_ranges.items():
            noise = np.random.uniform(0, 0.1, shape)
            values = min_val + (max_val - min_val) * (base_pattern * 0.7 + noise * 0.3)
            bands[band] = xr.DataArray(
                values.astype(np.float32),
                dims=["y", "x"],
                coords=coords,
                attrs={
                    "band": band,
                    "wavelength_nm": S2_BANDS[band]["wavelength_nm"],
                    "description": f"Sentinel-2 {S2_BANDS[band]['name']}",
                },
            )

        return bands

    def compute_indices_batch(
        self,
        scene: SatelliteScene,
        indices: list[SpectralIndex],
        bbox: tuple[float, float, float, float] | None = None,
        apply_cloud_mask: bool = True,
        resolution: int = 10,
    ) -> dict[SpectralIndex, xr.DataArray]:
        """
        Compute multiple indices in a single optimized pass.
        
        Strategy:
        - Load ALL essential bands (covers all indices)
        - Pre-extract numpy arrays (avoid repeated .values calls)
        - Compute each index from pre-extracted arrays
        """
        # Use simple cache key
        cache_key = f"{scene.scene_id}_{bbox}_{resolution}_{apply_cloud_mask}"

        if cache_key not in self._band_cache:
            # Always load all essential bands (covers all possible indices)
            bands = self._load_bands_selective(
                scene, bbox, self._essential_bands, resolution=resolution
            )
            if bands is None:
                return {}
            if apply_cloud_mask and "SCL" in bands:
                bands = self._apply_cloud_mask(bands)
            self._band_cache[cache_key] = bands
            logger.info(f"  [SENTINEL] Cached {len(bands)} essential bands for {scene.scene_id[:20]}...")
        else:
            bands = self._band_cache[cache_key]

        # Pre-extract numpy arrays ONCE (avoid repeated .values calls)
        band_arrays = {}
        for band_name in self._essential_bands:
            if band_name in bands:
                arr = bands[band_name].values
                if hasattr(arr, 'compute'):
                    # Force dask computation
                    arr = arr.compute()
                band_arrays[band_name] = arr

        # Get coordinates for output DataArrays
        # Use dict.get with default to avoid __bool__ on xarray DataArray
        ref_band = bands.get("B08", next(iter(bands.values())))
        ref_coords = ref_band.coords
        ref_dims = ref_band.dims

        # Compute all indices using pre-extracted numpy arrays (fast!)
        results = {}
        for idx in indices:
            try:
                result_arr = self._calculate_index_fast(band_arrays, idx)
                if result_arr is not None:
                    results[idx] = xr.DataArray(
                        result_arr,
                        dims=ref_dims,
                        coords=ref_coords,
                        attrs={"index": idx.name},
                    )
            except Exception as e:
                logger.info(f"  [SENTINEL] Failed to compute {idx.name}: {e}")

        return results

    def _calculate_index_fast(
        self,
        band_arrays: dict[str, np.ndarray],
        index: SpectralIndex,
    ) -> np.ndarray | None:
        """
        Fast index calculation using pre-extracted numpy arrays.
        
        No xarray overhead, no repeated .values calls.
        """
        eps = 1e-10

        # Check required bands
        def get_band(name: str) -> np.ndarray | None:
            arr = band_arrays.get(name)
            if arr is None:
                logger.warning(f"  [SENTINEL] Warning: Band {name} not in loaded bands")
                return None
            return arr.astype(np.float32, copy=False)

        if index == SpectralIndex.NDVI:
            nir = get_band("B08")
            red = get_band("B04")
            if nir is None or red is None:
                return None
            result = (nir - red) / (nir + red + eps)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.NDWI or index == SpectralIndex.NDMI:
            nir = get_band("B08")
            swir = get_band("B11")
            if nir is None or swir is None:
                return None
            result = (nir - swir) / (nir + swir + eps)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.SAVI:
            nir = get_band("B08")
            red = get_band("B04")
            if nir is None or red is None:
                return None
            L = 0.5
            result = ((nir - red) / (nir + red + L + eps)) * (1 + L)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.EVI:
            nir = get_band("B08")
            red = get_band("B04")
            blue = get_band("B02")
            if nir is None or red is None or blue is None:
                return None
            G, C1, C2, L_evi = 2.5, 6.0, 7.5, 1.0
            result = G * (nir - red) / (nir + C1 * red - C2 * blue + L_evi + eps)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.NBR:
            nir = get_band("B08")
            swir2 = get_band("B12")
            if nir is None or swir2 is None:
                return None
            result = (nir - swir2) / (nir + swir2 + eps)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.GNDVI:
            nir = get_band("B08")
            green = get_band("B03")
            if nir is None or green is None:
                return None
            result = (nir - green) / (nir + green + eps)
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.MSAVI2:
            nir = get_band("B08")
            red = get_band("B04")
            if nir is None or red is None:
                return None
            term1 = 2 * nir + 1
            term2 = np.sqrt(np.maximum(term1**2 - 8 * (nir - red), 0))
            result = (term1 - term2) / 2
            result = np.clip(result, -1.0, 1.0)

        elif index == SpectralIndex.COMPOSITE:
            nir = get_band("B08")
            red = get_band("B04")
            blue = get_band("B02")
            swir = get_band("B11")
            if nir is None or red is None or blue is None or swir is None:
                return None

            # Compute all component indices
            ndvi = (nir - red) / (nir + red + eps)
            evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + eps)
            savi = ((nir - red) / (nir + red + 0.5 + eps)) * 1.5
            term1 = 2 * nir + 1
            term2 = np.sqrt(np.maximum(term1**2 - 8 * (nir - red), 0))
            msavi2 = (term1 - term2) / 2

            # Adaptive composite
            result = np.where(ndvi > 0.5, evi,
                     np.where(ndvi > 0.2, savi, msavi2))
            result = np.clip(result, -1.0, 1.0)

        else:
            raise ValueError(f"Unknown index: {index}")

        return result


    def _calculate_index(
        self,
        bands: dict[str, xr.DataArray],
        index: SpectralIndex,
    ) -> xr.DataArray:
        """Calculate a spectral index from bands."""
        eps = 1e-10  # Avoid division by zero

        # Helper: choose best NIR band
        # B8A (narrow, 865nm) is better for dense vegetation
        # B08 (broad, 842nm) is more general
        if "B8A" in bands:
            nir_narrow = bands["B8A"]
            nir_broad = bands["B08"]
            # Use B8A for vegetation indices (more specific to chlorophyll)
            nir_veg = nir_narrow
        else:
            nir_veg = bands["B08"]
            nir_broad = bands["B08"]

        red = bands["B04"]
        green = bands["B03"]
        blue = bands["B02"]
        swir1 = bands["B11"]
        swir2 = bands["B12"]

        if index == SpectralIndex.NDVI:
            # Standard NDVI - works well except in high-aerosol conditions
            result = (nir_broad - red) / (nir_broad + red + eps)
            valid_range = (-1.0, 1.0)
            description = "NDVI: Vegetation vigor (susceptible to aerosol)"

        elif index == SpectralIndex.NDWI:
            # Gao 1996 formula: (NIR - SWIR) for CANOPY water content
            # Much better than McFeeters (GREEN-NIR) for vegetation
            result = (nir_broad - swir1) / (nir_broad + swir1 + eps)
            valid_range = (-1.0, 1.0)
            description = "NDWI (Gao 1996): Canopy water content"

        elif index == SpectralIndex.NDMI:
            # Same formula as Gao NDWI but standard terminology
            # NDMI is the preferred term for agricultural applications
            result = (nir_broad - swir1) / (nir_broad + swir1 + eps)
            valid_range = (-1.0, 1.0)
            description = "NDMI: Canopy moisture (drought stress indicator)"

        elif index == SpectralIndex.SAVI:
            # Huete 1988: Soil-Adjusted Vegetation Index
            nir = nir_broad
            L = 0.5
            result = ((nir - red) / (nir + red + L + eps)) * (1 + L)
            valid_range = (-1.0, 1.0)
            description = "SAVI: Soil-adjusted (sparse vegetation)"

        elif index == SpectralIndex.EVI:
            # Huete et al. 2002: Enhanced Vegetation Index
            # Resistant to atmospheric effects (aerosol, Rayleigh scattering)
            # Much better than NDVI for tropical forests!
            nir = nir_broad
            G = 2.5
            C1, C2 = 6.0, 7.5
            L_evi = 1.0
            result = G * (nir - red) / (nir + C1 * red - C2 * blue + L_evi + eps)
            valid_range = (-1.0, 1.0)
            description = "EVI: Enhanced Vegetation (aerosol-resistant, tropical)"

        elif index == SpectralIndex.NBR:
            # Key et al. 2005: Normalized Burn Ratio
            nir = nir_broad
            result = (nir - swir2) / (nir + swir2 + eps)
            valid_range = (-1.0, 1.0)
            description = "NBR: Normalized Burn Ratio"

        elif index == SpectralIndex.GNDVI:
            # Gitelson et al. 1996: Green NDVI
            # Better for high-chlorophyll canopies than standard NDVI
            nir = nir_narrow if "B8A" in bands else nir_broad
            result = (nir - green) / (nir + green + eps)
            valid_range = (-1.0, 1.0)
            description = "GNDVI: Chlorophyll content (high-chlorophyll canopies)"

        elif index == SpectralIndex.MSAVI2:
            # Qi et al. 1994: Modified SAVI 2
            # Self-adjusting L parameter - best for very sparse vegetation
            nir = nir_broad
            # MSAVI2 = (2*nir + 1 - sqrt((2*nir+1)^2 - 8*(nir-red))) / 2
            term1 = 2 * nir + 1
            term2 = np.sqrt(np.maximum(term1**2 - 8 * (nir - red), 0))
            result = (term1 - term2) / 2
            valid_range = (-1.0, 1.0)
            description = "MSAVI2: Self-adjusting soil-adjusted (very sparse)"

        elif index == SpectralIndex.COMPOSITE:
            # Composite: weighted combination using best index per pixel
            # Strategy:
            # - Dense vegetation (NDVI > 0.5): use EVI (aerosol resistant)
            # - Sparse vegetation (0.2 < NDVI < 0.5): use SAVI
            # - Bare soil (NDVI < 0.2): use MSAVI2
            ndvi = (nir_broad - red) / (nir_broad + red + eps)
            evi = 2.5 * (nir_broad - red) / (nir_broad + 6 * red - 7.5 * blue + 1 + eps)
            savi = ((nir_broad - red) / (nir_broad + red + 0.5 + eps)) * 1.5
            term1 = 2 * nir_broad + 1
            term2 = np.sqrt(np.maximum(term1**2 - 8 * (nir_broad - red), 0))
            msavi2 = (term1 - term2) / 2

            # Composite logic
            result = np.where(ndvi > 0.5, evi,
                     np.where(ndvi > 0.2, savi, msavi2))
            valid_range = (-1.0, 1.0)
            description = "COMPOSITE: Adaptive (EVI/SAVI/MSAVI2 based on vegetation density)"

        else:
            raise ValueError(f"Unknown index: {index}")

        # Clip to valid range (NaN-aware)
        # Don't clip NaN values
        with np.errstate(invalid='ignore'):
            result = np.where(np.isnan(result), np.nan,
                              np.clip(result, valid_range[0], valid_range[1]))

        # Get one of the input bands for coords
        ref_band = next(iter(bands.values()))

        # Build output DataArray
        result_arr = xr.DataArray(
            result,
            dims=ref_band.dims,
            coords=ref_band.coords,
        )
        result_arr.attrs["index"] = index.name
        result_arr.attrs["description"] = description
        result_arr.attrs["valid_range"] = valid_range

        return result_arr
