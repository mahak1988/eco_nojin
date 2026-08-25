"""
Hydroma Nojin - Satellite Integration Layer

Bridges Sentinel-2 satellite data with all scientific motors:
- RUSLE Erosion: C-factor from NDVI/EVI/COMPOSITE
- Irrigation: Soil moisture proxy from NDMI
- Carbon Sequestration: Baseline SOC from NDVI time series
- Crop Advisor: Vegetation health validation from EVI
- Biofertilizer: Canopy vigor from NDVI
- Smart Map: Enhanced biomass from EVI+NDMI

Scientific basis:
- De Jong et al. (1999): C-factor from NDVI (Mediterranean)
- Van der Knijff et al. (2000): C = exp(-α × NDVI/β)
- FAO: NDMI correlation with soil moisture
- Rothamsted Research: NDVI-SOC relationships
"""
from __future__ import annotations

# =========================================================================
# C++ Bridge Integration - Satellite Integration with C++ indices
# Added by fix_future_imports.py
# =========================================================================
try:
    from engine.hydroma.cpp_bridge import (
        ndvi as _cpp_ndvi,
        evi as _cpp_evi,
        savi as _cpp_savi,
        ndwi as _cpp_ndwi,
        nbr as _cpp_nbr,
        ndvi_array as _cpp_ndvi_array,
        is_cpp_available,
    )
    _CPP_AVAILABLE = is_cpp_available()
except ImportError:
    _CPP_AVAILABLE = False


import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..satellite.sentinel2_provider import (
    Sentinel2Provider, SentinelProduct, SpectralIndex,
)


@dataclass
class SatelliteContext:
    """Context for satellite-derived inputs."""
    latitude: float
    longitude: float
    bbox: Tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    date: Optional[datetime] = None
    koppen_climate: str = "BSk"


@dataclass
class SatelliteDerivedParameters:
    """Parameters derived from satellite data for motors."""
    # For RUSLE
    c_factor: float  # 0-1, crop/management factor
    
    # For Irrigation
    ndmi_value: float  # -1 to 1
    soil_moisture_proxy: float  # 0-1
    
    # For Carbon
    baseline_soc_tC_ha: float
    ndvi_history_trend: float  # slope of NDVI time series
    
    # For Crop Advisor
    current_vegetation_health: str  # "poor", "moderate", "good", "excellent"
    biomass_proxy_t_ha: float
    
    # Metadata
    scene_id: str
    scene_date: str
    cloud_cover_pct: float


