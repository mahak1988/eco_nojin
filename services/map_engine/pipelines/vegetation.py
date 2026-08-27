"""Vegetation Pipeline (M-VEG) - NDVI, EVI, NDWI, NBR, LAI."""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import xarray as xr

from ..base import MapPipeline, MapRequest, MapResult, MapType


class VegetationPipeline(MapPipeline):
    """
    Computes vegetation indices from Sentinel-2-like spectral data.

    Output bands:
    1. NDVI - Normalized Difference Vegetation Index (-1 to 1)
    2. EVI  - Enhanced Vegetation Index (-1 to 1)
    3. NDWI - Normalized Difference Water Index (-1 to 1)
    4. NBR  - Normalized Burn Ratio (-1 to 1)
    5. LAI  - Leaf Area Index (0 to 8)
    6. veg_class - Vegetation density class (1-5)
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_VEG

    def get_required_layers(self) -> list:
        return ["vegetation"]

    async def execute(
        self,
        base_layers: dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Generate vegetation indices map."""
        start_time = time.time()

        s2_data = base_layers["vegetation"]

        # Extract bands (reflectance 0-10000 -> 0-1)
        B02 = self._extract_band(s2_data, "B02") / 10000.0
        B03 = self._extract_band(s2_data, "B03") / 10000.0
        B04 = self._extract_band(s2_data, "B04") / 10000.0
        B08 = self._extract_band(s2_data, "B08") / 10000.0
        B11 = self._extract_band(s2_data, "B11") / 10000.0
        SCL = self._extract_band(s2_data, "SCL")

        # Cloud mask (clear pixels only)
        # SCL: 4=vegetation, 5=bare, 6=water, 2=dark (clear)
        clear_mask = np.isin(SCL.values, [2, 4, 5, 6])

        # Compute vegetation indices
        ndvi = self._compute_ndvi(B04, B08)
        evi = self._compute_evi(B02, B04, B08)
        ndwi = self._compute_ndwi(B03, B08)
        nbr = self._compute_nbr(B08, B11)
        lai = self._compute_lai(ndvi)
        veg_class = self._classify_vegetation(ndvi)

        # Apply cloud mask (set clouded pixels to NaN)
        ndvi_vals = ndvi.values.copy()
        ndvi_vals[~clear_mask] = np.nan
        ndvi = xr.DataArray(
            ndvi_vals, coords=ndvi.coords, dims=ndvi.dims, attrs=ndvi.attrs
        ).rio.write_crs(ndvi.rio.crs)

        # Stack output bands
        stack = xr.concat(
            [ndvi, evi, ndwi, nbr, lai, veg_class.astype(np.float32)],
            dim="band",
        ).assign_coords(band=["NDVI", "EVI", "NDWI", "NBR", "LAI", "veg_class"])

        # Target CRS
        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        if str(s2_data.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

        # Save COG
        season = s2_data.attrs.get("season", "summer")
        map_id = f"M-VEG_{request.request_id[:8]}_{season}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cog_path = output_dir / "vegetation.tif"

        stack.rio.to_raster(
            str(cog_path),
            driver="COG",
            compress="DEFLATE",
            overview_resampling="average",
            nodata=np.nan,
        )

        processing_time = time.time() - start_time

        # Statistics (excluding NaN)
        ndvi_valid = ndvi.values[~np.isnan(ndvi.values)]
        cloud_pct = float((~clear_mask).sum() / clear_mask.size * 100)

        return MapResult(
            map_id=map_id,
            map_type=self.map_type,
            cog_path=cog_path,
            metadata={
                "title": f"Vegetation Indices Map ({season})",
                "abstract": "NDVI, EVI, NDWI, NBR, LAI from Sentinel-2-like data",
                "season": season,
                "cloud_cover_pct": cloud_pct,
                "bands": ["NDVI", "EVI", "NDWI", "NBR", "LAI", "veg_class"],
                "ndvi_stats": {
                    "min": float(ndvi_valid.min()) if len(ndvi_valid) > 0 else None,
                    "max": float(ndvi_valid.max()) if len(ndvi_valid) > 0 else None,
                    "mean": float(ndvi_valid.mean()) if len(ndvi_valid) > 0 else None,
                    "std": float(ndvi_valid.std()) if len(ndvi_valid) > 0 else None,
                },
                "vegetation_classes": {
                    "1": "barren (<0.1)",
                    "2": "sparse (0.1-0.3)",
                    "3": "moderate (0.3-0.5)",
                    "4": "dense (0.5-0.7)",
                    "5": "very dense (>0.7)",
                },
                "formulas": {
                    "NDVI": "(NIR - Red) / (NIR + Red)",
                    "EVI": "2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)",
                    "NDWI": "(Green - NIR) / (Green + NIR)",
                    "NBR": "(NIR - SWIR) / (NIR + SWIR)",
                    "LAI": "empirical from NDVI",
                },
                "standards": ["ESA Sentinel-2", "ISO 19115"],
            },
            processing_time_seconds=processing_time,
            data_sources=[f"Sentinel-2 (synthetic, {season})"],
            crs=target_crs,
            bounds=s2_data.rio.bounds(),
            resolution=float(request.resolution),
        )

    def _extract_band(self, s2_data: xr.DataArray, band_name: str) -> xr.DataArray:
        """Extract a single band from multi-band DataArray."""
        if "band" in s2_data.dims:
            return s2_data.sel(band=band_name)
        raise ValueError(f"Cannot extract band {band_name} from data")

    def _compute_ndvi(self, red: xr.DataArray, nir: xr.DataArray) -> xr.DataArray:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        eps = 1e-6
        ndvi = (nir - red) / (nir + red + eps)
        return xr.DataArray(
            ndvi.values.astype(np.float32),
            coords=red.coords, dims=red.dims,
            attrs={"description": "NDVI", "range": "[-1, 1]"},
        ).rio.write_crs(red.rio.crs)

    def _compute_evi(
        self,
        blue: xr.DataArray,
        red: xr.DataArray,
        nir: xr.DataArray,
    ) -> xr.DataArray:
        """EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)"""
        eps = 1e-6
        evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + eps)
        return xr.DataArray(
            evi.values.astype(np.float32),
            coords=red.coords, dims=red.dims,
            attrs={"description": "EVI", "range": "[-1, 1]"},
        ).rio.write_crs(red.rio.crs)

    def _compute_ndwi(self, green: xr.DataArray, nir: xr.DataArray) -> xr.DataArray:
        """NDWI = (Green - NIR) / (Green + NIR)"""
        eps = 1e-6
        ndwi = (green - nir) / (green + nir + eps)
        return xr.DataArray(
            ndwi.values.astype(np.float32),
            coords=green.coords, dims=green.dims,
            attrs={"description": "NDWI (McFeeters)", "range": "[-1, 1]"},
        ).rio.write_crs(green.rio.crs)

    def _compute_nbr(self, nir: xr.DataArray, swir: xr.DataArray) -> xr.DataArray:
        """NBR = (NIR - SWIR) / (NIR + SWIR) - for burn severity"""
        eps = 1e-6
        nbr = (nir - swir) / (nir + swir + eps)
        return xr.DataArray(
            nbr.values.astype(np.float32),
            coords=nir.coords, dims=nir.dims,
            attrs={"description": "NBR (Normalized Burn Ratio)", "range": "[-1, 1]"},
        ).rio.write_crs(nir.rio.crs)

    def _compute_lai(self, ndvi: xr.DataArray) -> xr.DataArray:
        """LAI from NDVI using empirical relationship (Ross 1976-like)."""
        # LAI = -ln(1 - fPAR) / k, where fPAR ~ NDVI for moderate values
        # Simplified: LAI = 3.5 * NDVI for NDVI > 0
        ndvi_vals = ndvi.values
        lai = np.where(ndvi_vals > 0, 3.5 * ndvi_vals, 0.0)
        lai = np.clip(lai, 0, 8)

        return xr.DataArray(
            lai.astype(np.float32),
            coords=ndvi.coords, dims=ndvi.dims,
            attrs={"description": "LAI (Leaf Area Index)", "units": "m2/m2"},
        ).rio.write_crs(ndvi.rio.crs)

    def _classify_vegetation(self, ndvi: xr.DataArray) -> xr.DataArray:
        """Classify vegetation density from NDVI."""
        values = ndvi.values
        classified = np.ones_like(values, dtype=np.uint8)
        classified[values >= 0.1] = 2  # sparse
        classified[values >= 0.3] = 3  # moderate
        classified[values >= 0.5] = 4  # dense
        classified[values >= 0.7] = 5  # very dense
        classified[np.isnan(values)] = 0  # no data

        return xr.DataArray(
            classified,
            coords=ndvi.coords, dims=ndvi.dims,
            attrs={"description": "Vegetation density class"},
        )
