
import numpy as np

"""Watershed structure calculator for soil and water conservation.

Implements design calculations for:
- Check dams (sediment retention)
- Contour trenches (infiltration)
- Half-moons (micro-catchments)
- Terraces (slope reduction)

Reference: FAO Watershed Management Field Manual
"""

import math
from enum import Enum


class StructureType(Enum):
    """Types of watershed conservation structures."""

    CHECK_DAM = "check_dam"
    CONTOUR_TRENCH = "contour_trench"
    HALF_MOON = "half_moon"
    TERRACE = "terrace"
    GULLY_PLUG = "gully_plug"


def calculate_runoff(
    area_m2: float,
    rainfall_mm: float,
    runoff_coefficient: float = 0.5,
) -> float:
    """Calculate runoff volume using rational method.

    Args:
        area_m2: Catchment area in m²
        rainfall_mm: Design rainfall in mm
        runoff_coefficient: Runoff coefficient (0-1)

    Returns:
        Runoff volume in m³
    """
    rainfall_m = rainfall_mm / 1000
    return area_m2 * rainfall_m * runoff_coefficient


def design_check_dam(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    target_retention_years: int = 10,
) -> dict:
    """Design a check dam for gully stabilization."""
    runoff_m3 = calculate_runoff(area_m2, rainfall_mm, runoff_coefficient=0.6)

    # Dam height based on slope
    dam_height = min(3.0, max(0.5, slope_pct / 10))

    # Dam volume (trapezoidal cross-section)
    top_width = 0.5
    bottom_width = dam_height * 2
    dam_length = 10
    dam_volume = (top_width + bottom_width) / 2 * dam_height * dam_length

    spacing = 5 * dam_height

    # Cost
    cost = dam_volume * 150

    return {
        "structure_type": "check_dam",
        "dam_height_m": round(dam_height, 2),
        "dam_volume_m3": round(dam_volume, 1),
        "spacing_m": round(spacing, 1),
        "runoff_volume_m3": round(runoff_m3, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["stone", "gabion"],
        "design_life_years": target_retention_years,
    }


def design_contour_trench(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
) -> dict:
    """Design contour trenches for infiltration."""
    depth = 0.5
    width = 0.5
    spacing = max(5, 10 / (slope_pct / 100))

    n_rows = math.ceil(math.sqrt(area_m2) / spacing)
    row_length = math.sqrt(area_m2)
    total_length = n_rows * row_length

    total_volume = total_length * depth * width
    infiltration_gain = total_volume * 0.8

    cost = total_length * 8

    return {
        "structure_type": "contour_trench",
        "total_length_m": round(total_length, 0),
        "spacing_m": round(spacing, 1),
        "trench_volume_m3": round(total_volume, 1),
        "infiltration_gain_m3": round(infiltration_gain, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["excavated_soil"],
    }


def design_half_moon(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
) -> dict:
    """Design half-moon micro-catchments."""
    diameter = 3.0
    depth = 0.4
    spacing = 4.0
    n_structures = math.ceil(area_m2 / (spacing * spacing))

    radius = diameter / 2
    volume_per_structure = 0.5 * math.pi * radius**2 * depth
    total_volume = n_structures * volume_per_structure

    cost = n_structures * 5

    return {
        "structure_type": "half_moon",
        "n_structures": n_structures,
        "diameter_m": diameter,
        "volume_per_structure_m3": round(volume_per_structure, 2),
        "total_volume_m3": round(total_volume, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["excavated_soil"],
    }


def design_watershed_structure(
    structure_type: str,
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
) -> dict:
    """Design a watershed structure based on type."""
    try:
        st = StructureType(structure_type)
    except ValueError:
        raise ValueError(f"Unknown structure type: {structure_type}")

    if st == StructureType.CHECK_DAM:
        return design_check_dam(slope_pct, area_m2, rainfall_mm)
    elif st == StructureType.CONTOUR_TRENCH:
        return design_contour_trench(slope_pct, area_m2, rainfall_mm)
    elif st == StructureType.HALF_MOON:
        return design_half_moon(slope_pct, area_m2, rainfall_mm)
    else:
        return {
            "structure_type": structure_type,
            "slope_pct": slope_pct,
            "area_m2": area_m2,
            "message": "Design calculation not yet implemented",
        }


# ═══════════════════════════════════════════════════════════════════
# STRAHLER STREAM ORDERING
# ═══════════════════════════════════════════════════════════════════

def calculate_strahler_order(stream_network: dict) -> dict:
    """
    Calculate Strahler stream order for a drainage network.
    
    Strahler ordering rules:
    - Headwater streams: Order 1
    - When two streams of same order join: Order + 1
    - When streams of different order join: Max order
    
    Args:
        stream_network: Dictionary with 'nodes' and 'edges'
        
    Returns:
        Dictionary with:
            - 'orders': Dict mapping edge_id to order
            - 'max_order': Maximum order in network
            - 'stream_count': Total number of streams
    """
    nodes = stream_network.get("nodes", [])
    edges = stream_network.get("edges", [])

    # Handle empty network
    if not edges:
        return {"orders": {}, "max_order": 0, "stream_count": 0}

    # Initialize all edges as order 1 (headwaters)
    orders = {edge["id"]: 1 for edge in edges}

    # Build adjacency: node -> list of incoming edge IDs
    incoming_to_node = {}
    for edge in edges:
        to_node = edge.get("to_node")
        if to_node not in incoming_to_node:
            incoming_to_node[to_node] = []
        incoming_to_node[to_node].append(edge["id"])

    # Iterate to convergence
    for iteration in range(10):
        changed = False

        for node, incoming_edges in incoming_to_node.items():
            if len(incoming_edges) >= 2:
                # Get orders of all incoming edges
                incoming_orders = [orders[e] for e in incoming_edges if e in orders]
                if not incoming_orders:
                    continue

                max_order = max(incoming_orders)
                count_max = incoming_orders.count(max_order)

                # Find outgoing edge (from this node)
                for edge in edges:
                    if edge.get("from_node") == node:
                        old_order = orders.get(edge["id"], 0)

                        # Strahler rule
                        if count_max >= 2:
                            new_order = max_order + 1
                        else:
                            new_order = max_order

                        if new_order != old_order:
                            orders[edge["id"]] = new_order
                            changed = True

        if not changed:
            break

    max_order = max(orders.values()) if orders else 0

    return {
        "orders": orders,
        "max_order": max_order,
        "stream_count": len(edges),
    }


# ═══════════════════════════════════════════════════════════════════
# HORTON RATIOS
# ═══════════════════════════════════════════════════════════════════

def calculate_horton_ratios(strahler_result: dict, stream_lengths: dict) -> dict:
    """
    Calculate Horton's ratios for stream network analysis.
    
    Horton's Laws:
    - Bifurcation Ratio (Rb): N_ω / N_(ω+1)
    - Length Ratio (Rl): L_(ω+1) / L_ω
    - Area Ratio (Ra): A_(ω+1) / A_ω
    
    Args:
        strahler_result: Result from calculate_strahler_order
        stream_lengths: Dict mapping edge_id to length
    
    Returns:
        Dictionary with Horton ratios
    """
    orders = strahler_result.get("orders", {})
    max_order = strahler_result.get("max_order", 0)

    if max_order < 2:
        return {"Rb": 0, "Rl": 0, "Ra": 0}

    # Count streams per order
    order_counts = {}
    for edge_id, order in orders.items():
        order_counts[order] = order_counts.get(order, 0) + 1

    # Calculate total length per order
    order_lengths = {}
    for edge_id, order in orders.items():
        length = stream_lengths.get(edge_id, 0)
        order_lengths[order] = order_lengths.get(order, 0) + length

    # Calculate ratios
    Rb_values = []
    Rl_values = []

    for w in range(1, max_order):
        if w in order_counts and (w + 1) in order_counts:
            if order_counts[w + 1] > 0:
                Rb = order_counts[w] / order_counts[w + 1]
                Rb_values.append(Rb)

        if w in order_lengths and (w + 1) in order_lengths:
            if order_lengths[w] > 0:
                Rl = order_lengths[w + 1] / order_lengths[w]
                Rl_values.append(Rl)

    return {
        "Rb": np.mean(Rb_values) if Rb_values else 0,
        "Rl": np.mean(Rl_values) if Rl_values else 0,
        "Ra": 0,  # Area ratio requires catchment data
        "order_counts": order_counts,
        "order_lengths": order_lengths,
    }


# ═══════════════════════════════════════════════════════════════════
# KIRPICH TIME OF CONCENTRATION
# ═══════════════════════════════════════════════════════════════════

def calculate_kirpich_tc(length_m: float, slope_m_m: float) -> float:
    """
    Calculate Time of Concentration using Kirpich formula.
    
    Tc = 0.0195 * L^0.77 * S^(-0.385)
    
    Where:
        Tc = Time of concentration (minutes)
        L = Length of longest flow path (meters)
        S = Average slope (m/m)
    
    Args:
        length_m: Length of longest flow path in meters
        slope_m_m: Average slope (m/m)
    
    Returns:
        Time of concentration in minutes
    """
    if length_m <= 0 or slope_m_m <= 0:
        return 0.0

    tc_minutes = 0.0195 * (length_m ** 0.77) * (slope_m_m ** -0.385)
    return float(tc_minutes)


# ═══════════════════════════════════════════════════════════════════
# MUSKINGUM ROUTING
# ═══════════════════════════════════════════════════════════════════

def muskingum_route(
    inflow: np.ndarray,
    K: float,
    x: float,
    dt: float,
) -> np.ndarray:
    """
    Route flow through channel using Muskingum method.
    
    Muskingum equation:
    O(t+1) = C0*I(t+1) + C1*I(t) + C2*O(t)
    
    Where:
        C0 = (-K*x + 0.5*dt) / (K - K*x + 0.5*dt)
        C1 = (K*x + 0.5*dt) / (K - K*x + 0.5*dt)
        C2 = (K - K*x - 0.5*dt) / (K - K*x + 0.5*dt)
    
    Args:
        inflow: Inflow hydrograph (array of flow values)
        K: Travel time parameter (hours)
        x: Weighting factor (0-0.5, 0.2 typical)
        dt: Time step (hours)
    
    Returns:
        Outflow hydrograph
    """
    if K <= 0 or dt <= 0:
        return inflow.copy()

    # Ensure x is in valid range
    x = max(0.0, min(0.5, x))

    # Calculate coefficients
    denom = K - K * x + 0.5 * dt
    if denom <= 0:
        return inflow.copy()

    C0 = (-K * x + 0.5 * dt) / denom
    C1 = (K * x + 0.5 * dt) / denom
    C2 = (K - K * x - 0.5 * dt) / denom

    # Check stability
    if C0 + C1 + C2 < 0.99 or C0 + C1 + C2 > 1.01:
        logger.warning(f"Muskingum coefficients sum to {C0 + C1 + C2}, should be ~1.0")

    # Route
    outflow = np.zeros_like(inflow)
    outflow[0] = inflow[0]  # Initial condition

    for t in range(1, len(inflow)):
        outflow[t] = C0 * inflow[t] + C1 * inflow[t-1] + C2 * outflow[t-1]

    return outflow
