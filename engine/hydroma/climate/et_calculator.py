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
from typing import Optional


@dataclass
class ClimateData:
    """داده‌های هواشناسی روزانه برای محاسبات FAO-56"""
    tmin: float                            # °C
    tmax: float                            # °C
    rh_min: Optional[float] = None         # %
    rh_max: Optional[float] = None         # %
    wind_speed: Optional[float] = None     # m/s at 2m
    solar_radiation: Optional[float] = None  # MJ/m2/day
    elevation: float = 0.0                 # m
    latitude: float = 0.0                  # degrees (+ = North)
    doy: int = 1                           # day of year


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
    ra = (24 * 60 / math.pi) * gsc * dr * (
        ws * math.sin(phi) * math.sin(delta_sun)
        + math.cos(phi) * math.cos(delta_sun) * math.sin(ws)
    )
    return max(0.0, ra)


# =============================================================================
# Hargreaves-Samani Method (معادله 52 FAO-56)
# =============================================================================

def _hargreaves_core(t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
    """
    هسته محاسباتی Hargreaves با پارامترهای صریح.
    ET0 = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
    """
    if t_max <= t_min:
        raise ValueError(f"t_max ({t_max}) must be greater than t_min ({t_min})")
    if ra_mj < 0:
        raise ValueError(f"ra_mj ({ra_mj}) must be non-negative")

    # تبدیل Ra از MJ/m2/day به mm/day (ضریب 0.408)
    ra_mm = ra_mj * 0.408
    et0 = 0.0023 * (t_mean + 17.8) * math.sqrt(t_max - t_min) * ra_mm
    return max(0.0, et0)


def calc_et0_hargreaves(
    t_min: Optional[float] = None,
    t_max: Optional[float] = None,
    t_mean: Optional[float] = None,
    ra_mj: Optional[float] = None,
    *,
    data: Optional[ClimateData] = None,
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
    """
    # حالت ۱: استفاده از dataclass جدید
    if data is not None:
        _t_mean = (data.tmax + data.tmin) / 2
        _ra = calc_extraterrestrial_radiation(data.latitude, data.doy)
        return _hargreaves_core(data.tmin, data.tmax, _t_mean, _ra)

    # حالت ۲: استفاده از پارامترهای صریح (legacy)
    if None in (t_min, t_max, ra_mj):
        raise ValueError(
            "باید یا data=ClimateData(...) ارائه شود، "
            "یا t_min, t_max, ra_mj به صورت keyword arguments."
        )
    if t_mean is None:
        t_mean = (t_min + t_max) / 2

    return _hargreaves_core(t_min, t_max, t_mean, ra_mj)


# =============================================================================
# Penman-Monteith Method (معادله 39 FAO-56)
# =============================================================================

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

    # فشار بخار واقعی (ea) - معادله 17 FAO-56
    es_tmax = calc_saturation_vapor_pressure(data.tmax)
    es_tmin = calc_saturation_vapor_pressure(data.tmin)
    ea = (es_tmin * (data.rh_max / 100) + es_tmax * (data.rh_min / 100)) / 2

    # تابش خالص (Rn) - albedo grass = 0.23
    rn = data.solar_radiation * 0.77

    numerator = (
        0.408 * delta * rn
        + gamma * (900 / (tmean + 273)) * data.wind_speed * (es_tmax - ea)
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
