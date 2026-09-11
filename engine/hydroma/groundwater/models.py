"""Module for basic groundwater models and estimations."""
import structlog

logger = structlog.get_logger()
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundwaterBucketInput:
    """Inputs for simple linear-reservoir groundwater balance."""

    initial_storage_mm: float = 200.0
    recharge_mm: float = 50.0
    pumping_mm: float = 0.0
    alpha: float = 0.03
    rcoeff: float = 0.15
    soil_water_mm: float = 150.0
    months: int = 12


@dataclass
class GroundwaterBucketOutput:
    """Outputs from simple linear-reservoir groundwater balance."""

    storage_series_mm: list[float] = field(default_factory=list)
    baseflow_series_mm: list[float] = field(default_factory=list)
    recharge_series_mm: list[float] = field(default_factory=list)
    pumping_series_mm: list[float] = field(default_factory=list)
    final_storage_mm: float = 0.0
    total_baseflow_mm: float = 0.0
    total_recharge_mm: float = 0.0
    total_pumping_mm: float = 0.0
    data_source: str = "simulated"
    model: str = "Groundwater bucket (linear reservoir)"


def run_groundwater_bucket(inputs: GroundwaterBucketInput) -> GroundwaterBucketOutput:
    """Run monthly groundwater balance with linear reservoir."""
    storage = max(inputs.initial_storage_mm, 0.0)
    storage_series: list[float] = []
    baseflow_series: list[float] = []
    recharge_series: list[float] = []
    pumping_series: list[float] = []

    total_baseflow = 0.0
    total_recharge = 0.0
    total_pumping = 0.0

    for _ in range(inputs.months):
        recharge = max(inputs.soil_water_mm * inputs.rcoeff, 0.0)
        baseflow = max(storage * inputs.alpha, 0.0)
        pumping = max(inputs.pumping_mm, 0.0)

        storage = storage + recharge - baseflow - pumping
        storage = max(storage, 0.0)

        storage_series.append(round(storage, 4))
        baseflow_series.append(round(baseflow, 4))
        recharge_series.append(round(recharge, 4))
        pumping_series.append(round(pumping, 4))

        total_baseflow += baseflow
        total_recharge += recharge
        total_pumping += pumping

    return GroundwaterBucketOutput(
        storage_series_mm=storage_series,
        baseflow_series_mm=baseflow_series,
        recharge_series_mm=recharge_series,
        pumping_series_mm=pumping_series,
        final_storage_mm=round(storage, 4),
        total_baseflow_mm=round(total_baseflow, 4),
        total_recharge_mm=round(total_recharge, 4),
        total_pumping_mm=round(total_pumping, 4),
    )


def estimate_aquifer_properties(hydraulic_conductivity_m_s: float,
                               specific_yield: float,
                               area_m2: float,
                               water_level_drop_m: float) -> dict[str, Any]:
    """
    Estimates basic aquifer properties and available volume.

    Args:
        hydraulic_conductivity_m_s: Hydraulic conductivity (m/s).
        specific_yield: Specific yield (dimensionless).
        area_m2: Area of the aquifer (m2).
        water_level_drop_m: Predicted drop in water level (m).

    Returns:
        A dictionary containing the estimated properties.
    """
    if specific_yield <= 0:
        raise ValueError("Specific yield must be greater than zero.")

    # Estimated volume of water released per unit drop in head
    storage_coefficient = specific_yield
    volume_available_m3 = area_m2 * water_level_drop_m * specific_yield

    # Transmissivity (assuming confined aquifer for this simple calc)
    # Needs thickness for a more accurate transmissivity
    # transmissivity_m2_per_s = hydraulic_conductivity * thickness

    estimates = {
        "hydraulic_conductivity_m_s": hydraulic_conductivity_m_s,
        "specific_yield": specific_yield,
        "storage_coefficient": storage_coefficient,
        "volume_available_m3": round(volume_available_m3, 2),
        "volume_available_liters": round(volume_available_m3 * 1000, 2),
        "notes": "This is a simplified estimation. A detailed hydrogeological survey is required for accurate values."
    }
    return estimates

def calculate_theis_drawdown(transmissivity_m2day: float,
                             storativity: float,
                             pumping_rate_m3day: float,
                             distance_from_well_m: float,
                             time_since_pumping_start_days: float) -> float | None:
    """
    Calculates drawdown using the Theis equation for a confined aquifer.
    """
    if storativity <= 0 or transmissivity_m2day <= 0:
        logger.info("Invalid parameters for Theis equation.")
        return None

    from scipy.special import expi  # Import here to avoid hard dependency

    # Convert units to m2/s, m3/s, m, s if needed internally
    # For simplicity, using days and m3/day here directly
    T = transmissivity_m2day  # m2/day
    S = storativity # dimensionless
    Q = pumping_rate_m3day / 86400  # m3/s
    r = distance_from_well_m # m
    t = time_since_pumping_start_days * 86400 # seconds

    if t <= 0:
        return 0.0

    u = (r**2 * S) / (4 * T * time_since_pumping_start_days) # Using days for T
    if u <= 0:
        return 0.0

    # W(u) is approximated by the exponential integral -Ei(-u)
    W_u = -expi(-u)
    s = (Q / (4 * math.pi * T)) * W_u # Result in m if units are consistent
    return s

# Example usage
if __name__ == "__main__":
    props = estimate_aquifer_properties(
        hydraulic_conductivity_m_s=1e-5, specific_yield=0.1, area_m2=10000, water_level_drop_m=2
    )
    logger.info("Aquifer Properties:", props)

    drawdown = calculate_theis_drawdown(
        transmissivity_m2day=100, storativity=0.0001, pumping_rate_m3day=1000,
        distance_from_well_m=100, time_since_pumping_start_days=1
    )
    logger.info(f"Theis Drawdown Estimate: {drawdown} m")
