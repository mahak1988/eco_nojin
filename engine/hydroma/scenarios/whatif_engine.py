"""What-If analysis engine for comparing alternative scenarios.

Allows users to compare:
- Different cropping patterns
- Irrigation methods
- Climate scenarios
- Soil amendment strategies
"""

from dataclasses import dataclass

from .climate_scenarios import apply_climate_change, get_climate_projection
from .crop_scenarios import simulate_crop_yield


@dataclass
class Scenario:
    """A single scenario definition."""

    name: str
    crop_type: str
    available_water: float  # mm
    mean_temp: float  # °C
    co2_concentration: float = 420.0  # ppm
    irrigation_efficiency: float = 0.6
    description: str = ""


def run_whatif_analysis(scenarios: list[Scenario]) -> dict:
    """Run what-if analysis comparing multiple scenarios.

    Args:
        scenarios: List of Scenario objects to compare

    Returns:
        Comparison results with rankings and recommendations
    """
    results = []

    for scenario in scenarios:
        yield_result = simulate_crop_yield(
            crop_type=scenario.crop_type,
            available_water=scenario.available_water,
            mean_temp=scenario.mean_temp,
            co2_concentration=scenario.co2_concentration,
            irrigation_efficiency=scenario.irrigation_efficiency,
        )

        results.append(
            {
                "scenario_name": scenario.name,
                "crop": scenario.crop_type,
                "description": scenario.description,
                "yield_kg_ha": yield_result["actual_yield_kg_ha"],
                "revenue_usd_ha": yield_result["gross_revenue_usd_ha"],
                "water_use_mm": scenario.available_water,
                "water_productivity": yield_result["system_water_productivity"],
                "yield_reduction_pct": yield_result["yield_reduction_pct"],
            }
        )

    # Rankings
    by_yield = sorted(results, key=lambda x: x["yield_kg_ha"], reverse=True)
    by_revenue = sorted(results, key=lambda x: x["revenue_usd_ha"], reverse=True)
    by_wp = sorted(results, key=lambda x: x["water_productivity"], reverse=True)

    return {
        "scenarios": results,
        "best_yield": by_yield[0]["scenario_name"] if by_yield else None,
        "best_revenue": by_revenue[0]["scenario_name"] if by_revenue else None,
        "best_water_productivity": by_wp[0]["scenario_name"] if by_wp else None,
        "n_scenarios": len(results),
    }


def generate_climate_transition_scenarios(
    baseline_water: float,
    baseline_temp: float,
    crop_type: str,
    ssp_scenario: str = "SSP2-4.5",
) -> dict:
    """Generate scenarios showing climate change impact over time.

    Creates scenarios for 2030, 2050, 2100 under specified SSP.
    """
    scenarios = []
    years = [2030, 2050, 2100]

    for year in years:
        projection = get_climate_projection(ssp_scenario, year)
        apply_climate_change(baseline_temp, 300.0, baseline_water, projection)

        # Adjust available water based on climate projection
        # Assume precipitation change affects available water
        adjusted_water = baseline_water * (1 + projection.delta_precip / 100)
        adjusted_temp = baseline_temp + projection.delta_temp
        adjusted_co2 = 420 + (year - 2025) * 2.5  # ~2.5 ppm/year increase

        scenario = Scenario(
            name=f"{ssp_scenario}_{year}",
            crop_type=crop_type,
            available_water=adjusted_water,
            mean_temp=adjusted_temp,
            co2_concentration=adjusted_co2,
            description=projection.description,
        )
        scenarios.append(scenario)

    return run_whatif_analysis(scenarios)
