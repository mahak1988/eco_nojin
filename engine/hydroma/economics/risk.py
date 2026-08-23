"""
Economic Engine - Financial Risk Assessment Module.

Evaluates potential financial risks associated with projects.
"""
from typing import Dict, Any, List
import numpy as np
from scipy.stats import norm


def assess_market_price_risk(
    base_price: float,
    volatility: float, # Standard deviation of price changes (e.g., 0.15 for 15%)
    time_horizon_years: int,
    confidence_level: float = 0.05 # e.g., 0.05 for 5% VaR (95% confidence)
) -> Dict[str, Any]:
    """
    Assesses risk due to market price fluctuations using Value at Risk (VaR).

    Args:
        base_price: Current or expected average price.
        volatility: Historical or estimated price volatility (standard deviation).
        time_horizon_years: Time period for the risk assessment.
        confidence_level: Confidence level for VaR calculation (alpha).

    Returns:
        Dictionary containing risk metrics (e.g., VaR).
    """
    # Adjust volatility for the time horizon: sigma_T = sigma * sqrt(T)
    adjusted_volatility = volatility * np.sqrt(time_horizon_years)

    # Calculate VaR: VaR = base_price * Z_alpha * sigma_T
    # Where Z_alpha is the inverse CDF of the standard normal distribution
    z_score = norm.ppf(confidence_level) # e.g., norm.ppf(0.05) ~ -1.645
    var_absolute = base_price * abs(z_score) * adjusted_volatility
    var_percentage = (var_absolute / base_price) * 100

    # Expected worst case price
    worst_case_price = base_price + (z_score * adjusted_volatility)

    return {
        "risk_type": "market_price_fluctuation",
        "base_price_irr": base_price,
        "volatility_fraction": volatility,
        "time_horizon_years": time_horizon_years,
        "confidence_level": confidence_level,
        "value_at_risk_irr": var_absolute,
        "value_at_risk_percentage": var_percentage,
        "expected_worst_case_price_irr": worst_case_price,
        "notes": f"There is a {(confidence_level*100):.0f}% chance the price could drop by at least {var_absolute:.0f} IRR within {time_horizon_years} years."
    }


def assess_yield_risk(
    expected_yield: float,
    yield_std_dev: float, # Standard deviation of yield
    area_hectares: float,
    price_per_unit: float,
    confidence_level: float = 0.05
) -> Dict[str, Any]:
    """
    Assesses risk due to yield variability.

    Args:
        expected_yield: Expected yield per unit area.
        yield_std_dev: Standard deviation of yield.
        area_hectares: Cultivated area.
        price_per_unit: Price per unit of yield.
        confidence_level: Confidence level for VaR calculation.

    Returns:
        Dictionary containing yield-related risk metrics.
    """
    total_expected_revenue = expected_yield * area_hectares * price_per_unit
    total_yield_std_dev = yield_std_dev * area_hectares
    total_revenue_std_dev = total_yield_std_dev * price_per_unit

    z_score = norm.ppf(confidence_level)
    var_revenue = abs(z_score) * total_revenue_std_dev

    worst_case_yield = expected_yield + (z_score * yield_std_dev)
    worst_case_revenue = max(0, worst_case_yield * area_hectares * price_per_unit)

    return {
        "risk_type": "yield_variability",
        "expected_yield_per_ha": expected_yield,
        "yield_std_dev_per_ha": yield_std_dev,
        "area_hectares": area_hectares,
        "price_per_unit_irr": price_per_unit,
        "expected_total_revenue_irr": total_expected_revenue,
        "value_at_risk_revenue_irr": var_revenue,
        "expected_worst_case_yield_per_ha": worst_case_yield,
        "expected_worst_case_revenue_irr": worst_case_revenue,
        "notes": f"There is a {(confidence_level*100):.0f}% chance revenue could drop by at least {var_revenue:.0f} IRR due to yield variability."
    }


def assess_combined_project_risk(
    revenue_streams_with_risks: List[Dict[str, Any]],
    cost_streams_with_risks: List[Dict[str, Any]],
    correlation_matrix: np.ndarray = None # Correlation between different risks
) -> Dict[str, Any]:
    """
    Performs a basic aggregation of different risks to estimate overall project risk.

    Args:
        revenue_streams_with_risks: List of revenue risks (e.g., from assess_market_price_risk).
        cost_streams_with_risks: List of cost risks (similar structure, to be implemented).
        correlation_matrix: Matrix defining correlations between risk factors.

    Returns:
        Dictionary containing an overview of combined risks.
    """
    # This is a simplified aggregation. A full Monte Carlo simulation would be more robust.
    # For now, we just summarize the individual risks identified.

    total_revenue_var = sum(stream.get("value_at_risk_revenue_irr", stream.get("value_at_risk_irr", 0)) for stream in revenue_streams_with_risks)
    # Similar logic would apply for costs if cost risks were provided.

    # Placeholder for a combined metric (e.g., Net Revenue VaR)
    combined_risk_summary = {
        "total_identified_revenue_var_irr": total_revenue_var,
        "number_of_revenue_risks_assessed": len(revenue_streams_with_risks),
        "number_of_cost_risks_assessed": len(cost_streams_with_risks),
        "individual_risk_summaries": {
            "revenue_risks": [r for r in revenue_streams_with_risks],
            "cost_risks": [c for c in cost_streams_with_risks]
        },
        "notes": "This is a basic aggregation. A Monte Carlo simulation considering correlations would provide a more accurate combined risk assessment."
    }

    return combined_risk_summary