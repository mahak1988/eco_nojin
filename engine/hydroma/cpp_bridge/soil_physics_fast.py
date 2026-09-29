"""Numba-accelerated soil physics calculations.

Implements van Genuchten (1980) soil water retention curve and
hydraulic conductivity functions.

Reference: van Genuchten, M.Th. 1980. "A closed-form equation for
predicting the hydraulic conductivity of unsaturated soils."
Soil Science Society of America Journal 44:892-898.

The parameter table is not local to this file. It is read from
engine/data/soil_vg_table.csv, which every backend shares, and converted to
cm/hr for the compiled kernel. See engine/hydroma/soil/parameters.py.
"""

import numpy as np

from engine.data.soil_table import load_table_ks_cm_per_hour

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
# van Genuchten parameters, generated from the single source at
# engine/data/soil_vg_table.csv. Ks is converted to cm/hr here because the
# compiled kernel has always used that unit; every other value is carried
# across unchanged. Before consolidation this was a hand-written seven-row table
# that agreed with soil/physics.py on theta_r, theta_s, alpha and n, differed on
# Ks by the unit factor of 24 for six rows, and disagreed on clay outright
# (2.88 against 4.80 cm/day).
SOIL_PARAMETERS: dict[str, dict[str, float]] = load_table_ks_cm_per_hour()


@njit(cache=True)
def _van_genuchten_theta(
    h_matric: np.ndarray, theta_r: float, theta_s: float, alpha: float, n: float
) -> np.ndarray:
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
def _van_genuchten_K(
    h_matric: np.ndarray, Ks: float, theta_r: float, theta_s: float, alpha: float, n: float
) -> np.ndarray:
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
                inner = 1.0 - (1.0 - Se ** (1.0 / m)) ** m
                result[i] = Ks * (Se**0.5) * (inner**2)
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
        raise ValueError(
            f"Unknown texture: {soil_texture}. Available: {list(SOIL_PARAMETERS.keys())}"
        )

    params = SOIL_PARAMETERS[soil_texture]
    h_array = np.asarray(h_matric, dtype=np.float64)

    return _van_genuchten_theta(
        h_array, params["theta_r"], params["theta_s"], params["alpha"], params["n"]
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
        h_array, params["Ks"], params["theta_r"], params["theta_s"], params["alpha"], params["n"]
    )


def get_soil_parameters(soil_texture: str) -> dict:
    """Get van Genuchten parameters for a soil texture."""
    if soil_texture not in SOIL_PARAMETERS:
        raise ValueError(
            f"Unknown texture: {soil_texture}. Available: {list(SOIL_PARAMETERS.keys())}"
        )
    return SOIL_PARAMETERS[soil_texture].copy()
