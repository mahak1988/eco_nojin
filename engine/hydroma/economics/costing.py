"""
Economic Engine - Costing Module.

Calculates various types of costs associated with land management,
agriculture, infrastructure, and biofertilizer application.
"""
from typing import Dict, Any, List
from dataclasses import dataclass
import math


@dataclass
class CostComponent:
    """Represents a single cost item."""
    name: str
    category: str  # e.g., 'labor', 'materials', 'equipment', 'land_rent', 'biofertilizer'
    type: str      # e.g., 'fixed', 'variable', 'one_time', 'annual'
    amount: float  # Cost in local currency
    quantity: float = 1.0
    unit: str = "unit"
    description: str = ""


def calculate_agricultural_cost(
    area_hectares: float,
    crop_type: str,
    labor_hours_per_hectare: float,
    labor_cost_per_hour: float,
    seed_cost_per_hectare: float,
    fertilizer_cost_per_hectare: float, # Includes chemical and biofertilizer
    machinery_cost_per_hectare: float,
    land_rent_per_hectare: float = 0.0,
    other_variable_costs_per_hectare: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates total agricultural production costs.

    Args:
        area_hectares: Cultivated area.
        crop_type: Type of crop.
        labor_hours_per_hectare: Labor hours required per hectare.
        labor_cost_per_hour: Cost per labor hour.
        seed_cost_per_hectare: Seed cost per hectare.
        fertilizer_cost_per_hectare: Fertilizer cost per hectare.
        machinery_cost_per_hectare: Machinery cost per hectare.
        land_rent_per_hectare: Rent cost per hectare (optional).
        other_variable_costs_per_hectare: Other variable costs per hectare (optional).

    Returns:
        Dictionary containing breakdown of costs.
    """
    labor_cost = area_hectares * labor_hours_per_hectare * labor_cost_per_hour
    seed_cost = area_hectares * seed_cost_per_hectare
    fert_cost = area_hectares * fertilizer_cost_per_hectare
    mach_cost = area_hectares * machinery_cost_per_hectare
    rent_cost = area_hectares * land_rent_per_hectare
    other_cost = area_hectares * other_variable_costs_per_hectare

    total_variable_cost = labor_cost + seed_cost + fert_cost + mach_cost + other_cost
    total_fixed_cost = rent_cost
    total_cost = total_variable_cost + total_fixed_cost

    cost_breakdown = [
        CostComponent("Labor", "labor", "variable", labor_cost, area_hectares * labor_hours_per_hectare, "hours", "Human labor"),
        CostComponent("Seed", "materials", "variable", seed_cost, area_hectares, "hectares", f"Seeds for {crop_type}"),
        CostComponent("Fertilizer", "materials", "variable", fert_cost, area_hectares, "hectares", "Chemical and biofertilizer"),
        CostComponent("Machinery", "equipment", "variable", mach_cost, area_hectares, "hectares", "Fuel, maintenance, depreciation"),
        CostComponent("Land Rent", "land", "fixed", rent_cost, area_hectares, "hectares", "Annual rent"),
        CostComponent("Other Variable", "misc", "variable", other_cost, area_hectares, "hectares", "Pesticides, insurance, etc."),
    ]

    return {
        "total_cost_irr": total_cost,
        "total_variable_cost_irr": total_variable_cost,
        "total_fixed_cost_irr": total_fixed_cost,
        "cost_per_hectare_irr": total_cost / area_hectares if area_hectares > 0 else 0,
        "breakdown": [{"name": c.name, "category": c.category, "amount_irr": c.amount, "description": c.description} for c in cost_breakdown]
    }


def calculate_infrastructure_cost(
    structure_type: str,
    design_calculation_output: Dict[str, Any], # Output from e.g., draining.py, channels.py
    material_specifications: Dict[str, Any], # Material types, densities, costs
    labor_complexity_factor: float = 1.0, # Multiplier for complex structures
) -> Dict[str, Any]:
    """
    Calculates cost for engineering structures.

    Args:
        structure_type: Type of structure (e.g., 'drain', 'channel', 'weir').
        design_calculation_output: Output from the corresponding design module.
        material_specifications: Pricing data for materials.
        labor_complexity_factor: Factor to account for labor difficulty.

    Returns:
        Dictionary containing estimated costs.
    """
    # Example calculation for a trapezoidal channel from design output
    if structure_type == "channel" and design_calculation_output.get("shape") == "trapezoidal":
        length = design_calculation_output.get("length_m", 0)
        excavation_vol = design_calculation_output.get("excavation_volume_per_meter", 0) * length
        concrete_vol = design_calculation_output.get("lining_volume_m3", 0) # If lined
        rebar_mass = design_calculation_output.get("rebar_mass_kg", 0) # If reinforced

        # Get material costs from specifications
        cost_excavation = excavation_vol * material_specifications.get("excavation_cost_per_m3", 0)
        cost_concrete = concrete_vol * material_specifications.get("concrete_cost_per_m3", 0)
        cost_rebar = rebar_mass * material_specifications.get("rebar_cost_per_kg", 0)

        # Estimate labor based on complexity and volume
        labor_hours_excavation = excavation_vol * material_specifications.get("labor_hours_per_m3_excavation", 0.1)
        labor_hours_concrete = concrete_vol * material_specifications.get("labor_hours_per_m3_concrete", 0.5)
        total_labor_hours = (labor_hours_excavation + labor_hours_concrete) * labor_complexity_factor
        labor_cost = total_labor_hours * material_specifications.get("labor_cost_per_hour", 10000)

        total_material_cost = cost_excavation + cost_concrete + cost_rebar
        total_cost = total_material_cost + labor_cost

        return {
            "structure_type": structure_type,
            "estimated_total_cost_irr": total_cost,
            "material_cost_irr": total_material_cost,
            "labor_cost_irr": labor_cost,
            "breakdown": {
                "excavation_m3": excavation_vol,
                "excavation_cost_irr": cost_excavation,
                "concrete_m3": concrete_vol,
                "concrete_cost_irr": cost_concrete,
                "rebar_kg": rebar_mass,
                "rebar_cost_irr": cost_rebar,
                "labor_hours": total_labor_hours,
                "labor_cost_irr": labor_cost,
            }
        }

    # Add logic for other structure types (drain, weir, etc.)
    return {"error": f"Cost calculation not implemented for structure type: {structure_type}"}


def calculate_biofertilizer_cost(
    formulation_id: str,
    area_hectares: float,
    dosage_kg_per_ha: float,
    unit_cost_per_kg: float,
    application_method: str = "broadcast"
) -> Dict[str, Any]:
    """
    Calculates cost for biofertilizer application.

    Args:
        formulation_id: ID of the biofertilizer formulation.
        area_hectares: Area to be treated.
        dosage_kg_per_ha: Application rate.
        unit_cost_per_kg: Cost per kilogram of the formulation.
        application_method: Method of application (affects labor cost).

    Returns:
        Dictionary containing cost details.
    """
    total_quantity_kg = area_hectares * dosage_kg_per_ha
    product_cost = total_quantity_kg * unit_cost_per_kg

    # Estimate application labor cost based on method and area
    labor_cost_per_ha = {
        "broadcast": 50000,
        "band_placement": 75000,
        "seed_treatment": 25000
    }.get(application_method, 50000)

    labor_cost = area_hectares * labor_cost_per_ha
    total_cost = product_cost + labor_cost

    return {
        "formulation_id": formulation_id,
        "total_quantity_kg": total_quantity_kg,
        "product_cost_irr": product_cost,
        "application_labor_cost_irr": labor_cost,
        "total_cost_irr": total_cost,
        "cost_per_hectare_irr": total_cost / area_hectares if area_hectares > 0 else 0,
    }
