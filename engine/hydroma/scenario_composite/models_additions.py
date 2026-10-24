"""Standard equations the engine did not have, plus the local model catalog.

Why this module exists
----------------------
The composite scenario engine composes *every* scientific model the gateway can
dispatch into one DAG. Several equations that a full FAO-56 / farm-economics
chain needs are published, standard, and absent from the engine: the
Priestley-Taylor, Blaney-Criddle, Turc and Makkink reference-evaporation
formulas, the FAO-56 dual-crop-coefficient stress term, and the farm-economics
ratios (benefit-cost, break-even, land expectation value). They live here,
implemented purely (``math``/``numpy``), each carrying its published reference,
each exposed for later registration with the main gateway.

Ownership boundary
------------------
``engine/models/registry.py`` owns the model registry and ``engine/gateway`` owns
dispatch. This module therefore does **not** touch them: it publishes
:data:`LOCAL_MODELS` (a plain, JSON-serialisable catalog) and
:func:`local_model_specs` so that a future owner can register these models with
``EngineGateway.register_model``. :func:`register_local_models` does that work
for an explicitly injected registry; it never mutates the process-wide registry
that ``engine.models.get_registry()`` returns, so importing this package cannot
change any other suite's view of the registry.

Unit conventions
----------------
* Energy flux: ``MJ m-2 day-1``; the latent heat of vaporisation is
  ``LAMBDA_MJ_PER_KG`` = 2.45 MJ/kg, so 1 mm of evaporation equals
  ``2.45 MJ m-2 day-1`` (FAO-56 eq. 20 conversion, ``1 MJ m-2 = 0.408 mm``).
* Radiation in the Turc equation: ``cal cm-2 day-1`` in the published form,
  converted with :data:`CAL_PER_CM2_DAY_TO_MJ_PER_M2_DAY` = 0.041868.
* Depths: ``mm``; areas: ``ha``; volumes: ``m3``; currency: whatever the caller
  states (the scenario catalog uses Iranian rial, "IRR").
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

__all__ = [
    # constants
    "LAMBDA_MJ_PER_KG",
    "SOLAR_CONSTANT_MJ_M2_MIN",
    "STEFAN_BOLTZMANN_MJ",
    "CAL_PER_CM2_DAY_TO_MJ_PER_M2_DAY",
    "PRIESTLEY_TAYLOR_ALPHA",
    "TURC_ADDITIVE_RADIATION_CAL_CM2_DAY",
    "MAKKINK_SLOPE",
    "MAKKINK_INTERCEPT",
    # helpers
    "saturation_vapour_pressure",
    "slope_vapour_pressure_curve",
    "psychrometric_constant",
    "net_radiation",
    "extraterrestrial_radiation",
    "daylight_hours",
    "annual_daylight_hours",
    "daylight_fraction_of_year",
    "mm_per_m_from_volumetric",
    # reference evaporation
    "priestley_taylor_et0",
    "blaney_criddle_et0",
    "turc_et0",
    "makkink_et0",
    "crop_evapotranspiration",
    # soil water
    "total_available_water",
    "readily_available_water",
    "root_zone_depletion",
    "stress_coefficient_ks",
    "effective_rainfall",
    "blue_green_water_split",
    # economics
    "net_present_value",
    "benefit_cost_ratio",
    "break_even_yield",
    "land_expectation_value",
    "water_productivity",
    "irrigation_water_use_efficiency",
    # social
    "direct_employment_fte",
    "household_income_effect",
    # food security
    "self_sufficiency_ratio",
    "import_dependency_ratio",
    "per_capita_dietary_supply",
    "cereal_yield_gap",
    # catalog
    "LocalModel",
    "LOCAL_MODELS",
    "local_model_specs",
    "register_local_models",
    "method_spread",
]


# --------------------------------------------------------------------------- #
# Physical constants (each with its source)                                   #
# --------------------------------------------------------------------------- #

#: Latent heat of vaporisation, MJ/kg. FAO-56 eq. 20 / FAO-24. At this value
#: 1 mm of evaporation consumes 2.45 MJ per m2, so a flux in MJ m-2 day-1 is
#: converted to mm/day by dividing by this constant.
LAMBDA_MJ_PER_KG = 2.45

#: Solar constant, MJ m-2 min-1 (FAO-56 eq. 21).
SOLAR_CONSTANT_MJ_M2_MIN = 0.0820

#: Stefan-Boltzmann constant, MJ K-4 m-2 day-1 (FAO-56 eq. 40).
STEFAN_BOLTZMANN_MJ = 4.903e-9

#: 1 cal cm-2 day-1 = 4.1868 J cm-2 s-1 x 1 d = 0.041868 MJ m-2 day-1
#: (thermochemical calorie, exact by definition since 1956).
CAL_PER_CM2_DAY_TO_MJ_PER_M2_DAY = 0.041868

#: Priestley-Taylor (1972) alpha for a well-watered surface.
PRIESTLEY_TAYLOR_ALPHA = 1.26

#: Additive constant of the Turc (1961) radiation term, cal cm-2 day-1.
TURC_ADDITIVE_RADIATION_CAL_CM2_DAY = 50.0

#: Makkink (1957) slope and intercept on the radiation term, mm/day.
MAKKINK_SLOPE = 0.61
MAKKINK_INTERCEPT = -0.12


def _require_finite(value: Any, name: str) -> float:
    """Coerce to a finite float or raise a ``ValueError`` naming the input."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return number


# --------------------------------------------------------------------------- #
# FAO-56 psychrometric helpers                                                 #
# --------------------------------------------------------------------------- #


def saturation_vapour_pressure(temp_c: float) -> float:
    """Saturation vapour pressure es(T), kPa (FAO-56 eq. 11).

    ``es(T) = 0.6108 * exp(17.27 T / (T + 237.3))``

    Reference: Allen, R.G., Pereira, L.S., Raes, D. & Smith, M. (1998), FAO
    Irrigation and Drainage Paper 56, Chapter 3, equation 11.
    """
    t = _require_finite(temp_c, "temp_c")
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def slope_vapour_pressure_curve(temp_c: float) -> float:
    """Slope of the saturation-vapour-pressure curve, kPa/C (FAO-56 eq. 13).

    ``D = 4098 es(T) / (T + 237.3)^2``
    """
    t = _require_finite(temp_c, "temp_c")
    es = saturation_vapour_pressure(t)
    return 4098.0 * es / (t + 237.3) ** 2


def psychrometric_constant(elevation_m: float) -> float:
    """Psychrometric constant, kPa/C (FAO-56 eq. 8).

    ``g = 0.000665 P`` with the atmospheric pressure ``P`` from the hypsometric
    relation ``P = 101.3 ((293 - 0.0065 z) / 293)^5.26`` (eq. 7), ``z`` in metres.
    """
    z = _require_finite(elevation_m, "elevation_m")
    pressure = 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26
    psychrometric: float = 0.000665 * pressure
    return psychrometric


