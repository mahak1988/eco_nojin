"""
Soil Salinity Analysis.

Implements salinity classification and management recommendations.

References:
    [1] USDA, "Diagnosis and Improvement of Saline and Alkali Soils",
        Agriculture Handbook 60, 1954
    [2] Rhoades, J.D., et al., "Using Soil Salinity to Improve Crop Production",
        2000
"""
import logging

logger = logging.getLogger(__name__)

# Salinity classification thresholds (EC in dS/m)
SALINITY_CLASSES = {
    'non_saline': {'max_ec': 2, 'description': 'No salinity problem'},
    'slightly_saline': {'max_ec': 4, 'description': 'Yield of sensitive crops may be affected'},
    'moderately_saline': {'max_ec': 8, 'description': 'Yield of many crops is restricted'},
    'strongly_saline': {'max_ec': 16, 'description': 'Only tolerant crops yield satisfactorily'},
    'very_strongly_saline': {'max_ec': float('inf'), 'description': 'Only very tolerant crops yield'}
}


def classify_salinity(ec: float) -> dict:
    """Classify soil salinity based on electrical conductivity.
    
    Args:
        ec: Electrical conductivity (dS/m)
        
    Returns:
        Dict: Salinity classification and interpretation
        
    Example:
        >>> result = classify_salinity(6.5)
        >>> print(result['classification'])
        'moderately_saline'
        
    References:
        [1] USDA Handbook 60, 1954
    """
    if ec < 0:
        raise ValueError("EC cannot be negative")

    # Determine classification
    for class_name, thresholds in SALINITY_CLASSES.items():
        if ec < thresholds['max_ec']:
            classification = class_name
            description = thresholds['description']
            break

    # Crop tolerance recommendations
    crop_recommendations = _get_crop_recommendations(classification)

    # Management recommendations
    management = _get_management_recommendations(classification, ec)

    return {
        'ec': ec,
        'unit': 'dS/m',
        'classification': classification,
        'description': description,
        'crop_recommendations': crop_recommendations,
        'management': management
    }


def _get_crop_recommendations(classification: str) -> dict:
    """Get crop recommendations based on salinity."""
    recommendations = {
        'non_saline': {
            'suitable_crops': ['Most crops', 'Sensitive vegetables', 'Fruits'],
            'limitation': 'None'
        },
        'slightly_saline': {
            'suitable_crops': ['Wheat', 'Corn', 'Tomato', 'Lettuce'],
            'avoid': ['Very sensitive crops', 'Strawberry'],
            'limitation': 'Sensitive crops may show reduced yield'
        },
        'moderately_saline': {
            'suitable_crops': ['Barley', 'Cotton', 'Sugar beet', 'Date palm'],
            'avoid': ['Sensitive vegetables', 'Most fruits'],
            'limitation': 'Only moderately tolerant crops'
        },
        'strongly_saline': {
            'suitable_crops': ['Barley', 'Cotton', 'Sugar beet', 'Some grasses'],
            'avoid': ['Most field crops', 'Vegetables'],
            'limitation': 'Severe limitation'
        },
        'very_strongly_saline': {
            'suitable_crops': ['Salt-tolerant grasses', 'Some halophytes'],
            'avoid': ['All conventional crops'],
            'limitation': 'Extreme limitation'
        }
    }

    return recommendations.get(classification, recommendations['non_saline'])


def _get_management_recommendations(classification: str, ec: float) -> dict:
    """Get management recommendations based on salinity."""
    if classification == 'non_saline':
        return {
            'action': 'no_action_needed',
            'description': 'Maintain current practices',
            'monitoring': 'Regular EC monitoring'
        }

    elif classification == 'slightly_saline':
        return {
            'action': 'monitor_and_manage',
            'description': 'Monitor EC and adjust irrigation',
            'practices': [
                'Ensure good drainage',
                'Use quality irrigation water',
                'Avoid over-irrigation'
            ]
        }

    elif classification == 'moderately_saline':
        return {
            'action': 'leaching_required',
            'description': 'Leaching may be needed',
            'practices': [
                'Apply excess irrigation for leaching',
                'Install or improve drainage',
                'Consider gypsum application if sodic'
            ]
        }

    else:
        return {
            'action': 'major_remediation',
            'description': 'Significant remediation required',
            'practices': [
                'Install subsurface drainage',
                'Heavy leaching applications',
                'Chemical amendments (gypsum)',
                'Consider salt-tolerant crops'
            ]
        }


def calculate_leaching_requirement(ec_soil: float, ec_water: float,
                                      target_ec: float | None = None) -> dict:
    """Calculate leaching requirement to reduce soil salinity.
    
    Formula (simplified):
        LR = EC_water / (EC_soil - EC_water)
        
    Args:
        ec_soil: Current soil EC (dS/m)
        ec_water: Irrigation water EC (dS/m)
        target_ec: Target soil EC (optional)
        
    Returns:
        Dict: Leaching requirement calculations
    """
    if ec_soil <= ec_water:
        return {
            'leaching_required': False,
            'reason': 'Soil EC is not higher than water EC'
        }

    if target_ec is None:
        target_ec = 4.0  # Target for most crops

    # Simplified leaching requirement
    if ec_soil <= target_ec:
        return {
            'leaching_required': False,
            'reason': f'Soil EC ({ec_soil}) is already below target ({target_ec})'
        }

    # Calculate leaching fraction
    # LR = ECw / (ECe - ECw) where ECe is target
    lr = ec_water / (target_ec - ec_water)

    # Limit to reasonable range
    lr = min(0.5, max(0.1, lr))

    return {
        'leaching_required': True,
        'leaching_fraction': round(lr, 3),
        'leaching_percentage': round(lr * 100, 1),
        'current_ec': ec_soil,
        'target_ec': target_ec,
        'water_ec': ec_water,
        'interpretation': f'Apply {lr*100:.1f}% extra water for leaching'
    }


def calculate_sodic_soil_amendment(esp: float, soil_depth: float,
                                      bulk_density: float) -> dict:
    """Calculate gypsum requirement for sodic soil amendment.
    
    Args:
        esp: Exchangeable Sodium Percentage
        soil_depth: Soil depth to amend (cm)
        bulk_density: Soil bulk density (g/cm³)
        
    Returns:
        Dict: Gypsum requirement calculations
    """
    if esp < 10:
        return {
            'gypsum_required': False,
            'reason': f'ESP ({esp}) is below amendment threshold (10)'
        }

    # Calculate gypsum requirement
    # Rule of thumb: 1 ton gypsum per 1000 m² per 5 ESP points above 10

    esp_excess = esp - 10
    gypsum_rate = esp_excess * 0.1  # tons per 100 m²

    # Scale for depth
    depth_factor = soil_depth / 15  # Reference depth 15 cm
    gypsum_rate *= depth_factor

    # Convert to kg/ha
    gypsum_kg_ha = gypsum_rate * 10000  # tons/100m² * 10000 = kg/ha

    return {
        'gypsum_required': True,
        'gypsum_rate': round(gypsum_rate, 2),
        'gypsum_unit': 'tons/100m²',
        'gypsum_kg_per_ha': round(gypsum_kg_ha, 0),
        'esp': esp,
        'soil_depth': soil_depth,
        'interpretation': f'Apply {gypsum_kg_ha:.0f} kg/ha of gypsum'
    }
