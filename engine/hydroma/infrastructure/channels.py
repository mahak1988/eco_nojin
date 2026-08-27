"""
Hydraulic Design Engine - Open Channels.

Calculates and designs stable open channels for water conveyance
based on discharge, slope, and soil characteristics.
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .draining import calculate_open_channel_flow


class ChannelShape(Enum):
    RECTANGULAR = "rectangular"
    TRAPEZOIDAL = "trapezoidal"
    TRIANGULAR = "triangular"
    PARABOLIC = "parabolic"


@dataclass
class ChannelDesignCriteria:
    """Criteria for channel design."""
    design_discharge: float  # m3/s
    longitudinal_slope: float  # m/m
    side_slope_horizontal: float = 1.0  # H:V (for trapezoidal/triangular)
    bottom_width: float = 1.0  # m (for rectangular/trapezoidal)
    max_velocity: float = 3.0  # m/s (to prevent erosion)
    min_velocity: float = 0.3  # m/s (to prevent sedimentation)
    freeboard: float = 0.3  # m
    Manning_n: float = 0.025  # Typical for excavated earth


def design_trapezoidal_channel(criteria: ChannelDesignCriteria) -> dict[str, Any]:
    """
    Designs a trapezoidal channel.

    Args:
        criteria: Design criteria.

    Returns:
        Dictionary containing calculated channel dimensions and properties.
    """
    Q_des = criteria.design_discharge
    S = criteria.longitudinal_slope
    n = criteria.Manning_n
    z = criteria.side_slope_horizontal
    b = criteria.bottom_width
    V_max = criteria.max_velocity
    V_min = criteria.min_velocity

    # Estimate depth based on minimum velocity requirement
    # A = Q / V_min, for trapezoid A = (b + z*y)*y
    # So, (b + z*y)*y = Q/V_min -> z*y^2 + b*y - Q/V_min = 0
    a_quad = z
    b_quad = b
    c_quad = - Q_des / V_min

    discriminant = b_quad**2 - 4*a_quad*c_quad
    if discriminant < 0:
        raise ValueError("No feasible depth found for min velocity constraint.")

    y_estimated = (-b_quad + math.sqrt(discriminant)) / (2*a_quad)

    # Iteratively adjust depth until calculated Q matches design Q within tolerance
    tolerance = 0.01
    depth = y_estimated
    max_iterations = 100
    iteration = 0

    while iteration < max_iterations:
        A = (b + z * depth) * depth
        P = b + 2 * depth * math.sqrt(1 + z**2)
        R = A / P if P > 0 else 0
        Q_calc = calculate_open_channel_flow(A, R, S, n)
        V_calc = Q_calc / A if A > 0 else 0

        if abs(Q_calc - Q_des) < tolerance:
            break
        elif Q_calc < Q_des:
            depth *= 1.02
        else:
            depth *= 0.98
        iteration += 1

    A_final = (b + z * depth) * depth
    P_final = b + 2 * depth * math.sqrt(1 + z**2)
    R_final = A_final / P_final if P_final > 0 else 0
    Q_final = calculate_open_channel_flow(A_final, R_final, S, n)
    V_final = Q_final / A_final if A_final > 0 else 0
    T_water_surface = b + 2 * z * depth

    return {
        "shape": ChannelShape.TRAPEZOIDAL.value,
        "discharge_m3_s": Q_final,
        "velocity_m_s": V_final,
        "bottom_width_m": b,
        "depth_m": depth,
        "side_slope_H_V": z,
        "top_width_m": T_water_surface,
        "cross_section_area_m2": A_final,
        "wetted_perimeter_m": P_final,
        "hydraulic_radius_m": R_final,
        "longitudinal_slope": S,
        "manning_n": n,
        "freeboard_m": criteria.freeboard,
        "excavation_volume_per_meter": A_final # Volume per unit length
    }
