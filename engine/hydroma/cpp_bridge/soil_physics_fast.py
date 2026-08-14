"""Numba-accelerated soil physics calculations.

Implements van Genuchten (1980) soil water retention curve and
hydraulic conductivity functions.

Reference: van Genuchten, M.Th. 1980. "A closed-form equation for
predicting the hydraulic conductivity of unsaturated soils."
Soil Science Society of America Journal 44:892-898.
"""
import numpy as np

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    prange = range


# Typical van Genuchten parameters for common soil textures
SOIL_PARAMETERS = {
    "sand": {"theta_r": 0.045, "theta_s": 0.43, "alpha": 0.145, "n": 2.68, "Ks": 29.7},
    "loamy_sand": {"theta_r": 0.057, "theta_s": 0.41, "alpha": 0.124, "n": 2.28, "Ks": 14.6},
    "sandy_loam": {"theta_r": 0.065, "theta_s": 0.41, "alpha": 0.075, "n": 1.89, "Ks": 4.42},
    "loam": {"theta_r": 0.078, "theta_s": 0.43, "alpha": 0.036, "n": 1.56, "Ks": 1.05},
    "silt_loam": {"theta_r": 0.067, "theta_s": 0.45, "alpha": 0.020, "n": 1.41, "Ks": 0.45},
    "clay_loam": {"theta_r": 0.095, "theta_s": 0.41, "alpha": 0.019, "n": 1.31, "Ks": 0.26},
    "clay": {"theta_r": 0.068, "theta_s": 0.38, "alpha": 0.008, "n": 1.09, "Ks": 0.12},
}


@njit(cache=True)
def _van_genuchten_theta(h_matric: np.ndarray, theta_r: float, theta_s: float,
                          alpha: float, n: float) -> np.ndarray:
    """Calculate soil water content from matric potential using van Genuchten.
    
    theta(h) = theta_r + (theta_s - theta_r) / [1 + |alpha*h|^n]^m
    where m = 1 - 1/n
    """
    m = 1.0 - 1.0 / n
    result = np.empty(len(h_matric), dtype=np.float64)
    
    for i in range(len(h_matric)):
        h = abs(h_matric[i])
        if h < 1e-10:
            result[i] = theta_s
        else:
            denom = (1.0 + (alpha * h) ** n) ** m
            result[i] = theta_r + (theta_s - theta_r) / denom
    
    return result


@njit(cache=True)
def _van_genuchten_K(h_matric: np.ndarray, Ks: float, theta_r: float,
                      theta_s: float, alpha: float, n: float) -> np.ndarray:
    """Calculate unsaturated hydraulic conductivity using van Genuchten-Mualem.
    
    K(h) = Ks * Se^0.5 * [1 - (1 - Se^(1/m))^m]^2
    where Se = (theta - theta_r) / (theta_s - theta_r)
    """
    m = 1.0 - 1.0 / n
    result = np.empty(len(h_matric), dtype=np.float64)
    
    for i in range(len(h_matric)):
        h = abs(h_matric[i])
        if h < 1e-10:
            result[i] = Ks
        else:
            # Calculate Se
            denom = (1.0 + (alpha * h) ** n) ** m
            Se = 1.0 / denom
            
            # Mualem model
            if Se > 0 and Se < 1:
                inner = 1.0 - (1.0 - Se ** (1.0/m)) ** m
                result[i] = Ks * (Se ** 0.5) * (inner ** 2)
            else:
                result[i] = Ks if Se >= 1 else 0.0
    
    return result


def soil_water_content(h_matric: np.ndarray, soil_texture: str) -> np.ndarray:
    """Calculate soil water content for given matric potential and texture.
    
    Args:
        h_matric: Matric potential [cm, positive values]
        soil_texture: Soil texture class (sand, loam, clay, etc.)
    
    Returns:
        Volumetric water content [cm³/cm³]
    """
    if soil_texture not in SOIL_PARAMETERS:
        raise ValueError(f"Unknown texture: {soil_texture}. Available: {list(SOIL_PARAMETERS.keys())}")
    
    params = SOIL_PARAMETERS[soil_texture]
    h_array = np.asarray(h_matric, dtype=np.float64)
    
    return _van_genuchten_theta(
        h_array, params["theta_r"], params["theta_s"],
        params["alpha"], params["n"]
    )


def hydraulic_conductivity(h_matric: np.ndarray, soil_texture: str) -> np.ndarray:
    """Calculate unsaturated hydraulic conductivity.
    
    Args:
        h_matric: Matric potential [cm, positive values]
        soil_texture: Soil texture class
    
    Returns:
        Hydraulic conductivity [cm/day]
    """
    if soil_texture not in SOIL_PARAMETERS:
        raise ValueError(f"Unknown texture: {soil_texture}")
    
    params = SOIL_PARAMETERS[soil_texture]
    h_array = np.asarray(h_matric, dtype=np.float64)
    
    return _van_genuchten_K(
        h_array, params["Ks"], params["theta_r"], params["theta_s"],
        params["alpha"], params["n"]
    )


def get_soil_parameters(soil_texture: str) -> dict:
    """Get van Genuchten parameters for a soil texture."""
    if soil_texture not in SOIL_PARAMETERS:
        raise ValueError(f"Unknown texture: {soil_texture}. Available: {list(SOIL_PARAMETERS.keys())}")
    return SOIL_PARAMETERS[soil_texture].copy()
