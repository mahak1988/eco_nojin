"""
Climate Engine: FAO-56 Reference Evapotranspiration (ET0)
منبع: Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
        FAO Irrigation and Drainage Paper 56.

Implemented methods:
- Hargreaves-Samani (when only temperature data available)
- Penman-Monteith (full standard, when all data available)

API Compatibility:
- Legacy signature: calc_et0_hargreaves(t_min, t_max, t_mean, ra_mj)
- New signature: calc_et0_hargreaves(data: ClimateData)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ClimateData:
    """داده‌های هواشناسی روزانه برای محاسبات FAO-56"""

    tmin: float  # °C
    tmax: float  # °C
    rh_min: float | None = None  # %
    rh_max: float | None = None  # %
    wind_speed: float | None = None  # m/s at 2m
    solar_radiation: float | None = None  # MJ/m2/day
    elevation: float = 0.0  # m
    latitude: float = 0.0  # degrees (+ = North)
    doy: int = 1  # day of year


# =============================================================================
# توابع کمکی (FAO-56 Equations)
# =============================================================================


def calc_saturation_vapor_pressure(t: float) -> float:
    """فشار بخار اشباع (kPa) - معادله 11 FAO-56"""
    return 0.6108 * math.exp((17.27 * t) / (t + 237.3))


def calc_delta(t: float) -> float:
    """شیب منحنی فشار بخار (kPa/°C) - معادله 13 FAO-56"""
    es = calc_saturation_vapor_pressure(t)
    return 4098 * es / ((t + 237.3) ** 2)


def calc_psychrometric(elevation: float) -> float:
    """ثابت روان‌سنجی (kPa/°C) - معادله 8 FAO-56"""
    pressure = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26
    return 0.000665 * pressure


def calc_extraterrestrial_radiation(latitude: float, doy: int) -> float:
    """
    تابش فرازمینی Ra (MJ/m2/day) - معادله 21 FAO-56
    """
    phi = math.radians(latitude)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta_sun = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    tan_product = math.tan(phi) * math.tan(delta_sun)
    ws = math.acos(max(-1.0, min(1.0, -tan_product)))
    gsc = 0.0820  # solar constant MJ/m2/min
    ra = (
        (24 * 60 / math.pi)
        * gsc
        * dr
        * (
            ws * math.sin(phi) * math.sin(delta_sun)
            + math.cos(phi) * math.cos(delta_sun) * math.sin(ws)
        )
    )
    return max(0.0, ra)


# =============================================================================
# Hargreaves-Samani Method (معادله 52 FAO-56)
# =============================================================================


def _hargreaves_core(t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
    """
    هسته محاسباتی Hargreaves با پارامترهای صریح.

    FAO-56 eq. 52, with the published exponent:

        ET0 = 0.0023 * (Tmean + 17.8) * (Tmax - Tmin)^0.48 * Ra

    The exponent is **0.48**, not 0.50. All five copies of this formula in the
    engine used math.sqrt, i.e. 0.50, which overstates ET0 by 3.3 % at a 5 degC
    diurnal range and 6.6 % at 25 degC. The correction is here, once; the other
    four copies delegate to this function.

    Ra enters as the millimetre-equivalent, so Ra in MJ/m2/day is multiplied by
    0.408 (FAO-56 eq. 40).

    A diurnal range of exactly zero is not a bad input. FAO-56 eq. 52 carries
    (Tmax - Tmin)^0.48, and a uniformly overcast day or a polar night genuinely
    has no swing, for which the published expression is exactly zero. Only an
    inverted range -- t_max below t_min, which no day can have -- is refused.
    """
    if t_max < t_min:
        raise ValueError(f"t_max ({t_max}) must be greater than t_min ({t_min})")
    if ra_mj < 0:
        raise ValueError(f"ra_mj ({ra_mj}) must be non-negative")

    # تبدیل Ra از MJ/m2/day به mm/day (ضریب 0.408)
    ra_mm = ra_mj * 0.408
    et0 = 0.0023 * (t_mean + 17.8) * (t_max - t_min) ** 0.48 * ra_mm
    return max(0.0, et0)


def calc_et0_hargreaves(
    t_min: float | None = None,
    t_max: float | None = None,
    t_mean: float | None = None,
    ra_mj: float | None = None,
    *,
    data: "ClimateData | None" = None,
    dtr_floor: float | None = None,
) -> float:
    """
    محاسبه ET0 با روش Hargreaves-Samani.

    پشتیبانی از دو امضا:
    1. Legacy: calc_et0_hargreaves(t_min=10, t_max=25, t_mean=17.5, ra_mj=15)
    2. New:    calc_et0_hargreaves(data=ClimateData(...))

    Parameters
    ----------
    t_min : float, optional
        حداقل دمای روزانه (°C)
    t_max : float, optional
        حداکثر دمای روزانه (°C)
    t_mean : float, optional
        میانگین دما (°C). اگر None باشد، از (t_min + t_max) / 2 محاسبه می‌شود.
    ra_mj : float, optional
        تابش فرازمینی (MJ/m2/day)
    data : ClimateData, keyword-only
        شیء داده هواشناسی (API جدید)
    dtr_floor : float, optional
        کف دامنهٔ دمای روزانه [°C]. When given, a diurnal range below it is
        clamped up rather than returned as the eq. 52 value. Two of the four
        consolidated copies had their own 0.1 degC floor, and this is how that
        behaviour is preserved without a second implementation. Without it a
        zero range yields the eq. 52 value of zero and an inverted range raises.
    """
    # حالت ۱: استفاده از dataclass جدید
    if data is not None:
        _t_mean = (data.tmax + data.tmin) / 2
        _ra = calc_extraterrestrial_radiation(data.latitude, data.doy)
        return _hargreaves_core(
            data.tmin,
            data.tmax if dtr_floor is None else data.tmin + max(
                data.tmax - data.tmin, dtr_floor
            ),
            _t_mean,
            _ra,
        )

    # حالت ۲: استفاده از پارامترهای صریح (legacy)
    if None in (t_min, t_max, ra_mj):
        raise ValueError(
            "باید یا data=ClimateData(...) ارائه شود، "
            "یا t_min, t_max, ra_mj به صورت keyword arguments."
        )
    if t_mean is None:
        t_mean = (t_min + t_max) / 2
    if dtr_floor is not None:
        t_max = t_min + max(t_max - t_min, dtr_floor)

    return _hargreaves_core(t_min, t_max, t_mean, ra_mj)


# =============================================================================
# Penman-Monteith Method (معادله 39 FAO-56)
# =============================================================================


def calc_net_radiation(
    t_min: float,
    t_max: float,
    ea_kpa: float,
    solar_radiation_mj: float,
    elevation_m: float,
    latitude_deg: float,
    doy: int,
) -> float:
    """Net radiation, FAO-56 equations 38 to 40.

        Rns = (1 - alpha) * Rs                          eq. 38, alpha = 0.23
        Rso = (0.75 + 2e-5 z) * Ra                      eq. 39
        Rnl = sigma * [(Tmax_K^4 + Tmin_K^4)/2]
                   * (0.34 - 0.14 sqrt(ea)) * (1.35 Rs/Rso - 0.35)   eq. 40
        Rn  = Rns - Rnl

    The longwave term uses Stull's (1996) cloudiness factor and is clamped to
    its physical band, as FAO-56 eq. 40 requires: the expression goes negative
    below a cloud fraction of about 0.26 and above 1.0, and FAO-56 states the
    result should be taken as zero in the first case. A clear sky has
    Rs/Rso near 0.75, for which the factor is 0.6625; an overcast sky has
    Rs/Rso near 0.20, for which it is negative and the net longwave is zero.

    Without this term Rn is net SHORT-wave only, and the aerodynamic part of
    eq. 39 is left without an energy budget to draw on. Measured before the term
    existed, the returned ET0 exceeded the first-principles ceiling implied by
    Rn = lambda * ET on 11.2 % of physically valid days, by as much as 27x at
    the worst corner.
    """
    if solar_radiation_mj < 0.0:
        raise ValueError("solar radiation must be non-negative")
    ra = calc_extraterrestrial_radiation(latitude_deg, doy)
    rso = (0.75 + 2.0e-5 * elevation_m) * ra
    rns = (1.0 - 0.23) * solar_radiation_mj

    if rso > 0.0:
        rs_over_rso = min(max(solar_radiation_mj / rso, 0.3), 1.0)
    else:
        # Polar night: there is no shortwave to lose, so the longwave loss is the
        # whole of the net radiation.
        rs_over_rso = 0.3
    cloudiness = 1.35 * rs_over_rso - 0.35
    if cloudiness < 0.0:
        # Overcast: the atmosphere returns more longwave than the surface emits
        # in this direction, and eq. 40 says to take the net loss as zero.
        cloudiness = 0.0

    sigma = 4.903e-9  # MJ K-4 m-2 day-1, FAO-56
    tmax_k = t_max + 273.16
    tmin_k = t_min + 273.16
    rnl = (
        sigma
        * ((tmax_k**4 + tmin_k**4) / 2.0)
        * (0.34 - 0.14 * math.sqrt(max(ea_kpa, 0.0)))
        * cloudiness
    )
    return rns - rnl


def calc_et0_penman_monteith(data: ClimateData) -> float:
    """
    محاسبه ET0 با روش Penman-Monteith (استاندارد جهانی فائو).
    نیازمند همه پارامترها: tmin, tmax, rh_min, rh_max, wind_speed, solar_radiation
    """
    if None in (data.rh_min, data.rh_max, data.wind_speed, data.solar_radiation):
        raise ValueError(
            "داده‌های ناقص. برای Penman-Monteith به همه پارامترها نیاز است: "
            "rh_min, rh_max, wind_speed, solar_radiation."
        )

    tmean = (data.tmax + data.tmin) / 2
    delta = calc_delta(tmean)
    gamma = calc_psychrometric(data.elevation)

    # Actual vapour pressure, FAO-56 eq. 17.
    es_tmax = calc_saturation_vapor_pressure(data.tmax)
    es_tmin = calc_saturation_vapor_pressure(data.tmin)
    ea = (es_tmin * (data.rh_max / 100) + es_tmax * (data.rh_min / 100)) / 2

    # In eq. 39 the symbol ``es`` is the MEAN of the saturation vapour pressures
    # at the maximum and minimum air temperature (FAO-56 eq. 11, note a), and the
    # vapour-pressure deficit is that mean less ``ea``. The engine used es(Tmax)
    # alone, which overstates the deficit and therefore the aerodynamic term. The
    # compiled kernel records that it once used e0(Tmean) and moved off it; the
    # mean of the two endpoints is what the published form specifies.
    es_mean = (es_tmax + es_tmin) / 2

    # Net radiation, eq. 38 to 40. The previous expression was
    # rn = solar_radiation * 0.77, which is net shortwave only: the longwave loss
    # Rnl was absent, so the aerodynamic term of eq. 39 drew on energy the
    # atmosphere had already taken. cpp_core/src/climate.cpp has had the full
    # form since its own comment records the divergence being found; this is
    # that implementation ported rather than re-derived.
    #
    # A slightly negative Rn is a real winter condition, not a bad input. Near
    # the solstice at mid latitudes a 0-2 degC day in January can lose marginally
    # more longwave than it gains in shortwave: a surface that is a net energy
    # sink is exactly why it is cold. The radiation term is therefore floored at
    # zero, because the surface cannot evaporate using energy it does not have,
    # while the aerodynamic term is a transport of advected energy and is left
    # to act. The uncapped value stays available from calc_net_radiation.
    rn_raw = calc_net_radiation(
        t_min=data.tmin,
        t_max=data.tmax,
        ea_kpa=ea,
        solar_radiation_mj=data.solar_radiation,
        elevation_m=data.elevation,
        latitude_deg=data.latitude,
        doy=data.doy,
    )
    rn = max(rn_raw, 0.0)

    numerator = 0.408 * delta * rn + gamma * (900 / (tmean + 273)) * data.wind_speed * (
        es_mean - ea
    )
    denominator = delta + gamma * (1 + 0.34 * data.wind_speed)
    et0 = numerator / denominator
    return max(0.0, et0)


def calc_et0(data: ClimateData) -> float:
    """
    انتخاب خودکار روش بر اساس داده‌های موجود.
    اگر همه داده‌ها موجود باشد → Penman-Monteith
    در غیر این صورت → Hargreaves
    """
    try:
        return calc_et0_penman_monteith(data)
    except ValueError:
        return calc_et0_hargreaves(data=data)
