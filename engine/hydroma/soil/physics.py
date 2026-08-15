"""Soil water retention and hydraulic conductivity models (Phase 1).

References:
- van Genuchten, M.Th. (1980). A closed-form equation for predicting the
  hydraulic conductivity of unsaturated soils. SSSAJ 44:892-898.
- Mualem, Y. (1976). A new model for predicting the hydraulic conductivity
  of unsaturated porous media. Water Resources Research 12:513-522.
- Brooks, R.H. & Corey, A.T. (1964). Hydraulic properties of porous media.
- Campbell, G.S. (1974). A simple method for determining unsaturated
  conductivity from moisture retention data. Soil Science 117:311-314.
- Carsel, R.F. & Parrish, R.S. (1988). Developing joint probability
  distributions of soil water retention characteristics. WRR 24:755-769.
"""

import numpy as np


def van_genuchten_theta(
    h: float,
    theta_r: float,
    theta_s: float,
    alpha: float,
    n: float,
) -> float:
    """Water content at matric potential h using van Genuchten (1980).

    theta(h) = theta_r + (theta_s - theta_r) / (1 + |alpha*h|^n)^m
    with m = 1 - 1/n.

    Args:
        h: matric potential head [cm] (negative for unsaturated)
        theta_r: residual water content [cm3/cm3]
        theta_s: saturated water content [cm3/cm3]
        alpha: van Genuchten alpha [1/cm]
        n: van Genuchten n [-]
    """
    if theta_s <= theta_r:
        raise ValueError("theta_s must be > theta_r")
    if n <= 1:
        raise ValueError("n must be > 1")
    m = 1.0 - 1.0 / n
    ah = abs(alpha * h)
    if ah == 0:
        return theta_s
    return theta_r + (theta_s - theta_r) / (1.0 + ah**n) ** m


def van_genuchten_k(
    h: float,
    theta_r: float,
    theta_s: float,
    alpha: float,
    n: float,
    ks: float,
) -> float:
    """Hydraulic conductivity using van Genuchten-Mualem (1980/1976).

    K(h) = Ks * Se^0.5 * [1 - (1 - Se^(1/m))^m]^2
    with Se = (theta - theta_r)/(theta_s - theta_r), m = 1 - 1/n.

    Args:
        h: matric potential head [cm]
        theta_r, theta_s, alpha, n: van Genuchten parameters
        ks: saturated hydraulic conductivity [cm/day]
    """
    if ks <= 0:
        raise ValueError("ks must be positive")
    if n <= 1:
        raise ValueError("n must be > 1")
    m = 1.0 - 1.0 / n
    theta = van_genuchten_theta(h, theta_r, theta_s, alpha, n)
    if theta <= theta_r:
        return 0.0
    se = (theta - theta_r) / (theta_s - theta_r)
    se = min(max(se, 0.0), 1.0)
    term = 1.0 - (1.0 - se ** (1.0 / m)) ** m
    return ks * (se**0.5) * (term**2)


def brooks_corey_theta(
    h: float,
    theta_r: float,
    theta_s: float,
    hb: float,
    lam: float,
) -> float:
    """Water content using Brooks & Corey (1964).

    theta(h) = theta_r + (theta_s - theta_r) * (hb/h)^lam  for h < hb
    theta(h) = theta_s                                  for h >= hb
    """
    if theta_s <= theta_r:
        raise ValueError("theta_s must be > theta_r")
    if h >= hb:
        return theta_s
    return theta_r + (theta_s - theta_r) * (abs(hb) / abs(h)) ** lam


def campbell_theta(
    h: float,
    theta_r: float,
    theta_s: float,
    he: float,
    b: float,
) -> float:
    """Water content using Campbell (1974).

    theta(h) = theta_s * (he/h)^(1/b)  for h < he
    theta(h) = theta_s                 for h >= he
    """
    if h >= he:
        return theta_s
    return theta_r + (theta_s - theta_r) * (he / h) ** (1.0 / b)


# Carsel & Parrish (1988) van Genuchten parameters for 12 USDA textures
# Ks in cm/day (converted from their cm/hr values *24)
SOIL_PARAMETERS_VG: dict[str, dict[str, float]] = {
    "sand": {"theta_r": 0.045, "theta_s": 0.430, "alpha": 0.145, "n": 2.68, "Ks": 712.8},
    "loamy_sand": {"theta_r": 0.057, "theta_s": 0.410, "alpha": 0.124, "n": 2.28, "Ks": 350.2},
    "sandy_loam": {"theta_r": 0.065, "theta_s": 0.410, "alpha": 0.075, "n": 1.89, "Ks": 106.1},
    "loam": {"theta_r": 0.078, "theta_s": 0.430, "alpha": 0.036, "n": 1.56, "Ks": 25.0},
    "silt_loam": {"theta_r": 0.067, "theta_s": 0.450, "alpha": 0.020, "n": 1.41, "Ks": 10.8},
    "sandy_clay_loam": {"theta_r": 0.100, "theta_s": 0.390, "alpha": 0.059, "n": 1.48, "Ks": 31.4},
    "clay_loam": {"theta_r": 0.095, "theta_s": 0.410, "alpha": 0.019, "n": 1.31, "Ks": 6.2},
    "silty_clay_loam": {"theta_r": 0.089, "theta_s": 0.430, "alpha": 0.010, "n": 1.23, "Ks": 2.9},
    "sandy_clay": {"theta_r": 0.100, "theta_s": 0.380, "alpha": 0.027, "n": 1.23, "Ks": 2.9},
    "silty_clay": {"theta_r": 0.070, "theta_s": 0.360, "alpha": 0.005, "n": 1.09, "Ks": 0.5},
    "clay": {"theta_r": 0.068, "theta_s": 0.380, "alpha": 0.008, "n": 1.09, "Ks": 4.8},
    "silt": {"theta_r": 0.050, "theta_s": 0.460, "alpha": 0.016, "n": 1.37, "Ks": 6.0},
}

# Field capacity (-330 cm) and permanent wilting point (-15000 cm) heads
FC_HEAD_CM = 330.0
PWP_HEAD_CM = 15000.0


def water_content_at(matric_potential_cm: float, texture: str) -> float:
    """Water content at a given matric potential for a texture (VG model)."""
    if texture not in SOIL_PARAMETERS_VG:
        raise KeyError(f"Unknown texture: {texture!r}")
    p = SOIL_PARAMETERS_VG[texture]
    return van_genuchten_theta(matric_potential_cm, p["theta_r"], p["theta_s"], p["alpha"], p["n"])


def available_water_capacity(texture: str) -> float:
    """Plant-available water capacity: AWC = theta(FC) - theta(PWP)."""
    fc = water_content_at(-FC_HEAD_CM, texture)
    pwp = water_content_at(-PWP_HEAD_CM, texture)
    return fc - pwp


def water_retention_curve(texture: str, heads_cm: np.ndarray) -> np.ndarray:
    """Vectorized retention curve for a texture over an array of heads."""
    if texture not in SOIL_PARAMETERS_VG:
        raise KeyError(f"Unknown texture: {texture!r}")
    p = SOIL_PARAMETERS_VG[texture]
    return np.array(
        [
            van_genuchten_theta(float(h), p["theta_r"], p["theta_s"], p["alpha"], p["n"])
            for h in heads_cm
        ]
    )
