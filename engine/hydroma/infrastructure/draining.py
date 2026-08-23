"""
Hydraulic Design Engine - Draining Systems.

Calculates and designs draining systems based on land topography,
soil permeability, and rainfall intensity to prevent waterlogging.
"""
import math
from typing import Dict, Any, List
from dataclasses import dataclass

# Constants
GRAVITY = 9.81  # m/s^2


@dataclass
class DrainDesignCriteria:
    """Criteria for drain design."""
    max_flow_rate: float  # m3/s
    max_velocity: float  # m/s
    min_velocity: float  # m/s
    freeboard: float  # m
    side_slope: float  # H:V (horizontal:vertical)
    bottom_width: float  # m
    Manning_n: float  # Roughness coefficient
    soil_permeability: float  # m/s


@dataclass
class DrainSection:
    """Calculated dimensions for a drain section."""
    length: float  # m
    bottom_width: float  # m
    depth: float  # m
    top_width: float  # m
    cross_section_area: float  # m2
    wetted_perimeter: float  # m
    hydraulic_radius: float  # m
    velocity: float  # m/s
    capacity: float  # m3/s
    excavation_volume: float  # m3


def calculate_open_channel_flow(area: float, radius: float, slope: float, manning_n: float) -> float:
    """Calculate flow rate using Manning's equation."""
    if radius <= 0 or slope <= 0:
        return 0.0
    return (1.0 / manning_n) * area * (radius ** (2.0 / 3.0)) * (slope ** 0.5)


def design_rectangular_drain(criteria: DrainDesignCriteria, channel_slope: float) -> DrainSection:
    """
    Designs a rectangular drain section.

    Args:
        criteria: Design criteria.
        channel_slope: Longitudinal slope of the channel.

    Returns:
        Calculated DrainSection.
    """
    # Initial guess for depth based on max flow and min velocity
    min_cross_area = criteria.max_flow_rate / criteria.min_velocity
    estimated_depth = min_cross_area / criteria.bottom_width

    # Iteratively refine depth until capacity meets max_flow_rate
    depth = estimated_depth
    tolerance = 0.01
    max_iterations = 50
    iteration = 0

    while iteration < max_iterations:
        # Calculate geometric properties
        A = criteria.bottom_width * depth
        P = criteria.bottom_width + 2 * depth
        R = A / P if P > 0 else 0
        Q_calc = calculate_open_channel_flow(A, R, channel_slope, criteria.Manning_n)
        V_calc = Q_calc / A if A > 0 else 0

        if abs(Q_calc - criteria.max_flow_rate) < tolerance:
            break
        elif Q_calc < criteria.max_flow_rate:
            depth *= 1.05
        else:
            depth *= 0.95
        iteration += 1

    # Final calculations
    A_final = criteria.bottom_width * depth
    P_final = criteria.bottom_width + 2 * depth
    R_final = A_final / P_final if P_final > 0 else 0
    Q_final = calculate_open_channel_flow(A_final, R_final, channel_slope, criteria.Manning_n)
    V_final = Q_final / A_final if A_final > 0 else 0

    # Calculate top width (for trapezoidal, it would be B + 2*depth*side_slope)
    top_width = criteria.bottom_width + 2 * depth * criteria.side_slope

    return DrainSection(
        length=100.0,  # Placeholder, actual length comes from design route
        bottom_width=criteria.bottom_width,
        depth=depth,
        top_width=top_width,
        cross_section_area=A_final,
        wetted_perimeter=P_final,
        hydraulic_radius=R_final,
        velocity=V_final,
        capacity=Q_final,
        excavation_volume=A_final * 100.0 # Volume per unit length * length
    )


def design_pipe_drain(max_flow_rate: float, slope: float, material_roughness: float) -> Dict[str, Any]:
    """
    Designs a circular pipe drain.

    Args:
        max_flow_rate: Required flow rate (m3/s).
        slope: Pipe slope.
        material_roughness: Manning's n for pipe material.

    Returns:
        Dictionary containing calculated pipe diameter and properties.
    """
    # For a full circular pipe: A = pi*D^2/4, R = D/4
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    # => Q = (1/n) * (pi*D^2/4) * (D/4)^(2/3) * S^(1/2)
    # => Q = (1/n) * (pi/4) * (1/4)^(2/3) * D^(8/3) * S^(1/2)
    # => D = ( Q * n * 4^(5/3) / (pi * S^(1/2) ) )^(3/8)

    numerator = max_flow_rate * material_roughness * (4 ** (5.0 / 3.0))
    denominator = math.pi * (slope ** 0.5)
    if denominator <= 0:
        raise ValueError("Slope must be positive for pipe flow calculation.")

    D_cubed_over_eight = numerator / denominator
    diameter = D_cubed_over_eight ** (3.0 / 8.0)

    A = math.pi * (diameter**2) / 4
    R = diameter / 4
    V = calculate_open_channel_flow(A, R, slope, material_roughness)

    return {
        "diameter_m": diameter,
        "cross_section_area_m2": A,
        "hydraulic_radius_m": R,
        "velocity_m_s": V,
        "capacity_m3_s": max_flow_rate, # Assumed to meet requirement after design
        "material_roughness": material_roughness
    }