class SatelliteIntegration:
    """
    High-level integration layer connecting Sentinel-2 with motors.
    
    Usage:
        integration = SatelliteIntegration()
        params = integration.derive_parameters(
            SatelliteContext(lat, lon, bbox),
            crop_id="wheat",
            koppen="BSk"
        )
        # Use params.c_factor in RUSLE
        # Use params.ndmi_value in Irrigation
        # Use params.baseline_soc_tC_ha in Carbon
    """

    def __init__(self):
        self.provider = Sentinel2Provider(use_planetary_computer=True)

    def derive_parameters(
        self,
        context: SatelliteContext,
        crop_id: str = "wheat",
        koppen: str = "BSk",
    ) -> SatelliteDerivedParameters:
        """
        Derive satellite-based parameters for all motors.
        
        Returns a SatelliteDerivedParameters object ready for use.
        """
        # Get date range (last 30 days)
        date_to = context.date or datetime.now()
        date_from = date_to - timedelta(days=30)

        # Get scene
        scene = self.provider.get_scene(
            bbox=context.bbox,
            date_from=date_from,
            date_to=date_to,
            max_cloud_pct=30.0,
            product=SentinelProduct.L2A,
        )

        if scene is None:
            # Fallback to default values
            return self._default_parameters(context, crop_id)

        # Use batch computation (single load, multiple indices)
        # This ensures disk cache hit
        batch_results = self.provider.compute_indices_batch(
            scene,
            [SpectralIndex.NDVI, SpectralIndex.EVI, SpectralIndex.NDMI,
             SpectralIndex.COMPOSITE, SpectralIndex.SAVI],
            bbox=context.bbox,
            apply_cloud_mask=True,
            resolution=10,
        )
        
        indices = {}
        for idx, result in batch_results.items():
            if result is not None:
                valid = result.values[~np.isnan(result.values)]
                if len(valid) > 0:
                    indices[idx.name] = {
                        "mean": float(np.nanmean(result)),
                        "std": float(np.nanstd(result)),
                        "max": float(np.nanmax(result)),
                        "min": float(np.nanmin(result)),
                    }

        if not indices:
            return self._default_parameters(context, crop_id)

        # Derive C-factor from COMPOSITE (best index per condition)
        c_factor = self._compute_c_factor(indices, koppen)

        # Derive soil moisture proxy from NDMI
        ndmi_val = indices.get("NDMI", {}).get("mean", 0.0)
        soil_moisture_proxy = self._ndmi_to_soil_moisture(ndmi_val)

        # Derive baseline SOC from NDVI (empirical relationship)
        ndvi_val = indices.get("NDVI", {}).get("mean", 0.1)
        baseline_soc = self._ndvi_to_soc(ndvi_val, koppen)

        # Vegetation health classification
        veg_health = self._classify_vegetation_health(indices)

        # Biomass proxy
        evi_val = indices.get("EVI", {}).get("mean", 0.1)
        biomass = self._evi_to_biomass(evi_val, crop_id)

        return SatelliteDerivedParameters(
            c_factor=c_factor,
            ndmi_value=ndmi_val,
            soil_moisture_proxy=soil_moisture_proxy,
            baseline_soc_tC_ha=baseline_soc,
            ndvi_history_trend=0.0,  # TODO: multi-temporal
            current_vegetation_health=veg_health,
            biomass_proxy_t_ha=biomass,
            scene_id=scene.scene_id,
            scene_date=scene.datetime.strftime("%Y-%m-%d"),
            cloud_cover_pct=scene.cloud_cover_pct,
        )

    # =================================================================
    # Scientific Conversions
    # =================================================================

    def _compute_c_factor(self, indices: Dict, koppen: str) -> float:
        """
        Compute C-factor from vegetation indices.
        
        Van der Knijff et al. (2000):
            C = exp(-α × NDVI / β)
        where α=2, β=1 for European conditions
        
        For arid/semi-arid: use adjusted formula
        """
        # Use best available index
        composite = indices.get("COMPOSITE", {}).get("mean", 0.2)
        ndvi = indices.get("NDVI", {}).get("mean", 0.2)
        evi = indices.get("EVI", {}).get("mean", 0.2)
        
        # Choose best: COMPOSITE > EVI > NDVI
        veg_index = max(composite, evi, ndvi)
        veg_index = max(0.0, min(1.0, veg_index))
        
        # Climate-specific α parameter
        if koppen in ["BWh", "BWk", "BSh", "BSk"]:
            # Arid/semi-arid: sparser vegetation, different scaling
            alpha = 1.5
        elif koppen.startswith("A"):
            # Tropical: higher biomass, need steeper scaling
            alpha = 2.5
        else:
            # Temperate/continental: standard
            alpha = 2.0
        
        beta = 1.0
        
        # Van der Knijff formula
        c_factor = np.exp(-alpha * veg_index / beta)
        
        # Clip to valid range
        return max(0.001, min(1.0, c_factor))

    def _ndmi_to_soil_moisture(self, ndmi: float) -> float:
        """
        Convert NDMI to soil moisture proxy (0-1).
        
        Empirical relationship (Ceccato et al. 2001):
        NDMI < -0.3 → very dry (0.1)
        NDMI -0.3 to 0 → dry (0.2-0.4)
        NDMI 0 to 0.2 → moderate (0.4-0.6)
        NDMI > 0.2 → wet (0.6-0.9)
        """
        if ndmi < -0.5:
            return 0.05
        elif ndmi < -0.3:
            return 0.05 + (ndmi + 0.5) / 0.2 * 0.15
        elif ndmi < 0.0:
            return 0.20 + (ndmi + 0.3) / 0.3 * 0.20
        elif ndmi < 0.2:
            return 0.40 + ndmi / 0.2 * 0.20
        elif ndmi < 0.5:
            return 0.60 + (ndmi - 0.2) / 0.3 * 0.25
        else:
            return min(0.95, 0.85 + (ndmi - 0.5) * 0.1)

    def _ndvi_to_soc(self, ndvi: float, koppen: str) -> float:
        """
        Estimate baseline SOC from NDVI (empirical).
        
        Typical relationships:
        - Temperate grasslands: SOC = 20 + 80 × NDVI (tC/ha)
        - Forests: SOC = 50 + 150 × NDVI
        - Croplands: SOC = 15 + 60 × NDVI
        
        This is a rough proxy; real SOC needs soil sampling.
        """
        ndvi = max(0.0, min(1.0, ndvi))
        
        if koppen.startswith("A"):
            # Tropical: high biomass but rapid decomposition
            baseline = 25 + 50 * ndvi
        elif koppen in ["BWh", "BWk", "BSh", "BSk"]:
            # Arid: low SOC
            baseline = 5 + 40 * ndvi
        elif koppen.startswith("D"):
            # Boreal/continental: moderate-high SOC
            baseline = 30 + 80 * ndvi
        else:
            # Temperate
            baseline = 20 + 60 * ndvi
        
        return max(1.0, min(150.0, baseline))

    def _classify_vegetation_health(self, indices: Dict) -> str:
        """Classify vegetation health from indices."""
        ndvi = indices.get("NDVI", {}).get("mean", 0.0)
        evi = indices.get("EVI", {}).get("mean", 0.0)
        ndmi = indices.get("NDMI", {}).get("mean", 0.0)
        
        # Composite score
        veg_score = ndvi * 0.4 + evi * 0.4 + max(0, ndmi) * 0.2
        
        if veg_score > 0.6:
            return "excellent"
        elif veg_score > 0.4:
            return "good"
        elif veg_score > 0.2:
            return "moderate"
        else:
            return "poor"

    def _evi_to_biomass(self, evi: float, crop_id: str) -> float:
        """
        Convert EVI to above-ground biomass (t/ha).
        
        Empirical relationships (Gitelson et al. 2003):
        biomass = a × EVI + b
        """
        # Crop-specific coefficients
        coefficients = {
            "wheat": (15.0, 0.5),      # a, b
            "maize": (30.0, 1.0),
            "rice_paddy": (20.0, 0.8),
            "soybean": (12.0, 0.4),
            "cotton": (10.0, 0.3),
            "default": (15.0, 0.5),
        }
        
        a, b = coefficients.get(crop_id, coefficients["default"])
        evi = max(0.0, min(1.0, evi))
        
        return max(0.0, a * evi + b)

    def _default_parameters(self, context: SatelliteContext, crop_id: str) -> SatelliteDerivedParameters:
        """Default parameters when no satellite data is available."""
        return SatelliteDerivedParameters(
            c_factor=0.3,
            ndmi_value=0.0,
            soil_moisture_proxy=0.4,
            baseline_soc_tC_ha=20.0,
            ndvi_history_trend=0.0,
            current_vegetation_health="moderate",
            biomass_proxy_t_ha=5.0,
            scene_id="NO_DATA",
            scene_date="unknown",
            cloud_cover_pct=100.0,
        )


# Singleton for reuse
_integration: Optional[SatelliteIntegration] = None


def get_satellite_integration() -> SatelliteIntegration:
    """Get singleton SatelliteIntegration instance."""
    global _integration
    if _integration is None:
        _integration = SatelliteIntegration()
    return _integration
