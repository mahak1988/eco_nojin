"""
Economic Engine - Revenue Module.

Calculates various types of revenue streams including agricultural yield,
carbon credits, and other ecosystem services.
"""
from typing import Dict, Any, List
from datetime import date


def calculate_agricultural_revenue(
    area_hectares: float,
    yield_ton_per_ha: float,
    market_price_per_ton: float,
    quality_factor: float = 1.0, # Premium for high quality produce
    market_access_factor: float = 1.0 # Discount for poor access
) -> Dict[str, Any]:
    """
    Calculates revenue from agricultural produce sales.

    Args:
        area_hectares: Cultivated area.
        yield_ton_per_ha: Yield per hectare.
        market_price_per_ton: Base price per ton.
        quality_factor: Multiplier for quality (e.g., 1.1 for 10% premium).
        market_access_factor: Multiplier for market access (e.g., 0.9 for 10% discount).

    Returns:
        Dictionary containing revenue details.
    """
    total_yield_ton = area_hectares * yield_ton_per_ha
    base_revenue = total_yield_ton * market_price_per_ton
    adjusted_revenue = base_revenue * quality_factor * market_access_factor

    return {
        "category": "agricultural",
        "type": "produce_sales",
        "total_yield_ton": total_yield_ton,
        "market_price_per_ton_irr": market_price_per_ton,
        "quality_factor": quality_factor,
        "market_access_factor": market_access_factor,
        "base_revenue_irr": base_revenue,
        "adjusted_revenue_irr": adjusted_revenue,
        "revenue_per_hectare_irr": adjusted_revenue / area_hectares if area_hectares > 0 else 0
    }


def calculate_carbon_credit_revenue(
    carbon_sequestered_tonnes: float,
    carbon_price_per_tonne: float,
    verification_factor: float = 1.0 # Reduction due to verification/crediting rules
) -> Dict[str, Any]:
    """
    Calculates revenue from selling carbon credits.

    Args:
        carbon_sequestered_tonnes: Amount of CO2 equivalent sequestered.
        carbon_price_per_tonne: Price per tonne of CO2 equivalent.
        verification_factor: Fraction of sequestered C credited (e.g., 0.8 for 80%).

    Returns:
        Dictionary containing carbon credit revenue details.
    """
    credited_tonnes = carbon_sequestered_tonnes * verification_factor
    revenue = credited_tonnes * carbon_price_per_tonne

    return {
        "category": "environmental",
        "type": "carbon_credits",
        "carbon_sequestered_tonnes_co2e": carbon_sequestered_tonnes,
        "verification_factor": verification_factor,
        "credited_tonnes_co2e": credited_tonnes,
        "carbon_price_per_tonne_irr": carbon_price_per_tonne,
        "revenue_irr": revenue
    }


def calculate_ecosystem_service_revenue(
    service_type: str,
    service_value_per_unit: float,
    service_units_provided: float,
    sustainability_premium: float = 0.0 # Additional value for certified sustainable practices
) -> Dict[str, Any]:
    """
    Calculates revenue from other ecosystem services (e.g., pollination, water filtration).

    Args:
        service_type: Type of service (e.g., 'pollination', 'water_filtration').
        service_value_per_unit: Economic value per unit of service.
        service_units_provided: Quantity of service units provided.
        sustainability_premium: Additional multiplier for sustainable practices.

    Returns:
        Dictionary containing ecosystem service revenue details.
    """
    base_revenue = service_units_provided * service_value_per_unit
    adjusted_revenue = base_revenue * (1 + sustainability_premium)

    return {
        "category": "environmental",
        "type": service_type,
        "service_units_provided": service_units_provided,
        "service_value_per_unit_irr": service_value_per_unit,
        "sustainability_premium_fraction": sustainability_premium,
        "base_revenue_irr": base_revenue,
        "adjusted_revenue_irr": adjusted_revenue
    }


def aggregate_revenue_streams(revenue_streams: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates multiple revenue streams into a total.

    Args:
        revenue_streams: List of individual revenue dictionaries.

    Returns:
        Dictionary containing aggregated revenue and breakdown.
    """
    total_revenue = 0.0
    breakdown = {}
    categories = {}

    for stream in revenue_streams:
        rev_amount = stream.get("adjusted_revenue_irr", stream.get("revenue_irr", 0))
        total_revenue += rev_amount

        # Breakdown by type
        stream_type = stream.get("type", "unknown")
        if stream_type not in breakdown:
            breakdown[stream_type] = 0.0
        breakdown[stream_type] += rev_amount

        # Breakdown by category
        cat = stream.get("category", "other")
        if cat not in categories:
            categories[cat] = 0.0
        categories[cat] += rev_amount

    return {
        "total_revenue_irr": total_revenue,
        "revenue_breakdown_by_type": breakdown,
        "revenue_breakdown_by_category": categories,
        "number_of_streams": len(revenue_streams)
    }