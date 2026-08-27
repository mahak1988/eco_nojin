"""
Hydroma Nojin - Core Engine
Central scientific computation engine.

Architecture:
- Pure scientific logic (no I/O, no async)
- Used by all scientific motors in services/
- Tested independently with unit tests
- Version-controlled and documented

Scientific Standards:
- FAO-56 (Irrigation)
- RUSLE (Erosion)
- RothC-26.3 (Soil Carbon)
- USDA LCC (Land Capability)
- Köppen-Geiger (Climate Classification)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EngineVersion(Enum):
    """نسخه‌های موتور هسته"""
    V1_0 = "1.0.0"  # Initial release
    V1_1 = "1.1.0"  # Carbon calibration
    V1_2 = "1.2.0"  # Erosion calibration


@dataclass
class EngineContext:
    """Context for engine computations."""
    latitude: float = 35.0
    longitude: float = 51.0
    altitude_m: float = 1000.0
    koppen_climate: str = "BSk"
    soil_texture: int = 5
    soil_ph: float = 7.0
    soil_clay_fraction: float = 0.25
    soil_organic_matter_pct: float = 1.5
    annual_rainfall_mm: float = 300.0
    mean_annual_temp_c: float = 15.0


class HydromaCore:
    """
    Hydroma Nojin Core Engine
    
    Provides unified scientific computations for:
    - Soil analysis
    - Water balance
    - Carbon dynamics
    - Erosion assessment
    - Climate classification
    """

    VERSION = EngineVersion.V1_0.value

    def __init__(self, context: EngineContext | None = None):
        self.context = context or EngineContext()

    # ==================== Soil Module ====================

    @staticmethod
    def compute_soil_health_score(
        ph: float,
        organic_matter_pct: float,
        clay_fraction: float,
        texture_class: int,
    ) -> float:
        """Compute soil health score (0-100).
        
        Based on USDA Soil Quality Index.
        """
        # pH score (optimal: 6.0-7.5)
        if 6.0 <= ph <= 7.5:
            ph_score = 100
        else:
            ph_score = max(0, 100 - abs(ph - 6.75) * 15)

        # Organic matter score (optimal: >2%)
        om_score = min(100, organic_matter_pct * 40)

        # Texture score (optimal: loam, silt loam = 4-7)
        if 4 <= texture_class <= 7:
            tex_score = 100
        elif 3 <= texture_class <= 8:
            tex_score = 70
        else:
            tex_score = 40

        # Clay balance (optimal: 15-35%)
        if 0.15 <= clay_fraction <= 0.35:
            clay_score = 100
        else:
            clay_score = 60

        return (ph_score * 0.25 + om_score * 0.30 +
                tex_score * 0.25 + clay_score * 0.20)

    @staticmethod
    def estimate_soil_erodibility(texture_class: int, organic_matter_pct: float) -> float:
        """Estimate K-factor (soil erodibility) for RUSLE."""
        texture_factors = {
            1: 0.05, 2: 0.10, 3: 0.15,
            4: 0.35, 5: 0.45, 6: 0.50,
            7: 0.55, 8: 0.60,
            9: 0.30, 10: 0.20, 11: 0.15, 12: 0.10,
        }
        k = texture_factors.get(texture_class, 0.30)
        # OM reduces erodibility
        k = k * (1.0 - 0.10 * min(organic_matter_pct, 5))
        return max(0.01, min(k, 0.70))

    # ==================== Water Module ====================

    @staticmethod
    def compute_rainfall_erosivity(annual_rainfall_mm: float) -> float:
        """R-factor for RUSLE using FAO piecewise-linear method."""
        points = [
            (100, 100), (400, 400), (800, 1200),
            (1200, 2800), (1800, 5500), (2500, 8500), (3000, 11000),
        ]
        p = annual_rainfall_mm

        if p <= points[0][0]:
            return points[0][1] * (p / points[0][0])
        if p >= points[-1][0]:
            last = points[-1]
            slope = (last[1] - points[-2][1]) / (last[0] - points[-2][0])
            return last[1] + slope * (p - last[0])

        for i in range(len(points) - 1):
            p1, r1 = points[i]
            p2, r2 = points[i + 1]
            if p1 <= p <= p2:
                return r1 + (r2 - r1) * (p - p1) / (p2 - p1)
        return 3000

    @staticmethod
    def compute_crop_water_requirement(
        et0_mm_day: float,
        kc: float,
        area_ha: float = 1.0,
    ) -> dict[str, float]:
        """FAO-56 crop water requirement."""
        etc_mm_day = et0_mm_day * kc
        etc_mm_season = etc_mm_day * 30  # Monthly estimate
        water_volume_m3 = etc_mm_day * area_ha * 10  # 1mm/ha = 10 m³

        return {
            "etc_mm_day": etc_mm_day,
            "etc_mm_month": etc_mm_season,
            "water_volume_m3_ha": water_volume_m3,
        }

    # ==================== Carbon Module ====================

    @staticmethod
    def rothc_decomposition_rate_modifier(
        annual_rainfall_mm: float,
        mean_temp_c: float,
        plant_cover_fraction: float = 0.6,
    ) -> float:
        """RothC decomposition rate modifier."""
        # Temperature factor (Q10 = 2)
        temp_factor = 2.0 ** ((mean_temp_c - 20) / 10)
        temp_factor = max(0.1, min(temp_factor, 3.0))

        # Moisture factor
        if annual_rainfall_mm < 400:
            moisture_factor = 0.4
        elif annual_rainfall_mm < 800:
            moisture_factor = 0.7
        elif annual_rainfall_mm < 1500:
            moisture_factor = 0.9
        else:
            moisture_factor = 1.0

        return temp_factor * moisture_factor * plant_cover_fraction

    @staticmethod
    def estimate_carbon_sequestration_potential(
        method: str,
        climate: str,
        soil_texture: int,
    ) -> tuple[float, float]:
        """Estimate carbon sequestration potential range (tCO2e/ha/yr)."""
        method_potentials = {
            "no_till": (0.3, 0.8),
            "cover_crops": (0.5, 1.5),
            "biochar": (2.0, 5.0),
            "agroforestry": (1.0, 4.0),
            "residue_retention": (0.2, 0.6),
            "manure": (0.3, 1.0),
        }

        base_min, base_max = method_potentials.get(method, (0.3, 0.8))

        # Climate adjustment
        climate_multiplier = {
            "tropical": 1.3,
            "temperate": 1.0,
            "arid": 0.7,
            "cold": 0.5,
        }.get(climate, 1.0)

        return (base_min * climate_multiplier, base_max * climate_multiplier)

    # ==================== Erosion Module ====================

    @staticmethod
    def rusle_soil_loss(
        r_factor: float,
        k_factor: float,
        ls_factor: float,
        c_factor: float,
        p_factor: float,
        calibration: float = 0.10,
    ) -> float:
        """RUSLE soil loss calculation (t/ha/yr)."""
        return r_factor * k_factor * ls_factor * c_factor * p_factor * calibration

    @staticmethod
    def classify_erosion_risk(soil_loss: float) -> str:
        """Classify erosion risk."""
        if soil_loss < 5:
            return "Low"
        elif soil_loss < 12:
            return "Moderate"
        elif soil_loss < 25:
            return "High"
        elif soil_loss < 50:
            return "Severe"
        else:
            return "Critical"

    # ==================== Climate Module ====================

    @staticmethod
    def classify_koppen_climate(
        mean_annual_temp_c: float,
        annual_rainfall_mm: float,
    ) -> str:
        """Simplified Köppen climate classification."""
        if mean_annual_temp_c >= 18:
            if annual_rainfall_mm < 250:
                return "BWh"
            elif annual_rainfall_mm < 500:
                return "BSh"
            else:
                return "Aw"
        elif mean_annual_temp_c >= 10:
            if annual_rainfall_mm < 400:
                return "BSk"
            else:
                return "Csa"
        elif mean_annual_temp_c >= 0:
            return "Dfb"
        else:
            return "ET"


# Singleton instance for easy access
core_engine = HydromaCore()
