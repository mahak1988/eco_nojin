"""ECSI — EcoNojin Carbon Sequestration Index.

Single source of truth
----------------------
The carbon maths is delegated to the canonical in-house RothC port
(``engine.hydroma.simulation.runners.rothc_runner``): temperature modifier,
first-order exponential decay, the clay-dependent CO2 / (BIO+HUM) partition
and the IOM estimator. This module owns only the *annual, input-light*
interface used by the model hub / dashboard, so there is exactly one
implementation of RothC-derived carbon dynamics in the engine.

Honesty notes
-------------
* ``moisture_factor`` here is a rainfall/evaporation proxy (the canonical RothC
  moisture modifier needs a soil-moisture deficit, which this annual interface
  does not receive). It is reported explicitly via ``moisture_model`` so a
  caller can never mistake it for the RothC SMD modifier. Use
  ``rothc_runner.run_rothc`` directly when SMD is available.
* Reference: Coleman & Jenkinson (1996) for the rate constants, modifiers and
  partition. Validation anchor: the Rothamsted Broadbalk steady state
  (see ``engine/hydroma/models/validation/reference_data.py``).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from engine.hydroma.simulation.runners.rothc_runner import (
    BIO_FRAC,
    HUM_FRAC,
    RATES,
    initial_pools,
    stabilization_split,
    temp_factor,
    water_factor,
)
from .base import ScientificModel, ValidationResult


class ECSI(ScientificModel):
    """EcoNojin Carbon Sequestration Index (RothC-26.3 carbon maths)."""

    name = "ECSI"
    version = "2.0.0"
    description = "Annual soil-carbon dynamics using the canonical RothC-26.3 kernel"

    REFERENCES = {
        "Coleman1996": "Coleman, K. & Jenkinson, D.S. (1996). RothC-26.3 - A model for the turnover of carbon in soil.",
    }

    #: Canonical RothC-26.3 pool decomposition rates (yr^-1).
    POOLS = dict(RATES)

    def validate_inputs(
        self,
        initial_soc,
        carbon_input,
        t_mean,
        rainfall,
        evaporation,
        clay_fraction,
        land_use,
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
        """RothC-26.3 temperature rate modifier (canonical implementation)."""
        return float(temp_factor(t_mean_c))

    @staticmethod
    def moisture_factor(
        rainfall_mm: float, evaporation_mm: float, clay_fraction: float = 0.23
    ) -> float:
        """Rainfall/evaporation moisture proxy (NOT the RothC SMD modifier).

        Kept for the annual interface; the result is clipped to [0, 1] and
        reported alongside ``moisture_model`` in the payload.
        """
        if evaporation_mm <= 0:
            return 1.0
        ratio = rainfall_mm / evaporation_mm
        return float(np.clip(ratio * (1 - clay_fraction), 0.0, 1.0))

    @staticmethod
    def plant_retain_factor(land_use: str) -> float:
        """RothC plant-retainment factor P by land use."""
        factors = {
            "arable": 0.6,
            "grassland": 1.0,
            "forest": 1.0,
            "bare": 0.0,
            "orchard": 1.0,
            "wetland": 1.0,
        }
        return factors.get(land_use, 0.6)

    @staticmethod
    def co2_bio_hum_ratio(clay_fraction: float) -> float:
        """CO2/(BIO+HUM) ratio for a clay fraction (canonical RothC relation)."""
        co2_fraction, stabilized_fraction = stabilization_split(clay_fraction * 100.0)
        return co2_fraction / stabilized_fraction

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
        smd_mm: float | None = None,
        max_smd_mm: float = 100.0,
    ) -> dict[str, Any]:
        """Compute annual SOC change with the canonical RothC kernel.

        Moisture: when ``smd_mm`` is supplied the canonical RothC soil-moisture
        deficit modifier is used (preferred, and required to reproduce
        RothC-26.3 reference behaviour). When it is ``None`` the documented
        rainfall/evaporation proxy is used and clearly labelled in
        ``moisture_model``.

        The annual carbon input is spread evenly over the year and the standard
        RothC first-order, exponential, monthly-step scheme is applied, then the
        result is scaled to ``dt_years``.
        """
        ok, errors = self.validate_inputs(
            initial_soc_t_ha,
            carbon_input_t_ha,
            t_mean_c,
            rainfall_mm,
            evaporation_mm,
            clay_fraction,
            land_use,
        )
        if not ok:
            raise ValueError("; ".join(errors))

        clay_pct = clay_fraction * 100.0
        f_T = self.temperature_factor(t_mean_c)
        if smd_mm is None:
            f_M = self.moisture_factor(rainfall_mm, evaporation_mm, clay_fraction)
            moisture_model = "rainfall_evaporation_proxy"
        else:
            f_M = float(water_factor(smd_mm, max_smd_mm))
            moisture_model = "rothc_smd_modifier"
        f_P = self.plant_retain_factor(land_use)

        pools, iom = initial_pools(initial_soc_t_ha)
        co2_fraction, stab_fraction = stabilization_split(clay_pct)

        input_m = carbon_input_t_ha / 12.0
        total_decomposition = 0.0
        months = max(1, int(round(12 * max(dt_years, 1e-9))))
        for _ in range(months):
            rate = {p: RATES[p] / 12.0 * f_T * f_M * f_P for p in pools}
            decomposed = {p: pools[p] * (1.0 - np.exp(-rate[p])) for p in pools}
            stabilized = sum(decomposed[p] * stab_fraction for p in pools)
            total_decomposition += sum(decomposed.values())
            pools["DPM"] = pools["DPM"] - decomposed["DPM"] + input_m * 0.59
            pools["RPM"] = pools["RPM"] - decomposed["RPM"] + input_m * 0.41
            pools["BIO"] = pools["BIO"] - decomposed["BIO"] + stabilized * BIO_FRAC
            pools["HUM"] = pools["HUM"] - decomposed["HUM"] + stabilized * HUM_FRAC

        final_soc = sum(pools.values()) + iom
        delta_soc = (final_soc - initial_soc_t_ha) / dt_years
        co2_eq = delta_soc * 3.667

        return {
            "delta_soc_t_ha_yr": float(delta_soc),
            "co2_eq_t_ha_yr": float(co2_eq),
            "final_soc_t_ha": float(final_soc),
            "temperature_factor": f_T,
            "moisture_factor": f_M,
            "plant_retain_factor": f_P,
            "total_decomposition_t_ha": float(total_decomposition),
            "co2_fraction": float(co2_fraction),
            "stabilized_fraction": float(stab_fraction),
            "moisture_model": moisture_model,
            "kernel": "rothc_runner (Coleman & Jenkinson 1996)",
        }

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.3,
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
