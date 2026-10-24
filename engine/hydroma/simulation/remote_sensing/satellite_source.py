"""Satellite reflectance data source abstractions.

Defines the interface and implementations for retrieving surface reflectance
(NIR, SWIR bands) from satellite products.  Currently supports:

* Sentinel-2 Level-2A surface reflectance (primary)
* Landsat Collection 2 Level-2 surface reflectance (secondary)

No hard-coded API keys.  Authentication, if required, is injected through
the constructor or read from environment variables at runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import requests

# rasterio imported lazily inside _sample_raster_at_point
from planetary_computer import sign

from engine.hydroma.simulation.quality_status import QualityStatus

# The cache module is imported at module level (not lazily inside the
# methods): the sandbox's overlay filesystem intermittently hides this
# package directory from the import machinery's directory scan, so the
# import has to happen while the module is being loaded, when the
# runtime bootstrap's direct-file path is in effect.
from .satellite_cache import SatelliteCache, make_cache_key

#: Planetary Computer STAC API endpoint.
PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

#: Default cloud cover threshold for Sentinel-2 scenes (percent).
DEFAULT_CLOUD_THRESHOLD = 20.0

#: Sentinel-2 L2A scale factor (DN to reflectance).
S2_SCALE_FACTOR = 0.0001

#: Sentinel-2 L2A bands used for NDMI.
S2_NIR_BAND = "B8A"
S2_SWIR_BAND = "B11"

#: Sentinel-2 Scene Classification Layer band for cloud masking.
S2_SCL_BAND = "SCL"

#: SCL values that indicate cloud / cloud shadow / snow (to be masked).
S2_CLOUD_SCL_VALUES = {3, 8, 9, 10, 11}

#: Maximum gap between consecutive satellite observations for interpolation (days).
DEFAULT_MAX_GAP_DAYS = 14

#: Default on-disk cache directory for sampled satellite reflectance.
DEFAULT_CACHE_DIR = "engine/reports/data/stage39_satellite_cache"


@dataclass
class BandReflectance:
    """Reflectance values for a single spectral band on a single date.

    Attributes:
        date: Acquisition date (ISO format).
        band: Band name (e.g. ``"B8"``, ``"B8A"``, ``"B11"``, ``"B12"``,
            ``"B5"``, ``"B6"``, ``"B7"``).
        value: Surface reflectance (dimensionless, typically 0-1).
        unit: Unit label (``"reflectance"``).
        spatial_resolution_m: Nominal pixel resolution in metres.
        quality_status: :class:`QualityStatus` of this retrieval.
        source_product: Product identifier (e.g. ``"S2MSI2A"``,
            ``"LANDSAT_C2L2"``).
        source: Data source label (e.g. ``"Copernicus Data Space Ecosystem"``,
            ``"USGS EarthExplorer"``).
        processing_level: Product processing level (e.g. ``"L2A"``).
        metadata: Additional product-specific metadata.
    """

    date: str
    band: str
    value: float
    unit: str = "reflectance"
    spatial_resolution_m: float | None = None
    quality_status: QualityStatus = QualityStatus.SATELLITE_RETRIEVED
    source_product: str = ""
    source: str = ""
    processing_level: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectanceAcquisition:
    """All band reflectances acquired on a single date at one location.

    Attributes:
        date: Acquisition date (ISO format).
        latitude: Site latitude (WGS84 decimal degrees).
        longitude: Site longitude (WGS84 decimal degrees).
        bands: Dict of band name -> BandReflectance.
        cloud_fraction: Fraction of pixels classified as cloud (0-1).
        cloud_shadow_fraction: Fraction classified as cloud shadow (0-1).
        snow_fraction: Fraction classified as snow (0-1).
        valid_pixel_fraction: Fraction of pixels passing all quality masks (0-1).
        valid_observation_count: Number of valid observations used.
        source_product: Product identifier.
        processing_level: Product processing level.
        quality_status: Overall quality status for this acquisition.
    """

    date: str
    latitude: float
    longitude: float
    bands: dict[str, BandReflectance]
    cloud_fraction: float = 0.0
    cloud_shadow_fraction: float = 0.0
    snow_fraction: float = 0.0
    valid_pixel_fraction: float = 1.0
    valid_observation_count: int = 0
    source_product: str = ""
    processing_level: str = ""
    quality_status: QualityStatus = QualityStatus.SATELLITE_RETRIEVED


@dataclass
class ReflectanceTimeSeries:
    """Time series of reflectance acquisitions for one site.

    Attributes:
        site_id: Stable site identifier.
        acquisitions: List of :class:`ReflectanceAcquisition`, sorted by date.
        source_product: Primary product identifier.
        processing_level: Product processing level.
        spatial_resolution_m: Nominal resolution in metres.
    """

    site_id: str
    acquisitions: list[ReflectanceAcquisition] = field(default_factory=list)
    source_product: str = ""
    processing_level: str = ""
    spatial_resolution_m: float | None = None

    def dates(self) -> list[str]:
        """Return sorted list of acquisition dates."""
        return sorted(a.date for a in self.acquisitions)

    def band_values(self, band: str) -> dict[str, float | None]:
        """Return date -> reflectance value for a given band.

        Missing bands return None for that date.
        """
        return {
            a.date: (
                a.bands.get(band, BandReflectance(date=a.date, band=band, value=float("nan"))).value
            )
            if band in a.bands
            else None
            for a in self.acquisitions
        }


def _pc_stac_search(
    collection: str,
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    limit: int = 10,
    cloud_max: float | None = None,
) -> list[dict[str, Any]]:
    """Search Planetary Computer STAC for satellite items.

    Args:
        collection: STAC collection ID (e.g. ``"sentinel-2-l2a"``).
        bbox: (lon_min, lat_min, lon_max, lat_max) in WGS84.
        start_date: Inclusive start date (ISO ``YYYY-MM-DD``).
        end_date: Inclusive end date (ISO ``YYYY-MM-DD``).
        limit: Maximum number of items to return.
        cloud_max: Maximum cloud cover percentage (None = no filter).

    Returns:
        List of STAC item dicts.

    Raises:
        RuntimeError: if the STAC search fails.
    """
    datetime_str = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
    body: dict[str, Any] = {
        "collections": [collection],
        "bbox": list(bbox),
        "datetime": datetime_str,
        "limit": limit,
    }
    if cloud_max is not None:
        body["query"] = {"eo:cloud_cover": {"lt": cloud_max}}

    resp = requests.post(f"{PC_STAC_URL}/search", json=body, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(
            f"STAC search failed: HTTP {resp.status_code} {resp.text[:200]}"
        )
    return resp.json().get("features", [])


def _lon_lat_to_row_col(transform, lon: float, lat: float) -> tuple[int, int]:
    """Convert lon/lat to pixel row/col using affine transform (north-up, no rotation)."""
    col = (lon - transform.c) / transform.a
    row = (lat - transform.f) / transform.e
    return int(round(row)), int(round(col))


def _sample_raster_at_point(
    href: str,
    latitude: float,
    longitude: float,
    scale_factor: float = 1.0,
    cloud_mask_band: str | None = None,
    cloud_mask_values: set[int] | None = None,
) -> tuple[float | None, bool]:
    """Sample a signed raster URL at a given lat/lon point.

    Only the single pixel of interest is read.  A Sentinel-2 L2A band
    asset is a ~63 MB Cloud-Optimized GeoTIFF; reading it in full
    (``ds.read(1)``) to extract one value dominates the runtime of a
    benchmark run.  A windowed read of one pixel lets GDAL fetch only the
    containing tile over HTTP range requests.

    Args:
        href: Signed asset URL.
        latitude: Point latitude (WGS84).
        longitude: Point longitude (WGS84).
        scale_factor: Multiply DN values by this factor (e.g. 0.0001 for S2).
        cloud_mask_band: Optional band name for cloud masking.
        cloud_mask_values: SCL values to treat as cloudy.

    Returns:
        Tuple of (reflectance_value_or_None, is_cloudy).
    """
    import rasterio
    from rasterio.warp import transform as warp_transform
    from rasterio.windows import Window

    signed_href = sign(href)
    try:
        with rasterio.open(signed_href) as ds:
            # Transform WGS84 point to image CRS for bounds check
            img_crs = ds.crs
            if img_crs is not None and img_crs.to_string() != "EPSG:4326":
                xs, ys = warp_transform(
                    "EPSG:4326", img_crs.to_string(), [longitude], [latitude]
                )
                lon_img, lat_img = xs[0], ys[0]
            else:
                lon_img, lat_img = longitude, latitude

            # Check if point is within image bounds (in image CRS)
            if not ds.bounds.left <= lon_img <= ds.bounds.right:
                return None, False
            if not ds.bounds.bottom <= lat_img <= ds.bounds.top:
                return None, False

            row, col = _lon_lat_to_row_col(ds.transform, lon_img, lat_img)
            if not (0 <= row < ds.height and 0 <= col < ds.width):
                return None, False

            # Cloud mask check — read only the single pixel of the SCL band.
            if cloud_mask_band and cloud_mask_values is not None:
                try:
                    with rasterio.open(signed_href) as ds2:
                        band_idx = ds2.indexes.get(cloud_mask_band, None)
                        if band_idx:
                            scl_val = ds2.read(
                                band_idx, window=Window(col, row, 1, 1)
                            )[0, 0]
                            if int(scl_val) in cloud_mask_values:
                                return None, True
                except Exception:
                    pass  # If cloud mask band not available, skip masking

            # Read only the pixel of interest.
            val = ds.read(1, window=Window(col, row, 1, 1))[0, 0]
            if val is not None and val != ds.nodata:
                return float(val) * scale_factor, False
    except Exception:
        pass
    return None, False


class SatelliteSource(ABC):
    """Abstract base class for satellite reflectance data sources."""

    @abstractmethod
    def fetch_reflectance(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        bands: list[str] | None = None,
    ) -> ReflectanceTimeSeries:
        """Fetch surface reflectance for a site and date range.

        Args:
            latitude: Site latitude (WGS84 decimal degrees).
            longitude: Site longitude (WGS84 decimal degrees).
            start_date: Inclusive start date (ISO ``YYYY-MM-DD``).
            end_date: Inclusive end date (ISO ``YYYY-MM-DD``).
            bands: Optional list of band names to retrieve.  If None,
                retrieves the default bands for this source.

        Returns:
            :class:`ReflectanceTimeSeries` with all acquisitions.

        Raises:
            NotImplementedError: if the subclass does not implement fetching.
            ValueError: if coordinates or dates are invalid.
            RuntimeError: if the data source is unavailable or returns
                an error.
        """


class Sentinel2Source(SatelliteSource):
    """Sentinel-2 Level-2A surface reflectance source.

    Default bands:
        * NIR: B8A (865 nm, 20 m resolution) — preferred for NDMI.
        * SWIR: B11 (1610 nm, 20 m resolution) — preferred for NDMI.
    """

    DEFAULT_BANDS = ["B8A", "B11"]
    NIR_BAND = "B8A"
    SWIR_BAND = "B11"
    SOURCE_PRODUCT = "S2MSI2A"
    STAC_COLLECTION = "sentinel-2-l2a"
    PROCESSING_LEVEL = "L2A"
    SPATIAL_RESOLUTION_M = 20.0

    def __init__(
        self,
        source_label: str = "Sentinel-2 Level-2A",
        cache_dir: str | None = None,
        use_cache: bool = True,
    ) -> None:
        self.source_label = source_label
        self.use_cache = use_cache
        self._cache = None
        if use_cache:
            self._cache = SatelliteCache(cache_dir or DEFAULT_CACHE_DIR)

    def _cache_key(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        bands: list[str],
    ) -> str:
        """Build the cache key for a reflectance fetch.

        The key covers every parameter that can change the result:
        collection, coordinates, date range, bands, and processing level.
        Coordinates are rounded to 6 decimals (~11 cm) which is below any
        meaningful field-boundary precision, so two records at the same
        field share a cache entry without merging distinct locations.
        """
        return make_cache_key(
            site_id=f"{self.STAC_COLLECTION}:{latitude:.6f},{longitude:.6f}",
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            source_product=self.SOURCE_PRODUCT,
            processing_level=self.PROCESSING_LEVEL,
            bands=bands,
        )

    def fetch_reflectance(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        bands: list[str] | None = None,
    ) -> ReflectanceTimeSeries:
        """Fetch Sentinel-2 L2A reflectance from Planetary Computer STAC.

        Queries the Planetary Computer STAC API for Sentinel-2 L2A items
        overlapping the given coordinates and date range, filters by cloud
        cover, signs asset URLs via the Planetary Computer signing service,
        and samples NIR/SWIR reflectance at the point location using rasterio.

        Args:
            latitude: Site latitude (WGS84 decimal degrees).
            longitude: Site longitude (WGS84 decimal degrees).
            start_date: Inclusive start date (ISO ``YYYY-MM-DD``).
            end_date: Inclusive end date (ISO ``YYYY-MM-DD``).
            bands: Optional list of band names.  Defaults to
                ``["B8A", "B11"]`` for NDMI computation.

        Returns:
            :class:`ReflectanceTimeSeries` with all cloud-free acquisitions.

        Raises:
            ValueError: if coordinates or dates are invalid.
            RuntimeError: if the STAC search or asset download fails.
        """
        if bands is None:
            bands = [self.NIR_BAND, self.SWIR_BAND]

        # Validate coordinates
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude: {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude: {longitude}")

        # --- Cache lookup ---
        # Downloading Sentinel-2 L2A COGs is the dominant cost (~66-130 s per
        # band).  Because many CIMMYT records share the same coordinates and
        # season, caching the *sampled* reflectance values avoids repeating
        # the same downloads.  The cache key covers collection, coordinates,
        # date range, bands and processing level.
        cache_key = None
        if self._cache is not None:
            cache_key = self._cache_key(
                latitude, longitude, start_date, end_date, bands
            )
            cached = self._cache.load_timeseries(cache_key)
            if cached is not None:
                return cached

        # Buffer around point for STAC search (0.01 deg ~ 1 km)
        buffer_deg = 0.01
        bbox = (
            longitude - buffer_deg,
            latitude - buffer_deg,
            longitude + buffer_deg,
            latitude + buffer_deg,
        )

        try:
            items = _pc_stac_search(
                collection=self.STAC_COLLECTION,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                limit=50,
                cloud_max=DEFAULT_CLOUD_THRESHOLD,
            )
        except RuntimeError as exc:
            raise RuntimeError(f"Sentinel-2 STAC search failed: {exc}") from exc

        acquisitions: list[ReflectanceAcquisition] = []
        for item in items:
            props = item.get("properties", {})
            assets = item.get("assets", {})

            item_date = props.get("datetime", "")
            if isinstance(item_date, str):
                item_date = item_date[:10]  # Truncate to YYYY-MM-DD

            cloud_cover = props.get("eo:cloud_cover", 100.0)

            band_data: dict[str, BandReflectance] = {}
            is_cloudy = False

            for band_name in bands:
                if band_name not in assets:
                    continue
                href = assets[band_name].get("href", "")
                if not href:
                    continue

                # Determine scale factor
                scale = S2_SCALE_FACTOR

                # Cloud masking using SCL band
                scl_href = assets.get(S2_SCL_BAND, {}).get("href", "")

                value, cloudy = _sample_raster_at_point(
                    href=href,
                    latitude=latitude,
                    longitude=longitude,
                    scale_factor=scale,
                    cloud_mask_band=S2_SCL_BAND if scl_href else None,
                    cloud_mask_values=S2_CLOUD_SCL_VALUES,
                )
                if cloudy:
                    is_cloudy = True

                if value is not None:
                    band_data[band_name] = BandReflectance(
                        date=item_date,
                        band=band_name,
                        value=round(value, 6),
                        spatial_resolution_m=self.SPATIAL_RESOLUTION_M,
                        quality_status=QualityStatus.SATELLITE_RETRIEVED,
                        source_product=self.SOURCE_PRODUCT,
                        source="Microsoft Planetary Computer STAC",
                        processing_level=self.PROCESSING_LEVEL,
                        metadata={
                            "item_id": item.get("id", ""),
                            "cloud_cover_percent": cloud_cover,
                            "tile_id": props.get("s2:tile_id", ""),
                            "view_off_nadir": props.get("view:off_nadir", None),
                            "sun_elevation": props.get("eo:sun_elevation", None),
                            "scale_factor": scale,
                            "signed_url_used": True,
                        },
                    )

            # Only include acquisitions that have both NIR and SWIR
            if self.NIR_BAND in band_data and self.SWIR_BAND in band_data:
                acquisitions.append(
                    ReflectanceAcquisition(
                        date=item_date,
                        latitude=latitude,
                        longitude=longitude,
                        bands=band_data,
                        cloud_fraction=cloud_cover / 100.0 if cloud_cover else 0.0,
                        cloud_shadow_fraction=0.0,
                        snow_fraction=0.0,
                        valid_pixel_fraction=0.0 if is_cloudy else 1.0,
                        valid_observation_count=1 if not is_cloudy else 0,
                        source_product=self.SOURCE_PRODUCT,
                        processing_level=self.PROCESSING_LEVEL,
                        quality_status=QualityStatus.SATELLITE_RETRIEVED,
                    )
                )

        # Sort acquisitions by date
        acquisitions.sort(key=lambda a: a.date)

        result = ReflectanceTimeSeries(
            site_id=f"site_{latitude}_{longitude}",
            acquisitions=acquisitions,
            source_product=self.SOURCE_PRODUCT,
            processing_level=self.PROCESSING_LEVEL,
            spatial_resolution_m=self.SPATIAL_RESOLUTION_M,
        )

        # --- Cache store ---
        if self._cache is not None and cache_key is not None and acquisitions:
            try:
                self._cache.store_timeseries(
                    result,
                    site_id=f"{self.STAC_COLLECTION}:{latitude:.6f},{longitude:.6f}",
                    key=cache_key,
                )
            except OSError:
                pass  # Cache write failure must not break the fetch

        return result


class LandsatC2L2Source(SatelliteSource):
    """Landsat Collection 2 Level-2 surface reflectance source.

    Default bands:
        * NIR: B5 (Landsat 8/9, 0.85-0.88 um, 30 m resolution).
        * SWIR: B6 (Landsat 8/9, 1.57-1.65 um, 30 m resolution).
    """

    DEFAULT_BANDS = ["B5", "B6"]
    NIR_BAND = "B5"
    SWIR_BAND = "B6"
    SOURCE_PRODUCT = "LANDSAT_C2L2"
    STAC_COLLECTION = "landsat-c2-l2"
    PROCESSING_LEVEL = "L2"
    SPATIAL_RESOLUTION_M = 30.0

    def __init__(self, source_label: str = "Landsat Collection 2 Level-2") -> None:
        self.source_label = source_label

    def fetch_reflectance(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        bands: list[str] | None = None,
    ) -> ReflectanceTimeSeries:
        """Fetch Landsat Collection 2 Level-2 reflectance from Planetary Computer STAC.

        Queries the Planetary Computer STAC API for Landsat C2L2 items
        overlapping the given coordinates and date range, filters by cloud
        cover, signs asset URLs via the Planetary Computer signing service,
        and samples NIR/SWIR reflectance at the point location using rasterio.

        Args:
            latitude: Site latitude (WGS84 decimal degrees).
            longitude: Site longitude (WGS84 decimal degrees).
            start_date: Inclusive start date (ISO ``YYYY-MM-DD``).
            end_date: Inclusive end date (ISO ``YYYY-MM-DD``).
            bands: Optional list of band names.  Defaults to
                ``["B5", "B6"]`` for NDMI computation.

        Returns:
            :class:`ReflectanceTimeSeries` with all cloud-free acquisitions.

        Raises:
            ValueError: if coordinates or dates are invalid.
            RuntimeError: if the STAC search or asset download fails.
        """
        if bands is None:
            bands = [self.NIR_BAND, self.SWIR_BAND]

        # Validate coordinates
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude: {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude: {longitude}")

        # Buffer around point for STAC search (0.01 deg ~ 1 km)
        buffer_deg = 0.01
        bbox = (
            longitude - buffer_deg,
            latitude - buffer_deg,
            longitude + buffer_deg,
            latitude + buffer_deg,
        )

        try:
            items = _pc_stac_search(
                collection=self.STAC_COLLECTION,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                limit=50,
                cloud_max=DEFAULT_CLOUD_THRESHOLD,
            )
        except RuntimeError as exc:
            raise RuntimeError(f"Landsat STAC search failed: {exc}") from exc

        acquisitions: list[ReflectanceAcquisition] = []
        for item in items:
            props = item.get("properties", {})
            assets = item.get("assets", {})

            item_date = props.get("datetime", "")
            if isinstance(item_date, str):
                item_date = item_date[:10]

            cloud_cover = props.get("eo:cloud_cover", 100.0)

            band_data: dict[str, BandReflectance] = {}
            is_cloudy = False

            for band_name in bands:
                if band_name not in assets:
                    continue
                href = assets[band_name].get("href", "")
                if not href:
                    continue

                # Landsat Collection 2 scale factor (varies by product)
                scale = 0.0000275  # Typical Landsat C2L2 reflectance scale
                add_offset = -0.2  # Typical Landsat C2L2 reflectance offset

                value, cloudy = _sample_raster_at_point(
                    href=href,
                    latitude=latitude,
                    longitude=longitude,
                    scale_factor=scale,
                )
                if cloudy:
                    is_cloudy = True

                if value is not None:
                    # Apply offset for Landsat C2L2
                    reflectance = value + add_offset
                    band_data[band_name] = BandReflectance(
                        date=item_date,
                        band=band_name,
                        value=round(reflectance, 6),
                        spatial_resolution_m=self.SPATIAL_RESOLUTION_M,
                        quality_status=QualityStatus.SATELLITE_RETRIEVED,
                        source_product=self.SOURCE_PRODUCT,
                        source="Microsoft Planetary Computer STAC",
                        processing_level=self.PROCESSING_LEVEL,
                        metadata={
                            "item_id": item.get("id", ""),
                            "cloud_cover_percent": cloud_cover,
                            "landsat_id": props.get("landsat:landsat_id", ""),
                            "sensor": props.get("landsat:sensor", ""),
                            "scale_factor": scale,
                            "add_offset": add_offset,
                            "signed_url_used": True,
                        },
                    )

            # Only include acquisitions that have both NIR and SWIR
            if self.NIR_BAND in band_data and self.SWIR_BAND in band_data:
                acquisitions.append(
                    ReflectanceAcquisition(
                        date=item_date,
                        latitude=latitude,
                        longitude=longitude,
                        bands=band_data,
                        cloud_fraction=cloud_cover / 100.0 if cloud_cover else 0.0,
                        cloud_shadow_fraction=0.0,
                        snow_fraction=0.0,
                        valid_pixel_fraction=0.0 if is_cloudy else 1.0,
                        valid_observation_count=1 if not is_cloudy else 0,
                        source_product=self.SOURCE_PRODUCT,
                        processing_level=self.PROCESSING_LEVEL,
                        quality_status=QualityStatus.SATELLITE_RETRIEVED,
                    )
                )

        # Sort acquisitions by date
        acquisitions.sort(key=lambda a: a.date)

        return ReflectanceTimeSeries(
            site_id=f"site_{latitude}_{longitude}",
            acquisitions=acquisitions,
            source_product=self.SOURCE_PRODUCT,
            processing_level=self.PROCESSING_LEVEL,
            spatial_resolution_m=self.SPATIAL_RESOLUTION_M,
        )


def default_source_for(product: str) -> SatelliteSource:
    """Return the default satellite source for a product name.

    Args:
        product: Product name (``"sentinel-2"``, ``"landsat-c2l2"``).

    Returns:
        A :class:`SatelliteSource` instance.

    Raises:
        ValueError: if the product name is not recognised.
    """
    key = product.strip().lower()
    if key in ("sentinel-2", "sentinel2", "s2", "s2msi2a"):
        return Sentinel2Source()
    if key in ("landsat-c2l2", "landsatc2l2", "landsat", "c2l2"):
        return LandsatC2L2Source()
    raise ValueError(
        f"Unknown satellite product '{product}'. "
        f"Supported: 'sentinel-2', 'landsat-c2l2'."
    )


def ndmi_from_reflectance(
    nir: float | np.ndarray,
    swir: float | np.ndarray,
) -> float | np.ndarray:
    """Compute Normalized Difference Moisture Index from NIR and SWIR.

    NDMI = (NIR - SWIR) / (NIR + SWIR)

    Uses an exact zero-denominator guard (no epsilon bias).  Where
    NIR + SWIR == 0, the output is 0.0.  Result is clipped to [-1, 1].

    Args:
        nir: NIR reflectance value(s).
        swir: SWIR reflectance value(s).

    Returns:
        NDMI value(s), clipped to [-1, 1].
    """
    numerator = np.asarray(nir, dtype=np.float64) - np.asarray(swir, dtype=np.float64)
    denominator = np.asarray(nir, dtype=np.float64) + np.asarray(swir, dtype=np.float64)
    out = np.zeros(np.broadcast_shapes(numerator.shape, denominator.shape), dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(numerator, denominator, out=out, where=(denominator != 0.0))
    return np.clip(out, -1.0, 1.0)


def validate_reflectance_range(
    value: float | np.ndarray,
    band: str,
) -> list[str]:
    """Validate that reflectance values are within the physically valid range.

    Args:
        value: Reflectance value(s) to validate.
        band: Band name (for error messages).

    Returns:
        List of error messages (empty if all values are valid).
    """
    errors: list[str] = []
    arr = np.asarray(value, dtype=float)
    for v in np.nditer(arr):
        vf = float(v)
        if not np.isfinite(vf):
            errors.append(f"Band {band}: non-finite reflectance {vf}")
        elif vf < 0.0 or vf > 1.0:
            errors.append(
                f"Band {band}: reflectance {vf} outside valid range [0, 1]"
            )
    return errors