def extraterrestrial_radiation(latitude_deg: float, doy: int) -> float:
    """Extraterrestrial radiation Ra, MJ m-2 day-1 (FAO-56 eq. 21).

    ``Ra = (24*60/pi) Gsc dr [ws sin(phi) sin(delta) + cos(phi) cos(delta) sin(ws)]``
    with ``dr = 1 + 0.033 cos(2 pi J/365)`` and
    ``delta = 0.409 sin(2 pi J/365 - 1.39)`` (solar declination, radians).
    """
    phi = math.radians(_require_finite(latitude_deg, "latitude_deg"))
    day = _require_finite(doy, "doy")
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day / 365.0)
    declination = 0.409 * math.sin(2.0 * math.pi * day / 365.0 - 1.39)
    tangent = math.tan(phi) * math.tan(declination)
    sunset_hour_angle = math.acos(max(-1.0, min(1.0, -tangent)))
    ra = (
        (24.0 * 60.0 / math.pi)
        * SOLAR_CONSTANT_MJ_M2_MIN
        * dr
        * (
            sunset_hour_angle * math.sin(phi) * math.sin(declination)
            + math.cos(phi) * math.cos(declination) * math.sin(sunset_hour_angle)
        )
    )
    # A polar night gives a marginally negative Ra in the bracket form; the
    # physically meaningful value is zero daylight, hence zero incoming energy.
    return max(0.0, ra)


def daylight_hours(latitude_deg: float, doy: int) -> float:
    """Daylight duration N, hours (FAO-56 eq. 34).

    ``N = 24/pi * ws`` with ``ws`` the sunset hour angle, radians. At the
    equator N = 12 h every day; at 32 N it ranges from 9.8 h (December) to
    14.2 h (June).
    """
    phi = math.radians(_require_finite(latitude_deg, "latitude_deg"))
    day = _require_finite(doy, "doy")
    declination = 0.409 * math.sin(2.0 * math.pi * day / 365.0 - 1.39)
    tangent = math.tan(phi) * math.tan(declination)
    sunset_hour_angle = math.acos(max(-1.0, min(1.0, -tangent)))
    return 24.0 / math.pi * sunset_hour_angle


def annual_daylight_hours(latitude_deg: float, days: int = 365) -> float:
    """Daylight hours summed over a year, hours.

    The sum runs over day-of-year 1..``days``. This is the denominator of the
    Blaney-Criddle daylight percentage, so it is defined as a sum rather than
    approximated by 12 x 365: at 32 N the true annual total is 4400 h, which is
    not 4380 h, and the ~0.5 % difference propagates straight into ET0.
    """
    if days < 1:
        raise ValueError(f"days must be >= 1 (got {days})")
    total = sum(daylight_hours(latitude_deg, doy) for doy in range(1, days + 1))
    return float(total)


def daylight_fraction_of_year(latitude_deg: float, doy: int) -> float:
    """The Blaney-Criddle p as a FRACTION of the year's daylight, dimensionless.

    ``p_fraction = N(doy) / sum(N)``. FAO-24 writes p as a percentage of annual
    daytime hours, so ``p_percent = 100 * p_fraction``. Keeping the fraction
    here and applying the factor 100 in :func:`blaney_criddle_et0` makes the
    dimensionless quantity the caller passes, instead of letting a percentage
    enter a formula that multiplies by 100 later.
    """
    numerator = daylight_hours(latitude_deg, doy)
    denominator = annual_daylight_hours(latitude_deg)
    if denominator <= 0.0:
        raise ValueError("annual daylight hours must be positive")
    return numerator / denominator


def mm_per_m_from_volumetric(volumetric_water_content: float) -> float:
    """Convert a volumetric water content to a depth per metre of soil.

    1 m3 of water per m3 of soil over a 1 m depth is 1 m of water = 1000 mm, so
    ``mm/m = cm3/cm3 * 1000``. The gateway's ``SOIL_AWC`` route reports
    ``theta(FC) - theta(PWP)`` from ``engine/hydroma/soil/physics.py`` (a
    volumetric fraction, e.g. 0.2503 for loam) while labelling the unit
    ``mm/m``; this function states the conversion the route's label omits.
    """
    value = _require_finite(volumetric_water_content, "volumetric_water_content")
    if value < 0.0:
        raise ValueError(
            f"volumetric water content must be non-negative (got {volumetric_water_content})"
        )
    return value * 1000.0


def net_radiation(
    temp_min_c: float,
    temp_max_c: float,
    relative_humidity_min_pct: float,
    relative_humidity_max_pct: float,
    solar_radiation_mj_m2_day: float,
    elevation_m: float,
    latitude_deg: float,
    doy: int,
) -> float:
    """Net radiation Rn, MJ m-2 day-1 (FAO-56 equations 38 to 40).

    ``Rns = 0.77 Rs`` (eq. 38), ``Rso = (0.75 + 2e-5 z) Ra`` (eq. 39),
    ``Rnl = sigma [(Kmax^4 + Kmin^4)/2] (0.34 - 0.14 sqrt(ea))
    (1.35 Rs/Rso - 0.35)`` (eq. 40), with the cloudiness factor clamped to zero
    because eq. 40 instructs taking the net longwave loss as zero for a fully
    overcast sky. The actual vapour pressure ``ea`` is eq. 17, the mean of the
    saturation pressures weighted by ``RHmax``/``RHmin`` over ``RHmin``/``RHmax``.
    """
    tmin = _require_finite(temp_min_c, "temp_min_c")
    tmax = _require_finite(temp_max_c, "temp_max_c")
    rh_min = _require_finite(relative_humidity_min_pct, "relative_humidity_min_pct")
    rh_max = _require_finite(relative_humidity_max_pct, "relative_humidity_max_pct")
    rs = _require_finite(solar_radiation_mj_m2_day, "solar_radiation_mj_m2_day")
    if rs < 0.0:
        raise ValueError(f"solar_radiation_mj_m2_day must be non-negative (got {rs})")
    ra = extraterrestrial_radiation(latitude_deg, doy)
    rso = (0.75 + 2.0e-5 * _require_finite(elevation_m, "elevation_m")) * ra
    rns = (1.0 - 0.23) * rs

    if rso > 0.0:
        ratio = min(max(rs / rso, 0.3), 1.0)
    else:
        # Polar night: Ra is zero, so the ratio is undefined; the clear-sky end
        # (1.0) is the physically meaningful limit (FAO-56 Annex 3 note).
        ratio = 1.0
    cloudiness = max(0.0, 1.35 * ratio - 0.35)

    es_tmax = saturation_vapour_pressure(tmax)
    es_tmin = saturation_vapour_pressure(tmin)
    ea = (es_tmin * (rh_max / 100.0) + es_tmax * (rh_min / 100.0)) / 2.0

    rnl = (
        STEFAN_BOLTZMANN_MJ
        * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0)
        * (0.34 - 0.14 * math.sqrt(max(ea, 0.0)))
        * cloudiness
    )
    return rns - rnl


# --------------------------------------------------------------------------- #
# Reference-evaporation equations the engine lacked                           #
# --------------------------------------------------------------------------- #


