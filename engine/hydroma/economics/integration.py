"""
Economic Engine - Integration Module.

Connects economic calculations with outputs from other modules like agriculture,
infrastructure, and carbon.
"""
from typing import Dict, Any, List
from datetime import date
from .costing import calculate_agricultural_cost, calculate_infrastructure_cost, calculate_biofertilizer_cost
from .revenue import calculate_agricultural_revenue, calculate_carbon_credit_revenue, aggregate_revenue_streams
from .roi import calculate_agricultural_roi
from .risk import assess_market_price_risk, assess_yield_risk
from .employment import estimate_direct_employment


def calculate_agricultural_project_economics(
    land_profile_data: Dict[str, Any],
    crop_advisor_output: Dict[str, Any],
    biofertilizer_output: Dict[str, Any],
    market_data: Dict[str, Any],
    costing_params: Dict[str, Any],
    roi_params: Dict[str, Any],
    risk_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates comprehensive economics for an agricultural project based on inputs from
    land profile, crop advisor, biofertilizer recommender, and market data.

    Args:
        land_profile_data: Data from land profile analysis.
        crop_advisor_output: Output from crop advisor motor.
        biofertilizer_output: Output from biofertilizer motor.
        market_data: Current market prices, volatilities.
        costing_params: Parameters for cost calculation.
        roi_params: Parameters for ROI calculation.
        risk_params: Parameters for risk assessment.

    Returns:
        Dictionary containing full economic analysis.
    """
    # Extract key data
    area_ha = land_profile_data.get("area_hectares", 0)
    top_crop_rec = crop_advisor_output["top_recommendations"][0] if crop_advisor_output["top_recommendations"] else {}
    crop_type = top_crop_rec.get("name_en", "wheat")
    expected_yield_ton_per_ha = top_crop_rec.get("yield_t_ha", 3.0)
    bio_rec = biofertilizer_output["recommendations"][0] if biofertilizer_output["recommendations"] else {}
    bio_dosage_kg_per_ha = bio_rec.get("dosage_kg_ha", 5.0)

    # --- Costing ---
    print("Calculating costs...")
    agr_cost_details = calculate_agricultural_cost(
        area_hectares=area_ha,
        crop_type=crop_type,
        labor_hours_per_hectare=costing_params.get("labor_hours_per_ha", 50),
        labor_cost_per_hour=costing_params.get("labor_cost_per_hour_irr", 20000),
        seed_cost_per_hectare=costing_params.get("seed_cost_per_ha_irr", 500000),
        fertilizer_cost_per_hectare=costing_params.get("chem_fert_cost_per_ha_irr", 300000) + (bio_dosage_kg_per_ha * costing_params.get("bio_fert_cost_per_kg_irr", 1000)),
        machinery_cost_per_hectare=costing_params.get("mach_cost_per_ha_irr", 200000),
        land_rent_per_hectare=costing_params.get("rent_cost_per_ha_irr", 0),
    )

    # Biofertilizer specific cost
    bio_cost_details = calculate_biofertilizer_cost(
        formulation_id=bio_rec.get("name", "Generic_BioFert"),
        area_hectares=area_ha,
        dosage_kg_per_ha=bio_dosage_kg_per_ha,
        unit_cost_per_kg=costing_params.get("bio_fert_cost_per_kg_irr", 1000),
        application_method=bio_rec.get("application_method", "broadcast")
    )

    total_production_cost_irr = agr_cost_details["total_cost_irr"]

    # --- Revenue ---
    print("Calculating revenues...")
    agr_rev_details = calculate_agricultural_revenue(
        area_hectares=area_ha,
        yield_ton_per_ha=expected_yield_ton_per_ha,
        market_price_per_ton=market_data.get("commodity_price_per_ton_irr", 2000000),
        quality_factor=1.05, # Assuming slight premium for good practices
        market_access_factor=0.95 # Assuming slight discount for remote area
    )

    # Example: Assume biofert increases yield by 10%
    improved_yield = expected_yield_ton_per_ha * 1.10
    agr_rev_with_bio_details = calculate_agricultural_revenue(
        area_hectares=area_ha,
        yield_ton_per_ha=improved_yield,
        market_price_per_ton=market_data.get("commodity_price_per_ton_irr", 2000000),
        quality_factor=1.05,
        market_access_factor=0.95
    )

    # Aggregate revenue streams
    revenue_streams = [agr_rev_with_bio_details]
    # Add carbon revenue if available (requires carbon module output)
    # carbon_revenue = calculate_carbon_credit_revenue(...)
    # revenue_streams.append(carbon_revenue)

    aggregated_revenue = aggregate_revenue_streams(revenue_streams)
    total_revenue_irr = aggregated_revenue["total_revenue_irr"]

    # --- ROI ---
    print("Calculating ROI...")
    roi_details = calculate_agricultural_roi(
        area_hectares=area_ha,
        yield_ton_per_ha=improved_yield, # Use improved yield
        market_price_per_ton=market_data.get("commodity_price_per_ton_irr", 2000000),
        total_production_cost_irr=total_production_cost_irr / area_ha, # Cost per ha
        discount_rate=roi_params.get("discount_rate", 0.08),
        years_operation=roi_params.get("projection_years", 10),
        initial_land_prep_cost_irr=costing_params.get("initial_prep_cost_irr", 500000 * area_ha)
    )

    # --- Risk ---
    print("Assessing risks...")
    market_risk = assess_market_price_risk(
        base_price=market_data.get("commodity_price_per_ton_irr", 2000000),
        volatility=risk_params.get("price_volatility", 0.15),
        time_horizon_years=roi_params.get("projection_years", 10),
        confidence_level=0.05
    )
    yield_risk = assess_yield_risk(
        expected_yield=expected_yield_ton_per_ha,
        yield_std_dev=risk_params.get("yield_std_dev", 0.3),
        area_hectares=area_ha,
        price_per_unit=market_data.get("commodity_price_per_ton_irr", 2000000),
        confidence_level=0.05
    )

    # --- Employment (Direct only for this example) ---
    print("Estimating employment...")
    employment = estimate_direct_employment(
        activity_type="cultivation",
        scale_of_activity=area_ha,
        employment_intensity_per_unit=costing_params.get("labor_hours_per_ha", 50) / 2000, # Convert hours to FTE (assuming 2000 work hours/year)
        job_type="seasonal",
        duration_months=6 # Cultivation cycle
    )

    return {
        "project_summary": {
            "area_hectares": area_ha,
            "crop_type": crop_type,
            "expected_yield_ton_per_ha": expected_yield_ton_per_ha,
            "improved_yield_ton_per_ha_with_biofert": improved_yield
        },
        "costing": {
            "agricultural_cost": agr_cost_details,
            "biofertilizer_cost": bio_cost_details,
            "total_production_cost_irr": total_production_cost_irr
        },
        "revenue": {
            "agricultural_revenue_without_biofert": agr_rev_details,
            "agricultural_revenue_with_biofert": agr_rev_with_bio_details,
            "aggregated_revenue": aggregated_revenue,
            "total_revenue_irr": total_revenue_irr
        },
        "roi": roi_details,
        "risk_assessment": {
            "market_price_risk": market_risk,
            "yield_risk": yield_risk
        },
        "employment_impact": employment,
        "analysis_date": date.today().isoformat()
    }


def calculate_infrastructure_project_economics(
    structure_design_output: Dict[str, Any],
    costing_params: Dict[str, Any],
    roi_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates economics for an engineering structure project.

    Args:
        structure_design_output: Output from an infrastructure design module.
        costing_params: Parameters for cost calculation.
        roi_params: Parameters for ROI calculation.

    Returns:
        Dictionary containing economic analysis for the structure.
    """
    # Extract design data (example for a channel)
    structure_type = structure_design_output.get("type", "channel")
    design_calc_output = structure_design_output.get("design_calculation", {})
    material_specs = costing_params.get("material_specifications", {})

    # --- Costing ---
    infra_cost_details = calculate_infrastructure_cost(
        structure_type=structure_type,
        design_calculation_output=design_calc_output,
        material_specifications=material_specs,
        labor_complexity_factor=costing_params.get("labor_complexity_factor", 1.0)
    )

    initial_investment = infra_cost_details["estimated_total_cost_irr"]

    # --- Revenue / Benefit (Harder to quantify, often done separately) ---
    # This could include avoided damages, increased productivity, etc.
    # For now, let's assume a hypothetical annual benefit based on cost savings or increased yield
    annual_benefit_irr = costing_params.get("estimated_annual_benefit_irr", initial_investment * 0.1) # 10% of investment as benefit
    project_lifetime = roi_params.get("project_lifetime_years", 20)

    # Create a simple cash flow: -Initial_Investment, then +Annual_Benefit for N years
    cash_flows = [annual_benefit_irr] * project_lifetime

    # --- ROI ---
    roi_details = calculate_financial_metrics(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        discount_rate=roi_params.get("discount_rate", 0.08),
        project_lifetime_years=project_lifetime,
        salvage_value=0.0
    )

    return {
        "structure_summary": {
            "type": structure_type,
            "design_output": design_calc_output
        },
        "costing": infra_cost_details,
        "initial_investment_irr": initial_investment,
        "estimated_annual_benefit_irr": annual_benefit_irr,
        "roi": roi_details,
        "analysis_date": date.today().isoformat()
    }