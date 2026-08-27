"""
ESRI — EcoNojin Salinity Risk Index

Spectral Salinity Index + soil EC + irrigation management.

Reference: Ayers & Westcot (1985) FAO-29, Richards (1954)
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .base import ScientificModel, ValidationResult


class ESRI(ScientificModel):
    """EcoNojin Salinity Risk Index"""

    name = "ESRI"
    version = "1.0.0"
    description = "Salinity Risk Index (spectral + soil + irrigation)"

    REFERENCES = {
        "Ayers1985": "Ayers, R.S. & Westcot, D.W. (1985). Water quality for agriculture. FAO Irrigation and Drainage Paper 29.",
        "Richards1954": "Richards, L.A. (1954). Diagnosis and improvement of saline and alkali soils.",
    }

    def validate_inputs(
        self, blue, red, nir, swir, ec_soil_dsm, ec_irrigation_dsm,
    ) -> tuple[bool, list[str]]:
        errors = []
        for band_name, band in [("blue", blue), ("red", red), ("nir", nir), ("swir", swir)]:
            if np.any(band < 0) or np.any(band > 1):
                errors.append(f"{band_name} band reflectance out of range [0, 1]")
        if ec_soil_dsm < 0 or ec_soil_dsm > 30:
            errors.append("Soil EC out of range [0, 30] dS/m")
        if ec_irrigation_dsm < 0 or ec_irrigation_dsm > 10:
            errors.append("Irrigation EC out of range [0, 10] dS/m")
        return len(errors) == 0, errors

    @staticmethod
    def salinity_index_s2(blue: np.ndarray, red: np.ndarray,
                          nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Sentinel-2 Salinity Index"""
        with np.errstate(divide="ignore", invalid="ignore"):
            numerator = np.sqrt(blue * red + 1e-9)
            ratio1 = nir / (swir + 1e-6)
            ratio2 = blue / (red + 1e-6)
            si = numerator / (ratio1 * ratio2 + 1e-6)
        return np.nan_to_num(si, nan=np.nan)

    @staticmethod
    def leaching_requirement(ec_w: float, ec_e: float) -> float:
        """FAO-32 Leaching Requirement"""
        if ec_w <= 0:
            return 0.0
        denominator = 5 * ec_e - ec_w
        if denominator <= 0:
            return 1.0
        return min(1.0, ec_w / denominator)

    def compute(
        self,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir: np.ndarray,
        ec_soil_dsm: float = 2.0,
        ec_irrigation_dsm: float = 0.5,
        actual_leaching_fraction: float = 0.2,
        weights: tuple[float, float, float] = (0.3, 0.5, 0.2),
    ) -> dict[str, Any]:
        """Compute ESRI"""
        alpha, beta, gamma = weights

        si = self.salinity_index_s2(blue, red, nir, swir)
        si_norm = np.clip(si / 10, 0, 1)

        ec_norm = np.clip(ec_soil_dsm / 16, 0, 1)

        lr_required = self.leaching_requirement(ec_irrigation_dsm, ec_soil_dsm)
        lr_deficit = np.clip(lr_required - actual_leaching_fraction, 0, 1)

        esri = alpha * si_norm + beta * ec_norm + gamma * lr_deficit

        return {
            "esri": np.clip(esri, 0, 1),
            "classification": self.classify(esri),
            "salinity_index": si,
            "ec_norm": ec_norm,
            "leaching_requirement": lr_required,
            "leaching_deficit": lr_deficit,
        }

    @staticmethod
    def classify(esri: np.ndarray) -> np.ndarray:
        """طبقه‌بندی ریسک شوری"""
        return np.select(
            [esri < 0.3, esri < 0.6, esri < 0.8],
            ["low", "moderate", "high"],
            default="severe"
        )

    def validate_against_reference(
        self, inputs: dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.15,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["esri"]))

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ESRI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
