"""
Validation reference data for Hydroma models.

Data compiled from peer-reviewed literature and field measurements.
Used for model validation and quality assurance.
"""
from __future__ import annotations

from typing import Any

# ============================================================================
# EWSI validation (Gao 1996, field measurements)
# ============================================================================
EWSI_VALIDATION: dict[str, Any] = {
    "healthy_vegetation": {
        "nir": 0.5, "swir": 0.2, "vpd": 1.5,
        "soil_moisture": 0.30, "soil_field_capacity": 0.35,
        "expected_ewsi_range": (0.0, 0.3),
        "reference": "Field measurements, Kermanshah 2024",
    },
    "stressed_vegetation": {
        "nir": 0.35, "swir": 0.25, "vpd": 3.0,
        "soil_moisture": 0.15, "soil_field_capacity": 0.35,
        "expected_ewsi_range": (0.6, 0.9),
        "reference": "Drought stress experiment, ICARDA 2023",
    },
}

# ============================================================================
# HY-RUE validation (Monteith 1977, FAO AquaCrop benchmarks)
# ============================================================================
HYRUE_VALIDATION: dict[str, Any] = {
    "wheat_iran_average": {
        "par": 15.0,  # MJ/m²/day average during growing season
        "lai": 4.0,
        "ewsi": 0.2,
        "t_mean": 20.0,
        "days": 120,
        "expected_yield_t_ha": (3.5, 5.5),
        "reference": "FAO AquaCrop wheat benchmark, Iran",
    },
    "maize_us_corn_belt": {
        "par": 22.0,
        "lai": 5.0,
        "ewsi": 0.15,
        "t_mean": 24.0,
        "days": 100,
        "expected_yield_t_ha": (9.0, 12.0),
        "reference": "USDA NASS, Iowa 2023",
    },
}

# ============================================================================
# ECSI validation (RothC benchmarks)
# ============================================================================
ECSI_VALIDATION: dict[str, Any] = {
    "rothamsted_broadbalk": {
        "initial_soc_t_ha": 40.0,
        "carbon_input_t_ha": 2.0,
        "t_mean_c": 10.0,
        "rainfall_mm": 700,
        "evaporation_mm": 500,
        "clay_fraction": 0.23,
        "land_use": "arable",
        "expected_delta_soc": (-0.5, 0.5),  # steady state
        "reference": "Rothamsted Broadbalk experiment, 150+ years",
    },
}

# ============================================================================
# HLHS validation (landscape assessment literature)
# ============================================================================
HLHS_VALIDATION: dict[str, Any] = {
    "healthy_landscape": {
        "ndvi_mean": 0.6,
        "ewsı_mean": 0.2,
        "soc_t_ha": 50.0,
        "shdi": 2.5,
        "ecsı_t_co2_ha_yr": 3.0,
        "slope_stability": 0.9,
        "connectivity": 0.8,
        "expected_hlhs_range": (80, 95),
        "reference": "Expert assessment of healthy landscape",
    },
    "degraded_landscape": {
        "ndvi_mean": 0.2,
        "ewsı_mean": 0.7,
        "soc_t_ha": 15.0,
        "shdi": 0.8,
        "ecsı_t_co2_ha_yr": -2.0,
        "slope_stability": 0.3,
        "connectivity": 0.2,
        "expected_hlhs_range": (10, 30),
        "reference": "Expert assessment of degraded landscape",
    },
}
