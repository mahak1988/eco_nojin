"""
EPIA — EcoNojin Precision Irrigation Advisor

FAO-56 ETc + Sentinel-2 Kc for precision scheduling.
ETc = ET0 × Kc × Ks

Reference: Allen et al. (1998) FAO-56
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .base import ScientificModel, ValidationResult


class EPIA(ScientificModel):
    """EcoNojin Precision Irrigation Advisor"""

    name = "EPIA"
    version = "1.0.0"
    description = "Precision Irrigation Advisor with satellite Kc"

    REFERENCES = {
        "Allen1998": "Allen et al. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56.",
        "Jensen2016": "Jensen, M.E. & Allen, R.G. (2016). Crop Water Requirements.",
    }

    def validate_inputs(
        self, et0, lai, soil_moisture, rainfall_forecast_mm,
    ) -> tuple[bool, list[str]]:
        errors = []
        if not (0 <= et0 <= 20):
            errors.append("ET0 out of range")
        if np.any(lai < 0) or np.any(lai > 10):
            errors.append("LAI out of range")
        if not (0 <= soil_moisture <= 0.6):
            errors.append("Soil moisture out of range")
        if rainfall_forecast_mm < 0:
            errors.append("Rainfall must be non-negative")
        return len(errors) == 0, errors

    @staticmethod
    def kc_from_lai(lai: np.ndarray, lai_max: float = 6.0,
                    kc_min: float = 0.1, kc_max: float = 1.2) -> np.ndarray:
        """Derive Kc from LAI"""
        return np.clip(
            kc_min + (kc_max - kc_min) * (lai / lai_max),
            kc_min, kc_max
        )

    @staticmethod
    def ks_water_stress(soil_moisture: float, depletion_fraction: float = 0.5,
                        taw: float = 50.0) -> float:
        """Water stress coefficient Ks (FAO-56)"""
        raw = depletion_fraction * taw
        dr = taw * (1 - soil_moisture / 0.4)  # Simplified
        if dr <= raw:
            return 1.0
        return float(np.clip((taw - dr) / (taw - raw + 1e-6), 0, 1))

    @staticmethod
    def effective_rainfall(rainfall_mm: float, method: str = "usda_scs") -> float:
        """Effective rainfall (USDA-SCS method)"""
        if rainfall_mm <= 250:
            return float((125 - 0.2 * rainfall_mm) * rainfall_mm / 125)
        return float(0.75 * rainfall_mm - 25)

    def compute(
        self,
        et0: float,
        lai: np.ndarray,
        soil_moisture: float,
        rainfall_forecast_mm: float,
        irrigation_efficiency: float = 0.85,
        taw: float = 50.0,
        depletion_fraction: float = 0.5,
    ) -> dict[str, Any]:
        """Generate irrigation recommendation"""
        kc = self.kc_from_lai(lai)
        ks = self.ks_water_stress(soil_moisture, depletion_fraction, taw)
        etc = et0 * kc * ks

        p_eff = self.effective_rainfall(rainfall_forecast_mm)
        irri_net = np.maximum(0, etc - p_eff)
        irri_gross = irri_net / irrigation_efficiency
        irri_m3_ha = irri_gross * 10  # mm to m³/ha

        raw = depletion_fraction * taw
        days = max(1, int(raw / (et0 + 1e-6)))

        mean_kc = float(np.mean(kc))
        if mean_kc < 0.3:
            stage = "initial"
        elif mean_kc < 0.8:
            stage = "development"
        elif mean_kc < 1.1:
            stage = "mid-season"
        else:
            stage = "late-season"

        return {
            "et0": et0,
            "kc": kc,
            "ks": ks,
            "etc": etc,
            "irrigation_need_mm": irri_net,
            "irrigation_need_m3_ha": irri_m3_ha,
            "days_until_irrigation": days,
            "crop_stage": stage,
            "recommendation": f"Irrigate {float(np.mean(irri_gross)):.1f} mm in {days} days ({stage})",
        }

    def validate_against_reference(
        self, inputs: dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["etc"]))

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ETc (mm/day)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
