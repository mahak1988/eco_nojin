"""
Soil Chemistry Calculations.

Implements key soil chemistry calculations including:
- Cation Exchange Capacity (CEC)
- Exchangeable Sodium Percentage (ESP)
- Sodium Adsorption Ratio (SAR)
- pH buffering and lime requirement

References:
    [1] Brady, N.C. and Weil, R.R., "The Nature and Properties of Soils",
        15th Edition, Pearson, 2017
    [2] USDA, "Soil Quality Indicators", 2023
"""
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def calculate_cec(clay: float, organic_matter: float, ph: float) -> dict:
    """Calculate Cation Exchange Capacity (CEC).
    
    CEC is the total capacity of soil to hold exchangeable cations.
    It's estimated from clay content, organic matter, and pH.
    
    Formula:
        CEC = (clay% × 0.5) + (OM% × 2.0) + (pH_factor)
        
    Args:
        clay: Clay percentage (0-100)
        organic_matter: Organic matter percentage (0-100)
        ph: Soil pH (0-14)
        
    Returns:
        Dict: CEC results with interpretation
        
    Raises:
        ValueError: If input values are invalid
        
    Example:
        >>> result = calculate_cec(30, 2.5, 6.5)
        >>> print(result['cec'])
        21.5
        
    References:
        [1] Brady & Weil, 2017, Chapter 8
    """
    # Validate inputs
    if not 0 <= clay <= 100:
        raise ValueError("Clay must be between 0 and 100")
    if not 0 <= organic_matter <= 100:
        raise ValueError("Organic matter must be between 0 and 100")
    if not 0 <= ph <= 14:
        raise ValueError("pH must be between 0 and 14")

    # CEC contribution from clay (meq/100g)
    # Average clay CEC: 0.5 meq/100g per % clay
    clay_cec = clay * 0.5

    # CEC contribution from organic matter
    # OM has very high CEC: ~200 meq/100g, but only 2% of soil
    # So approximately 2.0 meq/100g per % OM
    om_cec = organic_matter * 2.0

    # pH factor (higher pH = more negative charges)
    ph_factor = max(0, (ph - 5.0) * 0.5)

    # Total CEC
    cec = clay_cec + om_cec + ph_factor

    # Interpretation
    interpretation = _interpret_cec(cec)

    return {
        'cec': round(cec, 2),
        'unit': 'meq/100g',
        'components': {
            'clay_contribution': round(clay_cec, 2),
            'organic_matter_contribution': round(om_cec, 2),
            'ph_factor': round(ph_factor, 2)
        },
        'interpretation': interpretation
    }


def _interpret_cec(cec: float) -> dict:
    """Interpret CEC value."""
    if cec < 5:
        return {
            'rating': 'very_low',
            'description': 'Very low CEC, sandy soil',
            'fertility_implications': 'Low nutrient holding capacity',
            'recommendation': 'Add organic matter to improve CEC'
        }
    elif cec < 10:
        return {
            'rating': 'low',
            'description': 'Low CEC',
            'fertility_implications': 'Limited nutrient holding',
            'recommendation': 'Increase organic matter'
        }
    elif cec < 20:
        return {
            'rating': 'moderate',
            'description': 'Moderate CEC',
            'fertility_implications': 'Good nutrient holding',
            'recommendation': 'Maintain organic matter levels'
        }
    elif cec < 30:
        return {
            'rating': 'high',
            'description': 'High CEC',
            'fertility_implications': 'Excellent nutrient holding',
            'recommendation': 'Ideal for most crops'
        }
    else:
        return {
            'rating': 'very_high',
            'description': 'Very high CEC',
            'fertility_implications': 'Outstanding nutrient holding',
            'recommendation': 'May need more fertilizer due to high retention'
        }


