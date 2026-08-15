"""Pedotransfer functions for soil hydraulic properties (Phase 1).

Reference:
- Saxton, K.E. & Rawls, W.J. (2006). Soil Water Characteristic Estimates
  by Texture and Organic Matter for Hydrologic Solutions. SSSAJ 70:1569-1578.
  (Approximation of their regression equations; units converted to cm/cm and cm/day)
"""


def estimate_soil_parameters(
    sand_pct: float,
    clay_pct: float,
    om_pct: float = 1.0,
) -> dict[str, float]:
    """Estimate hydraulic parameters from texture + organic matter.

    Implements the Saxton & Rawls (2006) regression-style estimates
    (sand/clay/organic-matter fractions are used as decimals in the
    original regressions; here we reproduce the standard published form).

    Args:
        sand_pct: sand percentage (0-100)
        clay_pct: clay percentage (0-100)
        om_pct: organic matter percentage (default 1.0)

    Returns:
        dict with theta_1500 (PWP), theta_33 (FC), theta_s, Ks (cm/day)
    """
    S = sand_pct / 100.0
    C = clay_pct / 100.0
    OM = om_pct / 100.0

    # Moisture at 1500 kPa (permanent wilting point)
    theta_1500 = (
        -0.024 * S
        + 0.487 * C
        + 0.006 * OM
        + 0.005 * (S * OM)
        - 0.013 * (C * OM)
        + 0.068 * (S * C)
        + 0.031
    )
    # Moisture at 33 kPa (field capacity)
    theta_33 = (
        -0.251 * S
        + 0.195 * C
        + 0.011 * OM
        + 0.006 * (S * OM)
        - 0.027 * (C * OM)
        + 0.452 * (S * C)
        + 0.299
    )
    # Saturated water content
    theta_s = (
        0.278 * S
        + 0.034 * C
        + 0.022 * OM
        - 0.018 * (S * OM)
        - 0.027 * (C * OM)
        - 0.584 * (S * C)
        + 0.078
    )

    # Saturated hydraulic conductivity [cm/h] then converted to cm/day
    # (published Saxton-Rawls log form)
    ln_ks_cmh = (
        12.012
        - 0.0755 * (sand_pct)
        + (
            -3.895
            + 0.03671 * (sand_pct)
            - 0.110 * (clay_pct)
            + 0.00876 * (clay_pct**2)
            + 0.000501 * (sand_pct**2) * (clay_pct)
            - 0.000452 * (sand_pct) * (clay_pct**2)
        )
    )
    ks_cmh = 2.778 * max(1e-6, float(__import__("math").exp(ln_ks_cmh)))
    ks_cm_day = ks_cmh * 24.0

    # Sanity clamps (prevent non-physical values)
    theta_s = max(theta_s, theta_33 + 0.02)
    theta_33 = max(theta_33, theta_1500 + 0.01)
    theta_1500 = max(theta_1500, 0.01)
    theta_s = min(theta_s, 0.60)

    return {
        "theta_1500": round(theta_1500, 4),
        "theta_33": round(theta_33, 4),
        "theta_s": round(theta_s, 4),
        "awc": round(theta_33 - theta_1500, 4),
        "ks_cm_per_day": round(ks_cm_day, 2),
    }


def estimate_texture_from_particles(sand_pct: float, clay_pct: float) -> str:
    """Quick texture estimate from sand/clay (silt = remainder)."""
    from .texture import classify_texture

    silt = 100.0 - sand_pct - clay_pct
    return classify_texture(sand_pct, silt, clay_pct)