def priestley_taylor_et0(
    net_radiation_mj_m2_day: float,
    mean_temp_c: float,
    elevation_m: float = 0.0,
    ground_heat_flux_mj_m2_day: float = 0.0,
    alpha: float = PRIESTLEY_TAYLOR_ALPHA,
) -> float:
    """Priestley-Taylor (1972) potential evaporation, mm/day.

    ``ET0 = alpha * (D / (D + g)) * (Rn - G) / lambda`` with ``alpha = 1.26``.

    Units: ``(MJ m-2 day-1) / (MJ kg-1)`` gives ``kg m-2 day-1`` = ``mm/day``,
    because one kilogram per square metre is one millimetre of depth.

    Reference: Priestley, C.H.B. & Taylor, R.J. (1972), "On the assessment of
    surface heat flux and evaporation using large-scale parameters", *Monthly
    Weather Review* 100(2):81-92. The 1.26 coefficient is the paper's value for
    a well-watered surface without moisture advection; the equation carries no
    aerodynamic term, which is exactly why it is used here as the wind-free
    lower bound on the multi-method ET0 spread.

    Note the form is *potential* evaporation, not the FAO-56 grass reference:
    Priestley-Taylor omits the drying power of the air, so in an arid basin
    (the semi-arid scenario this engine is built for) it tends to sit *above*
    Penman-Monteith rather than below it, and the spread is reported rather
    than averaged away.
    """
    if alpha <= 0.0:
        raise ValueError(f"alpha must be positive (got {alpha})")
    rn = _require_finite(net_radiation_mj_m2_day, "net_radiation_mj_m2_day")
    soil_heat = _require_finite(ground_heat_flux_mj_m2_day, "ground_heat_flux_mj_m2_day")
    temperature = _require_finite(mean_temp_c, "mean_temp_c")
    delta = slope_vapour_pressure_curve(temperature)
    gamma = psychrometric_constant(elevation_m)
    if delta + gamma <= 0.0:
        raise ValueError("delta + gamma must be positive")
    available = rn - soil_heat
    et0 = alpha * (delta / (delta + gamma)) * available / LAMBDA_MJ_PER_KG
    # The published form is a potential surface flux and is clamped at zero:
    # a net energy sink cannot drive evaporation, it drives condensation.
    return max(0.0, et0)


def blaney_criddle_et0(
    mean_temp_c: float,
    daylight_fraction: float,
    coefficient: float = 1.0,
) -> float:
    """Blaney-Criddle (FAO-24) reference evaporation, mm/day.

    ``ET0 = c * p * (0.46 T + 8.18)`` where ``p`` is the daylight FRACTION
    FRACTION of the year (``N(doy) / annual daylight hours``, from
    :func:`daylight_fraction_of_year`), ``T`` the mean temperature in C, and
    ``c`` the consumptive-use coefficient (1.0 for a reference crop).

    The published form writes ``p`` as a percentage of annual daytime hours;
    because the parameter here is the FRACTION (0..1), the percentage
    conversion is the caller's and is NOT applied. An earlier revision
    multiplied by 100, which made every result 100x too large; the guard in
    engine/tests/test_composite_scenario_engine.py pins the fraction form
    against the published equation.

    Reference: Doorenbos, J. & Pruitt, W.O. (1977), *Guidelines for predicting
    crop water requirements*, FAO Irrigation and Drainage Paper 24, 2nd ed.,
    Chapter 4 ("Evapotranspiration ... Blaney-Criddle"), the form
    ``ETo = c [p (0.46T + 8.18)]`` with p the mean daily percentage of annual
    daytime hours. Original method: Blaney, H.F. & Criddle, W.D. (1950),
    *Determining water requirements in irrigated areas from climatological and
    irrigation data*, USDA SCS TP-96.
    """
    temperature = _require_finite(mean_temp_c, "mean_temp_c")
    fraction = _require_finite(daylight_fraction, "daylight_fraction")
    if not 0.0 < fraction <= 1.0:
        raise ValueError(
            "daylight_fraction must lie in (0, 1]: it is the fraction of the year's "
            f"daylight controlled by this day (got {daylight_fraction})"
        )
    if coefficient <= 0.0:
        raise ValueError(f"coefficient c must be positive (got {coefficient})")
    return coefficient * fraction * (0.46 * temperature + 8.18)


def turc_et0(
    mean_temp_c: float,
    solar_radiation_mj_m2_day: float,
    relative_humidity_pct: float | None = None,
) -> float:
    """Turc (1961) reference evaporation, mm/day.

    ``ET0 = 0.013 (T / (T + 15)) (Rs_cal + 50)``, with ``Rs_cal`` the global
    radiation in ``cal cm-2 day-1`` (converted from MJ with
    :data:`CAL_PER_CM2_DAY_TO_MJ_PER_M2_DAY`) and 50 the additive radiation
    constant of the published formula. In radiation-equivalent (mm/day) form the
    same equation reads ``ET0 = 0.013 (T/(T+15)) (58.52 (Rs/lambda) + 50)``,
    where the additive constant 50 cal cm-2 day-1 = 0.854 mm/day and
    1 mm/day = 58.52 cal cm-2 day-1 (``2.45 / 0.041868``).

    The humidity correction of FAO-24 is applied when the mean relative humidity
    is below 50 %: ``ET0 = ET0_dry (1 + (50 - RH)/70)``, which accounts for the
    drying power of the air the temperature-only form cannot see.

    Reference: Turc, L. (1961), "Evaluation des besoins en eau d'irrigation,
    evapotranspiration potentielle, formule climatique simplifiee et mise a
    jour", *Annales Agronomiques* 12(1):13-49. Humidity correction as published
    with the method in Doorenbos & Pruitt (1977), FAO-24, Chapter 2.
    """
    temperature = _require_finite(mean_temp_c, "mean_temp_c")
    rs = _require_finite(solar_radiation_mj_m2_day, "solar_radiation_mj_m2_day")
    if rs < 0.0:
        raise ValueError(f"solar_radiation_mj_m2_day must be non-negative (got {rs})")
    rs_cal = rs / CAL_PER_CM2_DAY_TO_MJ_PER_M2_DAY
    et0 = 0.013 * (temperature / (temperature + 15.0)) * (
        rs_cal + TURC_ADDITIVE_RADIATION_CAL_CM2_DAY
    )
    if relative_humidity_pct is not None:
        humidity = _require_finite(relative_humidity_pct, "relative_humidity_pct")
        if not 0.0 < humidity <= 100.0:
            raise ValueError(
                f"relative_humidity_pct must lie in (0, 100] (got {relative_humidity_pct})"
            )
        if humidity < 50.0:
            et0 *= 1.0 + (50.0 - humidity) / 70.0
    return max(0.0, et0)


def makkink_et0(
    mean_temp_c: float,
    solar_radiation_mj_m2_day: float,
    elevation_m: float = 0.0,
) -> float:
    """Makkink (1957) reference evaporation, mm/day.

    ``ET0 = 0.61 (D / (D + g)) (Rs / lambda) - 0.12``

    Reference: Makkink, G.F. (1957), "Testing the Penman formula by means of
    lysimeters", *Journal of the Institution of Water Engineers* 11(3):277-288.
    The equation is the citation's eq. 2, fitted against lysimeter measurements
    at Wageningen: the radiation term weighted by the ratio of the saturation
    slope to the psychrometric constant, less a 0.12 mm/day offset.
    """
    temperature = _require_finite(mean_temp_c, "mean_temp_c")
    rs = _require_finite(solar_radiation_mj_m2_day, "solar_radiation_mj_m2_day")
    if rs < 0.0:
        raise ValueError(f"solar_radiation_mj_m2_day must be non-negative (got {rs})")
    delta = slope_vapour_pressure_curve(temperature)
    gamma = psychrometric_constant(elevation_m)
    if delta + gamma <= 0.0:
        raise ValueError("delta + gamma must be positive")
    return MAKKINK_SLOPE * (delta / (delta + gamma)) * (rs / LAMBDA_MJ_PER_KG) + MAKKINK_INTERCEPT


