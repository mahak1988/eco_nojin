"""Climate change scenarios based on CMIP6 SSP pathways.

Implements simplified regional climate projections for:
- SSP1-2.6: Sustainability pathway (best case)
- SSP2-4.5: Middle of the road
- SSP5-8.5: Fossil-fueled development (worst case)

Reference: IPCC AR6, Chapter 4 (Future Climate)
"""

from dataclasses import dataclass


@dataclass
class ClimateProjection:
    """Climate projection for a specific scenario and time horizon."""

    scenario: str
    time_horizon: int  # Year
    delta_temp: float  # °C change from baseline
    delta_precip: float  # % change from baseline
    delta_et0: float  # % change in reference evapotranspiration
    confidence: str  # low, medium, high
    description: str


# Simplified regional projections (Middle East / Iran region)
# Based on IPCC AR6 Table 4.2 and CMIP6 multi-model means
CLIMATE_PROJECTIONS: dict[str, dict[int, tuple[float, float]]] = {
    # SSP1-2.6: Low emissions
    "SSP1-2.6": {
        2030: (1.2, -3.0),  # +1.2°C, -3% precipitation
        2050: (1.8, -5.0),  # +1.8°C, -5% precipitation
        2100: (2.2, -8.0),  # +2.2°C, -8% precipitation
    },
    # SSP2-4.5: Medium emissions
    "SSP2-4.5": {
        2030: (1.4, -4.0),
        2050: (2.4, -8.0),
        2100: (3.5, -15.0),
    },
    # SSP5-8.5: High emissions
    "SSP5-8.5": {
        2030: (1.6, -5.0),
        2050: (3.2, -12.0),
        2100: (5.2, -25.0),
    },
}


def get_climate_projection(
    scenario: str,
    time_horizon: int,
    baseline_temp: float = 18.0,
    baseline_precip: float = 300.0,
    baseline_et0: float = 1500.0,
) -> ClimateProjection:
    """Get climate projection for a specific scenario and year.

    Args:
        scenario: SSP scenario name (SSP1-2.6, SSP2-4.5, SSP5-8.5)
        time_horizon: Target year (2030, 2050, 2100)
        baseline_temp: Baseline mean annual temperature [°C]
        baseline_precip: Baseline annual precipitation [mm]
        baseline_et0: Baseline annual ET0 [mm]

    Returns:
        ClimateProjection with projected changes

    Raises:
        ValueError: If scenario or time_horizon is invalid
    """
    if scenario not in CLIMATE_PROJECTIONS:
        raise ValueError(
            f"Unknown scenario: {scenario}. Available: {list(CLIMATE_PROJECTIONS.keys())}"
        )

    projections = CLIMATE_PROJECTIONS[scenario]

    # Find closest time horizon
    available_years = sorted(projections.keys())
    closest_year = min(available_years, key=lambda y: abs(y - time_horizon))

    delta_temp, delta_precip = projections[closest_year]

    # ET0 increases approximately 2-3% per °C warming (Penman-Monteith sensitivity)
    delta_et0 = delta_temp * 2.5

    # Confidence based on time horizon and scenario
    if time_horizon <= 2030:
        confidence = "high"
    elif time_horizon <= 2050:
        confidence = "medium"
    else:
        confidence = "low" if scenario == "SSP5-8.5" else "medium"

    description = (
        f"Under {scenario}, by {closest_year}: "
        f"temperature +{delta_temp:.1f}°C, "
        f"precipitation {delta_precip:+.0f}%, "
        f"ET0 {delta_et0:+.0f}%"
    )

    return ClimateProjection(
        scenario=scenario,
        time_horizon=closest_year,
        delta_temp=delta_temp,
        delta_precip=delta_precip,
        delta_et0=delta_et0,
        confidence=confidence,
        description=description,
    )


def compare_scenarios(
    time_horizon: int,
    baseline_temp: float = 18.0,
    baseline_precip: float = 300.0,
) -> dict[str, ClimateProjection]:
    """Compare all SSP scenarios for a given time horizon.

    Returns dictionary with all three scenarios.
    """
    return {
        scenario: get_climate_projection(scenario, time_horizon, baseline_temp, baseline_precip)
        for scenario in CLIMATE_PROJECTIONS
    }


def apply_climate_change(
    baseline_temp: float,
    baseline_precip: float,
    baseline_et0: float,
    projection: ClimateProjection,
) -> dict[str, float]:
    """Apply climate projection to baseline values.

    Returns projected absolute values.
    """
    projected_temp = baseline_temp + projection.delta_temp
    projected_precip = baseline_precip * (1 + projection.delta_precip / 100)
    projected_et0 = baseline_et0 * (1 + projection.delta_et0 / 100)

    return {
        "temperature": round(projected_temp, 1),
        "precipitation": round(projected_precip, 0),
        "et0": round(projected_et0, 0),
        "water_balance_change": round(projected_precip - projected_et0, 0),
    }
