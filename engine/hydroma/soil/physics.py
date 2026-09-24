"""Soil water retention and hydraulic conductivity models (Phase 1, extended 2026-09-18).

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
- Durner, W. (1994). Multimodality of the water retention function. SSSAJ 58:179-185.
- Assouline, S. & Or, D. (2013). The Brooks-Corey model thirty years later.
- Schaap, M.G. & van Genuchten, M.Th. (2006). A closed-form expression for
  the hydraulic conductivity of unsaturated soils. SSSAJ 70:1940-1948.
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
    "silty_clay": {"theta_r": 0.070, "theta_s": 0.360, "alpha": 0.005, "n": 1.09, "Ks": 1.92},
    "clay": {"theta_r": 0.068, "theta_s": 0.380, "alpha": 0.008, "n": 1.09, "Ks": 4.8},
    "silt": {"theta_r": 0.034, "theta_s": 0.460, "alpha": 0.016, "n": 1.37, "Ks": 6.0},
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


def dual_pores_theta(
    h: float,
    theta_r1: float,
    theta_s1: float,
    alpha1: float,
    n1: float,
    theta_r2: float,
    theta_s2: float,
    alpha2: float,
    n2: float,
    beta: float = 0.5,
) -> float:
    """
    Dual-pores model combining macropores and micropores.

    Based on Durner (1994) and Schaap & van Genuchten (2006).
    theta = (1 - beta) * theta1(h) + beta * theta2(h)

    Args:
        h: matric potential [cm] (negative for unsaturated)
        theta_r1, theta_s1, alpha1, n1: parameters for macropores
        theta_r2, theta_s2, alpha2, n2: parameters for micropores
        beta: fraction of micropore contribution [0, 1]
    """
    theta1 = van_genuchten_theta(h, theta_r1, theta_s1, alpha1, n1)
    theta2 = van_genuchten_theta(h, theta_r2, theta_s2, alpha2, n2)
    return (1.0 - beta) * theta1 + beta * theta2


def richards_buildup(
    h: float,
    theta_r: float,
    theta_s: float,
    alpha: float,
    n: float,
    Ks: float,
    dt: float = 1.0,
    h_initial: float | None = None,
) -> float:
    """
    Approximate solution of Richard's equation for buildup drainage.

    Uses the Schaap & van Genuchten (2006) closed-form for the
    hydraulic conductivity function K(theta).

    Args:
        h: current matric potential [cm]
        theta_r, theta_s, alpha, n: van Genuchten parameters
        Ks: saturated hydraulic conductivity [cm/day]
        dt: time step [days]
        h_initial: initial matric potential [cm] (defaults to h)
    """
    if h_initial is None:
        h_initial = h

    # Compute specific moisture capacity from van Genuchten
    m = 1.0 - 1.0 / n
    ah = abs(alpha * h)
    if ah == 0:
        se = 1.0
    else:
        se = (theta_r + (theta_s - theta_r) / (1.0 + ah**n) ** m - theta_r) / (theta_s - theta_r)
    se = max(0.0, min(1.0, se))

    # Specific moisture capacity dtheta/dh
    dtheta_dh = (
        -(alpha / (n - 1)) * (theta_s - theta_r) * (ah ** (n - 1)) / (1.0 + ah**n) ** (m + 1)
    )

    # Hydraulic conductivity from Schaap & van Genuchten
    (dtheta_dh**2) / (Ks * (theta_s - theta_r) / alpha**2)
    K = Ks * se**0.5 * ((1.0 - (1.0 - se ** (1.0 / m)) ** m) ** 2)

    # Simple time stepping: dh/dt = -K / (dtheta/dh)
    # dh = -K / (dtheta_dh) * dt
    dh = -K / dtheta_dh * dt if abs(dtheta_dh) > 1e-12 else 0.0

    h_new = h + dh
    # Ensure we don't jump past the air-entry value unrealistically
    if h_new > h_initial:
        dh = h_initial - h
        h_new = h_initial

    return h_new


def schaap_vg_k(
    se: float,
    m: float,
    Ks: float,
) -> float:
    """
    Hydraulic conductivity from Schaap & van Genuchten (2006) closed-form.

    K = Ks * se^0.5 * [1 - (1 - se^(1/m))^m]^2
    """
    if se <= 0 or se > 1:
        return 0.0
    if m <= 0 or m > 1:
        raise ValueError("m must be in (0, 1]")
    term = 1.0 - (1.0 - se ** (1.0 / m)) ** m
    return Ks * (se**0.5) * (term**2)


# Convenience wrappers for the existing SOIL_PARAMETERS_VG dict
def water_content_at_dual_pores(
    matric_potential_cm: float,
    texture_primary: str,
    texture_secondary: str,
    beta: float = 0.5,
) -> float:
    """Water content using dual-pores model with two texture descriptions."""
    if texture_primary not in SOIL_PARAMETERS_VG:
        raise KeyError(f"Unknown primary texture: {texture_primary!r}")
    if texture_secondary not in SOIL_PARAMETERS_VG:
        raise KeyError(f"Unknown secondary texture: {texture_secondary!r}")
    p1 = SOIL_PARAMETERS_VG[texture_primary]
    p2 = SOIL_PARAMETERS_VG[texture_secondary]
    theta = dual_pores_theta(
        matric_potential_cm,
        p1["theta_r"],
        p1["theta_s"],
        p1["alpha"],
        p1["n"],
        p2["theta_r"],
        p2["theta_s"],
        p2["alpha"],
        p2["n"],
        beta,
    )
    return float(theta)


def available_water_capacity_dual(
    texture_primary: str,
    texture_secondary: str,
    beta: float = 0.5,
) -> float:
    """Plant-available water capacity using dual-pores model."""
    fc = water_content_at_dual_pores(-330.0, texture_primary, texture_secondary, beta)
    pwp = water_content_at_dual_pores(-15000.0, texture_primary, texture_secondary, beta)
    return fc - pwp
