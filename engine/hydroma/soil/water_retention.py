"""
Soil Water Retention Modeling.

Implements van Genuchten water retention model and hydraulic conductivity.

References:
    [1] van Genuchten, M.Th., "A closed-form equation for predicting 
        the hydraulic conductivity of unsaturated soils", 
        Soil Sci. Soc. Am. J., 44:892-898, 1980
    [2] Mualem, Y., "A new model for predicting the hydraulic conductivity 
        of unsaturated porous media", Water Resources Research, 12:513-522, 1976
"""
from typing import Dict, Optional
import math
import logging

logger = logging.getLogger(__name__)

# Default van Genuchten parameters for common soil textures
# Format: (theta_r, theta_s, alpha, n)
VG_PARAMETERS = {
    'sand': (0.045, 0.437, 0.145, 2.68),
    'loamy_sand': (0.057, 0.437, 0.124, 2.28),
    'sandy_loam': (0.065, 0.453, 0.075, 1.89),
    'loam': (0.078, 0.463, 0.036, 1.56),
    'silt_loam': (0.065, 0.454, 0.020, 1.41),
    'silt': (0.034, 0.464, 0.016, 1.37),
    'sandy_clay_loam': (0.100, 0.398, 0.027, 1.48),
    'clay_loam': (0.095, 0.464, 0.019, 1.31),
    'silty_clay_loam': (0.089, 0.471, 0.010, 1.23),
    'sandy_clay': (0.100, 0.382, 0.027, 1.23),
    'silty_clay': (0.070, 0.479, 0.005, 1.09),
    'clay': (0.068, 0.475, 0.008, 1.09),
}


def van_genuchten_retention(theta_r: float, theta_s: float, 
                              alpha: float, n: float, h: float) -> float:
    """Calculate water content using van Genuchten model.
    
    The van Genuchten equation:
        θ(h) = θr + (θs - θr) / [1 + (α|h|)^n]^m
        where m = 1 - 1/n
        
    Args:
        theta_r: Residual water content (cm³/cm³)
        theta_s: Saturated water content (cm³/cm³)
        alpha: van Genuchten alpha parameter (1/cm)
        n: van Genuchten n parameter (dimensionless)
        h: Pressure head (cm, negative for unsaturated)
        
    Returns:
        float: Water content (cm³/cm³)
        
    Raises:
        ValueError: If parameters are invalid
        
    Example:
        >>> theta = van_genuchten_retention(0.078, 0.463, 0.036, 1.56, -100)
        >>> print(f"Water content: {theta:.3f}")
        Water content: 0.245
        
    References:
        [1] van Genuchten, 1980
    """
    # Validate parameters
    if theta_r < 0 or theta_s <= theta_r:
        raise ValueError("Invalid water content parameters")
    if alpha <= 0 or n <= 1:
        raise ValueError("Invalid van Genuchten parameters")
    
    # m parameter
    m = 1 - 1/n
    
    # For saturated conditions (h >= 0)
    if h >= 0:
        return theta_s
    
    # Calculate effective saturation
    abs_h = abs(h)
    denominator = (1 + (alpha * abs_h) ** n) ** m
    
    theta = theta_r + (theta_s - theta_r) / denominator
    
    return theta


def van_genuchten_conductivity(theta_r: float, theta_s: float,
                                alpha: float, n: float, 
                                k_s: float, h: float) -> float:
    """Calculate hydraulic conductivity using van Genuchten-Mualem model.
    
    K(h) = Ks × Se^0.5 × [1 - (1 - Se^(1/m))^m]²
    where Se = (θ - θr) / (θs - θr)
    
    Args:
        theta_r: Residual water content
        theta_s: Saturated water content
        alpha: van Genuchten alpha
        n: van Genuchten n
        k_s: Saturated hydraulic conductivity (cm/day)
        h: Pressure head (cm)
        
    Returns:
        float: Hydraulic conductivity (cm/day)
    """
    # Get water content
    theta = van_genuchten_retention(theta_r, theta_s, alpha, n, h)
    
    # Effective saturation
    se = (theta - theta_r) / (theta_s - theta_r)
    
    # For saturated conditions
    if se >= 1:
        return k_s
    
    # m parameter
    m = 1 - 1/n
    
    # Calculate conductivity
    term1 = se ** 0.5
    term2 = (1 - (1 - se ** (1/m)) ** m) ** 2
    
    k = k_s * term1 * term2
    
    return max(0, k)


