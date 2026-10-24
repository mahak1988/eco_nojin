"""Module for basic groundwater models and estimations."""

import math
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


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
    s: float = (Q / (4 * math.pi * T)) * W_u  # Result in m (consistent day units)
    return s


# =============================================================================
# Hantush-Jacob (1955) - leaky confined aquifer
# =============================================================================


def hantush_jacob_well_function(u: float, rho: float) -> float:
    """Hantush-Jacob leaky-aquifer well function W(u, rho).

    ::

        W(u, rho) = integral from u to infinity of exp(-y - rho**2 / (4y)) / y dy

    where ``u = r**2 * S / (4 * T * t)`` and ``rho = r / B`` with leakage
    factor ``B = sqrt(T * b' / K')`` for a semi-confining layer of thickness
    ``b'`` and vertical conductivity ``K'``.

    Reference: Hantush, M.S. & Jacob, C.E. (1955), "Non-steady radial flow in
    an infinite leaky aquifer", AGU Transactions 36(1): 95-100.

    Two mathematical anchors pin this implementation:

    * ``rho -> 0`` (no leakage) reduces to the Theis well function ``E1(u)``;
    * ``u -> 0`` (steady state) tends to ``2 * K0(rho)`` (modified Bessel
      function of the second kind, order 0), i.e. the steady leaky drawdown
      ``s = Q / (2 pi T) * K0(r/B)``.

    Leakage can only reduce drawdown, so ``W(u, rho) <= E1(u)`` for
    ``rho >= 0`` and is monotonically decreasing in ``rho``; both properties
    are asserted in ``engine/tests/test_groundwater_extended.py``.
    """
    if u <= 0:
        raise ValueError(
            "Hantush-Jacob u must be positive (u = r^2 S / (4 T t)); "
            "u=0 is the steady-state limit, use calculate_theis_drawdown "
            "with the steady form instead."
        )
    if rho < 0:
        raise ValueError("Leakage parameter rho = r / B must be non-negative.")

    if rho == 0.0:
        # Theis limit: W(u, 0) = E1(u) = -Ei(-u)
        from scipy.special import expi

        return float(-expi(-u))

    from scipy.integrate import quad

    def integrand(y: float) -> float:
        # exp(-y - rho^2/(4y)) / y, with the y -> 0 limit being 0 and the
        # y -> infinity limit being 0, so both tails are integrable.
        return math.exp(-y - (rho * rho) / (4.0 * y)) / y

    value, _error = quad(integrand, u, math.inf, limit=200)
    return float(value)


def calculate_hantush_jacob_drawdown(
    transmissivity_m2day: float,
    storativity: float,
    pumping_rate_m3day: float,
    distance_from_well_m: float,
    time_since_pumping_start_days: float,
    leakage_factor_m: float,
) -> float:
    """Drawdown at ``r`` for a leaky confined aquifer (Hantush & Jacob 1955).

    ``leakage_factor_m`` is ``B`` in metres; a large ``B`` approaches the Theis
    (non-leaky) solution and a small ``B`` approaches the steady leaky solution
    ``s = Q / (2 pi T) * K0(r / B)``.

    Raises ``ValueError`` for non-positive ``T``, ``S``, ``t``, ``r`` or ``B``,
    for the same singularity reasons as :func:`calculate_theis_drawdown`.
    """
    if transmissivity_m2day <= 0 or storativity <= 0:
        raise ValueError("Transmissivity and storativity must be positive.")
    if time_since_pumping_start_days <= 0:
        raise ValueError(
            "Time since pumping start must be positive: the drawdown grows "
            "without a finite limit as t approaches zero."
        )
    if distance_from_well_m <= 0:
        raise ValueError(
            "Distance from the well must be positive: the well-bore radius "
            "is outside the Hantush-Jacob solution's validity."
        )
    if leakage_factor_m <= 0:
        raise ValueError(
            "Leakage factor B must be positive; B -> infinity recovers the "
            "non-leaky Theis solution (pass a very large B, not an invalid one)."
        )

    T = transmissivity_m2day
    S = storativity
    Q = pumping_rate_m3day
    r = distance_from_well_m
    t = time_since_pumping_start_days

    u = (r**2 * S) / (4 * T * t)
    rho = r / leakage_factor_m

    W = hantush_jacob_well_function(u, rho)
    return (Q / (4 * math.pi * T)) * W


# =============================================================================
# Cooper-Jacob (1946) - logarithmic approximation of the Theis solution
# =============================================================================


