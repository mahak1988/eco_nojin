import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Constants for RUSLE model components (simplified)
# R (Climate): MJ * mm / (ha * h * yr) - Typically derived from rainfall data
# K (Soil Erodibility): t * ha * h / (ha * MJ * mm) - From soil surveys
# LS (Length/Slope): Unitless - Calculated from DEM
# C (Cover Management): Unitless, 0-1 - From land use/cover maps
# P (Support Practice): Unitless, 0-1 - From farming practices

# Simplified constants for demonstration
DEFAULT_R_FACTOR = 150.0  # MJ*mm/(ha*h*yr)
DEFAULT_K_FACTOR = 0.25   # t*ha*h/(ha*MJ*mm)
DEFAULT_C_FACTOR = 0.3    # Unitless
DEFAULT_P_FACTOR = 1.0    # Unitless (no conservation practice)


def calculate_ls_factor(slope_degrees: np.ndarray, cell_size_m: float = 30.0) -> np.ndarray:
    """
    Calculates the LS factor of the RUSLE model based on slope and cell size.
    This is a simplified version. A full implementation requires flow direction/path length.

    Args:
        slope_degrees: A 2D numpy array of slope values in degrees.
        cell_size_m: The ground resolution of the DEM pixels in meters.

    Returns:
        A 2D numpy array of LS factors.
    """
    # Convert slope to rise/run (tan)
    slope_radians = np.radians(slope_degrees)
    tan_slope = np.tan(slope_radians)
    
    # Simplified LS calculation (often involves slope length L and steepness S)
    # L = (cell_length / 22.13)^0.4
    # S = 10.8 * sin(slope) + 0.03 (for slope in degrees)
    # LS = L * S
    # For a more robust calculation, a flow accumulation algorithm is needed.
    # Here, we use a proxy based on slope^2 for demonstration.
    ls_factor = np.power(tan_slope, 0.4) * np.power((10.8 * np.sin(slope_radians) + 0.03), 1.0)
    
    # Ensure no NaN values are introduced, replace with a small positive number
    ls_factor = np.nan_to_num(ls_factor, nan=0.001, posinf=1e6, neginf=-1e6)
    
    # Clamp extreme values to prevent unrealistic outputs
    ls_factor = np.clip(ls_factor, 0.0, 100.0)
    
    return ls_factor


def estimate_erosion_risk(
    slope_degrees: np.ndarray,
    cell_size_m: float = 30.0,
    r_factor: float = DEFAULT_R_FACTOR,
    k_factor: float = DEFAULT_K_FACTOR,
    c_factor: float = DEFAULT_C_FACTOR,
    p_factor: float = DEFAULT_P_FACTOR,
) -> Tuple[np.ndarray, str]:
    """
    Estimates erosion risk using a simplified RUSLE-like model.

    Args:
        slope_degrees: A 2D numpy array of slope values in degrees.
        cell_size_m: The ground resolution of the DEM pixels in meters.
        r_factor: Climate factor (MJ*mm/(ha*h*yr)).
        k_factor: Soil erodibility factor (t*ha*h/(ha*MJ*mm)).
        c_factor: Cover management factor (unitless).
        p_factor: Support practice factor (unitless).

    Returns:
        A tuple containing the 2D numpy array of estimated erosion rates (t/ha/yr)
        and a qualitative risk level string ('Low', 'Moderate', 'High', 'Very High').
    """
    logger.info("Estimating erosion risk using simplified RUSLE model.")
    
    ls_factor = calculate_ls_factor(slope_degrees, cell_size_m)
    
    # RUSLE: A = R * K * LS * C * P
    # A is the predicted soil loss (t/ha/yr)
    predicted_loss_t_per_ha_per_yr = r_factor * k_factor * ls_factor * c_factor * p_factor
    
    # Determine qualitative risk level based on mean predicted loss
    mean_loss = float(np.nanmean(predicted_loss_t_per_ha_per_yr))
    if mean_loss < 5:
        risk_level = "Low"
    elif mean_loss < 12:
        risk_level = "Moderate"
    elif mean_loss < 25:
        risk_level = "High"
    else:
        risk_level = "Very High"

    logger.info(f"Erosion risk calculated. Mean loss: {mean_loss:.2f} t/ha/yr. Risk Level: {risk_level}")
    return predicted_loss_t_per_ha_per_yr, risk_level