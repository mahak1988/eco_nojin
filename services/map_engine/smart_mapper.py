"""
Hydroma Nojin - Smart Map Generator
Generates agricultural maps from satellite imagery and soil data.
"""

import numpy as np
import xarray as xr


class SmartMapGenerator:
    """Generate smart agricultural maps."""

    @staticmethod
    def calculate_ndvi(
        red_band: xr.DataArray,
        nir_band: xr.DataArray,
    ) -> xr.DataArray:
        """Calculate Normalized Difference Vegetation Index."""
        ndvi = (nir_band - red_band) / (nir_band + red_band + 1e-10)
        ndvi = np.clip(ndvi, -1, 1)

        return xr.DataArray(
            ndvi.values,
            dims=red_band.dims,
            coords=red_band.coords,
            attrs={
                "units": "index",
                "description": "NDVI (-1 to 1)",
                "optimal_range": "0.3-0.8 for healthy vegetation",
            },
        )

    @staticmethod
    def classify_vegetation_health(ndvi: xr.DataArray) -> xr.DataArray:
        """Classify vegetation health based on NDVI."""
        health = np.ones_like(ndvi.values, dtype=np.int32)

        health[ndvi.values < 0.1] = 1  # Bare soil / water
        health[(ndvi.values >= 0.1) & (ndvi.values < 0.3)] = 2  # Stressed
        health[(ndvi.values >= 0.3) & (ndvi.values < 0.6)] = 3  # Moderate
        health[(ndvi.values >= 0.6) & (ndvi.values < 0.8)] = 4  # Healthy
        health[ndvi.values >= 0.8] = 5  # Very healthy

        return xr.DataArray(
            health,
            dims=ndvi.dims,
            coords=ndvi.coords,
            attrs={
                "units": "class",
                "description": "Vegetation health (1=bare, 5=very healthy)",
            },
        )

    @staticmethod
    def estimate_biomass(
        ndvi: xr.DataArray,
        crop_type: str = "wheat",
    ) -> xr.DataArray:
        """Estimate above-ground biomass from NDVI."""
        # Empirical relationship: Biomass = a * NDVI + b
        crop_params = {
            "wheat": {"a": 8.5, "b": 0.5},
            "maize": {"a": 12.0, "b": 0.8},
            "barley": {"a": 7.0, "b": 0.4},
            "cotton": {"a": 10.0, "b": 0.6},
        }

        params = crop_params.get(crop_type, crop_params["wheat"])
        biomass = params["a"] * ndvi + params["b"]
        biomass = np.maximum(biomass, 0)

        return xr.DataArray(
            biomass.values,
            dims=ndvi.dims,
            coords=ndvi.coords,
            attrs={
                "units": "ton/ha",
                "description": f"Estimated {crop_type} biomass",
            },
        )

    @staticmethod
    def calculate_crop_water_requirement(
        et0: xr.DataArray,
        crop_type: str = "wheat",
        growth_stage: str = "mid-season",
    ) -> xr.DataArray:
        """Calculate crop water requirement (ETc = ET0 * Kc)."""
        # Crop coefficients (Kc) for different stages
        kc_values = {
            "wheat": {
                "initial": 0.7,
                "development": 1.0,
                "mid-season": 1.15,
                "late-season": 0.8,
            },
            "maize": {
                "initial": 0.7,
                "development": 1.1,
                "mid-season": 1.2,
                "late-season": 0.9,
            },
        }

        crop_kc = kc_values.get(crop_type, kc_values["wheat"])
        kc = crop_kc.get(growth_stage, 1.0)

        etc = et0 * kc

        return xr.DataArray(
            etc.values,
            dims=et0.dims,
            coords=et0.coords,
            attrs={
                "units": "mm/day",
                "description": f"Crop water requirement ({crop_type}, {growth_stage})",
            },
        )

    @staticmethod
    def generate_irrigation_recommendation(
        soil_moisture: xr.DataArray,
        etc: xr.DataArray,
        field_capacity: float = 0.30,
        wilting_point: float = 0.15,
    ) -> dict[str, xr.DataArray]:
        """Generate irrigation recommendations."""
        # Available water capacity
        awc = field_capacity - wilting_point

        # Management allowed depletion (50% of AWC)
        mad = awc * 0.5

        # Irrigation need
        deficit = np.maximum(mad - (soil_moisture - wilting_point), 0)
        irrigation_need = deficit * 1000  # Convert to mm

        # Days until next irrigation
        days_to_irrigate = np.where(
            etc > 0,
            (soil_moisture - wilting_point) / etc,
            999
        )
        days_to_irrigate = np.clip(days_to_irrigate, 0, 30)

        return {
            "irrigation_need_mm": xr.DataArray(
                irrigation_need.values,
                dims=soil_moisture.dims,
                coords=soil_moisture.coords,
                attrs={"units": "mm", "description": "Irrigation water needed"},
            ),
            "days_to_irrigate": xr.DataArray(
                days_to_irrigate.values,
                dims=soil_moisture.dims,
                coords=soil_moisture.coords,
                attrs={"units": "days", "description": "Days until next irrigation"},
            ),
        }
