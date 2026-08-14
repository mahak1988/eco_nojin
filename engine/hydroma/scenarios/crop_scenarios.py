"""Crop yield scenarios using simplified AquaCrop approach.

Implements water-limited yield potential based on:
- FAO AquaCrop principles (Steduto et al., 2009)
- Water productivity concept
- Crop coefficient adjustments for climate change

Reference: Steduto, P. et al. (2009). "AquaCrop - The FAO crop model
to simulate yield. Water productivity."
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class CropParameters:
    """Crop-specific parameters for yield simulation."""
    name: str
    water_productivity: float  # kg/m³ (yield per unit water)
    crop_coefficient_max: float  # Maximum Kc
    growing_season_days: int
    base_temp: float  # Base temperature for growth [°C]
    optimal_temp: float  # Optimal temperature [°C]
    max_temp: float  # Maximum temperature for growth [°C]
    drought_sensitivity: float  # 0-1 (1 = very sensitive)
    price_per_kg: float  # Market price [USD/kg]


# Crop database (simplified from FAO AquaCrop)
CROP_DATABASE = {
    "wheat": CropParameters(
        name="Wheat",
        water_productivity=1.2,
        crop_coefficient_max=1.1,
        growing_season_days=180,
        base_temp=0.0,
        optimal_temp=20.0,
        max_temp=35.0,
        drought_sensitivity=0.6,
        price_per_kg=0.25,
    ),
    "barley": CropParameters(
        name="Barley",
        water_productivity=1.0,
        crop_coefficient_max=1.0,
        growing_season_days=150,
        base_temp=0.0,
        optimal_temp=18.0,
        max_temp=32.0,
        drought_sensitivity=0.5,
        price_per_kg=0.20,
    ),
    "corn": CropParameters(
        name="Corn (Maize)",
        water_productivity=1.8,
        crop_coefficient_max=1.2,
        growing_season_days=140,
        base_temp=8.0,
        optimal_temp=25.0,
        max_temp=38.0,
        drought_sensitivity=0.7,
        price_per_kg=0.18,
    ),
    "millet": CropParameters(
        name="Millet",
        water_productivity=0.8,
        crop_coefficient_max=0.9,
        growing_season_days=100,
        base_temp=10.0,
        optimal_temp=28.0,
        max_temp=42.0,
        drought_sensitivity=0.2,  # Very drought tolerant
        price_per_kg=0.30,
    ),
    "sorghum": CropParameters(
        name="Sorghum",
        water_productivity=1.0,
        crop_coefficient_max=1.0,
        growing_season_days=120,
        base_temp=10.0,
        optimal_temp=27.0,
        max_temp=40.0,
        drought_sensitivity=0.3,
        price_per_kg=0.22,
    ),
    "chickpea": CropParameters(
        name="Chickpea",
        water_productivity=0.9,
        crop_coefficient_max=1.0,
        growing_season_days=120,
        base_temp=5.0,
        optimal_temp=22.0,
        max_temp=35.0,
        drought_sensitivity=0.5,
        price_per_kg=0.80,
    ),
    "safflower": CropParameters(
        name="Safflower",
        water_productivity=0.6,
        crop_coefficient_max=0.9,
        growing_season_days=150,
        base_temp=5.0,
        optimal_temp=24.0,
        max_temp=38.0,
        drought_sensitivity=0.3,
        price_per_kg=1.50,
    ),
    "medicinal_herbs": CropParameters(
        name="Medicinal Herbs (Thyme/Sage)",
        water_productivity=0.4,
        crop_coefficient_max=0.8,
        growing_season_days=200,
        base_temp=5.0,
        optimal_temp=22.0,
        max_temp=35.0,
        drought_sensitivity=0.2,
        price_per_kg=8.00,  # High value
    ),
}


def simulate_crop_yield(
    crop_type: str,
    available_water: float,
    mean_temp: float,
    growing_season_precip: float = 0.0,
    irrigation_efficiency: float = 0.6,
    co2_concentration: float = 420.0,
) -> dict:
    """Simulate water-limited crop yield.
    
    Args:
        crop_type: Crop name from CROP_DATABASE
        available_water: Total available water [mm] (precip + irrigation)
        mean_temp: Mean growing season temperature [°C]
        growing_season_precip: Precipitation during growing season [mm]
        irrigation_efficiency: Irrigation system efficiency [0-1]
        co2_concentration: Atmospheric CO2 [ppm]
    
    Returns:
        Yield simulation results dictionary
    """
    if crop_type not in CROP_DATABASE:
        raise ValueError(f"Unknown crop: {crop_type}. "
                        f"Available: {list(CROP_DATABASE.keys())}")
    
    crop = CROP_DATABASE[crop_type]
    
    # Temperature stress factor
    if mean_temp < crop.base_temp:
        temp_factor = 0.0
    elif mean_temp <= crop.optimal_temp:
        temp_factor = (mean_temp - crop.base_temp) / (crop.optimal_temp - crop.base_temp)
    elif mean_temp <= crop.max_temp:
        temp_factor = 1.0 - 0.5 * (mean_temp - crop.optimal_temp) / (crop.max_temp - crop.optimal_temp)
    else:
        temp_factor = max(0, 0.5 - (mean_temp - crop.max_temp) / 10)
    
    # Water stress factor
    crop_water_requirement = crop.crop_coefficient_max * crop.growing_season_days * 3.0  # ~3mm/day ET0
    
    if available_water >= crop_water_requirement:
        water_factor = 1.0
    else:
        water_deficit_ratio = available_water / crop_water_requirement
        water_factor = 1.0 - crop.drought_sensitivity * (1.0 - water_deficit_ratio)
        water_factor = max(0, water_factor)
    
    # CO2 fertilization effect (approximately +5% yield per 100ppm above 400)
    co2_factor = 1.0 + 0.05 * (co2_concentration - 400) / 100
    co2_factor = min(co2_factor, 1.3)  # Cap at 30% increase
    
    # Potential yield (water productivity × transpiration)
    actual_transpiration = min(available_water, crop_water_requirement) * irrigation_efficiency
    potential_yield = crop.water_productivity * actual_transpiration
    
    # Apply stress factors
    actual_yield = potential_yield * temp_factor * water_factor * co2_factor
    
    # Economic value
    gross_revenue = actual_yield * crop.price_per_kg
    
    # Water productivity of the system
    system_wp = actual_yield / available_water if available_water > 0 else 0
    
    return {
        "crop": crop.name,
        "potential_yield_kg_ha": round(potential_yield * 10, 0),  # Convert to kg/ha
        "actual_yield_kg_ha": round(actual_yield * 10, 0),
        "yield_reduction_pct": round((1 - actual_yield / max(potential_yield, 0.01)) * 100, 1),
        "water_requirement_mm": round(crop_water_requirement, 0),
        "water_stress_factor": round(water_factor, 2),
        "temp_stress_factor": round(temp_factor, 2),
        "co2_fertilization": round(co2_factor, 2),
        "gross_revenue_usd_ha": round(gross_revenue * 10, 0),
        "system_water_productivity": round(system_wp, 2),
    }


def compare_crops(
    available_water: float,
    mean_temp: float,
    co2_concentration: float = 420.0,
) -> dict:
    """Compare all crops for given conditions.
    
    Returns ranking by economic value.
    """
    results = {}
    
    for crop_type in CROP_DATABASE:
        try:
            result = simulate_crop_yield(
                crop_type=crop_type,
                available_water=available_water,
                mean_temp=mean_temp,
                co2_concentration=co2_concentration,
            )
            results[crop_type] = result
        except Exception:
            continue
    
    # Sort by gross revenue
    ranked = sorted(
        results.items(),
        key=lambda x: x[1]["gross_revenue_usd_ha"],
        reverse=True
    )
    
    return {
        "ranking": [r[0] for r in ranked],
        "details": results,
        "best_economic_choice": ranked[0][0] if ranked else None,
        "most_drought_tolerant": min(
            results.items(),
            key=lambda x: x[1]["water_stress_factor"] * -1
        )[0] if results else None,
    }
