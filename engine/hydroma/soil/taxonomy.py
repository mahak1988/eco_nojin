"""
USDA Soil Taxonomy Classification.

Implements USDA soil texture classification and taxonomy system.

References:
    [1] USDA, "Keys to Soil Taxonomy", 13th Edition, 2017
    [2] USDA NRCS, "Soil Texture Calculator", 2023
"""
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# USDA texture triangle boundaries
# Format: (clay_min, clay_max, silt_min, silt_max, sand_min, sand_max)
TEXTURE_CLASSES = {
    'clay': {'clay': (40, 100), 'silt': (0, 45), 'sand': (0, 45)},
    'silty_clay': {'clay': (40, 100), 'silt': (40, 100), 'sand': (0, 20)},
    'sandy_clay': {'clay': (35, 100), 'silt': (0, 20), 'sand': (45, 100)},
    'clay_loam': {'clay': (27, 40), 'silt': (20, 45), 'sand': (20, 45)},
    'silty_clay_loam': {'clay': (27, 40), 'silt': (40, 73), 'sand': (0, 20)},
    'sandy_clay_loam': {'clay': (20, 35), 'silt': (0, 20), 'sand': (45, 80)},
    'loam': {'clay': (7, 27), 'silt': (28, 50), 'sand': (23, 52)},
    'silt_loam': {'clay': (12, 27), 'silt': (50, 88), 'sand': (0, 23)},
    'silt': {'clay': (0, 12), 'silt': (80, 100), 'sand': (0, 20)},
    'sandy_loam': {'clay': (0, 20), 'silt': (0, 28), 'sand': (43, 85)},
    'loamy_sand': {'clay': (0, 15), 'silt': (0, 25), 'sand': (70, 90)},
    'sand': {'clay': (0, 10), 'silt': (0, 15), 'sand': (85, 100)},
}

# Soil taxonomy hierarchy
TAXONOMY_LEVELS = ['order', 'suborder', 'great_group', 'subgroup', 'family', 'series']

# Common soil orders
SOIL_ORDERS = {
    'alfisol': 'Alfisol',
    'andisol': 'Andisol',
    'aridisol': 'Aridisol',
    'entisol': 'Entisol',
    'gelisol': 'Gelisol',
    'histosol': 'Histosol',
    'inceptisol': 'Inceptisol',
    'mollisol': 'Mollisol',
    'oxisol': 'Oxisol',
    'spodosol': 'Spodosol',
    'ultisol': 'Ultisol',
    'vertisol': 'Vertisol',
}


def validate_percentages(clay: float, silt: float, sand: float) -> None:
    """Validate that soil percentages sum to 100.
    
    Args:
        clay: Clay percentage (0-100)
        silt: Silt percentage (0-100)
        sand: Sand percentage (0-100)
        
    Raises:
        ValueError: If percentages are invalid or don't sum to 100
    """
    if any(v < 0 or v > 100 for v in [clay, silt, sand]):
        raise ValueError("Soil percentages must be between 0 and 100")
    
    total = clay + silt + sand
    if abs(total - 100) > 1:  # Allow 1% tolerance
        raise ValueError(f"Soil percentages must sum to 100 (got {total})")


def classify_usda_texture(clay: float, silt: float, sand: float) -> Dict:
    """Classify soil texture according to USDA system.
    
    Args:
        clay: Clay percentage (0-100)
        silt: Silt percentage (0-100)
        sand: Sand percentage (0-100)
        
    Returns:
        Dict: Classification results including:
            - texture: USDA texture class
            - texture_details: Detailed breakdown
            - water_holding_capacity: Estimated capacity
            - permeability: Permeability class
            - erodibility: Erodibility factor
            
    Raises:
        ValueError: If input percentages are invalid
        
    Example:
        >>> result = classify_usda_texture(20, 40, 40)
        >>> print(result['texture'])
        'loam'
        
    References:
        [1] USDA, "Keys to Soil Taxonomy", 13th Edition, 2017
    """
    validate_percentages(clay, silt, sand)
    
    # Determine texture class
    texture = _determine_texture_class(clay, silt, sand)
    
    # Calculate derived properties
    properties = _calculate_texture_properties(texture, clay, silt, sand)
    
    result = {
        'texture': texture,
        'texture_details': {
            'clay_percent': clay,
            'silt_percent': silt,
            'sand_percent': sand
        },
        **properties
    }
    
    logger.info(f"Soil classified as {texture}")
    return result


