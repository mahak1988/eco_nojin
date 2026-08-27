"""Module for watershed structure design calculations."""
from typing import Any


def design_check_dam(slope_pct: float, area_m2: float, rainfall_mm: float) -> dict[str, Any]:
    """
    Designs a basic check dam based on slope, area, and rainfall.

    Args:
        slope_pct: Average slope of the area in percent.
        area_m2: Contributing area upstream in square meters.
        rainfall_mm: Design rainfall intensity in millimeters per hour.

    Returns:
        A dictionary containing the design proposal.
    """
    # Simple empirical formula for discharge (Q = CIA, C=runoff coeff, I=rainfall, A=area)
    # Assume a typical runoff coefficient for the given conditions
    runoff_coefficient = 0.6 + (slope_pct / 100.0) * 0.2 # Simplified assumption
    rainfall_m_per_hour = rainfall_mm / 1000.0
    area_m2 = max(area_m2, 1.0) # Avoid division by zero
    discharge_m3_per_sec = (runoff_coefficient * rainfall_m_per_hour * area_m2) / 3600.0

    # Simplified design for a trapezoidal weir
    design_head_m = 0.3  # Assumed head over weir
    weir_length_m = discharge_m3_per_sec / (1.84 * (design_head_m ** 1.5))

    # Dimensions
    height_m = design_head_m + 0.3  # Freeboard
    width_m = weir_length_m
    material_estimate_m3 = height_m * width_m * 0.5  # Rough estimate

    proposal = {
        "type": "check_dam",
        "material": "concrete",
        "dimensions": {
            "height_m": round(height_m, 2),
            "width_m": round(width_m, 2),
            "length_m": round(weir_length_m, 2),
        },
        "estimated_discharge_m3s": round(discharge_m3_per_sec, 4),
        "material_estimate_m3": round(material_estimate_m3, 2),
        "notes": "This is a simplified preliminary design. A detailed engineering study is required for construction."
    }
    return proposal

# Example usage
if __name__ == "__main__":
    result = design_check_dam(slope_pct=15.0, area_m2=5000.0, rainfall_mm=50.0)
    print(result)