def crop_evapotranspiration(et0_mm_day: float, crop_coefficient: float) -> float:
    """Crop evapotranspiration ETc, mm/day (FAO-56 chapter 6).

    ``ETc = Kc * ET0``. Only the single (or, here, a fixed mid-season) crop
    coefficient is used: the dual-coefficient split into a transpiration and an
    evaporation term needs a wetting-frequency input the composite scenario
    engine does not carry, so it is deliberately not claimed.
    """
    et0 = _require_finite(et0_mm_day, "et0_mm_day")
    kc = _require_finite(crop_coefficient, "crop_coefficient")
    if et0 < 0.0:
        raise ValueError(f"et0_mm_day must be non-negative (got {et0})")
    if kc <= 0.0:
        raise ValueError(f"crop_coefficient must be positive (got {kc})")
    return kc * et0


# --------------------------------------------------------------------------- #
# Soil-water balance                                                           #
# --------------------------------------------------------------------------- #


def total_available_water(available_water_mm_per_m: float, root_depth_m: float) -> float:
    """Total available water TAW, mm (FAO-56 eq. 87).

    ``TAW = 1000 (theta_FC - theta_WP) Zr``. The factor 1000 converts the
    volumetric water content difference into a depth per metre of soil, and
    ``Zr`` is the rooting depth in metres.
    """
    awc = _require_finite(available_water_mm_per_m, "available_water_mm_per_m")
    depth = _require_finite(root_depth_m, "root_depth_m")
    if awc < 0.0:
        raise ValueError(f"available_water_mm_per_m must be non-negative (got {awc})")
    if depth <= 0.0:
        raise ValueError(f"root_depth_m must be positive (got {depth})")
    return awc * depth


def readily_available_water(total_available_water_mm: float, depletion_fraction: float) -> float:
    """Readily available water RAW, mm (FAO-56 eq. 86).

    ``RAW = p * TAW``, where ``p`` is the management-allowed depletion
    fraction for the crop (0.55 for most field crops).
    """
    taw = _require_finite(total_available_water_mm, "total_available_water_mm")
    fraction = _require_finite(depletion_fraction, "depletion_fraction")
    if taw < 0.0:
        raise ValueError(f"total_available_water_mm must be non-negative (got {taw})")
    if not 0.0 < fraction <= 1.0:
        raise ValueError(
            "depletion_fraction is the allowed-depletion FRACTION and must lie in (0, 1] "
            f"(got {depletion_fraction}); pass 0.55 for 55 %, not 55"
        )
    return taw * fraction


def root_zone_depletion(
    previous_depletion_mm: float,
    crop_evapotranspiration_mm: float,
    effective_rain_mm: float,
    irrigation_mm: float,
    deep_percolation_mm: float = 0.0,
) -> float:
    """Root-zone water depletion Dr after one period, mm (FAO-56 chapter 8).

    ``Dr_i = Dr_{i-1} - Pe - I - Dp + ETc + ROI`` with the run-off term omitted
    (it is carried separately by the curve-number step of the composite DAG,
    which is where the SCS-CN route lives). The result is bounded to
    ``[0, TAW_max]`` implicitly by :func:`stress_coefficient_ks`, which treats
    ``Dr > TAW`` as full stress rather than as a negative available store.
    """
    previous = _require_finite(previous_depletion_mm, "previous_depletion_mm")
    etc = _require_finite(crop_evapotranspiration_mm, "crop_evapotranspiration_mm")
    effective = _require_finite(effective_rain_mm, "effective_rain_mm")
    irrigation = _require_finite(irrigation_mm, "irrigation_mm")
    percolation = _require_finite(deep_percolation_mm, "deep_percolation_mm")
    return previous - effective - irrigation - percolation + etc


def stress_coefficient_ks(
    depletion_mm: float,
    total_available_water_mm: float,
    depletion_fraction: float,
) -> float:
    """Water stress coefficient Ks, dimensionless (FAO-56 eq. 84).

    ``Ks = (TAW - Dr) / ((1 - p) TAW)`` for ``Dr > RAW``, else ``Ks = 1``.

    The result is the reduction the crop suffers from the current soil-water
    deficit: 1 is a turgid root zone, 0 is a fully stressed one. ``Dr`` beyond
    ``TAW`` means the deficit exceeds the store, which is a stress of 0, not a
    negative supply.
    """
    depletion = _require_finite(depletion_mm, "depletion_mm")
    taw = _require_finite(total_available_water_mm, "total_available_water_mm")
    fraction = _require_finite(depletion_fraction, "depletion_fraction")
    if taw <= 0.0:
        raise ValueError(f"total_available_water_mm must be positive (got {taw})")
    if not 0.0 <= fraction < 1.0:
        raise ValueError(
            f"depletion_fraction must lie in [0, 1) (got {depletion_fraction}); at p = 1 "
            "the stress band of eq. 84 has zero width and Ks is undefined"
        )
    raw = readily_available_water(taw, fraction)
    if depletion <= raw:
        return 1.0
    return max(0.0, (taw - depletion) / ((1.0 - fraction) * taw))


def effective_rainfall(precipitation_mm: float, effectiveness_fraction: float = 0.75) -> float:
    """Effective rainfall, mm (documented planning proxy).

    ``Pe = f * P`` with ``f`` the fraction of rainfall retained in the root
    zone. Published methods for this fraction (FAO Irrigation and Drainage
    Paper 33 / CROPWAT's "fixed percentage" method, USDA-SCS) differ by more
    than the crop response does, so ``f`` is a scenario input rather than a
    model output, and the indicator that consumes it is labelled ``proxy``.
    """
    precipitation = _require_finite(precipitation_mm, "precipitation_mm")
    fraction = _require_finite(effectiveness_fraction, "effectiveness_fraction")
    if precipitation < 0.0:
        raise ValueError(f"precipitation_mm must be non-negative (got {precipitation})")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(
            f"effectiveness_fraction must lie in [0, 1] (got {effectiveness_fraction})"
        )
    return precipitation * fraction


def blue_green_water_split(
    season_evapotranspiration_mm: float,
    effective_rain_mm: float,
    irrigation_mm: float,
) -> dict[str, float]:
    """Split consumed water into green (rain-fed) and blue (irrigated), mm.

    Proxy rule, per the green/blue framing of Falkenmark, M. & Rockstrom, J.
    (2004), "Balancing water for humans and nature: the new approach in
    ecohydrology", *Water Resources Research* 40(7):W07S03: green water is the
    rainfall retained in the soil and consumed by the crop, blue water is the
    irrigation consumed. ``green = min(Pe, ET)``, ``blue = min(I, ET - green)``
    and any deficit is reported as ``unmet_demand_mm`` rather than folded into
    either store, because a shortfall is neither rainfall nor irrigation.
    """
    et = _require_finite(season_evapotranspiration_mm, "season_evapotranspiration_mm")
    effective = _require_finite(effective_rain_mm, "effective_rain_mm")
    irrigation = _require_finite(irrigation_mm, "irrigation_mm")
    if min(et, effective, irrigation) < 0.0:
        raise ValueError("green/blue split takes non-negative depths only")
    green = min(effective, et)
    blue = min(irrigation, max(0.0, et - green))
    return {
        "green_mm": green,
        "blue_mm": blue,
        "unmet_demand_mm": max(0.0, et - green - blue),
        "green_fraction": (green / et) if et > 0.0 else 0.0,
        "blue_fraction": (blue / et) if et > 0.0 else 0.0,
    }


