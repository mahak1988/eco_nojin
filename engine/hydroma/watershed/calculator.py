"""Watershed structure calculator for soil and water conservation.

Implements design calculations for:
- Check dams (sediment retention)
- Contour trenches (infiltration)
- Half-moons (micro-catchments)
- Terraces (slope reduction)

Reference: FAO Watershed Management Field Manual
"""
import math
from typing import Dict
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
    volume_per_structure = 0.5 * math.pi * radius ** 2 * depth
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
