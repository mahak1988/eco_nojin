"""Monte Carlo uncertainty analysis for scenario projections.

Uses random sampling to quantify uncertainty in:
- Climate projections
- Crop yield predictions
- Economic outcomes
"""

import numpy as np


def monte_carlo_yield(
    crop_type: str,
    mean_water: float,
    water_std: float,
    mean_temp: float,
    temp_std: float,
    n_simulations: int = 1000,
    seed: int | None = None,
) -> dict:
    """Run Monte Carlo simulation for crop yield uncertainty.

    Args:
        crop_type: Crop to simulate
        mean_water: Mean available water [mm]
        water_std: Standard deviation of water [mm]
        mean_temp: Mean temperature [°C]
        temp_std: Standard deviation of temperature [°C]
        n_simulations: Number of Monte Carlo iterations
        seed: Random seed for reproducibility

    Returns:
        Statistics of yield distribution
    """
    if seed is not None:
        np.random.seed(seed)

    from .crop_scenarios import simulate_crop_yield

    yields = []

    for _ in range(n_simulations):
        # Sample water and temperature
        water = max(50, np.random.normal(mean_water, water_std))
        temp = np.random.normal(mean_temp, temp_std)

        try:
            result = simulate_crop_yield(
                crop_type=crop_type,
                available_water=water,
                mean_temp=temp,
            )
            yields.append(result["actual_yield_kg_ha"])
        except Exception:
            continue

    if not yields:
        return {"error": "All simulations failed"}

    yields = np.array(yields)

    return {
        "n_successful": len(yields),
        "n_simulations": n_simulations,
        "mean_yield_kg_ha": round(float(np.mean(yields)), 0),
        "std_yield_kg_ha": round(float(np.std(yields)), 0),
        "min_yield_kg_ha": round(float(np.min(yields)), 0),
        "max_yield_kg_ha": round(float(np.max(yields)), 0),
        "percentile_5": round(float(np.percentile(yields, 5)), 0),
        "percentile_25": round(float(np.percentile(yields, 25)), 0),
        "percentile_50": round(float(np.percentile(yields, 50)), 0),
        "percentile_75": round(float(np.percentile(yields, 75)), 0),
        "percentile_95": round(float(np.percentile(yields, 95)), 0),
        "probability_crop_failure": round(float(np.mean(yields < 500)), 3),  # <500 kg/ha
    }


def monte_carlo_climate(
    baseline_temp: float,
    baseline_precip: float,
    ssp_scenario: str,
    time_horizon: int,
    n_simulations: int = 500,
    seed: int | None = None,
) -> dict:
    """Run Monte Carlo on climate projections.

    Samples around the central projection to quantify uncertainty.
    """
    if seed is not None:
        np.random.seed(seed)

    from .climate_scenarios import get_climate_projection

    projection = get_climate_projection(ssp_scenario, time_horizon)

    temps = []
    precips = []

    # Uncertainty: ±0.5°C for 2030, ±1.5°C for 2100
    temp_uncertainty = 0.5 + (time_horizon - 2030) * 0.015
    precip_uncertainty = 5 + (time_horizon - 2030) * 0.2

    for _ in range(n_simulations):
        temp_change = np.random.normal(projection.delta_temp, temp_uncertainty)
        precip_change = np.random.normal(projection.delta_precip, precip_uncertainty)

        temps.append(baseline_temp + temp_change)
        precips.append(baseline_precip * (1 + precip_change / 100))

    return {
        "scenario": ssp_scenario,
        "time_horizon": time_horizon,
        "n_simulations": n_simulations,
        "temp_mean": round(float(np.mean(temps)), 1),
        "temp_std": round(float(np.std(temps)), 1),
        "temp_range": [round(float(np.min(temps)), 1), round(float(np.max(temps)), 1)],
        "precip_mean": round(float(np.mean(precips)), 0),
        "precip_std": round(float(np.std(precips)), 0),
        "precip_range": [round(float(np.min(precips)), 0), round(float(np.max(precips)), 0)],
        "probability_drying": round(float(np.mean(np.array(precips) < baseline_precip)), 3),
    }