def _determine_texture_class(clay: float, silt: float, sand: float) -> str:
    """Determine USDA texture class from percentages.
    
    Uses the USDA texture triangle to classify soil.
    
    Args:
        clay: Clay percentage
        silt: Silt percentage
        sand: Sand percentage
        
    Returns:
        str: USDA texture class name
    """
    # Check each texture class
    for texture, ranges in TEXTURE_CLASSES.items():
        clay_range = ranges['clay']
        silt_range = ranges['silt']
        sand_range = ranges['sand']
        
        if (clay_range[0] <= clay <= clay_range[1] and
            silt_range[0] <= silt <= silt_range[1] and
            sand_range[0] <= sand <= sand_range[1]):
            return texture
    
    # Default to loam if no match (shouldn't happen with valid input)
    return 'loam'


def _calculate_texture_properties(texture: str, clay: float, 
                                    silt: float, sand: float) -> Dict:
    """Calculate soil properties based on texture.
    
    Args:
        texture: USDA texture class
        clay: Clay percentage
        silt: Silt percentage
        sand: Sand percentage
        
    Returns:
        Dict: Calculated properties
    """
    # Water holding capacity (mm/m) - typical values by texture
    whc_values = {
        'sand': 80, 'loamy_sand': 100, 'sandy_loam': 130,
        'loam': 160, 'silt_loam': 180, 'silt': 200,
        'sandy_clay_loam': 170, 'clay_loam': 190,
        'silty_clay_loam': 210, 'sandy_clay': 180,
        'silty_clay': 220, 'clay': 230
    }
    
    # Permeability class
    permeability_values = {
        'sand': 'very_high', 'loamy_sand': 'high', 'sandy_loam': 'moderate_high',
        'loam': 'moderate', 'silt_loam': 'moderate_low', 'silt': 'low',
        'sandy_clay_loam': 'moderate_low', 'clay_loam': 'low',
        'silty_clay_loam': 'very_low', 'sandy_clay': 'low',
        'silty_clay': 'very_low', 'clay': 'very_low'
    }
    
    # Erodibility factor (K) - typical values
    erodibility_values = {
        'sand': 0.05, 'loamy_sand': 0.07, 'sandy_loam': 0.10,
        'loam': 0.20, 'silt_loam': 0.35, 'silt': 0.40,
        'sandy_clay_loam': 0.25, 'clay_loam': 0.30,
        'silty_clay_loam': 0.32, 'sandy_clay': 0.28,
        'silty_clay': 0.35, 'clay': 0.38
    }
    
    return {
        'water_holding_capacity': {
            'value': whc_values.get(texture, 150),
            'unit': 'mm/m',
            'description': 'Available water capacity'
        },
        'permeability': permeability_values.get(texture, 'moderate'),
        'erodibility_factor': erodibility_values.get(texture, 0.25),
        'drainage_class': _estimate_drainage(texture),
        'workability': _estimate_workability(texture)
    }


def _estimate_drainage(texture: str) -> str:
    """Estimate drainage class based on texture."""
    drainage_map = {
        'sand': 'excessive', 'loamy_sand': 'excessive',
        'sandy_loam': 'well', 'loam': 'well',
        'silt_loam': 'moderate', 'silt': 'poor',
        'sandy_clay_loam': 'moderate', 'clay_loam': 'poor',
        'silty_clay_loam': 'poor', 'sandy_clay': 'poor',
        'silty_clay': 'very_poor', 'clay': 'very_poor'
    }
    return drainage_map.get(texture, 'moderate')


def _estimate_workability(texture: str) -> str:
    """Estimate soil workability based on texture."""
    workability_map = {
        'sand': 'easy', 'loamy_sand': 'easy',
        'sandy_loam': 'easy', 'loam': 'moderate',
        'silt_loam': 'moderate', 'silt': 'moderate',
        'sandy_clay_loam': 'moderate', 'clay_loam': 'difficult',
        'silty_clay_loam': 'difficult', 'sandy_clay': 'difficult',
        'silty_clay': 'very_difficult', 'clay': 'very_difficult'
    }
    return workability_map.get(texture, 'moderate')