def get_vg_parameters(texture: str) -> Dict:
    """Get van Genuchten parameters for a soil texture.
    
    Args:
        texture: USDA texture class
        
    Returns:
        Dict: van Genuchten parameters
    """
    if texture not in VG_PARAMETERS:
        # Default to loam
        texture = 'loam'
        logger.warning(f"Unknown texture, using {texture}")
    
    theta_r, theta_s, alpha, n = VG_PARAMETERS[texture]
    
    return {
        'texture': texture,
        'theta_r': theta_r,
        'theta_s': theta_s,
        'alpha': alpha,
        'n': n,
        'm': 1 - 1/n,
        'description': f'van Genuchten parameters for {texture}'
    }


def calculate_water_retention_curve(texture: str, 
                                      h_values: Optional[list] = None) -> Dict:
    """Calculate complete water retention curve.
    
    Args:
        texture: USDA texture class
        h_values: List of pressure heads (optional)
        
    Returns:
        Dict: Water retention curve data
    """
    if h_values is None:
        # Default pressure heads (cm)
        h_values = [0, -10, -33, -100, -300, -1000, -15000]
    
    params = get_vg_parameters(texture)
    
    curve_data = []
    for h in h_values:
        theta = van_genuchten_retention(
            params['theta_r'], params['theta_s'],
            params['alpha'], params['n'], h
        )
        curve_data.append({
            'pressure_head': h,
            'water_content': round(theta, 4),
            'unit': 'cm³/cm³'
        })
    
    return {
        'texture': texture,
        'parameters': params,
        'curve': curve_data,
        'field_capacity': _find_field_capacity(curve_data),
        'wilting_point': _find_wilting_point(curve_data)
    }


def _find_field_capacity(curve_data: list) -> Optional[Dict]:
    """Find field capacity (at -33 cm pressure head)."""
    for point in curve_data:
        if point['pressure_head'] == -33:
            return point
    return None


def _find_wilting_point(curve_data: list) -> Optional[Dict]:
    """Find permanent wilting point (at -15000 cm pressure head)."""
    for point in curve_data:
        if point['pressure_head'] == -15000:
            return point
    return None


def calculate_available_water(theta_fc: float, theta_wp: float, 
                                root_depth: float) -> Dict:
    """Calculate plant available water capacity.
    
    Args:
        theta_fc: Water content at field capacity
        theta_wp: Water content at wilting point
        root_depth: Root zone depth (cm)
        
    Returns:
        Dict: Available water calculations
    """
    if theta_fc <= theta_wp:
        raise ValueError("Field capacity must be greater than wilting point")
    
    # Available water capacity (cm water / cm soil)
    awc = theta_fc - theta_wp
    
    # Total available water in root zone (cm)
    total_aw = awc * root_depth
    
    # Convert to mm
    total_aw_mm = total_aw * 10
    
    return {
        'available_water_capacity': round(awc, 4),
        'awc_unit': 'cm/cm',
        'total_available_water': round(total_aw, 2),
        'total_available_water_unit': 'cm',
        'total_available_water_mm': round(total_aw_mm, 2),
        'root_depth': root_depth,
        'interpretation': _interpret_awc(awc)
    }


def _interpret_awc(awc: float) -> Dict:
    """Interpret available water capacity."""
    if awc < 0.10:
        return {'rating': 'low', 'description': 'Low water holding capacity'}
    elif awc < 0.20:
        return {'rating': 'moderate', 'description': 'Moderate water holding'}
    else:
        return {'rating': 'high', 'description': 'High water holding capacity'}
