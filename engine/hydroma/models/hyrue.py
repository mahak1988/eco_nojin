"""
HY-RUE — Hydroma Radiation Use Efficiency Model

Based on Monteith (1977) enhanced with Sentinel-2 LAI retrieval.
B = Σ(PAR × fIPAR × ε × f_stress)
Y = B × HI

Reference: Monteith (1977), Steduto et al. (2009)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import ScientificModel, ValidationResult


@dataclass
class HYRUEParams:
    """پارامترهای مدل HY-RUE"""
    epsilon: float = 2.5  # RUE (g/MJ IPAR)
    k: float = 0.65  # Extinction coefficient
    hi: float = 0.45  # Harvest index
    lai_max: float = 6.0  # Maximum LAI
    t_opt: float = 25.0  # Optimal temperature (°C)
    t_min: float = 5.0  # Minimum temperature
    t_max: float = 35.0  # Maximum temperature

    # Crop-specific presets
    CROP_PRESETS = {
        "wheat": {"epsilon": 2.2, "hi": 0.45, "t_opt": 20.0},
        "maize": {"epsilon": 3.3, "hi": 0.50, "t_opt": 25.0},
        "rice": {"epsilon": 2.2, "hi": 0.45, "t_opt": 28.0},
        "potato": {"epsilon": 2.8, "hi": 0.75, "t_opt": 18.0},
    }

    @classmethod
    def for_crop(cls, crop_name: str) -> HYRUEParams:
        presets = cls.CROP_PRESETS.get(crop_name.lower())
        if presets:
            return cls(**presets)
        return cls()


class HYRUE(ScientificModel):
    """Hydroma Radiation Use Efficiency Model"""

    name = "HY-RUE"
    version = "1.0.0"
    description = "Radiation Use Efficiency with satellite LAI"

    REFERENCES = {
        "Monteith1977": "Monteith, J.L. (1977). Climate and the efficiency of crop production in Britain. Phil Trans R Soc B, 281, 277-294.",
        "Steduto2009": "Steduto et al. (2009). AquaCrop-The FAO crop model. Agronomy Journal, 101(3), 426-437.",
    }

    def __init__(self, params: HYRUEParams = None, crop: str = None, **config):
        super().__init__(**config)
        if crop:
            self.params = HYRUEParams.for_crop(crop)
        else:
            self.params = params or HYRUEParams()

    def validate_inputs(self, par, lai, ewsı, t_mean) -> tuple[bool, list[str]]:
        errors = []
        if not (0 <= par <= 50):
            errors.append(f"PAR {par} MJ/m² out of range")
        if np.any(lai < 0) or np.any(lai > 10):
            errors.append("LAI out of range [0, 10]")
        if np.any((ewsı < 0) | (ewsı > 1)):
            errors.append("EWSI out of range [0, 1]")
        if not (-10 <= t_mean <= 50):
            errors.append(f"Temperature {t_mean}°C out of range")
        return len(errors) == 0, errors

    @staticmethod
    def f_ipar(lai: np.ndarray, k: float = 0.65) -> np.ndarray:
        """Fraction of intercepted PAR (Beer-Lambert)"""
        return 1 - np.exp(-k * np.clip(lai, 0, 20))

    @staticmethod
    def stress_temperature(t_mean: float, t_opt: float = 25.0,
                           t_min: float = 5.0, t_max: float = 35.0) -> float:
        """Temperature stress factor (Gaussian response)"""
        if t_mean < t_min or t_mean > t_max:
            return 0.0
        return float(np.exp(-((t_mean - t_opt) / 8) ** 2))

    def compute_daily(
        self,
        par: float,
        lai: np.ndarray,
        ewsı: np.ndarray,
        t_mean: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """محاسبه روزانه"""
        f_ipar = self.f_ipar(lai, self.params.k)
        f_water = 1 - ewsı
        f_temp = self.stress_temperature(t_mean, self.params.t_opt,
                                          self.params.t_min, self.params.t_max)

        apár = par * f_ipar
        biomass = apár * self.params.epsilon * f_water * f_temp

        return f_ipar, biomass

    def compute(
        self,
        par: float,
        lai: np.ndarray,
        ewsı: np.ndarray,
        t_mean: float,
        days: int = 1,
    ) -> dict[str, Any]:
        """Compute biomass and yield"""
        f_ipar, daily_biomass = self.compute_daily(par, lai, ewsı, t_mean)

        total_biomass = daily_biomass * days
        yield_value = total_biomass * self.params.hi

        return {
            "f_ipar": f_ipar,
            "daily_biomass_g_m2": daily_biomass,
            "total_biomass_g_m2": total_biomass,
            "yield_g_m2": yield_value,
            "yield_t_ha": yield_value / 100,  # convert g/m² to t/ha
        }

    def validate_against_reference(
        self, inputs: dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["yield_t_ha"]))

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="Yield (t/ha)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
