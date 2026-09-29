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

        A weighted combination of four agronomic sub-scores. This is this
        project's construction, NOT the USDA Soil Quality Index.

        The docstring previously said "Based on USDA Soil Quality Index". The
        USDA NRCS SQI (Andrews et al., 2002) is a principal-components index: it
        derives weights from the observed covariance of the measurements. These
        weights are fixed and hand-chosen, and appear nowhere in that method or in
        any other. The component optima (pH 6.0-7.5, organic matter saturating at
        2.5%, clay 15-35%) are standard agronomic values; the combination is ours.
        See engine/hydroma/formulas/research/__init__.py::core_soil_health_score.
        """
        # pH score (optimal: 6.0-7.5)
        ph_score = 100 if 6.0 <= ph <= 7.5 else max(0, 100 - abs(ph - 6.75) * 15)

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
        clay_score = 100 if 0.15 <= clay_fraction <= 0.35 else 60

        return ph_score * 0.25 + om_score * 0.30 + tex_score * 0.25 + clay_score * 0.20

    @staticmethod
    def estimate_soil_erodibility(texture_class: int, organic_matter_pct: float) -> float:
        """Estimate K-factor (soil erodibility) for RUSLE."""
        texture_factors = {
            1: 0.05,
            2: 0.10,
            3: 0.15,
            4: 0.35,
            5: 0.45,
            6: 0.50,
            7: 0.55,
            8: 0.60,
            9: 0.30,
            10: 0.20,
            11: 0.15,
            12: 0.10,
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
            (100, 100),
            (400, 400),
            (800, 1200),
            (1200, 2800),
            (1800, 5500),
            (2500, 8500),
            (3000, 11000),
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
        """Combined RothC rate modifier: temperature x moisture x cover.

        Delegates to the canonical implementation in
        ``engine/hydroma/simulation/runners/rothc_runner.py``.

        This method previously computed its own, different result: a Q10
        exponential of 2.0 about a 20 C base with an ad-hoc [0.1, 3.0] clamp, and
        a four-step moisture ladder keyed on *annual rainfall* rather than on
        soil-moisture deficit. That is not RothC -- the canonical temperature
        response is ``47.9 / (1 + exp(106.06 / (T + 18.27)))`` and the canonical
        moisture response is a continuous function of the monthly deficit. Two
        implementations of the same named quantity guaranteed that a caller got a
        different answer depending on which one it reached.

        ``annual_rainfall_mm`` is retained in the signature, but rainfall does not
        determine a soil-moisture deficit -- a deficit is what evapotranspired,
        which needs potential ET. The mapping below is therefore an explicit
        stand-in, not a derivation: a wetter climate gets a smaller deficit and
        so a larger moisture factor, which is the direction the previous
        rainfall-keyed ladder had. Callers holding monthly rainfall and ET
        should use ``run_rothc`` directly, which takes the real deficit.
        """
        from engine.hydroma.simulation.runners.rothc_runner import (
            temp_factor,
            water_factor,
        )

        max_deficit = 60.0
        # 0 mm rain -> the full deficit; 1200 mm and above -> no deficit.
        wetness = min(max(annual_rainfall_mm / 1200.0, 0.0), 1.0)
        deficit = max_deficit * (1.0 - wetness)

        return (
            float(temp_factor(mean_temp_c))
            * float(water_factor(deficit, max_deficit))
            * float(plant_cover_fraction)
        )

    @staticmethod
    def estimate_carbon_sequestration_potential(
        method: str,
        climate: str,
        soil_texture: int,
    ) -> tuple[float, float]:
        """Estimate carbon sequestration potential range (tCO2e/ha/yr).

        Args:
            method: Sequestration method (no_till, cover_crops, biochar, etc.)
            climate: Climate zone (tropical, temperate, arid, cold)
            soil_texture: Soil texture class (1=clay, 2=silty_clay, 3=silty_clay_loam,
                         4=clay_loam, 5=silty_loam, 6=loam, 7=sandy_loam, 8=sand)
        """
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

        # Soil texture adjustment (IPCC-based factors)
        # Higher clay content generally increases sequestration potential
        texture_multiplier = {
            1: 1.2,  # clay
            2: 1.15,  # silty_clay
            3: 1.1,  # silty_clay_loam
            4: 1.05,  # clay_loam
            5: 1.0,  # silty_loam
            6: 1.0,  # loam
            7: 0.95,  # sandy_loam
            8: 0.9,  # sand
        }.get(soil_texture, 1.0)

        return (
            base_min * climate_multiplier * texture_multiplier,
            base_max * climate_multiplier * texture_multiplier,
        )

    # ==================== Erosion Module ====================

    @staticmethod
    def rusle_soil_loss(
        r_factor: float,
        k_factor: float,
        ls_factor: float,
        c_factor: float,
        p_factor: float,
    ) -> float:
        """RUSLE soil loss, t/ha/yr.

        A = R * K * LS * C * P, as in Renard et al., USDA Agriculture Handbook 703
        (1997) and Foster et al. (1981). The native kernel implements the same
        plain product at engine/cpp_core/src/erosion.cpp:19.

        This previously multiplied the result by a default ``calibration`` of
        0.10. That factor is not part of RUSLE, was cited nowhere, and silently
        divided a published quantity by ten. Any local calibration belongs to the
        caller, which is the only place that can justify it -- and it must be
        applied to a measured erosion rate, not buried in the standard equation.
        """
        return r_factor * k_factor * ls_factor * c_factor * p_factor

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
