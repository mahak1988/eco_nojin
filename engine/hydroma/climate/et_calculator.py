"""Scientific calculations for climate and water requirements."""

import math


def calc_et0_hargreaves(t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
    """Calculate reference evapotranspiration (ET0) using Hargreaves-Samani method.

    This method is recommended by FAO when only temperature data is available.

    Args:
        t_min: Minimum temperature (Celsius)
        t_max: Maximum temperature (Celsius)
        t_mean: Mean temperature (Celsius)
        ra_mj: Extraterrestrial radiation (MJ/m2/day)

    Returns:
        ET0 in mm/day
    """
    if t_max < t_min:
        raise ValueError("t_max must be >= t_min")
    if ra_mj < 0:
        raise ValueError("Radiation cannot be negative")

    # Hargreaves-Samani formula
    # 0.408 is the conversion factor from MJ/m2/day to mm/day equivalent
    return 0.0023 * 0.408 * ra_mj * (t_mean + 17.8) * math.sqrt(t_max - t_min)