# --------------------------------------------------------------------------- #
# Economics                                                                    #
# --------------------------------------------------------------------------- #


def net_present_value(cash_flows: list[float], discount_rate: float) -> float:
    """NPV, currency units (period 0 undiscounted).

    ``NPV = sum_t CF_t / (1 + r)^t`` for ``t = 0, 1, ...``. The convention is
    the one ``engine/hydroma/economics/analysis.py::calculate_npv`` publishes,
    so the composite engine's local ratio arithmetic is comparable with the
    ``ECON_NPV`` gateway route's answer for the same stream.
    """
    rate = _require_finite(discount_rate, "discount_rate")
    if rate <= -1.0:
        raise ValueError(f"discount_rate must exceed -100 % (got {discount_rate})")
    total = 0.0
    for year, flow in enumerate(cash_flows):
        total += _require_finite(flow, "cash flow") / (1.0 + rate) ** year
    return total


def benefit_cost_ratio(pv_benefits: float, pv_costs: float) -> float:
    """Benefit-cost ratio BCR, dimensionless.

    ``BCR = PV(benefits) / PV(costs)``. A project is worthwhile above 1. The
    denominator is the present value of the *cost* stream as a positive number;
    passing costs as negatives with the cash-flow-sign convention of
    :func:`net_present_value` would silently invert the ratio, so costs are
    taken positive here.
    """
    benefits = _require_finite(pv_benefits, "pv_benefits")
    costs = _require_finite(pv_costs, "pv_costs")
    if costs <= 0.0:
        raise ValueError(f"pv_costs must be positive (got {pv_costs})")
    if benefits < 0.0:
        raise ValueError(f"pv_benefits must be non-negative (got {pv_benefits})")
    return benefits / costs


def break_even_yield(fixed_cost: float, price_per_unit: float, variable_cost_per_unit: float) -> float:
    """Break-even yield, yield units.

    ``Y_be = fixed_cost / (price - variable_cost_per_unit)``: the yield at which
    revenue covers the fixed cost and the variable cost of the units produced.
    The margin per unit must be positive; at a zero margin no yield covers a
    fixed cost, so the equation has no solution and raises rather than
    returning an infinity a caller would read as "easy".
    """
    fixed = _require_finite(fixed_cost, "fixed_cost")
    price = _require_finite(price_per_unit, "price_per_unit")
    variable = _require_finite(variable_cost_per_unit, "variable_cost_per_unit")
    margin = price - variable
    if fixed < 0.0:
        raise ValueError(f"fixed_cost must be non-negative (got {fixed})")
    if margin <= 0.0:
        raise ValueError(
            "break-even yield is undefined when price <= variable cost per unit "
            f"(price {price}, variable cost {variable}): no yield covers a fixed cost"
        )
    return fixed / margin


def land_expectation_value(
    net_cash_flows: list[float],
    rotation_years: int,
    discount_rate: float,
) -> float:
    """Land expectation value of a perpetual rotation, currency units.

    ``LEV = V (1 + r)^R / ((1 + r)^R - 1)`` where ``V`` is the net present
    value of one rotation (period 0 at rotation start, index ``t`` discounted
    at ``(1 + r)^-t``) and ``R`` the rotation length. Identical rotations
    repeat at ``t = 0, R, 2R, ...`` so the series is geometric with ratio
    ``(1 + r)^-R`` and sums to ``V / (1 - (1 + r)^-R)``.

    Reference: Faustmann, M. (1849), "Berechnung des Werthes, welchen
    Waldboden, sowie noch nicht haubare Holzbestande fuer die Waldwirthschaft
    besitzen", *Allgemeine Forst- und Jagd-Zeitung* 15:441-455 -- the original
    land-expectation derivation, restated in every farm-management text since
    (e.g. Kay, R.D., Edwards, W.M. & Duffy, P.A., *Farm Management*, McGraw-
    Hill, chapter on investment analysis). The rotation length is an integer
    number of years because a rotation is counted in seasons, not fractions.
    """
    rate = _require_finite(discount_rate, "discount_rate")
    if rate <= -1.0:
        raise ValueError(f"discount_rate must exceed -100 % (got {discount_rate})")
    if not isinstance(rotation_years, int) or rotation_years < 1:
        raise ValueError(f"rotation_years must be a positive integer (got {rotation_years})")
    if rate == 0.0:
        # Discounting nothing: identical rotations repeat forever, so the land
        # value of a positive rotation is unbounded, not the rotation's value.
        raise ValueError(
            "land_expectation_value is undefined at a zero discount rate: identical "
            "rotations repeat forever, so a profitable rotation has unbounded land value"
        )
    rotation_value = net_present_value(list(net_cash_flows), rate)
    growth = (1.0 + rate) ** rotation_years
    return rotation_value * growth / (growth - 1.0)


def water_productivity(yield_kg_per_ha: float, et_mm: float) -> float:
    """Water productivity, kg/m3 (FAO WaPOR definition).

    ``WP = Y / ET`` with the yield in kg/ha and the consumed water as a volume;
    the unit bridge is 1 mm over 1 ha = 0.001 m x 10 000 m2 = 10 m3, so
    ``WP = Y / (ET x 10)``. This is the definition already published by
    ``engine/hydroma/water_productivity.py`` (indicator ``ENO_WP_001``) and is
    re-implemented here so the composite indicator set does not depend on a
    module outside this package's scope; the two agree by construction and the
    test suite pins that agreement.

    Reference: FAO Water Productivity Open Portal (WaPOR),
    https://www.fao.org/land-water/databases-and-software/wapor/en
    """
    yield_value = _require_finite(yield_kg_per_ha, "yield_kg_per_ha")
    consumption = _require_finite(et_mm, "et_mm")
    if yield_value < 0.0:
        raise ValueError(f"yield_kg_per_ha must be non-negative (got {yield_kg_per_ha})")
    if consumption <= 0.0:
        raise ValueError(f"et_mm must be positive (got {et_mm})")
    return yield_value / (consumption * 10.0)


def irrigation_water_use_efficiency(yield_kg_per_ha: float, applied_water_mm: float) -> float:
    """Irrigation water use efficiency, kg/m3.

    ``IWUE = Y / W_applied`` with the same 10 m3 per mm-per-ha unit bridge as
    :func:`water_productivity`, but the denominator is the water *applied*
    (gross irrigation depth) rather than the water *consumed* (ET), so
    conveyance and application losses count against the system.

    Reference: Keller, J. & Bliesner, R.D. (1990), *Sprinkler and Trickle
    Irrigation*, Van Nostrand Reinhold, chapter 5 ("Irrigation efficiency")
    for the efficiency ratio, with the FAO WaPOR unit bridge for the depth to
    volume conversion.
    """
    yield_value = _require_finite(yield_kg_per_ha, "yield_kg_per_ha")
    applied = _require_finite(applied_water_mm, "applied_water_mm")
    if yield_value < 0.0:
        raise ValueError(f"yield_kg_per_ha must be non-negative (got {yield_kg_per_ha})")
    if applied <= 0.0:
        raise ValueError(f"applied_water_mm must be positive (got {applied_water_mm})")
    return yield_value / (applied * 10.0)


