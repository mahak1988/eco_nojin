"""
EWSI — EcoNojin Water Stress Index

Multi-source fusion index combining:
- Sentinel-2 NDMI (optical)
- Atmospheric VPD (meteorological)
- Root zone soil moisture (pedological)

Reference: Gao (1996), Monteith (1993)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import ScientificModel, ValidationResult


@dataclass
class EWSIWeights:
    """وزن‌های مؤلفه‌های EWSI"""
    ndmi: float = 0.4
    vpd: float = 0.3
    soil: float = 0.3

    def __post_init__(self):
        total = self.ndmi + self.vpd + self.soil
        if abs(total - 1.0) > 1e-6:
            self.ndmi /= total
            self.vpd /= total
            self.soil /= total


class EWSI(ScientificModel):
    """EcoNojin Water Stress Index"""

    name = "EWSI"
    version = "1.0.0"
    description = "Multi-source Water Stress Index"

    REFERENCES = {
        "Gao1996": "Gao, B.C. (1996). NDWI - A normalized difference water index. Remote Sensing of Environment, 58(3), 257-266.",
        "Monteith1993": "Monteith, J.L. (1993). The exchange of water and carbon by crops in a semi-arid subtropical climate.",
    }

    # Valid ranges based on peer-reviewed literature
    NDMI_RANGE = (-1.0, 1.0)
    VPD_RANGE = (0.0, 10.0)  # kPa
    SOIL_MOISTURE_RANGE = (0.0, 0.6)  # m³/m³

    def __init__(self, weights: EWSIWeights = None, **config):
        super().__init__(**config)
        self.weights = weights or EWSIWeights()

    def validate_inputs(self, nir, swir, vpd, soil_moisture, soil_field_capacity) -> tuple[bool, list[str]]:
        errors = []

        # NDMI validation
        ndmi = (nir - swir) / (nir + swir + 1e-9)
        if np.any((ndmi < self.NDMI_RANGE[0]) | (ndmi > self.NDMI_RANGE[1])):
            errors.append(f"NDMI out of range {self.NDMI_RANGE}")

        # VPD validation
        if not (self.VPD_RANGE[0] <= vpd <= self.VPD_RANGE[1]):
            errors.append(f"VPD {vpd} out of range {self.VPD_RANGE}")

        # Soil moisture validation
        if not (self.SOIL_MOISTURE_RANGE[0] <= soil_moisture <= self.SOIL_MOISTURE_RANGE[1]):
            errors.append(f"Soil moisture {soil_moisture} out of range")

        if soil_moisture > soil_field_capacity * 1.1:
            errors.append("Soil moisture exceeds field capacity")

        return len(errors) == 0, errors

    @staticmethod
    def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Normalized Difference Moisture Index"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (nir - swir) / (nir + swir + 1e-9)
        return np.clip(np.nan_to_num(result, nan=np.nan), -1, 1)

    def compute(
        self,
        nir: np.ndarray,
        swir: np.ndarray,
        vpd: float,
        soil_moisture: float,
        soil_field_capacity: float,
    ) -> np.ndarray:
        """
        Compute EWSI
        
        Returns:
            numpy array in range [0, 1] where:
            - 0: no stress (optimal)
            - 1: severe stress
        """
        # Component 1: NDMI stress (inverted)
        ndmi_val = self.ndmi(nir, swir)
        ndmi_stress = np.clip(1 - ndmi_val, 0, 1)

        # Component 2: VPD stress (normalized)
        vpd_stress = np.clip((vpd - 0.5) / 3.5, 0, 1)

        # Component 3: Soil moisture stress
        soil_stress = np.clip(1 - (soil_moisture / soil_field_capacity), 0, 1)

        # Weighted fusion
        ewsı = (
            self.weights.ndmi * ndmi_stress +
            self.weights.vpd * vpd_stress +
            self.weights.soil * soil_stress
        )

        return np.clip(ewsı, 0, 1)

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.1,
    ) -> ValidationResult:
        computed = self.compute(**inputs)
        computed_value = float(np.mean(computed)) if isinstance(computed, np.ndarray) else float(computed)

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="EWSI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )

    @staticmethod
    def classify(ewsı: np.ndarray) -> np.ndarray:
        """طبقه‌بندی سطح تنش آبی"""
        return np.select(
            [ewsı < 0.3, ewsı < 0.6, ewsı < 0.8],
            ["optimal", "mild", "moderate"],
            default="severe"
        )
