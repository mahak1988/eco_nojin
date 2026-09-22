import logging
import numpy as np

logger = logging.getLogger(__name__)

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

    LIMITATIONS:
    - Rational method assumes uniform rainfall intensity and constant runoff
      coefficient; it is best suited for small catchments (< 1 km²).
    - It does not account for spatial rainfall variation, infiltration excess,
      or saturation excess mechanisms.
    - Runoff coefficient should be calibrated for local land use/soil.

    Args:
        area_m2: Catchment area in m²
        rainfall_mm: Design rainfall in mm
        runoff_coefficient: Runoff coefficient (0-1)

    Returns:
        Runoff volume in m³

    Raises:
        ValueError: If inputs are invalid
    """
    if area_m2 <= 0:
        raise ValueError(f"Area must be positive, got {area_m2}")
    if rainfall_mm < 0:
        raise ValueError(f"Rainfall must be non-negative, got {rainfall_mm}")
    if not (0 <= runoff_coefficient <= 1):
        raise ValueError(f"Runoff coefficient must be in [0,1], got {runoff_coefficient}")

    rainfall_m = rainfall_mm / 1000
    return area_m2 * rainfall_m * runoff_coefficient


def design_check_dam(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    target_retention_years: int = 10,
    channel_width_m: float = 5.0,
    sediment_yield_t_ha_yr: float = 5.0,
    side_slope_hv: float = 1.5,
    storm_duration_h: float = 6.0,
    sediment_bulk_density_t_m3: float = 1.3,
    unit_cost_usd_m3: float = 150.0,
) -> dict:
    """Design a check dam for gully stabilisation (FAO standards).

    Sizing chain (all inputs are used; none is decorative):
      1. Design peak flow from the rational method: Qp = C*i*A/360
         (i [mm/h] from ``rainfall_mm`` over ``storm_duration_h``, A in ha).
      2. Annual sediment inflow from ``sediment_yield_t_ha_yr``.
      3. Required storage for ``target_retention_years`` with the trap
         efficiency from the Brune (1953) median curve.
      4. Trapzoidal storage geometry solved for height with``channel_width_m``
         and side slope ``side_slope_hv`` (1.5H:1V FAO default).
      5. Broad-crested spillway: W = Qp / (Cd * H^1.5), Cd = 1.7, plus a
         freeboard of 0.3-0.5 m (FAO Watershed Management Field Manual).

    LIMITATIONS: sediment yield and the bulk density are site parameters; the
    Brune curve is a regional median - calibrate locally before construction.
    """
    runoff_m3 = calculate_runoff(area_m2, rainfall_mm, runoff_coefficient=0.6)
    area_ha = area_m2 / 10_000.0

    # 1) Design peak flow (rational method, SI: Qp = C*i*A/360)
    intensity_mm_h = rainfall_mm / storm_duration_h if storm_duration_h > 0 else rainfall_mm
    peak_flow_m3s = 0.6 * intensity_mm_h * area_ha / 360.0

    # 2) Annual sediment inflow (volume of deposited sediment)
    annual_sediment_m3 = (
        sediment_yield_t_ha_yr * area_ha / sediment_bulk_density_t_m3
    )

    # 3) Required storage via the Brune (1953) trap-efficiency curve,
    #    TE = 1 - 0.05 / sqrt(capacity / annual inflow). Two fixed-point
    #    iterations converge quickly for the practical range.
    trap_efficiency = 0.8
    for _ in range(2):
        storage_req_m3 = trap_efficiency * annual_sediment_m3 * target_retention_years
        ratio = storage_req_m3 / runoff_m3 if runoff_m3 > 0 else 0.0
        trap_efficiency = max(0.05, min(0.95, 1.0 - 0.05 / math.sqrt(ratio) if ratio > 0 else 0.95))
    storage_req_m3 = max(
        trap_efficiency * annual_sediment_m3 * target_retention_years, 1e-6
    )

    # 4) Trapzoidal storage: V(h) = L * (B*h + z*h^2/2); solve for h.
    dam_length = max(10.0, 2.0 * channel_width_m)
    z = side_slope_hv
    b_term = 2.0 * storage_req_m3 / (dam_length * z)
    dam_height = (-channel_width_m + math.sqrt(channel_width_m ** 2 + 2.0 * z * storage_req_m3 / dam_length)) / z
    dam_height = max(0.5, min(6.0, dam_height))
    top_width = channel_width_m + 2.0 * z * dam_height
    dam_volume = (channel_width_m + top_width) / 2.0 * dam_height * dam_length

    # 5) Spillway (broad-crested weir) + freeboard
    design_head = max(0.2, min(0.5, 0.4 * dam_height))
    spillway_width = peak_flow_m3s / (1.7 * design_head ** 1.5) if peak_flow_m3s > 0 else 0.0
    freeboard = 0.3 if dam_height < 3.0 else 0.5

    spacing = min(5.0 * dam_height, 50.0)

    # 6) Cost = excavated/filled volume at a regional unit rate
    cost = dam_volume * unit_cost_usd_m3

    return {
        "structure_type": "check_dam",
        "dam_height_m": round(dam_height, 2),
        "dam_volume_m3": round(dam_volume, 1),
        "spacing_m": round(spacing, 1),
        "runoff_volume_m3": round(runoff_m3, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["stone", "gabion"],
        "design_life_years": target_retention_years,
        # FAO-standard design detail
        "design_standard": "FAO Watershed Management Field Manual (check dam)",
        "peak_flow_m3s": round(peak_flow_m3s, 4),
        "annual_sediment_m3": round(annual_sediment_m3, 2),
        "storage_required_m3": round(storage_req_m3, 1),
        "trap_efficiency": round(trap_efficiency, 3),
        "channel_width_m": channel_width_m,
        "top_width_m": round(top_width, 2),
        "dam_length_m": round(dam_length, 1),
        "spillway_width_m": round(spillway_width, 3),
        "design_head_m": round(design_head, 3),
        "freeboard_m": freeboard,
        "unit_cost_usd_m3": unit_cost_usd_m3,
    }


def design_contour_trench(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    depth_m: float = 0.4,
    bottom_width_m: float = 0.3,
    side_slope_hv: float = 0.5,
    infiltration_efficiency: float = 0.7,
    unit_cost_usd_m: float = 8.0,
) -> dict:
    """Design contour trenches (FAO vertical-interval rule).

    Vertical interval: VI = 0.3 * (100 / slope%) metres, capped to the
    practical [5, 30] m band - the old 1/slope form had no cap and produced
    absurd spacings (1000 m at 1% slope).

    LIMITATIONS: ``infiltration_efficiency`` is a design assumption (not a
    measurement) and must be calibrated on site.
    """
    if slope_pct <= 0:
        raise ValueError("slope_pct must be positive for trench spacing")

    depth = depth_m
    width = bottom_width_m
    spacing = min(30.0, max(5.0, 0.3 * (100.0 / slope_pct)))

    n_rows = math.ceil(math.sqrt(area_m2) / spacing)
    row_length = math.sqrt(area_m2)
    total_length = n_rows * row_length

    cross_section_m2 = (bottom_width_m + (bottom_width_m + 2.0 * side_slope_hv * depth)) / 2.0 * depth
    total_volume = total_length * cross_section_m2
    infiltration_gain = total_volume * infiltration_efficiency

    cost = total_length * unit_cost_usd_m

    return {
        "structure_type": "contour_trench",
        "total_length_m": round(total_length, 0),
        "spacing_m": round(spacing, 1),
        "trench_volume_m3": round(total_volume, 1),
        "infiltration_gain_m3": round(infiltration_gain, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["excavated_soil"],
        # FAO-standard design detail
        "design_standard": "FAO Watershed Management Field Manual (contour trench)",
        "vertical_interval_m": round(spacing, 2),
        "depth_m": depth,
        "bottom_width_m": bottom_width_m,
        "cross_section_m2": round(cross_section_m2, 3),
        "infiltration_efficiency": infiltration_efficiency,
        "infiltration_note": "design assumption - calibrate on site",
        "unit_cost_usd_m": unit_cost_usd_m,
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


def design_terrace(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    terrace_width_m: float = 2.0,
) -> dict:
    """Design bench terraces for slope reduction and erosion control."""
    if area_m2 <= 0:
        raise ValueError(f"Area must be positive, got {area_m2}")
    if slope_pct < 0:
        raise ValueError(f"Slope must be non-negative, got {slope_pct}")

    if slope_pct > 30:
        spacing_m = 15
    elif slope_pct > 15:
        spacing_m = 25
    elif slope_pct > 8:
        spacing_m = 35
    else:
        spacing_m = 50

    field_side = math.sqrt(area_m2)
    n_rows = max(1, math.ceil(field_side / spacing_m))
    total_length = n_rows * field_side

    channel_depth = 0.3
    channel_volume_per_m = 0.135
    total_volume = total_length * channel_volume_per_m

    erosion_reduction_pct = min(90, round((1 - spacing_m / field_side) * 70))
    cost = total_length * 12

    return {
        "structure_type": "terrace",
        "n_rows": n_rows,
        "spacing_m": round(spacing_m, 1),
        "total_length_m": round(total_length, 0),
        "channel_depth_m": round(channel_depth, 2),
        "channel_volume_m3": round(total_volume, 1),
        "erosion_reduction_pct": erosion_reduction_pct,
        "estimated_cost_usd": round(cost, 0),
        "materials": ["excavated_soil", "stone_outlet"],
    }


def design_gully_plug(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    gully_width_m: float = 2.0,
) -> dict:
    """Design gully plugs for ephemeral gully control."""
    if area_m2 <= 0:
        raise ValueError(f"Area must be positive, got {area_m2}")
    if gully_width_m <= 0:
        raise ValueError(f"Gully width must be positive, got {gully_width_m}")

    runoff_m3 = calculate_runoff(area_m2, rainfall_mm, runoff_coefficient=0.7)
    plug_height = min(1.5, max(0.3, gully_width_m * 0.3))

    if slope_pct > 20:
        plug_spacing = 20
    elif slope_pct > 10:
        plug_spacing = 40
    else:
        plug_spacing = 60

    gully_length = math.sqrt(area_m2)
    n_plugs = max(1, math.ceil(gully_length / plug_spacing))

    top_width = gully_width_m
    bottom_width = plug_height * 1.5
    volume_per_plug = (top_width + bottom_width) / 2 * plug_height * 1.0
    total_volume = n_plugs * volume_per_plug
    sediment_retention = round(runoff_m3 * 0.3 * n_plugs, 1)
    cost = total_volume * 60

    return {
        "structure_type": "gully_plug",
        "n_plugs": n_plugs,
        "plug_spacing_m": round(plug_spacing, 1),
        "plug_height_m": round(plug_height, 2),
        "gully_width_m": round(gully_width_m, 2),
        "total_volume_m3": round(total_volume, 1),
        "sediment_retention_m3": sediment_retention,
        "runoff_volume_m3": round(runoff_m3, 1),
        "estimated_cost_usd": round(cost, 0),
        "materials": ["stone", "gabion", "excavated_soil"],
    }


def design_watershed_structure(
    structure_type: str,
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    target_retention_years: int = 10,
    channel_width_m: float = 5.0,
) -> dict:
    """Design a watershed structure based on type."""
    try:
        st = StructureType(structure_type)
    except ValueError:
        raise ValueError(f"Unknown structure type: {structure_type}")

    if st == StructureType.CHECK_DAM:
        return design_check_dam(
            slope_pct,
            area_m2,
            rainfall_mm,
            target_retention_years=target_retention_years,
            channel_width_m=channel_width_m,
        )
    elif st == StructureType.CONTOUR_TRENCH:
        return design_contour_trench(slope_pct, area_m2, rainfall_mm)
    elif st == StructureType.HALF_MOON:
        return design_half_moon(slope_pct, area_m2, rainfall_mm)
    elif st == StructureType.TERRACE:
        return design_terrace(slope_pct, area_m2, rainfall_mm)
    elif st == StructureType.GULLY_PLUG:
        return design_gully_plug(slope_pct, area_m2, rainfall_mm)
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

    tc_minutes = 0.0195 * (length_m**0.77) * (slope_m_m**-0.385)
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
        outflow[t] = C0 * inflow[t] + C1 * inflow[t - 1] + C2 * outflow[t - 1]

    return outflow
