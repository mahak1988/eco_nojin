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
    # Explicit monthly recharge [mm]. ``None`` (default) derives recharge
    # from soil_water_mm x rcoeff; a supplied value (including 0.0) is used
    # verbatim so callers can force a dry scenario.
    recharge_mm: float | None = None
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
    unmet_pumping_series_mm: list[float] = field(default_factory=list)
    total_unmet_pumping_mm: float = 0.0
    data_source: str = "simulated"
    model: str = "Groundwater bucket (linear reservoir)"


def run_groundwater_bucket(inputs: GroundwaterBucketInput) -> GroundwaterBucketOutput:
    """Run monthly groundwater balance with linear reservoir."""
    storage = max(inputs.initial_storage_mm, 0.0)
    storage_series: list[float] = []
    baseflow_series: list[float] = []
    recharge_series: list[float] = []
    pumping_series: list[float] = []
    unmet_pumping_series: list[float] = []

    for _ in range(inputs.months):
        if inputs.recharge_mm is None:
            recharge = max(inputs.soil_water_mm * inputs.rcoeff, 0.0)
        else:
            recharge = max(inputs.recharge_mm, 0.0)
        baseflow = max(storage * inputs.alpha, 0.0)
        pumping = max(inputs.pumping_mm, 0.0)

        storage = storage + recharge - baseflow - pumping

        # An aquifer that has run dry cannot deliver the water it was asked for.
        # The previous code clamped storage to zero, which silently destroyed the
        # shortfall, and still added the full requested pumping to the totals: a
        # 200 mm store against 240 mm of demand reported 240 mm extracted and
        # 0 mm remaining, so 40 mm came from nowhere and the reported extraction
        # was 2.1x the water that existed. Pumping is now capped at what the
        # aquifer can actually deliver after recharge, and the unmet part is
        # reported.
        if storage < 0.0:
            unmet_pumping = -storage
            pumping_actual = max(pumping - unmet_pumping, 0.0)
            storage = 0.0
        else:
            pumping_actual = pumping
            unmet_pumping = 0.0

        storage_series.append(round(storage, 4))
        baseflow_series.append(round(baseflow, 4))
        recharge_series.append(round(recharge, 4))
        pumping_series.append(round(pumping_actual, 4))
        unmet_pumping_series.append(round(unmet_pumping, 4))

    return GroundwaterBucketOutput(
        storage_series_mm=storage_series,
        baseflow_series_mm=baseflow_series,
        recharge_series_mm=recharge_series,
        pumping_series_mm=pumping_series,
        unmet_pumping_series_mm=unmet_pumping_series,
        final_storage_mm=round(storage, 4),
        # The totals are the sum of the published series, to the last bit. They
        # used to be accumulated from the unrounded monthly values while the
        # series were rounded to 4 decimals, so the four totals and the four
        # series described slightly different runs: a consumer reconstructing
        # the balance from the series got a different answer from one reading
        # the totals. The governing identity S(t+1) = S(t) + R - B - P is a
        # statement about the numbers this function publishes, so the totals
        # sum the published numbers rather than a private set of them.
        total_unmet_pumping_mm=sum(unmet_pumping_series),
        total_baseflow_mm=sum(baseflow_series),
        total_recharge_mm=sum(recharge_series),
        total_pumping_mm=sum(pumping_series),
    )


def estimate_aquifer_properties(
    hydraulic_conductivity_m_s: float,
    specific_yield: float,
    area_m2: float,
    water_level_drop_m: float,
) -> dict[str, Any]:
    """
    Estimates basic aquifer properties and available volume.

    The drained volume is the storage quantity S * A * dh (Freeze & Cherry,
    1979, ch. 5), so it is a function of specific yield, area and drawdown
    only. Hydraulic conductivity is echoed back as a property of the
    formation but does not enter this calculation: it sets how *fast* the
    drawdown develops, through transmissivity T = K * b, and the saturated
    thickness b is not an input here. Making the volume depend on K would
    contradict the storage definition.

    Args:
        hydraulic_conductivity_m_s: Hydraulic conductivity (m/s).
        specific_yield: Specific yield (dimensionless).
        area_m2: Area of the aquifer (m2).
        water_level_drop_m: Predicted drop in water level (m).

    Returns:
        A dictionary containing the estimated properties.

    Raises:
        ValueError: if specific yield, area or water level drop is not
            positive. A negative extent or drawdown yields a negative volume
            of water, which no caller can distinguish from a sign convention.
    """
    if specific_yield <= 0:
        raise ValueError("Specific yield must be greater than zero.")
    if area_m2 <= 0:
        raise ValueError("Aquifer area must be greater than zero.")
    if water_level_drop_m <= 0:
        raise ValueError("Water level drop must be greater than zero.")

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
        "notes": "This is a simplified estimation. A detailed hydrogeological survey is required for accurate values.",
    }
    return estimates


def calculate_theis_drawdown(
    transmissivity_m2day: float,
    storativity: float,
    pumping_rate_m3day: float,
    distance_from_well_m: float,
    time_since_pumping_start_days: float,
) -> float | None:
    """
    Calculates drawdown using the Theis equation for a confined aquifer.

    All inputs use day-based units:
    - transmissivity_m2day: m²/day
    - pumping_rate_m3day: m³/day
    - time_since_pumping_start_days: days

    Raises:
        ValueError: if the observation point is on the pumping well (r <= 0)
            or the observation time is not positive (t <= 0). Both are the
            singularity of the solution rather than a boundary case: s = Q /
            (4 pi T) E1(u) with u = r^2 S / (4 T t) is unbounded as r -> 0 and
            as t -> 0, because the instantaneous well function diverges there.
            The function used to answer both with 0.0, which reports no
            drawdown at all and is the opposite of the limit of the equation
            on the next line.
    """
    if storativity <= 0 or transmissivity_m2day <= 0:
        logger.info("Invalid parameters for Theis equation.")
        return None

    if time_since_pumping_start_days <= 0:
        raise ValueError(
            "Time since pumping start must be positive: the Theis "
            "well function W(u) diverges as t approaches zero."
        )
    if distance_from_well_m <= 0:
        raise ValueError(
            "Distance from the well must be positive: drawdown at "
            "the well face is the singularity of the Theis solution."
        )

    from scipy.special import expi  # Import here to avoid hard dependency

    T = transmissivity_m2day  # m²/day
    S = storativity  # dimensionless
    Q = pumping_rate_m3day  # m³/day (consistent with T)
    r = distance_from_well_m  # m
    t = time_since_pumping_start_days  # days

    u = (r**2 * S) / (4 * T * t)

    # W(u) is approximated by the exponential integral -Ei(-u)
    W_u = -expi(-u)
    s = (Q / (4 * math.pi * T)) * W_u  # Result in m (consistent day units)
    return s


# Example usage
if __name__ == "__main__":
    props = estimate_aquifer_properties(
        hydraulic_conductivity_m_s=1e-5, specific_yield=0.1, area_m2=10000, water_level_drop_m=2
    )
    logger.info("Aquifer Properties:", props)

    drawdown = calculate_theis_drawdown(
        transmissivity_m2day=100,
        storativity=0.0001,
        pumping_rate_m3day=1000,
        distance_from_well_m=100,
        time_since_pumping_start_days=1,
    )
    logger.info(f"Theis Drawdown Estimate: {drawdown} m")
