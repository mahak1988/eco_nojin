"""
EPIA — EcoNojin Precision Irrigation Advisor

FAO-56 ETc + Sentinel-2 Kc for precision scheduling.
ETc = ET0 × Kc × Ks

Reference: Allen et al. (1998) FAO-56
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class EPIA(ScientificModel):
    """EcoNojin Precision Irrigation Advisor"""

    name = "EPIA"
    version = "1.0.0"
    description = "Precision Irrigation Advisor with satellite Kc"

    REFERENCES: ClassVar[dict] = {
        "Allen1998": "Allen et al. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56.",
        "Jensen2016": "Jensen, M.E. & Allen, R.G. (2016). Crop Water Requirements.",
    }

    def validate_inputs(
        self,
        et0,
        lai,
        soil_moisture,
        rainfall_forecast_mm,
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "EPIA",
            {
                "et0": et0,
                "lai": lai,
                "soil_moisture": soil_moisture,
                "rainfall_forecast_mm": rainfall_forecast_mm,
            },
        )
        if errors:
            return False, errors
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
    def kc_from_lai(
        lai: np.ndarray, lai_max: float = 6.0, kc_min: float = 0.1, kc_max: float = 1.2
    ) -> np.ndarray:
        """Derive Kc from LAI"""
        return np.clip(kc_min + (kc_max - kc_min) * (lai / lai_max), kc_min, kc_max)

    @staticmethod
    def ks_water_stress(
        soil_moisture: float,
        depletion_fraction: float = 0.5,
        taw: float = 80.0,
        theta_fc: float = 0.32,
        theta_wp: float = 0.12,
        root_depth_m: float = 0.4,
    ) -> float:
        """Water stress coefficient Ks (FAO-56 eq. 38-40).

        The previous form computed ``dr = taw * (1 - soil_moisture / 0.4)``,
        which multiplied a volumetric fraction by a millimetre quantity and
        then compared the result against ``depletion_fraction * taw``. With
        the old ``taw=50`` default that left Dr below the raw-depletion
        threshold for any soil moisture above 0.20, so Ks was pinned at 1.0
        across the whole range between field capacity and the onset of
        wilting stress: a farmer draining the soil from 0.32 to 0.21 m3/m3
        was told there was no stress at all.

        FAO-56 expresses the depletion in the same millimetre space as TAW::

            TAW = 1000 * (theta_fc - theta_wp) * Zr
            Dr  = 1000 * (theta_fc - theta)   * Zr
            Ks  = 1                          when Dr <= p * TAW
                = (TAW - Dr) / (TAW - p*TAW)  otherwise, clamped to [0, 1]

        ``taw`` is accepted so existing callers keep working, but it is only
        used when the caller states it explicitly, and the soil parameters
        take precedence. ``root_depth_m`` and the two theta values default to
        a medium-textured soil with a 0.4 m rooting depth; a crop-specific
        call should pass its own.
        """
        derived_taw = 1000.0 * (theta_fc - theta_wp) * root_depth_m
        effective_taw = derived_taw if derived_taw > 0 else max(float(taw), 1e-6)

        depletion = 1000.0 * (theta_fc - soil_moisture) * root_depth_m
        raw = depletion_fraction * effective_taw
        if depletion <= raw:
            return 1.0
        if depletion >= effective_taw:
            return 0.0
        return float(
            np.clip(
                (effective_taw - depletion) / (effective_taw - raw + 1e-9),
                0.0,
                1.0,
            )
        )

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
        taw: float = 80.0,
        depletion_fraction: float = 0.5,
        theta_fc: float = 0.32,
        theta_wp: float = 0.12,
        root_depth_m: float = 0.4,
    ) -> dict[str, Any]:
        """Generate irrigation recommendation.

        ``taw`` now defaults to 80 mm, the value FAO-56 gives for a
        medium-textured soil with a 0.4 m rooting depth. It previously
        defaulted to 50 mm, which understated the plant-available water and,
        combined with the old depletion formula, removed the soil moisture
        term from the result almost entirely.
        """
        kc = self.kc_from_lai(lai)
        ks = self.ks_water_stress(
            soil_moisture,
            depletion_fraction,
            taw,
            theta_fc=theta_fc,
            theta_wp=theta_wp,
            root_depth_m=root_depth_m,
        )
        etc = et0 * kc * ks

        p_eff = self.effective_rainfall(rainfall_forecast_mm)
        irri_net = np.maximum(0, etc - p_eff)
        irri_gross = irri_net / irrigation_efficiency
        irri_m3_ha = irri_gross * 10  # mm to m³/ha

        # Days until the soil is drawn down to the depletion threshold.
        # Two problems with the previous form: it used the raw `taw` argument
        # rather than the TAW the soil parameters imply, and dividing by
        # `et0 + 1e-6` returned 25000000 days at et0 = 0, which is a number
        # no farmer can act on. A zero demand means the field needs no
        # irrigation, which is not the same as needing it very rarely.
        effective_taw = 1000.0 * (theta_fc - theta_wp) * root_depth_m
        depletion_window = depletion_fraction * (
            effective_taw if effective_taw > 0 else max(float(taw), 1e-6)
        )
        if et0 <= 0:
            days = 0
        else:
            days = max(1, int(depletion_window / et0))

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
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.2,
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
