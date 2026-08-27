"""
Soil Analysis Module for Eco Nojin.

This module provides comprehensive soil analysis capabilities including:
- USDA Soil Taxonomy classification
- Soil chemistry calculations (CEC, ESP, SAR)
- Water retention modeling (van Genuchten)
- Soil health assessment
- Salinity analysis
- Fertility recommendations

Author: Eco Nojin Team
Created: 2026-08-15
Version: 1.0.0

References:
    [1] USDA, "Keys to Soil Taxonomy", 13th Edition, 2017
    [2] van Genuchten, M.Th., "A closed-form equation for predicting 
        the hydraulic conductivity of unsaturated soils", 
        Soil Sci. Soc. Am. J., 44:892-898, 1980
    [3] Brady, N.C. and Weil, R.R., "The Nature and Properties of Soils",
        15th Edition, Pearson, 2017
"""

__version__ = "1.0.0"
__author__ = "Eco Nojin Team"

# Import main components
from .chemistry import calculate_cec, calculate_esp, calculate_ph_buffer, calculate_sar
from .health import assess_soil_quality, calculate_soil_health_index
from .recommendations import generate_recommendations
from .salinity import calculate_leaching_requirement, classify_salinity
from .taxonomy import classify_usda_texture, get_soil_taxonomy
from .water_retention import van_genuchten_conductivity, van_genuchten_retention

# Module exports
__all__ = [
    'assess_soil_quality',
    'calculate_cec',
    'calculate_esp',
    'calculate_leaching_requirement',
    'calculate_ph_buffer',
    'calculate_sar',
    'calculate_soil_health_index',
    'classify_salinity',
    'classify_usda_texture',
    'generate_recommendations',
    'get_soil_taxonomy',
    'van_genuchten_conductivity',
    'van_genuchten_retention',
]