# --------------------------------------------------------------------------- #
# Social                                                                      #
# --------------------------------------------------------------------------- #


def direct_employment_fte(
    area_ha: float,
    employment_intensity_fte_per_ha: float,
    months_per_year: float = 12.0,
) -> float:
    """Direct full-time-equivalent employment, FTE.

    ``FTE = area * intensity * (months / 12)``. This is the same arithmetic
    ``engine/hydroma/economics/employment.py::estimate_direct_employment``
    publishes (``direct_employment_full_time_equivalent``), re-implemented here
    so the social indicator does not depend on a module the composite engine
    treats as a black box.
    """
    area = _require_finite(area_ha, "area_ha")
    intensity = _require_finite(employment_intensity_fte_per_ha, "employment_intensity_fte_per_ha")
    months = _require_finite(months_per_year, "months_per_year")
    if area < 0.0 or intensity < 0.0:
        raise ValueError("area and employment intensity must be non-negative")
    if not 0.0 <= months <= 12.0:
        raise ValueError(f"months_per_year must lie in [0, 12] (got {months_per_year})")
    return area * intensity * (months / 12.0)


def household_income_effect(
    annual_net_income: float,
    households: int,
) -> float:
    """Average net income per household, currency units per household per year.

    ``income / households``. It is the simplest defensible household income
    effect: no multiplier, no spending leakage, both of which are separately
    estimated (as induced employment) by the engine's employment module and are
    not claimed here.
    """
    income = _require_finite(annual_net_income, "annual_net_income")
    if not isinstance(households, int) or households < 1:
        raise ValueError(f"households must be a positive integer (got {households})")
    return income / float(households)


# --------------------------------------------------------------------------- #
# Food security                                                               #
# --------------------------------------------------------------------------- #


def self_sufficiency_ratio(production: float, consumption: float) -> float:
    """Self-sufficiency ratio SSR, dimensionless.

    ``SSR = production / consumption`` for the same commodity, area and year.
    SSR = 1 is exact self-sufficiency; above 1 is a surplus. The FAO food-
    security indicator family defines the ratio over the *same market bounds*,
    so both quantities must be stated for the same population and period; the
    composite engine records both bounds in the indicator provenance.

    Reference: FAO, *Food Balance Sheets* handbook, "Self-sufficiency
    indicator" (ratio of domestic production to domestic utilisation).
    """
    produced = _require_finite(production, "production")
    consumed = _require_finite(consumption, "consumption")
    if produced < 0.0:
        raise ValueError(f"production must be non-negative (got {production})")
    if consumed <= 0.0:
        raise ValueError(f"consumption must be positive (got {consumption})")
    return produced / consumed


def import_dependency_ratio(production: float, consumption: float) -> float:
    """Import dependency ratio, fraction of consumption not produced locally.

    ``IDR = 1 - SSR``, clipped at zero: a production surplus is not a negative
    import dependency, and reporting one would let an abundance of one crop
    cancel an import bill for another. The clipping is recorded in the
    indicator's formula note.
    """
    ratio = self_sufficiency_ratio(production, consumption)
    return max(0.0, 1.0 - ratio)


def per_capita_dietary_supply(production: float, population: int) -> float:
    """Per-capita dietary supply of the commodity, kg per person per year.

    ``production / population``. FAO's per-capita supply is the food available
    for human consumption divided by the population de facto; here the
    production side only, because a food balance sheet's import, export, feed
    and seed terms are not carried by the scenario and are therefore not
    implied. The indicator's provenance states that scope.
    """
    produced = _require_finite(production, "production")
    if not isinstance(population, int) or population < 1:
        raise ValueError(f"population must be a positive integer (got {population})")
    if produced < 0.0:
        raise ValueError(f"production must be non-negative (got {production})")
    return produced / float(population)


def cereal_yield_gap(attainable_yield: float, actual_yield: float) -> float:
    """Cereal yield gap, yield units per hectare.

    ``gap = attainable - actual``, i.e. the distance between what the
    attainable (exploited benchmark) yield is and what the modelled scenario
    produced. The attainable yield is a *reference input*, not a model output:
    the engine does not estimate it from climate or soil, it is supplied by the
    scenario and labelled ``proxy`` in the indicator that carries it.

    Reference: van Ittersum, M.K., Cassman, K.G., Grassini, P., Wolf, J.,
    Tittonell, P. & Hochman, Z. (2013), "Yield gap analysis with local to
    global relevance: a review", *Field Crops Research* 143:4-17, for the
    attainable-yield tier of the yield-gap decomposition.
    """
    attainable = _require_finite(attainable_yield, "attainable_yield")
    actual = _require_finite(actual_yield, "actual_yield")
    if min(attainable, actual) < 0.0:
        raise ValueError("attainable and actual yields must be non-negative")
    return attainable - actual