def get_soil_taxonomy(clay: float, silt: float, sand: float,
                       organic_matter: float, ph: float,
                       cec: Optional[float] = None) -> Dict:
    """Get complete soil taxonomy classification.
    
    Args:
        clay: Clay percentage
        silt: Silt percentage
        sand: Sand percentage
        organic_matter: Organic matter percentage
        ph: Soil pH
        cec: Cation Exchange Capacity (optional)
        
    Returns:
        Dict: Complete taxonomy classification
    """
    # Get texture classification
    texture_result = classify_usda_texture(clay, silt, sand)
    
    # Determine soil order based on properties
    soil_order = _determine_soil_order(organic_matter, ph, cec)
    
    return {
        'texture': texture_result,
        'taxonomy': {
            'order': soil_order,
            'order_description': SOIL_ORDERS.get(soil_order.lower(), soil_order),
            'classification_basis': {
                'organic_matter': organic_matter,
                'ph': ph,
                'cec': cec
            }
        },
        'interpretation': _interpret_taxonomy(soil_order, texture_result['texture'])
    }


def _determine_soil_order(organic_matter: float, ph: float, 
                           cec: Optional[float] = None) -> str:
    """Determine soil order based on chemical properties.
    
    This is a simplified classification. Full taxonomy requires
    field observations and laboratory analysis.
    """
    # Histosol: high organic matter
    if organic_matter > 20:
        return 'Histosol'
    
    # Vertisol: high clay content (would need clay % here)
    # For now, use chemical properties
    
    # Acidic soils
    if ph < 5.5:
        return 'Ultisol'
    
    # Alkaline soils
    if ph > 8.0:
        return 'Aridisol'
    
    # Neutral, fertile soils
    if 6.0 <= ph <= 7.5 and organic_matter > 2:
        return 'Mollisol'
    
    # Default
    return 'Inceptisol'


def _interpret_taxonomy(soil_order: str, texture: str) -> Dict:
    """Provide interpretation of taxonomy results."""
    interpretations = {
        'Histosol': 'Organic soil, high water retention, requires drainage',
        'Ultisol': 'Acidic soil, may need lime, weathered',
        'Aridisol': 'Dry soil, low organic matter, irrigation needed',
        'Mollisol': 'Fertile grassland soil, excellent for agriculture',
        'Inceptisol': 'Young soil, moderate development',
        'Vertisol': 'High clay, shrink-swell behavior',
        'Alfisol': 'Fertile, clay accumulation in subsoil',
        'Entisol': 'Very young soil, little development'
    }
    
    return {
        'soil_order': soil_order,
        'texture': texture,
        'interpretation': interpretations.get(soil_order, 'General soil type'),
        'agricultural_suitability': _assess_agricultural_suitability(soil_order, texture)
    }


def _assess_agricultural_suitability(soil_order: str, texture: str) -> Dict:
    """Assess agricultural suitability."""
    # Base score on soil order
    order_scores = {
        'Mollisol': 90, 'Alfisol': 80, 'Inceptisol': 70,
        'Entisol': 60, 'Ultisol': 50, 'Aridisol': 40,
        'Vertisol': 65, 'Histosol': 55
    }
    
    base_score = order_scores.get(soil_order, 60)
    
    # Adjust based on texture
    texture_modifiers = {
        'loam': 10, 'silt_loam': 10, 'clay_loam': 5,
        'sandy_loam': 5, 'sand': -10, 'clay': -10
    }
    
    modifier = texture_modifiers.get(texture, 0)
    final_score = min(100, max(0, base_score + modifier))
    
    return {
        'score': final_score,
        'rating': 'excellent' if final_score >= 80 else 'good' if final_score >= 60 else 'moderate' if final_score >= 40 else 'poor',
        'limitations': _get_limitations(soil_order, texture)
    }


def _get_limitations(soil_order: str, texture: str) -> list:
    """Get limitations for agricultural use."""
    limitations = []
    
    if soil_order == 'Aridisol':
        limitations.append('Low water availability')
    if soil_order == 'Histosol':
        limitations.append('Requires drainage')
    if texture in ['sand', 'loamy_sand']:
        limitations.append('Low water holding capacity')
    if texture in ['clay', 'silty_clay']:
        limitations.append('Poor drainage')
    if texture == 'clay':
        limitations.append('Difficult tillage')
    
    return limitations
