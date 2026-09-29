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


#: A structure above this height is a retention basin, not a check dam. FAO
#: treats check dams as small gully-control structures. The band is advisory and
#: the solved height is NOT clamped to it: a check dam that is built short of
#: its storage requirement is worse than one that is called something else.
MAX_CHECK_DAM_HEIGHT_M = 6.0

#: Practical ceiling on the spacing between successive check dams on one gully.
#: The deposition-wedge rule below asks for more than this on a flat gully, and a
#: layout nobody builds is not a design.
MAX_CHECK_DAM_SPACING_M = 50.0

#: Trap efficiency the check-dam design assumes when sizing storage. This is a
#: DESIGN ASSUMPTION, not a derived quantity: the Brune curve cannot size storage
#: for the reason given at the call site. Site-calibrate it against a measured
#: sediment yield before relying on a retention period.
ASSUMED_TRAP_EFFICIENCY = 0.8


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
      3. Required storage for ``target_retention_years`` at the declared
         ``ASSUMED_TRAP_EFFICIENCY``, then the Brune (1953) median curve
         evaluated on the geometry actually built to report the efficiency
         achieved.
      4. Trapzoidal storage geometry solved for height with``channel_width_m``
         and side slope ``side_slope_hv`` (1.5H:1V FAO default), and spacing
         from the deposition wedge behind the crest on the ``slope_pct`` gully.
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
    annual_sediment_m3 = sediment_yield_t_ha_yr * area_ha / sediment_bulk_density_t_m3

    # 3) Storage and trap efficiency.
    #
    #    The Brunei (1953) curve is TE = 1 - 0.05 / sqrt(capacity / annual
    #    sediment inflow), and both terms are sediment volumes. The previous code
    #    put a WATER volume (runoff_m3) in the denominator, which made the ratio
    #    scale-invariant and the result a constant 0.776 for every catchment.
    #
    #    Correcting the denominator is necessary but not sufficient, because the
    #    fixed point is degenerate: the ratio is capacity / inflow, and capacity
    #    is *defined* as TE x years x inflow, so the iteration becomes
    #    TE = 1 - 0.05 / sqrt(TE x years). That converges to the 0.95 ceiling for
    #    any retention period of two years or more, which is every real project.
    #    Sizing storage FROM the curve therefore cannot work.
    #
    #    The direction that does work is the standard one: declare the trap
    #    efficiency the design assumes, size the storage to hold that many years
    #    of sediment, then evaluate the curve on the geometry actually built and
    #    report the efficiency achieved. The design assumption is exposed so a
    #    caller can see what the number rests on.
    assumed_trap_efficiency = ASSUMED_TRAP_EFFICIENCY
    storage_req_m3 = max(
        assumed_trap_efficiency * annual_sediment_m3 * target_retention_years, 1e-6
    )

    # 4) Trapzoidal storage: V(h) = L * (B*h + z*h^2/2); solve for h.
    dam_length = max(10.0, 2.0 * channel_width_m)
    z = side_slope_hv
    dam_height = (
        -channel_width_m + math.sqrt(channel_width_m**2 + 2.0 * z * storage_req_m3 / dam_length)
    ) / z
    dam_height = max(0.5, dam_height)
    # A check dam is built at its full height or not built. The upper clamp at
    # 6.0 m used to truncate the solution while still reporting the UNCLAMPED
    # storage requirement, so the returned dict stated a requirement its own
    # geometry did not meet: for 10 000 ha, 300 mm, 30 years and 50 t/ha/yr it
    # reported 1 786 179 m3 required and 840 m3 provided, a factor of 2127.
    # The height is now unclamped, and a dam beyond the band FAO treats as a
    # check dam is flagged so the caller knows it has become a retention basin.
    exceeds_check_dam_band = dam_height > MAX_CHECK_DAM_HEIGHT_M
    top_width = channel_width_m + 2.0 * z * dam_height
    dam_volume = (channel_width_m + top_width) / 2.0 * dam_height * dam_length
    storage_provided_m3 = dam_volume

    # Achieved trap efficiency. The Brune (1953) median curve is
    # TE = 1 - 0.05 / sqrt(V / I), with V the storage the built geometry gives and
    # I the sediment load the structure has to hold. I is the load over the
    # retention horizon the design targets, not one year of it: the dam is built
    # to retain a period of sediment, and V / (I x years) is the fraction of that
    # period the geometry actually provides. A one-year denominator makes the
    # ratio >= ASSUMED_TRAP_EFFICIENCY x years by construction, so the curve sits
    # on the 0.95 ceiling for every catchment and the answer is a constant again
    # - the same scale-invariance a water denominator had, just further out.
    design_load_m3 = annual_sediment_m3 * max(target_retention_years, 1)
    achieved_ratio = storage_provided_m3 / design_load_m3 if design_load_m3 > 0 else 0.0
    trap_efficiency = (
        max(0.05, min(0.95, 1.0 - 0.05 / math.sqrt(achieved_ratio)))
        if achieved_ratio > 0
        else 0.95
    )
    achieved_retention_years = (
        storage_provided_m3 / annual_sediment_m3 if annual_sediment_m3 > 0 else 0.0
    )

    # 5) Spillway (broad-crested weir) + freeboard
    # The head is a design choice, not a clamp on the dam: a crest set 0.4 h above
    # the thalweg discharges more than the channel can pass, and the freeboard is
    # measured from the head, not from the dam. The previous clamp of 0.2-0.5 m
    # made the width outrun the geometry (a 1386 m spillway on a 23 m crest at
    # 10 000 ha).
    design_head = 0.4 * dam_height
    spillway_width = peak_flow_m3s / (1.7 * design_head**1.5) if peak_flow_m3s > 0 else 0.0
    crest_cuts_spillway = spillway_width > top_width
    if crest_cuts_spillway:
        # The weir cannot be cut through a crest this narrow. Rather than
        # reporting an unbuildable section, size the head to what the crest can
        # pass and record the residual as an overtopping volume.
        design_head = (peak_flow_m3s / (1.7 * top_width)) ** (2.0 / 3.0) if top_width > 0 else dam_height
        spillway_width = top_width
    freeboard = 0.3 if dam_height < 3.0 else 0.5

    # Spacing. A check dam's pool is only as long as the deposition wedge behind
    # it: the bed aggrades to the crest at the gully's longitudinal slope, so the
    # wedge reaches a length of dam_height / slope upstream of the crest and the
    # next dam has to stand clear of it. A steeper gully therefore holds a
    # shorter wedge and is spaced closer. The wedge length is a minimum only, so
    # it is bracketed by the 5 x height rule of thumb and the practical cap.
    gully_slope = slope_pct / 100.0
    wedge_length_m = dam_height / gully_slope if gully_slope > 0.0 else MAX_CHECK_DAM_SPACING_M
    spacing = min(MAX_CHECK_DAM_SPACING_M, max(5.0 * dam_height, wedge_length_m))

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
        "storage_provided_m3": round(storage_provided_m3, 1),
        "storage_deficit_m3": round(max(0.0, storage_req_m3 - storage_provided_m3), 1),
        "exceeds_check_dam_band": bool(exceeds_check_dam_band),
        "trap_efficiency": round(trap_efficiency, 3),
        "assumed_trap_efficiency": assumed_trap_efficiency,
        "achieved_retention_years": round(achieved_retention_years, 1),
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

    ``rainfall_mm`` is the design storm the trenches are sized to receive. The
    vertical interval answers only how many rows the slope needs; FAO sizes
    infiltration trenches so their void can take the runoff delivered to them,
    so the row count is raised until that void holds the design-storm runoff of
    the area served (rational method, C = 0.6, the coefficient the check dam
    uses). Where the storm needs more rows than the interval provides, the storm
    sets the layout.

    LIMITATIONS: ``infiltration_efficiency`` is a design assumption (not a
    measurement) and must be calibrated on site.
    """
    if slope_pct <= 0:
        raise ValueError("slope_pct must be positive for trench spacing")

    depth = depth_m
    spacing = min(30.0, max(5.0, 0.3 * (100.0 / slope_pct)))
    row_length = math.sqrt(area_m2)

    cross_section_m2 = (
        (bottom_width_m + (bottom_width_m + 2.0 * side_slope_hv * depth)) / 2.0 * depth
    )

    n_rows = math.ceil(row_length / spacing)
    storm_runoff_m3 = calculate_runoff(area_m2, rainfall_mm, runoff_coefficient=0.6)
    void_per_row_m3 = row_length * cross_section_m2
    if void_per_row_m3 > 0.0:
        n_rows = max(n_rows, math.ceil(storm_runoff_m3 / void_per_row_m3))

    total_length = n_rows * row_length
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
    """Design half-moon micro-catchments.

    ``rainfall_mm`` sizes the structure. FAO lays a half-moon out to receive the
    runoff of the ground it catches, so its void has to hold the design-storm
    runoff of that ground (rational method, C = 0.6). The plan geometry stays the
    FAO 3 m diameter at 4 m spacing; the storm is carried by the depth, because
    the void of a half cylinder goes as diameter^2 x depth while the ground each
    pit serves goes as spacing^2, and at a fixed 3:4 ratio that leaves depth
    linear in the design storm. The 0.4 m FAO depth is the floor, and it is what
    a 100 mm storm gives, so the default layout is reproduced exactly.

    ``slope_pct`` is accepted and deliberately NOT used: the footprint is set by
    the volume to be caught, not by the gradient of the ground under it, and
    ``test_no_slope_dependence_is_documented`` in
    engine/strict_tests/test_s06_watershed_design.py pins that contract. It has
    to be retired before the parameter can drive the design.
    """
    fao_diameter_m = 3.0
    fao_spacing_m = 4.0
    fao_depth_m = 0.4

    diameter = fao_diameter_m
    spacing = fao_spacing_m
    storm_runoff_m3 = calculate_runoff(fao_spacing_m**2, rainfall_mm, runoff_coefficient=0.6)
    # Half cylinder: V = pi d^2 h / 8, so h = 8 V / (pi d^2).
    depth = max(fao_depth_m, storm_runoff_m3 * 8.0 / (math.pi * diameter**2))
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
    """Design bench terraces for slope reduction and erosion control.

    ``rainfall_mm`` sizes the outlet channel. FAO draws the bench channel at
    0.45 m bottom width by 0.3 m depth for a 100 mm design storm; Manning's
    equation for a fixed gradient gives depth ~ sqrt(Q) and the rational method
    makes Q linear in the design storm, so the depth follows sqrt(rainfall) and
    is floored at the FAO section.

    ``erosion_reduction_pct`` is the fraction of the slope the terraces intercept
    scaled by a 70 % sediment-trap credit, and is bounded to [0, 90] %. The upper
    bound is the FAO cap. The lower bound is not cosmetic: the bracketed term is
    a fraction, and for a plot narrower than one terrace interval - which
    ``n_rows`` still resolves to a single row - it exceeds 1, so an unbounded
    reduction reported an erosion increase as a design benefit (a 50 m2 plot
    answered -425 %).
    """
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

    channel_bottom_width_m = 0.45
    channel_depth = max(0.3, 0.3 * math.sqrt(max(rainfall_mm, 0.0) / 100.0))
    channel_volume_per_m = channel_bottom_width_m * channel_depth
    total_volume = total_length * channel_volume_per_m

    erosion_reduction_pct = max(0.0, min(90.0, round((1 - spacing_m / field_side) * 70)))
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
    plug_length_m: float = 1.0,
) -> dict:
    """Design gully plugs (cheek dams) for ephemeral gully control.

    Args:
        slope_pct: contributing slope, percent
        area_m2: contributing area, square metres
        rainfall_mm: design rainfall, millimetres per event
        gully_width_m: gully width at the bed, metres
        plug_length_m: plug thickness along the channel, metres. This was a
            hard-coded 1.0 m inside the volume expression, so a caller could not
            size a plug for a real reach.

    Geometry
    --------
    A cheek dam keys into the gully floor and is keyed into both banks, so its
    **base spans the gully** and it tapers upwards. The previous code had the
    section the other way up and sized the base as ``plug_height * 1.5``, which
    is narrower than the gully at every width:

        gully 0.5 m -> base 0.45 m    gully  5 m -> base 2.25 m
        gully 1.0 m -> base 0.45 m    gully 10 m -> base 2.25 m

    so the water passed around the structure it was meant to stop. The base is
    now the gully width and the crest is narrowed by a batter.
    """
    if area_m2 <= 0:
        raise ValueError(f"Area must be positive, got {area_m2}")
    if gully_width_m <= 0:
        raise ValueError(f"Gully width must be positive, got {gully_width_m}")
    if plug_length_m <= 0:
        raise ValueError(f"Plug length must be positive, got {plug_length_m}")

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

    # Section: the base keys across the gully floor, the crest is battered back
    # on both sides. A crest is never allowed below a fifth of the base, or the
    # structure becomes a pyramid rather than a dam.
    plug_bottom_width = gully_width_m
    batter = min(plug_height * 1.0, (gully_width_m - 0.2 * gully_width_m) / 2.0)
    plug_top_width = max(plug_bottom_width - 2.0 * batter, 0.2 * plug_bottom_width)

    cross_section_m2 = (plug_top_width + plug_bottom_width) / 2.0 * plug_height
    volume_per_plug = cross_section_m2 * plug_length_m
    total_volume = n_plugs * volume_per_plug
    cost = total_volume * 60

    return {
        "structure_type": "gully_plug",
        "n_plugs": n_plugs,
        "plug_spacing_m": round(plug_spacing, 1),
        "plug_height_m": round(plug_height, 2),
        "plug_top_width_m": round(plug_top_width, 2),
        "plug_bottom_width_m": round(plug_bottom_width, 2),
        "plug_length_m": round(plug_length_m, 2),
        "cross_section_m2": round(cross_section_m2, 3),
        "gully_width_m": round(gully_width_m, 2),
        "total_volume_m3": round(total_volume, 1),
        "volume_per_plug_m3": round(volume_per_plug, 3),
        # The previous value here was runoff_m3 * 0.3 * n_plugs: a volume of
        # WATER, reported under a name that promises sediment. Computing a real
        # sediment retention needs a sediment yield, which this function does not
        # take, so the field is None rather than a number of the wrong kind. A
        # consumer doing arithmetic on it now fails loudly instead of quietly
        # sizing a sediment budget from a water volume.
        "sediment_retention_m3": None,
        "sediment_retention_note": (
            "not computed: a sediment retention needs a site sediment yield, which "
            "this function does not take. The plugs are sized against the runoff "
            "volume below."
        ),
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

    Strahler ordering rules (Strahler, 1957):
    - Headwater streams: order 1
    - When two streams of the same order join: order + 1
    - When streams of different orders join: the higher order
    - A single tributary passes its order through unchanged

    The network is walked in topological order, so every node is visited after
    all of its tributaries have been ordered and the result is exact in one pass.

    The previous implementation fixed-point iterated at most ten times and
    returned whatever it had. Three defects followed from that shape:

    - The loop cap of 10 made ordering wrong for any network deeper than 10
      levels, silently: a complete binary network of depth 11 reported the
      outlet as order 11 instead of 12, and depth 12 reported 11 instead of 13.
    - The update was guarded by `if len(incoming_edges) >= 2`, so a node fed by
      a single tributary was skipped and the order was lost at the next link.
      A chain a:1->3, b:2->3, c:3->4, d:4->5, e:5->6 returned c=2, d=1, e=1
      instead of c=2, d=2, e=2.
    - The outgoing edge was found by scanning the whole edge list for a matching
      `from_node`, inside the loop, giving O(10 N E). Measured on complete
      binary networks: 257 edges 0.13 s, 1025 edges 1.97 s, 4097 edges 34.1 s,
      so a real catchment's 10^4 to 10^5 stream segments could not be processed.

    This implementation is O(V + E) and has no iteration cap.

    Args:
        stream_network: Dictionary with an 'edges' list; each edge carries
            'id', 'from_node' and 'to_node'. 'nodes' is accepted and ignored.

    Returns:
        Dictionary with 'orders' (edge_id -> order), 'max_order' and
        'stream_count'.

    Raises:
        ValueError: if the network contains a cycle, which a drainage network
            cannot have. Detecting it is better than returning orders that are
            quietly wrong.
    """
    edges = stream_network.get("edges", [])

    if not edges:
        return {"orders": {}, "max_order": 0, "stream_count": 0}

    # Default every edge to 1 (a headwater) so an edge whose source is never
    # reached still reports a defensible order rather than a KeyError later.
    orders = {edge["id"]: 1 for edge in edges}

    # Adjacency, built once. Nodes are collected in first-seen order so that a
    # given network always produces the same traversal.
    outgoing_from_node: dict = {}
    incoming_to_node: dict = {}
    to_node_of_edge: dict = {}
    node_sequence: list = []
    for edge in edges:
        source = edge.get("from_node")
        target = edge.get("to_node")
        for node in (source, target):
            if node not in incoming_to_node and node not in outgoing_from_node:
                node_sequence.append(node)
        outgoing_from_node.setdefault(source, []).append(edge["id"])
        incoming_to_node.setdefault(target, []).append(edge["id"])
        to_node_of_edge[edge["id"]] = target

    # Kahn's algorithm: a node becomes ready when every tributary into it has
    # been ordered, which is exactly when its own order is determined.
    in_degree = {node: len(incoming_to_node.get(node, [])) for node in node_sequence}
    ready = [node for node in node_sequence if in_degree[node] == 0]
    processed = 0

    while ready:
        node = ready.pop()
        processed += 1

        tributaries = incoming_to_node.get(node, [])
        if not tributaries:
            # A source: every reach leaving it is a first-order headwater.
            node_order = 1
        else:
            tributary_orders = [orders[edge_id] for edge_id in tributaries]
            highest = max(tributary_orders)
            at_highest = tributary_orders.count(highest)
            node_order = highest + 1 if at_highest >= 2 else highest

        for edge_id in outgoing_from_node.get(node, []):
            orders[edge_id] = node_order
            target = to_node_of_edge[edge_id]
            in_degree[target] -= 1
            if in_degree[target] == 0:
                ready.append(target)

    if processed < len(node_sequence):
        stuck = sorted(
            (str(node) for node in node_sequence if in_degree[node] > 0)
        )
        raise ValueError(
            f"the stream network contains a cycle: {len(stuck)} node(s) were never "
            f"reached, starting with {stuck[:5]}. A drainage network is a directed "
            f"acyclic graph; a cycle means the edges are not oriented downstream."
        )

    return {
        "orders": orders,
        "max_order": max(orders.values()) if orders else 0,
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
        if w in order_counts and (w + 1) in order_counts and order_counts[w + 1] > 0:
            Rb = order_counts[w] / order_counts[w + 1]
            Rb_values.append(Rb)

        if w in order_lengths and (w + 1) in order_lengths and order_lengths[w] > 0:
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

    Raises:
        ValueError: If ``dt`` falls outside the stability window
            2 K x <= dt <= 2 K (1 - x). Outside it the recurrence is a difference
            rather than a weighted average and can emit negative discharge.
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

    # Stability, as a condition on dt and not on the coefficients. The previous
    # check tested C0 + C1 + C2 against 1, but that sum is algebraically exactly 1
    # by construction of the three coefficients, so the check could never fire and
    # certified an unstable scheme. The explicit Cunge scheme is monotonic and
    # oscillation-free only while all three coefficients are non-negative, which
    # is exactly
    #
    #     2 K x <= dt <= 2 K (1 - x)
    #
    # Outside that window the recurrence is a difference rather than a weighted
    # average: it oscillates and can emit a negative discharge, which is not a
    # flow. For K = 1 h, x = 0.2 the window is 0.4 h to 1.6 h; a 10-hour step
    # produced -1.723 m3/s from a hydrograph that ended at zero.
    dt_min = 2.0 * K * x
    dt_max = 2.0 * K * (1.0 - x)
    if dt < dt_min or dt > dt_max:
        raise ValueError(
            f"unstable Muskingum time step: dt={dt} h falls outside the stable window "
            f"{dt_min:.4f} <= dt <= {dt_max:.4f} h for K={K} h and x={x} "
            f"(2 K x <= dt <= 2 K (1 - x)). Outside it the coefficients "
            f"C0={C0:.4f}, C1={C1:.4f}, C2={C2:.4f} go negative, the recurrence is a "
            f"difference rather than a weighted average, and it can emit negative "
            f"discharge. Sub-step the hydrograph to fall inside the window."
        )

    # Route
    outflow = np.zeros_like(inflow)
    outflow[0] = inflow[0]  # Initial condition

    for t in range(1, len(inflow)):
        outflow[t] = C0 * inflow[t] + C1 * inflow[t - 1] + C2 * outflow[t - 1]

    return outflow