# --------------------------------------------------------------------------- #
# Local model catalog                                                          #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LocalModel:
    """One locally implemented model, described for later registration.

    ``model_id``
        The id this package uses in a scenario trace for a locally computed
        step (``LOCAL:<id>``). It is deliberately *not* an id registered with
        the engine's registry: registering is the registry owner's decision, and
        this package must not change any other suite's view of the registry.
    ``inputs`` / ``outputs``
        Input and output names with units, so a future registration can build a
        ``REQUIRED_INPUTS`` contract without reading this file.
    """

    model_id: str
    name: str
    units: str
    reference: str
    inputs: tuple[tuple[str, str], ...]
    outputs: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, Any]:
        """The machine-readable form of this card (JSON-serialisable)."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "units": self.units,
            "reference": self.reference,
            "inputs": [{"name": n, "unit": u} for n, u in self.inputs],
            "outputs": [{"name": n, "unit": u} for n, u in self.outputs],
        }


#: The local catalog: every equation this package adds that the gateway cannot
#: dispatch. Serialisable through :meth:`LocalModel.as_dict`.
LOCAL_MODELS: dict[str, LocalModel] = {
    entry.model_id: entry
    for entry in (
        LocalModel(
            model_id="PRIESTLEY_TAYLOR_ET0",
            name="Priestley-Taylor potential evaporation",
            units="mm/day",
            reference="Priestley & Taylor (1972), Mon. Weather Rev. 100(2):81-92",
            inputs=(
                ("net_radiation_mj_m2_day", "MJ/m2/day"),
                ("mean_temp_c", "C"),
                ("elevation_m", "m"),
                ("alpha", "-"),
            ),
            outputs=(("et0_mm_day", "mm/day"),),
        ),
        LocalModel(
            model_id="BLANEY_CRIDDLE_ET0",
            name="Blaney-Criddle reference evaporation (FAO-24)",
            units="mm/day",
            reference="Doorenbos & Pruitt (1977), FAO-24; Blaney & Criddle (1950), USDA SCS TP-96",
            inputs=(
                ("mean_temp_c", "C"),
                ("daylight_fraction", "- (N(doy)/annual daylight hours)"),
                ("coefficient", "-"),
            ),
            outputs=(("et0_mm_day", "mm/day"),),
        ),
        LocalModel(
            model_id="TURC_ET0",
            name="Turc reference evaporation",
            units="mm/day",
            reference="Turc (1961), Annales Agronomiques 12(1):13-49",
            inputs=(
                ("mean_temp_c", "C"),
                ("solar_radiation_mj_m2_day", "MJ/m2/day"),
                ("relative_humidity_pct", "%"),
            ),
            outputs=(("et0_mm_day", "mm/day"),),
        ),
        LocalModel(
            model_id="MAKKINK_ET0",
            name="Makkink reference evaporation",
            units="mm/day",
            reference="Makkink (1957), J. Inst. Water Eng. 11(3):277-288",
            inputs=(
                ("mean_temp_c", "C"),
                ("solar_radiation_mj_m2_day", "MJ/m2/day"),
                ("elevation_m", "m"),
            ),
            outputs=(("et0_mm_day", "mm/day"),),
        ),
        LocalModel(
            model_id="FAO56_STRESS_COEFFICIENT",
            name="FAO-56 water stress coefficient",
            units="dimensionless",
            reference="Allen et al. (1998), FAO-56 chapter 8, eq. 84",
            inputs=(
                ("depletion_mm", "mm"),
                ("total_available_water_mm", "mm"),
                ("depletion_fraction", "-"),
            ),
            outputs=(("ks", "-"),),
        ),
        LocalModel(
            model_id="FAO56_CROP_ET",
            name="Crop evapotranspiration from ET0 and Kc",
            units="mm/day",
            reference="Allen et al. (1998), FAO-56 chapter 6",
            inputs=(("et0_mm_day", "mm/day"), ("crop_coefficient", "-")),
            outputs=(("etc_mm_day", "mm/day"),),
        ),
        LocalModel(
            model_id="BLUE_GREEN_WATER_SPLIT",
            name="Blue/green consumed-water split",
            units="mm",
            reference="Falkenmark & Rockstrom (2004), WRR 40(7):W07S03 (proxy rule)",
            inputs=(
                ("season_evapotranspiration_mm", "mm"),
                ("effective_rain_mm", "mm"),
                ("irrigation_mm", "mm"),
            ),
            outputs=(
                ("green_mm", "mm"),
                ("blue_mm", "mm"),
                ("unmet_demand_mm", "mm"),
            ),
        ),
        LocalModel(
            model_id="BENEFIT_COST_RATIO",
            name="Benefit-cost ratio",
            units="dimensionless",
            reference="FAO Investment Centre farm-project appraisal methodology",
            inputs=(("pv_benefits", "currency"), ("pv_costs", "currency")),
            outputs=(("bcr", "-"),),
        ),
        LocalModel(
            model_id="BREAK_EVEN_YIELD",
            name="Break-even yield",
            units="yield units",
            reference="Kay, Edwards & Duffy, Farm Management (McGraw-Hill)",
            inputs=(
                ("fixed_cost", "currency"),
                ("price_per_unit", "currency/unit"),
                ("variable_cost_per_unit", "currency/unit"),
            ),
            outputs=(("break_even_yield", "yield units"),),
        ),
        LocalModel(
            model_id="LAND_EXPECTATION_VALUE",
            name="Land expectation value of a perpetual rotation",
            units="currency",
            reference="Faustmann (1849); farm-management restatements",
            inputs=(
                ("net_cash_flows", "currency"),
                ("rotation_years", "years"),
                ("discount_rate", "-"),
            ),
            outputs=(("lev", "currency"),),
        ),
        LocalModel(
            model_id="WATER_PRODUCTIVITY",
            name="Water productivity",
            units="kg/m3",
            reference="FAO WaPOR; engine/hydroma/water_productivity.py (ENO_WP_001)",
            inputs=(("yield_kg_per_ha", "kg/ha"), ("et_mm", "mm")),
            outputs=(("wp", "kg/m3"),),
        ),
        LocalModel(
            model_id="IRRIGATION_WATER_USE_EFFICIENCY",
            name="Irrigation water use efficiency",
            units="kg/m3",
            reference="Keller & Bliesner (1990), Sprinkler and Trickle Irrigation",
            inputs=(("yield_kg_per_ha", "kg/ha"), ("applied_water_mm", "mm")),
            outputs=(("iwue", "kg/m3"),),
        ),
        LocalModel(
            model_id="DIRECT_EMPLOYMENT_FTE",
            name="Direct full-time-equivalent employment",
            units="FTE",
            reference="engine/hydroma/economics/employment.py::estimate_direct_employment",
            inputs=(
                ("area_ha", "ha"),
                ("employment_intensity_fte_per_ha", "FTE/ha"),
                ("months_per_year", "months"),
            ),
            outputs=(("fte", "FTE"),),
        ),
        LocalModel(
            model_id="SELF_SUFFICIENCY_RATIO",
            name="Self-sufficiency and import dependency ratios",
            units="dimensionless",
            reference="FAO Food Balance Sheets handbook (self-sufficiency indicator)",
            inputs=(("production", "kg"), ("consumption", "kg")),
            outputs=(("ssr", "-"), ("idr", "-")),
        ),
        LocalModel(
            model_id="CEREAL_YIELD_GAP",
            name="Cereal yield gap against an attainable reference",
            units="kg/ha",
            reference="van Ittersum et al. (2013), Field Crops Res. 143:4-17",
            inputs=(("attainable_yield_kg_ha", "kg/ha"), ("actual_yield_kg_ha", "kg/ha")),
            outputs=(("yield_gap_kg_ha", "kg/ha"),),
        ),
    )
}


def local_model_specs() -> list[Any]:
    """``ModelSpec`` objects for the local catalog, for a later registration.

    Returned as plain ``ModelSpec`` values so a caller can pass them to
    ``gateway.register_model`` with no conversion. Nothing here registers
    anything: that is the registry owner's call, and this package must not
    change the process-wide registry other suites read.
    """
    from engine.gateway import ModelSpec

    return [
        ModelSpec(
            model_id=model.model_id,
            model_version="1.0.0",
            model_name=model.name,
            model_type=model.model_id.lower(),
            domain="composite_scenario",
            purpose=f"{model.name} ({model.units}); added by engine.hydroma.scenario_composite",
            assumptions=["Local pure-Python implementation, registered by its owner"],
            limitations=["Exposed for registration; not registered with the gateway by this package"],
        )
        for model in LOCAL_MODELS.values()
    ]


def register_local_models(gateway: Any, registry: Any = None) -> list[str]:
    """Register the local models with an explicitly supplied gateway/registry.

    ``registry`` defaults to a **fresh** ``ModelRegistry`` built here, never the
    process-wide one from ``engine.models.get_registry``: the composite engine
    is invoked inside the existing test suites, and adding ids to that registry
    would change what unrelated suites observe. Pass
    ``EngineGateway(model_registry=reg).`` style injection to use your own.

    Returns the registered ids in catalog order.
    """
    specs = local_model_specs()
    if registry is None:
        from engine.models import ModelRegistry

        registry = ModelRegistry()
    for spec in specs:
        registry.register(spec)
        gateway.register_handler(spec.model_id, _make_handler(spec.model_id))
    return [spec.model_id for spec in specs]


#: Local id -> callable that consumes a normalized gateway input mapping and
#: returns a plain result mapping. The mapping is what ``EngineGateway.execute``
#: hands a handler: the inputs it was given, each with a ``<name>_unit`` twin.
_LOCAL_HANDLERS: dict[str, Any] = {
    "PRIESTLEY_TAYLOR_ET0": (
        ("net_radiation_mj_m2_day", "mean_temp_c", "elevation_m"),
        ("et0_mm_day",),
        lambda i: {
            "et0_mm_day": priestley_taylor_et0(
                float(i["net_radiation_mj_m2_day"]),
                float(i["mean_temp_c"]),
                float(i.get("elevation_m", 0.0)),
            )
        },
    ),
    "BLANEY_CRIDDLE_ET0": (
        ("mean_temp_c", "daylight_fraction", "coefficient"),
        ("et0_mm_day",),
        lambda i: {
            "et0_mm_day": blaney_criddle_et0(
                float(i["mean_temp_c"]),
                float(i["daylight_fraction"]),
                float(i.get("coefficient", 1.0)),
            )
        },
    ),
    "TURC_ET0": (
        ("mean_temp_c", "solar_radiation_mj_m2_day", "relative_humidity_pct"),
        ("et0_mm_day",),
        lambda i: {
            "et0_mm_day": turc_et0(
                float(i["mean_temp_c"]),
                float(i["solar_radiation_mj_m2_day"]),
                float(i["relative_humidity_pct"]) if i.get("relative_humidity_pct") is not None else None,
            )
        },
    ),
    "MAKKINK_ET0": (
        ("mean_temp_c", "solar_radiation_mj_m2_day", "elevation_m"),
        ("et0_mm_day",),
        lambda i: {
            "et0_mm_day": makkink_et0(
                float(i["mean_temp_c"]),
                float(i["solar_radiation_mj_m2_day"]),
                float(i.get("elevation_m", 0.0)),
            )
        },
    ),
    "FAO56_STRESS_COEFFICIENT": (
        ("depletion_mm", "total_available_water_mm", "depletion_fraction"),
        ("ks",),
        lambda i: {
            "ks": stress_coefficient_ks(
                float(i["depletion_mm"]),
                float(i["total_available_water_mm"]),
                float(i["depletion_fraction"]),
            )
        },
    ),
    "FAO56_CROP_ET": (
        ("et0_mm_day", "crop_coefficient"),
        ("etc_mm_day",),
        lambda i: {
            "etc_mm_day": crop_evapotranspiration(
                float(i["et0_mm_day"]), float(i["crop_coefficient"])
            )
        },
    ),
    "BENEFIT_COST_RATIO": (
        ("pv_benefits", "pv_costs"),
        ("bcr",),
        lambda i: {"bcr": benefit_cost_ratio(float(i["pv_benefits"]), float(i["pv_costs"]))},
    ),
    "BREAK_EVEN_YIELD": (
        ("fixed_cost", "price_per_unit", "variable_cost_per_unit"),
        ("break_even_yield",),
        lambda i: {
            "break_even_yield": break_even_yield(
                float(i["fixed_cost"]),
                float(i["price_per_unit"]),
                float(i["variable_cost_per_unit"]),
            )
        },
    ),
    "LAND_EXPECTATION_VALUE": (
        ("net_cash_flows", "rotation_years", "discount_rate"),
        ("lev",),
        lambda i: {
            "lev": land_expectation_value(
                list(i["net_cash_flows"]), int(i["rotation_years"]), float(i["discount_rate"])
            )
        },
    ),
    "WATER_PRODUCTIVITY": (
        ("yield_kg_per_ha", "et_mm"),
        ("wp_kg_per_m3",),
        lambda i: {
            "wp_kg_per_m3": water_productivity(float(i["yield_kg_per_ha"]), float(i["et_mm"]))
        },
    ),
    "IRRIGATION_WATER_USE_EFFICIENCY": (
        ("yield_kg_per_ha", "applied_water_mm"),
        ("iwue_kg_per_m3",),
        lambda i: {
            "iwue_kg_per_m3": irrigation_water_use_efficiency(
                float(i["yield_kg_per_ha"]), float(i["applied_water_mm"])
            )
        },
    ),
    "DIRECT_EMPLOYMENT_FTE": (
        ("area_ha", "employment_intensity_fte_per_ha", "months_per_year"),
        ("direct_employment_fte",),
        lambda i: {
            "direct_employment_fte": direct_employment_fte(
                float(i["area_ha"]),
                float(i["employment_intensity_fte_per_ha"]),
                float(i.get("months_per_year", 12.0)),
            )
        },
    ),
    "SELF_SUFFICIENCY_RATIO": (
        ("production", "consumption"),
        ("self_sufficiency_ratio", "import_dependency_ratio"),
        lambda i: {
            "self_sufficiency_ratio": self_sufficiency_ratio(
                float(i["production"]), float(i["consumption"])
            ),
            "import_dependency_ratio": import_dependency_ratio(
                float(i["production"]), float(i["consumption"])
            ),
        },
    ),
    "CEREAL_YIELD_GAP": (
        ("attainable_yield_kg_ha", "actual_yield_kg_ha"),
        ("cereal_yield_gap",),
        lambda i: {
            "cereal_yield_gap": cereal_yield_gap(
                float(i["attainable_yield_kg_ha"]), float(i["actual_yield_kg_ha"])
            )
        },
    ),
}


def _make_handler(model_id: str) -> Any:
    """Build the ``(inputs, parameters) -> dict`` handler for a local model."""

    def _handler(inputs: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in inputs.items() if not k.endswith("_unit")}
        required, outputs, compute = _LOCAL_HANDLERS[model_id]
        missing = [name for name in required if clean.get(name) is None]
        if missing:
            raise ValueError(f"{model_id} requires {missing}")
        computed = compute(clean)
        return {"model_id": model_id, "method": model_id.lower(), **computed, "units": outputs[0][1]}

    return _handler


#: Titles of the local equations, used in trace records and reports.
def local_equation_names() -> list[str]:
    """The catalog's model ids, in catalog order."""
    return list(LOCAL_MODELS)


def method_spread(estimates: list[float]) -> dict[str, float]:
    """Spread statistics over a set of method estimates.

    ``mean``, ``min``, ``max``, ``range`` and the population standard
    deviation, all in the estimates' units. The spread is reported instead of a
    single averaged ET0 because the methods disagree in *direction* in arid
    climates: Priestley-Taylor ignores the drying power of the air while Turc
    and Makkink are radiation-only, so the range is the honest statement of
    method uncertainty. The population (ddof=0) statistic is used because the
    methods are the whole population being compared, not a sample of them.
    """
    values = np.asarray([float(x) for x in estimates], dtype=float)
    if values.size == 0:
        raise ValueError("method_spread needs at least one estimate")
    if not np.all(np.isfinite(values)):
        raise ValueError("method_spread needs finite estimates")
    return {
        "mean": float(values.mean()),
        "min": float(values.min()),
        "max": float(values.max()),
        "range": float(values.max() - values.min()),
        "std_population": float(values.std()),
        "count": int(values.size),
    }