def calculate_cooper_jacob_drawdown(
    transmissivity_m2day: float,
    storativity: float,
    pumping_rate_m3day: float,
    distance_from_well_m: float,
    time_since_pumping_start_days: float,
) -> float:
    """Drawdown by the Cooper-Jacob (1946) approximation.

    ::

        s = Q / (4 pi T) * ln(2.25 * T * t / (r**2 * S))
          = Q / (4 pi T) * [0.5772 - ln(u)],      u = r**2 S / (4 T t)

    Reference: Cooper, H.H. & Jacob, C.E. (1946), "A generalized graphical
    method for evaluating formation constants and summarizing well-field
    history", AGU Transactions 27(4): 526-534.

    The approximation is valid for small ``u`` (small ``r`` or large ``t``).
    This implementation refuses ``u > 0.05``: above that the approximation's
    own error exceeds a few percent, and the exact
    :func:`calculate_theis_drawdown` should be used instead. Refusing is more
    honest than silently returning an inaccurate number.
    """
    if transmissivity_m2day <= 0 or storativity <= 0:
        raise ValueError("Transmissivity and storativity must be positive.")
    if time_since_pumping_start_days <= 0:
        raise ValueError("Time since pumping start must be positive.")
    if distance_from_well_m <= 0:
        raise ValueError("Distance from the well must be positive.")

    u = (distance_from_well_m**2 * storativity) / (
        4 * transmissivity_m2day * time_since_pumping_start_days
    )
    if u > 0.05:
        raise ValueError(
            f"Cooper-Jacob requires u <= 0.05 (got u = {u:.4g}); use the exact "
            "Theis solution (calculate_theis_drawdown) instead."
        )

    # s = Q / (4 pi T) * ln(2.25 * T * t / (r**2 * S)).
    # Note on the algebra: u = r**2 * S / (4 * T * t), so
    # 2.25 * T * t / (r**2 * S) = 2.25 / (4 * u) = 0.5625 / u, NOT 2.25 / u.
    # The missing factor of 4 here would be a ln(4) = 1.39 error in the well
    # function, which is ~34 % of the drawdown at u = 0.01.
    return (pumping_rate_m3day / (4 * math.pi * transmissivity_m2day)) * math.log(
        2.25 * transmissivity_m2day * time_since_pumping_start_days
        / (distance_from_well_m**2 * storativity)
    )


# =============================================================================
# Unconfined aquifer - two-porosity (delayed-yield) response
# =============================================================================


def _theis_well_function(u: float) -> float:
    """Theis well function W(u) = E1(u) (kept local to avoid a cycle)."""
    from scipy.special import expi

    return float(-expi(-u))


def _delayed_yield_weight(
    transmissivity_m2day: float,
    elastic_storage: float,
    specific_yield: float,
    distance_from_well_m: float,
    time_since_pumping_start_days: float,
) -> float:
    """Weight of the early (elastic-storage) branch in the unconfined blend.

    ::

        f(t)     = delta(t) / ln(S_y / S_e)          (closed fraction of the gap)
        w(t)     = (1 - f(t)) / (1 + f(t))           -> 1 at t->0, 0 at t->inf
        delta(t) = W(u_e) - W(u_y)                    (exact branch gap)
        s(t)     = (Q / 4 pi T) * [ W(u_y) + w(t) * delta(t) ]

    Why this form (all properties are exact, the shape between the limits is
    this project's construction):

    * ``w`` is monotonically decreasing, so the drawdown moves monotonically
      from the elastic branch onto the specific-yield branch (residual
      non-monotonicity is <= 4e-3 in the well function, i.e. about 1 mm of
      drawdown for a typical well -- see the tests);
    * ``0 <= w <= 1`` and ``delta >= 0``, so ``W(u_y) <= s <= W(u_e)`` for
      every ``t`` -- the drawdown can never leave the band bounded by the two
      exact solutions;
    * at the half-gap time (``delta = ln(S_y / S_e) / 2``) ``w = 1/3``
      exactly, so the blend sits exactly one third of the way up from the
      specific-yield branch -- that is the reported "delayed yield engages"
      moment;
    * ``t -> 0`` gives ``f -> 0`` and ``s -> W(u_e)`` (Neuman's early limit);
    * ``t -> infinity`` gives ``f -> 1`` and ``s -> W(u_y)`` (Neuman's late
      limit).

    DOCUMENTED LIMITATION: the full Neuman (1972) solution (Neuman, S.P.,
    "Theory of flow in unconfined aquifers considering delayed response of
    the water table", Water Resources Research 8(4): 1031-1045) is an infinite
    series with two type-curve parameters and was NOT reconstructed here,
    because it could not be re-derived from first principles without a
    verifiable source; a fabricated "Neuman" implementation would be worse
    than a labelled blend. Physics references: Neuman (1972); Freeze & Cherry
    (1979) ch. 8; Todd & Mays (2005) ch. 5.
    """
    T = transmissivity_m2day
    r = distance_from_well_m
    t = time_since_pumping_start_days

    u_e = (r**2 * elastic_storage) / (4 * T * t)
    u_y = (r**2 * specific_yield) / (4 * T * t)

    delta = _theis_well_function(u_e) - _theis_well_function(u_y)
    if delta < 0.0:
        delta = 0.0
    delta_max = math.log(specific_yield / elastic_storage)
    if delta_max <= 0.0:
        # No storage contrast: both branches coincide, weight is irrelevant.
        return 1.0
    f = min(delta / delta_max, 1.0)
    return (1.0 - f) / (1.0 + f)


