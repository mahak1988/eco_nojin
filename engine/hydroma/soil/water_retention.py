"""
Soil Water Retention Modeling.

Implements van Genuchten water retention model and hydraulic conductivity.
Uses SOIL_PARAMETERS_VG from physics.py as the single source of truth
for soil texture parameters (Carsel & Parrish, 1988).

References:
    [1] van Genuchten, M.Th., "A closed-form equation for predicting
        the hydraulic conductivity of unsaturated soils",
        Soil Sci. Soc. Am. J., 44:892-898, 1980
    [2] Mualem, Y., "A new model for predicting the hydraulic conductivity
        of unsaturated porous media", Water Resources Research, 12:513-522, 1976
    [3] Carsel, R.F. & Parrish, R.S. (1988). Developing joint probability
        distributions of soil water retention characteristics. WRR 24:755-769.
"""

import logging

from .physics import (
    SOIL_PARAMETERS_VG,
    van_genuchten_k,
    van_genuchten_theta,
)

logger = logging.getLogger(__name__)

# Re-export the canonical parameter table (single source of truth)
VG_PARAMETERS = SOIL_PARAMETERS_VG


def van_genuchten_retention(
    theta_r: float, theta_s: float, alpha: float, n: float, h: float
) -> float:
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
        >>> theta = van_genuchten_retention(0.078, 0.43, 0.036, 1.56, -100)
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

    # Single implementation. physics.van_genuchten_theta is the canonical
    # van Genuchten retention; this function kept its own argument order because
    # services/api_gateway/routers/hydroma_soil.py and services/validation/
    # formula_checks.py call it positionally, and the two copies previously
    # disagreed on the sign of the head: this one returned theta_s for h >= 0,
    # physics.py treated a positive head as a suction of the same magnitude and
    # returned 0.034 cm/day where this one returned Ks = 25 at +100 cm. The
    # behaviour here was the correct one, so it moved to the canonical function.
    return van_genuchten_theta(h, theta_r, theta_s, alpha, n)


def van_genuchten_conductivity(
    theta_r: float, theta_s: float, alpha: float, n: float, k_s: float, h: float
) -> float:
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
    # Single implementation, as for the retention function above.
    return van_genuchten_k(h, theta_r, theta_s, alpha, n, k_s)


def get_vg_parameters(texture: str) -> dict:
    """Get van Genuchten parameters for a soil texture.

    Args:
        texture: USDA texture class

    Returns:
        Dict: van Genuchten parameters
    """
    if texture not in VG_PARAMETERS:
        # Default to loam
        texture = "loam"
        logger.warning(f"Unknown texture, using {texture}")

    p = VG_PARAMETERS[texture]

    return {
        "texture": texture,
        "theta_r": p["theta_r"],
        "theta_s": p["theta_s"],
        "alpha": p["alpha"],
        "n": p["n"],
        "m": 1 - 1 / p["n"],
        "Ks": p.get("Ks", 25.0),
        "description": f"van Genuchten parameters for {texture} (Carsel & Parrish, 1988)",
    }


def calculate_water_retention_curve(texture: str, h_values: list | None = None) -> dict:
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
            params["theta_r"], params["theta_s"], params["alpha"], params["n"], h
        )
        curve_data.append({"pressure_head": h, "water_content": round(theta, 4), "unit": "cm³/cm³"})

    return {
        "texture": texture,
        "parameters": params,
        "curve": curve_data,
        "field_capacity": _find_field_capacity(curve_data),
        "wilting_point": _find_wilting_point(curve_data),
    }


def _find_field_capacity(curve_data: list) -> dict | None:
    """Find field capacity (at -33 cm pressure head)."""
    for point in curve_data:
        if point["pressure_head"] == -33:
            return point
    return None


def _find_wilting_point(curve_data: list) -> dict | None:
    """Find permanent wilting point (at -15000 cm pressure head)."""
    for point in curve_data:
        if point["pressure_head"] == -15000:
            return point
    return None


def calculate_available_water(theta_fc: float, theta_wp: float, root_depth: float) -> dict:
    """Calculate plant available water capacity.

    Args:
        theta_fc: Water content at field capacity (cm3/cm3)
        theta_wp: Water content at wilting point (cm3/cm3)
        root_depth: Root zone depth (cm)

    Returns:
        Dict: Available water calculations

    Raises:
        ValueError: if either water content lies outside the physical range of a
            volumetric water content, if field capacity is not above wilting
            point, or if the root zone depth is negative. A theta of 2.0 is not
            a soil that holds twice its own volume of water, and a root depth of
            -50 cm is not a root zone; either one produced a store of water
            with the wrong sign and no indication that the input was the
            problem. A root depth of exactly zero is a degenerate but possible
            root zone and is served as an empty store.
    """
    if not 0.0 <= theta_wp <= 1.0:
        raise ValueError(f"Wilting point water content must lie in [0, 1] cm3/cm3, got {theta_wp}")
    if not 0.0 <= theta_fc <= 1.0:
        raise ValueError(f"Field capacity water content must lie in [0, 1] cm3/cm3, got {theta_fc}")
    if theta_fc <= theta_wp:
        raise ValueError("Field capacity must be greater than wilting point")
    if root_depth < 0.0:
        raise ValueError(f"Root zone depth must be non-negative, got {root_depth} cm")

    # Available water capacity (cm water / cm soil)
    awc = theta_fc - theta_wp

    # Total available water in root zone (cm)
    total_aw = awc * root_depth

    # Convert to mm
    total_aw_mm = total_aw * 10

    return {
        "available_water_capacity": round(awc, 4),
        "awc_unit": "cm/cm",
        "total_available_water": round(total_aw, 2),
        "total_available_water_unit": "cm",
        "total_available_water_mm": round(total_aw_mm, 2),
        "root_depth": root_depth,
        "interpretation": _interpret_awc(awc),
    }


def _interpret_awc(awc: float) -> dict:
    """Interpret available water capacity."""
    if awc < 0.10:
        return {"rating": "low", "description": "Low water holding capacity"}
    elif awc < 0.20:
        return {"rating": "moderate", "description": "Moderate water holding"}
    else:
        return {"rating": "high", "description": "High water holding capacity"}