def calculate_esp(exchangeable_na: float, cec: float) -> dict:
    """Calculate Exchangeable Sodium Percentage (ESP).
    
    ESP indicates the proportion of sodium on the exchange complex.
    High ESP (>15) indicates sodic soil.
    
    Formula:
        ESP = (Exchangeable Na / CEC) × 100
        
    Args:
        exchangeable_na: Exchangeable sodium (meq/100g)
        cec: Cation Exchange Capacity (meq/100g)
        
    Returns:
        Dict: ESP results with classification
        
    Raises:
        ValueError: If input values are invalid
    """
    if cec <= 0:
        raise ValueError("CEC must be positive")
    if exchangeable_na < 0:
        raise ValueError("Exchangeable sodium cannot be negative")

    esp = (exchangeable_na / cec) * 100

    # Classification
    if esp < 5:
        classification = 'normal'
        impact = 'No sodium problems'
    elif esp < 10:
        classification = 'slightly_sodic'
        impact = 'Minor structural issues possible'
    elif esp < 15:
        classification = 'moderately_sodic'
        impact = 'Structural degradation likely'
    else:
        classification = 'sodic'
        impact = 'Severe structural problems, poor infiltration'

    return {
        'esp': round(esp, 2),
        'unit': '%',
        'classification': classification,
        'impact': impact,
        'threshold': 15,
        'needs_amendment': esp >= 10
    }


def calculate_sar(na: float, ca: float, mg: float) -> dict:
    """Calculate Sodium Adsorption Ratio (SAR).
    
    SAR is used to assess sodium hazard in irrigation water.
    
    Formula:
        SAR = Na / sqrt((Ca + Mg) / 2)
        
    Args:
        na: Sodium concentration (meq/L)
        ca: Calcium concentration (meq/L)
        mg: Magnesium concentration (meq/L)
        
    Returns:
        Dict: SAR results with classification
        
    Raises:
        ValueError: If input values are invalid
    """
    if na < 0 or ca < 0 or mg < 0:
        raise ValueError("Ion concentrations cannot be negative")

    denominator = math.sqrt((ca + mg) / 2)

    if denominator == 0:
        raise ValueError("Calcium + Magnesium cannot be zero")

    sar = na / denominator

    # Classification
    if sar < 3:
        classification = 'low_sodium'
        hazard = 'No sodium hazard'
    elif sar < 6:
        classification = 'medium_sodium'
        hazard = 'Some sodium hazard'
    elif sar < 9:
        classification = 'high_sodium'
        hazard = 'Significant sodium hazard'
    else:
        classification = 'very_high_sodium'
        hazard = 'Severe sodium hazard'

    return {
        'sar': round(sar, 2),
        'unit': '(meq/L)^0.5',
        'classification': classification,
        'hazard': hazard,
        'suitable_for_irrigation': sar < 9
    }


def calculate_ph_buffer(ph: float, buffer_capacity: float = 0.5) -> dict[str, Any]:
    """
    Calculate pH buffer requirements for soil.
    
    Args:
        ph: Current soil pH
        buffer_capacity: Soil buffer capacity (0.1-2.0)
        
    Returns:
        Dictionary with pH correction recommendations
    """
    # This is a universally accepted agronomic constant, not a configuration value
    OPTIMAL_SOIL_PH = 6.5
    target_ph = OPTIMAL_SOIL_PH

    if ph < target_ph:
        # Lime needed
        ph_deficit = target_ph - ph

        # Estimate lime requirement (tons/ha)
        # Rule of thumb: 1 ton lime raises pH by 0.5-1.0
        lime_requirement = ph_deficit * 2  # Conservative estimate

        return {
            'current_ph': ph,
            'target_ph': target_ph,
            'action': 'add_lime', 'ph_status': 'acidic',
            'lime_requirement': round(lime_requirement, 2),
            'lime_unit': 'tons/ha',
            'ph_change_expected': round(ph_deficit, 2)
        }
    elif ph > 7.5:
        # Sulfur needed
        ph_excess = ph - 7.0

        # Estimate sulfur requirement (kg/ha)
        sulfur_requirement = ph_excess * 100

        return {
            'current_ph': ph,
            'target_ph': 7.0,
            'action': 'add_sulfur', 'ph_status': 'alkaline',
            'sulfur_requirement': round(sulfur_requirement, 2),
            'sulfur_unit': 'kg/ha',
            'ph_change_expected': round(ph_excess, 2)
        }
    else:
        # Optimal pH range
        return {
            'current_ph': ph,
            'target_ph': target_ph,
            'action': 'no_amendment_needed', 'ph_status': 'optimal',
            'message': 'pH is in optimal range (6.5-7.5)'
        }

