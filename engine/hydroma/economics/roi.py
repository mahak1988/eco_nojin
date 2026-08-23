"""
Economic Engine - Return on Investment (ROI) Module.

Calculates financial performance indicators like NPV, IRR, ROI, Payback Period.
"""
from typing import Dict, Any, List
import numpy as np
from scipy.optimize import newton
from datetime import date


def calculate_financial_metrics(
    initial_investment: float,
    cash_flows: List[float], # Cash flows for years 1, 2, ..., n
    discount_rate: float,
    project_lifetime_years: int,
    salvage_value: float = 0.0
) -> Dict[str, Any]:
    """
    Calculates NPV, IRR, ROI, and Payback Period.

    Args:
        initial_investment: Upfront cost (positive value).
        cash_flows: List of net cash flows (revenue - cost) for each year of operation.
        discount_rate: Discount rate for NPV calculation (e.g., 0.05 for 5%).
        project_lifetime_years: Total operational life of the project.
        salvage_value: Value recovered at the end of project life.

    Returns:
        Dictionary containing calculated financial metrics.
    """
    # Ensure cash flows list covers the full lifetime
    if len(cash_flows) < project_lifetime_years:
        cash_flows.extend([0] * (project_lifetime_years - len(cash_flows)))

    # Calculate NPV
    # NPV = -Initial_Investment + Sum(CF_t / (1+r)^t) for t=1 to n
    npv = -initial_investment
    for t, cf in enumerate(cash_flows, 1):
        npv += cf / ((1 + discount_rate) ** t)
    # Add salvage value
    npv += salvage_value / ((1 + discount_rate) ** project_lifetime_years)

    # Calculate IRR
    # IRR is the rate r where NPV(r) = 0
    # Use scipy.optimize.newton to find the root of the NPV function
    def npv_func(rate):
        if rate <= -1:
            return float('-inf') # Avoid division by zero or negative base
        npv_val = -initial_investment
        for t, cf in enumerate(cash_flows, 1):
            npv_val += cf / ((1 + rate) ** t)
        npv_val += salvage_value / ((1 + rate) ** project_lifetime_years)
        return npv_val

    # Provide an initial guess for IRR, often close to discount rate or slightly higher
    initial_guess = discount_rate + 0.01
    try:
        # Ensure the function changes sign around the initial guess
        # If not, IRR might not exist or be non-unique
        irr = newton(npv_func, initial_guess, maxiter=100, tol=1e-6)
        if irr <= -1:
            irr = None # IRR is not meaningful if <= -100%
    except (RuntimeError, ValueError):
        irr = None # Could not converge

    # Calculate simple ROI (Total Gain / Total Investment)
    total_gain = sum(cash_flows) + salvage_value - initial_investment
    roi_simple = (total_gain / initial_investment) * 100 if initial_investment > 0 else 0.0

    # Calculate Payback Period (Time to recover initial investment)
    cumulative_cash_flow = -initial_investment
    payback_period_years = project_lifetime_years + 1.0 # Default if not recovered
    for t, cf in enumerate(cash_flows, 1):
        cumulative_cash_flow += cf
        if cumulative_cash_flow >= 0:
            # Interpolate for exact payback period if needed
            # Payback = Year_before_recovery + (Remaining_amount / Cash_flow_that_year)
            remaining = initial_investment - (cumulative_cash_flow - cf)
            payback_period_years = t - 1 + (remaining / cf) if cf != 0 else t
            break

    return {
        "npv_irr": npv,
        "irr_fraction": irr,
        "irr_percentage": irr * 100 if irr is not None else None,
        "roi_simple_percentage": roi_simple,
        "payback_period_years": payback_period_years if payback_period_years <= project_lifetime_years else None,
        "initial_investment_irr": initial_investment,
        "total_cash_inflows_irr": sum(cash_flows) + salvage_value,
        "project_lifetime_years": project_lifetime_years,
        "salvage_value_irr": salvage_value
    }


def calculate_agricultural_roi(
    area_hectares: float,
    yield_ton_per_ha: float,
    market_price_per_ton: float,
    total_production_cost_irr: float,
    discount_rate: float,
    years_operation: int,
    initial_land_prep_cost_irr: float = 0.0,
    annual_operating_cost_multiplier: float = 1.0 # To account for cost changes over time
) -> Dict[str, Any]:
    """
    Calculates ROI specifically for an agricultural venture.

    Args:
        area_hectares: Cultivated area.
        yield_ton_per_ha: Expected yield per hectare per year.
        market_price_per_ton: Selling price per ton.
        total_production_cost_irr: Total cost per hectare per year.
        discount_rate: Discount rate.
        years_operation: Number of years to project.
        initial_land_prep_cost_irr: One-time cost at start.
        annual_operating_cost_multiplier: Multiplier for costs in future years (e.g., 1.02 for 2% annual increase).

    Returns:
        Dictionary containing agricultural-specific financial metrics.
    """
    total_yield_per_year = area_hectares * yield_ton_per_ha
    revenue_per_year = total_yield_per_year * market_price_per_ton
    cost_per_year = area_hectares * total_production_cost_irr

    initial_investment = initial_land_prep_cost_irr
    cash_flows = []
    for year in range(1, years_operation + 1):
        adjusted_cost = cost_per_year * (annual_operating_cost_multiplier ** (year - 1))
        net_cf = revenue_per_year - adjusted_cost
        cash_flows.append(net_cf)

    metrics = calculate_financial_metrics(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        discount_rate=discount_rate,
        project_lifetime_years=years_operation
    )

    # Add agricultural-specific details
    metrics.update({
        "area_hectares": area_hectares,
        "yield_ton_per_ha_per_year": yield_ton_per_ha,
        "total_yield_per_year_ton": total_yield_per_year,
        "market_price_per_ton_irr": market_price_per_ton,
        "revenue_per_year_irr": revenue_per_year,
        "cost_per_year_irr": cost_per_year,
        "gross_margin_per_year_irr": revenue_per_year - cost_per_year
    })

    return metrics