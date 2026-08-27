"""
Hydraulic Design Engine - Water Structures.

Calculates and designs basic water structures like weirs, spillways, culverts.
"""
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class WeirDesignCriteria:
    """Criteria for weir design."""
    design_flow: float  # m3/s
    weir_type: str = "broad_crested" # "sharp_crested", "broad_crested", "ogee"
    crest_height: float = 1.0  # m (height of weir above bed)
    crest_length: float = 2.0  # m (width of weir perpendicular to flow)
    upstream_water_level: float = 2.0 # m above weir crest


def design_broad_crested_weir(criteria: WeirDesignCriteria) -> dict[str, Any]:
    """
    Designs a broad-crested weir for flow measurement or control.

    Uses the formula Q = Cd * L * H^(3/2), where Cd is discharge coefficient (~0.86 for broad-crested),
    L is crest length, H is head over crest.

    Args:
        criteria: Design criteria.

    Returns:
        Dictionary containing calculated weir dimensions and properties.
    """
    Q_des = criteria.design_flow
    L = criteria.crest_length
    H = criteria.upstream_water_level - criteria.crest_height

    if H <= 0:
        raise ValueError("Upstream water level must be higher than weir crest height.")

    Cd = 0.86 # Discharge coefficient for broad-crested weir
    g = 9.81
    theoretical_Q = Cd * L * (2/3) * math.sqrt(2*g) * (H**(3/2))

    # Note: The design flow is often the known parameter. This function checks if the proposed
    # dimensions can handle it, or calculates required dimensions if flow is fixed.
    # Let's assume we want to find the required length for a given H and Q.
    required_length = Q_des / (Cd * (2/3) * math.sqrt(2*g) * (H**(3/2)))

    return {
        "type": "broad_crested",
        "design_flow_m3_s": Q_des,
        "actual_capacity_m3_s": theoretical_Q,
        "crest_length_m": criteria.crest_length,
        "required_crest_length_m": required_length,
        "head_over_crest_m": H,
        "crest_height_m": criteria.crest_height,
        "upstream_water_level_m": criteria.upstream_water_level,
        "discharge_coefficient": Cd,
        "can_handle_flow": theoretical_Q >= Q_des
    }


@dataclass
class CulvertDesignCriteria:
    """Criteria for culvert design."""
    design_flow: float  # m3/s
    inlet_type: str = "headwall" # "headwall", "grove", "projecting"
    outlet_control: bool = True # Flow controlled at outlet or inlet
    barrel_slope: float = 0.01 # m/m
    Manning_n: float = 0.012 # For concrete
    max_headwater_depth: float = 2.0 # m above invert at inlet


def design_circular_culvert(criteria: CulvertDesignCriteria) -> dict[str, Any]:
    """
    Designs a circular culvert.

    Args:
        criteria: Design criteria.

    Returns:
        Dictionary containing calculated culvert dimensions and properties.
    """
    Q_des = criteria.design_flow
    S = criteria.barrel_slope
    n = criteria.Manning_n
    HW_max = criteria.max_headwater_depth

    # This is a simplified approach. Culvert design involves complex hydraulics
    # and often uses standard charts or empirical formulas.
    # Assume full flow condition initially for sizing.
    # Q = A * R^(2/3) * S^(1/2) / n
    # For a full circle: A = pi*D^2/4, R = D/4
    # Q = (pi*D^2/4) * (D/4)^(2/3) * S^(1/2) / n
    # Q = (pi/4) * (1/4)^(2/3) * D^(8/3) * S^(1/2) / n
    # D^(8/3) = (Q * n) / ((pi/4) * (1/4)^(2/3) * S^(1/2))
    # This gives an initial estimate.

    numerator = Q_des * n
    denominator = (math.pi / 4) * ((1 / 4) ** (2 / 3)) * (S ** 0.5)
    if denominator <= 0:
        raise ValueError("Slope must be positive for culvert design.")

    D_initial = (numerator / denominator) ** (3 / 8.0)

    # Check if initial D meets headwater criteria (simplified check)
    # A_real = pi*D^2/4, V = Q/A, Head loss = f * (L/D) * (V^2/2g) (Darcy-Weisbach simplified)
    # Inlet/Outlet control calculations are much more complex.
    # For this example, we'll just return the estimated diameter.
    A_real = math.pi * (D_initial**2) / 4
    V_real = Q_des / A_real if A_real > 0 else 0

    return {
        "type": "circular",
        "design_flow_m3_s": Q_des,
        "estimated_diameter_m": D_initial,
        "cross_section_area_full_m2": A_real,
        "velocity_full_m_s": V_real,
        "barrel_slope": S,
        "manning_n": n,
        "max_allowable_headwater_m": HW_max,
        "note": "Design is preliminary. Detailed inlet/outlet control checks required using standard culvert design methods."
    }
