"""
Earthwork Calculation Engine.

Calculates volumes of cut and fill for civil engineering projects
like roads, canals, dams, and land grading based on terrain analysis.
"""
import numpy as np
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class CrossSection:
    """Represents a single cross-section along a route."""
    station: float  # Distance along the route (m)
    ground_levels: List[float]  # Elevations at sample points (m)
    formation_width: float  # Width of the structure at this point (m)
    side_slope_cut: float  # Side slope for cutting (H:V)
    side_slope_fill: float  # Side slope for filling (H:V)
    formation_level: float  # Desired finished ground level (m)


def calculate_area_cut_fill(ground_levels: np.ndarray, formation_level: float, width: float, side_slope: float) -> Tuple[float, float]:
    """
    Calculates cut and fill area for a single cross-section.

    Args:
        ground_levels: Array of ground elevations across the section.
        formation_level: Target elevation for the finished surface.
        width: Formation width.
        side_slope: Side slope ratio (horizontal distance per unit vertical distance).

    Returns:
        Tuple of (cut_area, fill_area) in square meters.
    """
    # Simplified method: Trapezoidal approximation
    # Determine if section is pure cut, pure fill, or mixed
    avg_ground_level = np.mean(ground_levels)
    cut_depth = max(0, avg_ground_level - formation_level)
    fill_height = max(0, formation_level - avg_ground_level)

    cut_area = 0.0
    fill_area = 0.0

    if cut_depth > 0:
        # Area of a trapezoid: A = (a + b) * h / 2
        # For cut: a = width, b = width + 2 * cut_depth * side_slope, h = cut_depth
        top_width_cut = width + 2 * cut_depth * side_slope
        cut_area = (width + top_width_cut) * cut_depth / 2.0

    if fill_height > 0:
        # Area of a trapezoid for fill: A = (a + b) * h / 2
        # For fill: a = width, b = width + 2 * fill_height * side_slope, h = fill_height
        top_width_fill = width + 2 * fill_height * side_slope
        fill_area = (width + top_width_fill) * fill_height / 2.0

    return cut_area, fill_area


def calculate_earthwork_volumes(cross_sections: List[CrossSection]) -> Dict[str, Any]:
    """
    Calculates cumulative cut and fill volumes along a route using the Average End Area Method.

    Args:
        cross_sections: List of CrossSection objects along the route.

    Returns:
        Dictionary containing volume calculations.
    """
    if len(cross_sections) < 2:
        return {"error": "At least two cross-sections are required."}

    total_cut_vol = 0.0
    total_fill_vol = 0.0
    volumes = []

    for i in range(len(cross_sections) - 1):
        cs1 = cross_sections[i]
        cs2 = cross_sections[i+1]

        station_dist = cs2.station - cs1.station

        # Calculate areas for both sections
        cut_area_1, fill_area_1 = calculate_area_cut_fill(
            np.array(cs1.ground_levels), cs1.formation_level, cs1.formation_width, cs1.side_slope_cut
        )
        cut_area_2, fill_area_2 = calculate_area_cut_fill(
            np.array(cs2.ground_levels), cs2.formation_level, cs2.formation_width, cs2.side_slope_cut
        )

        # Average End Area Method: Vol = (A1 + A2) / 2 * L
        cut_vol_seg = (cut_area_1 + cut_area_2) / 2.0 * station_dist
        fill_vol_seg = (fill_area_1 + fill_area_2) / 2.0 * station_dist

        total_cut_vol += cut_vol_seg
        total_fill_vol += fill_vol_seg

        volumes.append({
            "segment_start_station": cs1.station,
            "segment_end_station": cs2.station,
            "distance_m": station_dist,
            "cut_area_start_m2": cut_area_1,
            "cut_area_end_m2": cut_area_2,
            "fill_area_start_m2": fill_area_1,
            "fill_area_end_m2": fill_area_2,
            "cut_volume_m3": cut_vol_seg,
            "fill_volume_m3": fill_vol_seg
        })

    # Calculate shrinkage/swell factors if needed
    net_volume = total_cut_vol - total_fill_vol

    return {
        "total_cut_volume_m3": total_cut_vol,
        "total_fill_volume_m3": total_fill_vol,
        "net_excess_or_shortage_m3": net_volume,
        "is_balanced": abs(net_volume) < 100,  # Arbitrary tolerance
        "segments": volumes
    }
