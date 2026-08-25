"""Runoff Pipeline (M-RUN) - SCS-CN Method."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

import numpy as np
import rioxarray
import xarray as xr

from ..base import MapPipeline, MapRequest, MapResult, MapType


class RunoffPipeline(MapPipeline):
    """
    Computes surface runoff using SCS-CN method (USDA).

    Equation:
        S  = (1000/CN - 10) * 25.4    [mm]
        Ia = 0.2 * S                   [mm]
        Q  = (P - Ia)^2 / (P - Ia + S)   if P > Ia
        Q  = 0                           if P <= Ia

    Output bands:
    1. runoff_mm (Q)
    2. runoff_class (1-5)
    3. cn_value
    4. retention_s
    5. peak_flow_estimate (simplified)
    """

    @property
    def map_type(self) -> MapType:
        return MapType.M_RUN

    def get_required_layers(self) -> list:
        return ["rainfall", "runoff"]

    async def execute(
        self,
        base_layers: Dict[str, xr.DataArray],
        request: MapRequest,
    ) -> MapResult:
        """Generate runoff map."""
        start_time = time.time()

        rainfall = base_layers["rainfall"]
        cn_layer = base_layers["runoff"]

        # Get precipitation from parameters (default 50mm - typical storm)
        precipitation_mm = request.parameters.get("precipitation_mm", 50.0)
        amc = request.parameters.get("amc", "II")  # I, II, or III

        # Align to common grid
        target_crs = (
            self.detect_utm_zone(request.region)
            if request.target_crs == "auto"
            else request.target_crs
        )

        cn = self._align_to_grid(cn_layer, rainfall)

        # AMC correction
        cn_adj = self._adjust_amc(cn, amc)

        # SCS-CN calculations
        retention_s = self._compute_s(cn_adj)
        initial_abstraction = 0.2 * retention_s

        # Uniform precipitation field (can be spatial in production)
        p = xr.full_like(rainfall, precipitation_mm, dtype=np.float32)

        # Runoff Q
        runoff = self._compute_runoff(p, initial_abstraction, retention_s)

        # Peak flow (simplified TR-55)
        area_ha = self._estimate_area(rainfall)
        peak_flow = self._estimate_peak_flow(runoff, area_ha)

        # Classification
        runoff_class = self._classify_runoff(runoff)

        # Stack
        stack = xr.concat(
            [runoff, runoff_class.astype(np.float32), cn_adj, retention_s, peak_flow],
            dim="band",
        ).assign_coords(
            band=["runoff_mm", "runoff_class", "cn", "retention_s", "peak_flow_m3s"]
        )

        if str(rainfall.rio.crs) != target_crs:
            stack = stack.rio.reproject(target_crs)

        # Save
        map_id = f"M-RUN_{request.request_id[:8]}"
        output_dir = Path("data/maps") / map_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cog_path = output_dir / "runoff.tif"

        stack.rio.to_raster(
            str(cog_path),
            driver="COG",
            compress="DEFLATE",
            overview_resampling="average",
        )

        processing_time = time.time() - start_time

        runoff_vals = runoff.values
        valid = runoff_vals[~np.isnan(runoff_vals)]

        return MapResult(
            map_id=map_id,
            map_type=self.map_type,
            cog_path=cog_path,
            metadata={
                "title": "SCS-CN Runoff Map",
                "abstract": "Surface runoff using SCS-CN method",
                "equation": "Q = (P - Ia)^2 / (P - Ia + S)",
                "precipitation_mm": precipitation_mm,
                "amc_class": amc,
                "bands": [str(b) for b in stack.band.values],
                "runoff_stats_mm": {
                    "min": float(valid.min()) if len(valid) > 0 else None,
                    "max": float(valid.max()) if len(valid) > 0 else None,
                    "mean": float(valid.mean()) if len(valid) > 0 else None,
                },
                "runoff_classes": {
                    "1": "very low (Q < 5 mm)",
                    "2": "low (5-15 mm)",
                    "3": "moderate (15-30 mm)",
                    "4": "high (30-50 mm)",
                    "5": "very high (> 50 mm)",
                },
                "standards": ["USDA TR-55", "ISO 19115"],
            },
            processing_time_seconds=processing_time,
            data_sources=["Rainfall", "Land Cover", "Soil (CN-derived)"],
            crs=target_crs,
            bounds=rainfall.rio.bounds(),
            resolution=float(request.resolution),
        )

    def _align_to_grid(self, source: xr.DataArray, target: xr.DataArray) -> xr.DataArray:
        try:
            if source.shape == target.shape:
                return source
            resampled = source.rio.reproject_match(target)
            if "band" in resampled.dims and resampled.sizes["band"] == 1:
                resampled = resampled.isel(band=0, drop=True)
            return resampled
        except Exception as e:
            print(f"  [WARN] Reproject failed: {e}")
            return source

    def _adjust_amc(self, cn: xr.DataArray, amc: str) -> xr.DataArray:
        """Adjust CN for Antecedent Moisture Condition."""
        values = cn.values

        if amc == "I":  # Dry
            cn_adj = 4.2 * values / (10 - 0.058 * values)
        elif amc == "III":  # Wet
            cn_adj = 23 * values / (10 + 0.13 * values)
        else:  # AMC-II (normal)
            cn_adj = values

        cn_adj = np.clip(cn_adj, 0, 100)

        return xr.DataArray(
            cn_adj.astype(np.float32),
            coords=cn.coords, dims=cn.dims,
            attrs={"description": f"CN adjusted for AMC-{amc}"},
        ).rio.write_crs(cn.rio.crs)

    def _compute_s(self, cn: xr.DataArray) -> xr.DataArray:
        """Compute retention parameter S in mm."""
        # S = (1000/CN - 10) * 25.4
        cn_vals = np.clip(cn.values, 1, 100)  # avoid div by zero
        s = (1000.0 / cn_vals - 10.0) * 25.4
        s = np.clip(s, 0, 1000)

        return xr.DataArray(
            s.astype(np.float32),
            coords=cn.coords, dims=cn.dims,
            attrs={"description": "Retention parameter S (mm)"},
        ).rio.write_crs(cn.rio.crs)

    def _compute_runoff(
        self,
        p: xr.DataArray,
        ia: xr.DataArray,
        s: xr.DataArray,
    ) -> xr.DataArray:
        """Compute runoff Q using SCS-CN equation."""
        p_vals = p.values
        ia_vals = ia.values
        s_vals = s.values

        q = np.zeros_like(p_vals, dtype=np.float32)
        valid = p_vals > ia_vals
        denominator = p_vals[valid] - ia_vals[valid] + s_vals[valid]
        q[valid] = (p_vals[valid] - ia_vals[valid]) ** 2 / denominator

        return xr.DataArray(
            q,
            coords=p.coords, dims=p.dims,
            attrs={"description": "Runoff depth Q (mm)", "units": "mm"},
        ).rio.write_crs(p.rio.crs)

    def _estimate_area(self, data: xr.DataArray) -> float:
        """Estimate total area in hectares."""
        bounds = data.rio.bounds()
        width_m = (bounds[2] - bounds[0]) * 111000 * np.cos(np.radians((bounds[1] + bounds[3]) / 2))
        height_m = (bounds[3] - bounds[1]) * 111000
        return (width_m * height_m) / 10000  # m^2 to ha

    def _estimate_peak_flow(
        self,
        runoff: xr.DataArray,
        area_ha: float,
    ) -> xr.DataArray:
        """Simplified peak flow (TR-55 approximation)."""
        # Qp ~ 0.0028 * A * Q / Tc (simplified)
        # For spatial map: scale runoff by area fraction
        pixel_area_ha = area_ha / runoff.size
        q_vals = runoff.values
        peak = 0.0028 * pixel_area_ha * q_vals  # m^3/s per pixel
        peak = np.clip(peak, 0, 1000)

        return xr.DataArray(
            peak.astype(np.float32),
            coords=runoff.coords, dims=runoff.dims,
            attrs={"description": "Estimated peak flow (m3/s)", "units": "m3/s"},
        ).rio.write_crs(runoff.rio.crs)

    def _classify_runoff(self, runoff: xr.DataArray) -> xr.DataArray:
        """Classify runoff into 5 classes."""
        values = runoff.values
        classified = np.ones_like(values, dtype=np.uint8)
        classified[values >= 5] = 2
        classified[values >= 15] = 3
        classified[values >= 30] = 4
        classified[values >= 50] = 5

        return xr.DataArray(
            classified,
            coords=runoff.coords, dims=runoff.dims,
            attrs={"description": "Runoff risk class"},
        )