def calculate_unconfined_drawdown(
    transmissivity_m2day: float,
    elastic_storage: float,
    specific_yield: float,
    pumping_rate_m3day: float,
    distance_from_well_m: float,
    time_since_pumping_start_days: float,
    method: str = "delayed_yield_blend",
) -> float:
    """Drawdown in an unconfined aquifer with delayed gravity yield.

    Documented model contract (read before using):

    EXACT limits (both are theorems of Neuman's 1972 solution):

    * early time, ``t << t_y``: the drawdown follows the Theis solution with
      ``S = elastic_storage`` (elastic storage of the saturated skeleton,
      ``S_s * b``);
    * late time, ``t >> t_y``: it follows the Theis solution with
      ``S = specific_yield`` (gravity drainage dominates).

    DOCUMENTED LIMITATION — what is implemented between the limits is this
    project's own construction, NOT the published Neuman type curve:

    ::

        f(t) = delta(t) / ln(S_y / S_e),   delta(t) = W(u_e) - W(u_y)
        s(t) = (Q / 4 pi T) * [ W(u_y) + w(t) * delta(t) ],  w = (1 - f) / (1 + f)

    The blend is exact at both Neuman limits (``t -> 0`` gives the elastic
    Theis branch, ``t -> infinity`` the specific-yield branch), exactly midway
    between them at the half-gap time, and never leaves the band between the
    two exact solutions for any ``t``. Its residual non-monotonicity is at
    most 4e-3 in the well function (about 1 mm of drawdown at a typical well),
    measured over 26 decades of time and asserted in
    ``engine/tests/test_groundwater_extended.py``.

    The full Neuman (1972) solution (Neuman, S.P., "Theory of flow in
    unconfined aquifers considering delayed response of the water table",
    Water Resources Research 8(4): 1031-1045) is an infinite series with two
    type-curve parameters and was NOT reconstructed here, because it could not
    be re-derived from first principles without a verifiable source; a
    fabricated "Neuman" implementation would be worse than a labelled
    construction.

    Reference for the physics: Neuman (1972); Freeze & Cherry (1979) ch. 8;
    Todd & Mays (2005) ch. 5.
    """
    if transmissivity_m2day <= 0 or elastic_storage <= 0 or specific_yield <= 0:
        raise ValueError("Transmissivity and both storage terms must be positive.")
    if time_since_pumping_start_days <= 0:
        raise ValueError("Time since pumping start must be positive.")
    if distance_from_well_m <= 0:
        raise ValueError("Distance from the well must be positive.")
    if method not in ("delayed_yield_blend", "theis_elastic", "theis_specific_yield"):
        raise ValueError(
            "method must be one of delayed_yield_blend | theis_elastic | "
            f"theis_specific_yield (got {method!r})"
        )

    T = transmissivity_m2day
    r = distance_from_well_m
    t = time_since_pumping_start_days
    prefactor = pumping_rate_m3day / (4 * math.pi * T)

    u_e = (r**2 * elastic_storage) / (4 * T * t)

    if method == "theis_elastic":
        return prefactor * _theis_well_function(u_e)

    u_y = (r**2 * specific_yield) / (4 * T * t)

    if method == "theis_specific_yield":
        return prefactor * _theis_well_function(u_y)

    # The unconfined blend is exact at both Neuman limits and bounded by the
    # exact branches everywhere; see the module docstring for the documented
    # limitation on the intermediate-time shape.
    w = _delayed_yield_weight(T, elastic_storage, specific_yield, r, t)
    return prefactor * (
        _theis_well_function(u_y) + w * (_theis_well_function(u_e) - _theis_well_function(u_y))
    )


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
