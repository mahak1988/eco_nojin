"""
ECSI — EcoNojin Carbon Sequestration Index

Based on RothC-26.3 model.
dC/dt = I - k × C × f(T) × f(M) × f(P)

Reference: Coleman & Jenkinson (1996)
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .base import ScientificModel, ValidationResult


class ECSI(ScientificModel):
    """EcoNojin Carbon Sequestration Index based on RothC"""

    name = "ECSI"
    version = "1.0.0"
    description = "Carbon Sequestration based on RothC-26.3"

    REFERENCES = {
        "Coleman1996": "Coleman, K. & Jenkinson, D.S. (1996). RothC-26.3 - A model for the turnover of carbon in soil.",
    }

    # RothC pool decomposition rates (per year)
    POOLS = {
        "DPM": 10.0,  # Decomposable Plant Material
        "RPM": 0.3,   # Resistant Plant Material
        "BIO": 0.66,  # Microbial Biomass
        "HUM": 0.02,  # Humified Organic Matter
        "IOM": 0.0,   # Inert Organic Matter
    }

    # Pool fractions in total SOC (typical for agricultural soils)
    POOL_FRACTIONS = {
        "DPM": 0.01,
        "RPM": 0.04,
        "BIO": 0.03,
        "HUM": 0.54,
        "IOM": 0.38,
    }

    def validate_inputs(
        self, initial_soc, carbon_input, t_mean, rainfall,
        evaporation, clay_fraction, land_use,
    ) -> tuple[bool, list[str]]:
        errors = []
        if initial_soc < 0 or initial_soc > 500:
            errors.append("Initial SOC out of range [0, 500] t/ha")
        if carbon_input < 0:
            errors.append("Carbon input must be non-negative")
        if not (-20 <= t_mean <= 40):
            errors.append("Temperature out of range")
        if rainfall < 0:
            errors.append("Rainfall must be non-negative")
        if evaporation < 0:
            errors.append("Evaporation must be non-negative")
        if not (0 <= clay_fraction <= 1):
            errors.append("Clay fraction must be in [0, 1]")
        return len(errors) == 0, errors

    @staticmethod
    def temperature_factor(t_mean_c: float) -> float:
        """RothC temperature rate modifier"""
        if t_mean_c <= -5.0:
            return 0.0
        return float(np.exp(0.047 * t_mean_c - 0.86))

    @staticmethod
    def moisture_factor(rainfall_mm: float, evaporation_mm: float,
                        clay_fraction: float = 0.23) -> float:
        """RothC moisture rate modifier"""
        if evaporation_mm <= 0:
            return 1.0
        ratio = rainfall_mm / evaporation_mm
        return float(np.clip(ratio * (1 - clay_fraction), 0.0, 1.0))

    @staticmethod
    def plant_retain_factor(land_use: str) -> float:
        """Plant retain factor by land use"""
        factors = {
            "arable": 0.6, "grassland": 0.85, "forest": 0.95,
            "bare": 0.0, "orchard": 0.8, "wetland": 0.9,
        }
        return factors.get(land_use, 0.6)

    @staticmethod
    def co2_bio_hum_ratio(clay_fraction: float) -> float:
        """CO2/(BIO+HUM) ratio from clay content"""
        return 1.67 + 1.94 * clay_fraction

    def compute(
        self,
        initial_soc_t_ha: float,
        carbon_input_t_ha: float,
        t_mean_c: float,
        rainfall_mm: float,
        evaporation_mm: float,
        clay_fraction: float = 0.23,
        land_use: str = "arable",
        dt_years: float = 1.0,
    ) -> dict[str, Any]:
        """Compute annual SOC sequestration"""
        f_T = self.temperature_factor(t_mean_c)
        f_M = self.moisture_factor(rainfall_mm, evaporation_mm, clay_fraction)
        f_P = self.plant_retain_factor(land_use)

        # Pool-specific decomposition
        pool_soc = {
            pool: initial_soc_t_ha * self.POOL_FRACTIONS[pool]
            for pool in self.POOLS
        }

        total_decomposition = sum(
            self.POOLS[pool] * pool_soc[pool] * f_T * f_M * f_P
            for pool in self.POOLS if pool != "IOM"
        ) * dt_years

        delta_soc = carbon_input_t_ha * dt_years - total_decomposition
        co2_eq = delta_soc * 44 / 12

        return {
            "delta_soc_t_ha_yr": delta_soc,
            "co2_eq_t_ha_yr": co2_eq,
            "final_soc_t_ha": initial_soc_t_ha + delta_soc,
            "temperature_factor": f_T,
            "moisture_factor": f_M,
            "plant_retain_factor": f_P,
            "total_decomposition_t_ha": total_decomposition,
        }

    def validate_against_reference(
        self, inputs: dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.3,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = result["delta_soc_t_ha_yr"]

        relative_error = abs(computed_value - reference_output) / (abs(reference_output) + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ΔSOC (t/ha/yr)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
