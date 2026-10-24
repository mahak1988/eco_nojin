"""
Model Registry (Phase 7) — 22 scientific models, fidelity-labelled.

Every entry wraps a REAL implemented function (no stubs). Fidelity badges:
- ``official``    — standard published method (FAO-56, RothC, Farquhar,
                    van Genuchten, RUSLE, IPCC allometric, FAO salinity…)
- ``simplified``  — practical simplification of a known method
- ``experimental``— exploratory / not yet validated against field data

``run_model`` validates input, executes, and returns
``{slug, fidelity, result, executed_at}`` — errors are explicit, never
silent fallbacks.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from services._gateway_facade import (
    CarbonProjectType,
    available_water_capacity,
    calc_et0_hargreaves,
    calculate_carbon_sequestration,
    calculate_leaching_requirement,
    calculate_runoff,
    calculate_soil_health_index,
    classify_salinity,
    compare_crops,
    compute_erosion,
    design_check_dam,
    design_contour_trench,
    design_half_moon,
    estimate_soil_parameters,
    get_climate_projection,
    simulate_crop_yield,
    van_genuchten_theta,
)
from services._gateway_facade import (
    apply_climate_change as _apply_climate_change,
)
from services.api_gateway.routers.carbon_engine import (
    biomass_aboveground,
    biomass_belowground,
    farquhar_photosynthesis,
    quantum_efficiency,
    rothc_carbon_pools,
)

# ---------------------------------------------------------------------------
# Spec types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParamSpec:
    name: str
    label: str
    unit: str = ""
    default: float | None = None
    kind: str = "float"  # float | int | str | select


@dataclass(frozen=True)
class ModelSpec:
    slug: str
    name_fa: str
    name_en: str
    domain: str
    fidelity: str  # official | simplified | experimental
    reference: str
    description: str
    run: Callable[..., Any]
    params: list[ParamSpec] = field(default_factory=list)

    @property
    def param_names(self) -> list[str]:
        return [p.name for p in self.params]


# ---------------------------------------------------------------------------
# Wrappers for awkward signatures
# ---------------------------------------------------------------------------


def _apply_climate_wrapper(
    scenario: str,
    time_horizon: int,
    baseline_temp: float = 18.0,
    baseline_precip: float = 300.0,
    baseline_et0: float = 1500.0,
) -> dict[str, Any]:
    proj = get_climate_projection(
        scenario, time_horizon, baseline_temp, baseline_precip, baseline_et0
    )
    return _apply_climate_change(baseline_temp, baseline_precip, baseline_et0, proj)


def _carbon_seq_wrapper(
    project_type: str, area_ha: float, duration_years: int = 10, region: str = "temperate"
) -> dict[str, Any]:
    try:
        ptype = CarbonProjectType(project_type)
    except ValueError as exc:
        raise ValueError(
            f"unknown project_type '{project_type}'; use one of "
            f"{[t.value for t in CarbonProjectType]}"
        ) from exc
    return calculate_carbon_sequestration(ptype, area_ha, duration_years, region)


# ---------------------------------------------------------------------------
# Adapters: the registry's declared parameters are the public contract, and
# they are not always the wrapped function's own parameter names. Every
# adapter below was needed because the model raised TypeError on every call.
# ---------------------------------------------------------------------------


def _et0_hargreaves_adapter(
    temp_max: float, temp_min: float, elevation: float, latitude: float, doy: int
) -> dict[str, Any]:
    """FAO-56 Hargreaves.

    The registry used to declare ``t_min`` / ``t_max`` / ``t_mean`` /
    ``ra_mj``, but ``ra_mj`` and ``t_mean`` are *derived* by the equation, not
    inputs: the function computes the mean temperature and the extraterrestrial
    radiation itself from the site (elevation, latitude) and the day of year.
    The declared parameters are therefore the ones the method consumes.
    """
    return calc_et0_hargreaves(temp_max, temp_min, elevation, latitude, doy)


def _runoff_adapter(
    precipitation: float, area_ha: float, rational_coefficient: float
) -> dict[str, Any]:
    """Rational-method runoff.

    The registry used to declare ``area_m2`` / ``rainfall_mm`` /
    ``runoff_coefficient``. The function works in hectares and takes the
    coefficient as ``rational_coefficient``, and the rational method is
    selected explicitly rather than left to the SCS-CN default.
    """
    return calculate_runoff(
        precipitation=precipitation,
        method="Rational",
        area_ha=area_ha,
        rational_coefficient=rational_coefficient,
    )


def _check_dam_adapter(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Check-dam design.

    The registry used to declare ``area_m2`` / ``rainfall_mm`` / ``slope_pct``.
    ``peak_flow`` is a *different quantity* from a rainfall depth: it is the
    design flood discharge, which needs a storm duration and a runoff
    coefficient to derive. The old declared parameters were therefore not
    derivable from what the model consumes, and the truthful ones are declared
    instead.
    """
    return design_check_dam(
        drainage_area_ha=drainage_area_ha, peak_flow=peak_flow, slope=slope
    )


def _contour_trench_adapter(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Contour-trench design -- see :func:`_check_dam_adapter`."""
    return design_contour_trench(
        drainage_area_ha=drainage_area_ha, peak_flow=peak_flow, slope=slope
    )


def _half_moon_adapter(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Half-moon bund design -- see :func:`_check_dam_adapter`."""
    return design_half_moon(
        drainage_area_ha=drainage_area_ha, peak_flow=peak_flow, slope=slope
    )


def _crop_yield_adapter(
    crop_type: str,
    available_water: float,
    mean_temp: float,
    growing_season_precip: float = 0.0,
    irrigation_efficiency: float = 0.6,
    co2_concentration: float = 420.0,
) -> dict[str, Any]:
    """Water-limited crop yield.

    The facade takes a ``climate`` / ``soil`` mapping; the engine route reads
    the scalars out of the climate mapping (and, since the B5 engine fix, the
    irrigation efficiency and the CO2 concentration too).
    """
    return simulate_crop_yield(
        crop_type,
        {
            "available_water": available_water,
            "mean_temp": mean_temp,
            "growing_season_precip": growing_season_precip,
            "irrigation_efficiency": irrigation_efficiency,
            "co2_concentration": co2_concentration,
        },
        {},
    )


def _compare_crops_adapter(
    available_water: float,
    mean_temp: float,
    co2_concentration: float = 420.0,
) -> dict[str, Any]:
    """Compare every crop under one climate.

    ``compare_crops`` takes the three scalars; the engine route used to
    forward ``crop_a`` / ``crop_b`` / ``climate_data`` positionally, which
    the B5 engine fix repaired.
    """
    return compare_crops(available_water, mean_temp, co2_concentration)


def _climate_projection_adapter(
    latitude: float, longitude: float, rcp: str, year: int
) -> dict[str, Any]:
    """IPCC AR6 projection for a site and a target year."""
    return get_climate_projection(latitude, longitude, rcp, year)


def _apply_climate_change_adapter(
    scenario: str,
    time_horizon: int,
    baseline_temp: float = 18.0,
    baseline_precip: float = 300.0,
) -> dict[str, Any]:
    """Apply a scenario to a baseline.

    ``time_horizon`` is a *duration* here -- the route converts it against the
    projection baseline year -- and the baseline is passed as the mapping the
    route reads.
    """
    return _apply_climate_change(
        {"temp": baseline_temp, "precip": baseline_precip},
        scenario,
        int(time_horizon),
    )



# ---------------------------------------------------------------------------
# The 22 models
# ---------------------------------------------------------------------------

REGISTRY: list[ModelSpec] = [
    ModelSpec(
        "et0_hargreaves",
        "تبخیر و تعرق مرجع (هارگریوز)",
        "Reference ET0 (Hargreaves)",
        "climate",
        "simplified",
        "FAO-56 Hargreaves",
        "محاسبه ET0 روزانه با روش هارگریوز — نیازمند Ra خورشیدی (MJ/m²/day).",
        _et0_hargreaves_adapter,
[
            ParamSpec("temp_max", "T max", "C"),
            ParamSpec("temp_min", "T min", "C"),
            ParamSpec("elevation", "Elevation", "m"),
            ParamSpec("latitude", "Latitude", "deg"),
            ParamSpec("doy", "Day of year", "day", kind="int"),
        ]
    ),
    ModelSpec(
        "runoff_volume",
        "حجم رواناب سطحی",
        "Surface runoff volume",
        "water",
        "simplified",
        "SCS-style rational",
        "حجم رواناب از مساحت، بارش و ضریب رواناب (m³).",
        _runoff_adapter,
[
            ParamSpec("precipitation", "Precipitation", "mm"),
            ParamSpec("area_ha", "Area", "ha"),
            ParamSpec("rational_coefficient", "Runoff coefficient", "", 0.5),
        ]
    ),
    ModelSpec(
        "check_dam_design",
        "طراحی بند خاکی",
        "Check dam design",
        "water",
        "simplified",
        "Watershed structures",
        "ابعاد پیشنهادی بند خاکی بر اساس شیب، مساحت و بارش.",
        _check_dam_adapter,
[
            ParamSpec("drainage_area_ha", "Drainage area", "ha"),
            ParamSpec("peak_flow", "Peak flow", "m3/s"),
            ParamSpec("slope", "Slope", "%"),
        ]
    ),
    ModelSpec(
        "contour_trench_design",
        "طراحی ترانشه کانتوری",
        "Contour trench design",
        "water",
        "simplified",
        "Watershed structures",
        "ابعاد پیشنهادی ترانشه کانتوری برای جمعآوری رواناب.",
        _contour_trench_adapter,
[
            ParamSpec("drainage_area_ha", "Drainage area", "ha"),
            ParamSpec("peak_flow", "Peak flow", "m3/s"),
            ParamSpec("slope", "Slope", "%"),
        ]
    ),
    ModelSpec(
        "half_moon_design",
        "طراحی هلالی آبگیر",
        "Half-moon catchment design",
        "water",
        "simplified",
        "Watershed structures",
        "ابعاد پیشنهادی هلالی آبگیر (banquette).",
        _half_moon_adapter,
[
            ParamSpec("drainage_area_ha", "Drainage area", "ha"),
            ParamSpec("peak_flow", "Peak flow", "m3/s"),
            ParamSpec("slope", "Slope", "%"),
        ]
    ),
    ModelSpec(
        "crop_yield",
        "پیشبینی عملکرد محصول",
        "Crop yield simulation",
        "crop",
        "simplified",
        "AquaCrop-style",
        "شبیهسازی عملکرد (kg/ha) بر اساس آب، دما و CO₂ — رویکرد سادهشده AquaCrop.",
        _crop_yield_adapter,
[
            ParamSpec("crop_type", "Crop", "", kind="str"),
            ParamSpec("available_water", "Available water", "mm"),
            ParamSpec("mean_temp", "Mean temperature", "C"),
            ParamSpec("growing_season_precip", "Growing season precipitation", "mm", 0),
            ParamSpec("irrigation_efficiency", "Irrigation efficiency", "", 0.6),
            ParamSpec("co2_concentration", "CO2", "ppm", 420),
        ]
    ),
    ModelSpec(
        "compare_crops",
        "مقایسه محصولات",
        "Compare crops",
        "crop",
        "simplified",
        "AquaCrop-style",
        "مقایسه عملکرد و سوددهی چند محصول در شرایط یکسان.",
        _compare_crops_adapter,
[
            ParamSpec("available_water", "Available water", "mm"),
            ParamSpec("mean_temp", "Mean temperature", "C"),
            ParamSpec("co2_concentration", "CO2", "ppm", 420),
        ]
    ),
    ModelSpec(
        "climate_projection",
        "پیشبینی اقلیمی",
        "Climate projection",
        "climate",
        "simplified",
        "IPCC-style scenarios",
        "پروژه اقلیمی (دما/بارش/ET0) برای سناریو و افق زمانی مشخص.",
        _climate_projection_adapter,
[
            ParamSpec("latitude", "Latitude", "deg"),
            ParamSpec("longitude", "Longitude", "deg"),
            ParamSpec("rcp", "Scenario", "", kind="str"),
            ParamSpec("year", "Target year", "year", kind="int"),
        ]
    ),
    ModelSpec(
        "apply_climate_change",
        "اثر تغییر اقلیم",
        "Apply climate change",
        "climate",
        "simplified",
        "IPCC-style scenarios",
        "مقادیر اقلیمی جدید پس از اعمال سناریو بر دادههای پایه.",
        _apply_climate_change_adapter,
[
            ParamSpec("scenario", "Scenario", "", kind="str"),
            ParamSpec("time_horizon", "Time horizon", "year", kind="int"),
            ParamSpec("baseline_temp", "Baseline temperature", "C", 18.0),
            ParamSpec("baseline_precip", "Baseline precipitation", "mm", 300.0),
        ]
    ),
    ModelSpec(
        "biomass_aboveground",
        "زیستتوده هوایی",
        "Aboveground biomass",
        "carbon",
        "official",
        "IPCC allometric (Chave et al.)",
        "زیستتوده هوایی درخت از قطر و ارتفاع.",
        biomass_aboveground,
        [
            ParamSpec("D_cm", "قطر در ارتفاع سینه", "cm"),
            ParamSpec("H_m", "ارتفاع", "m"),
            ParamSpec("wood_density", "چگالی چوب", "g/cm³", 0.55),
        ],
    ),
    ModelSpec(
        "biomass_belowground",
        "زیستتوده زیرزمینی",
        "Belowground biomass",
        "carbon",
        "official",
        "IPCC root:shoot ratio",
        "زیستتوده ریشه از نسبت ریشه به ساقه.",
        biomass_belowground,
        [ParamSpec("AGB_kg", "زیستتوده هوایی", "kg")],
    ),
    ModelSpec(
        "rothc_pools",
        "پولهای کربن RothC",
        "RothC carbon pools",
        "carbon",
        "official",
        "RothC 5-pool model",
        "توزیع کربن آلی خاک بین ۵ پول RothC (DPM/RPM/BIO/HUM/IOM).",
        rothc_carbon_pools,
        [
            ParamSpec("initial_C_tha", "کربن اولیه", "t/ha", 40.0),
            ParamSpec("annual_input_tha", "ورودی سالانه", "t/ha", 3.0),
            ParamSpec("DPM_RPM_ratio", "نسبت DPM/RPM", "", 1.44),
            ParamSpec("clay_pct", "رس", "%", 30.0),
            ParamSpec("temperature_C", "دما", "°C", 15.0),
            ParamSpec("rainfall_mm", "بارش", "mm", 500.0),
            ParamSpec("years", "سال", "year", 50, kind="int"),
        ],
    ),
    ModelSpec(
        "farquhar_photosynthesis",
        "فتوسنتز فارکوهار",
        "Farquhar photosynthesis",
        "carbon",
        "official",
        "Farquhar et al. 1980",
        "نرخ خالص فتوسنتز برگ (A) با مدل بیوشیمیایی فارکوهار.",
        farquhar_photosynthesis,
        [
            ParamSpec("PAR_umol", "تابش فعال فتوسنتزی", "µmol/m²/s", 1500),
            ParamSpec("T_leaf_C", "دمای برگ", "°C", 25.0),
            ParamSpec("CO2_ppm", "CO₂", "ppm", 420.0),
        ],
    ),
    ModelSpec(
        "quantum_efficiency",
        "بازده کوانتومی",
        "Quantum efficiency",
        "carbon",
        "experimental",
        "Exploratory",
        "بازده کوانتومی فتوسنتز بر اساس دما — تجربی، نیازمند اعتبارسنجی میدانی.",
        quantum_efficiency,
        [ParamSpec("T_C", "دما", "°C", 25.0)],
    ),
    ModelSpec(
        "carbon_sequestration",
        "ترسیب کربن پروژه",
        "Project carbon sequestration",
        "carbon",
        "simplified",
        "VM0042-aligned",
        "ترسیب کربن سالانه و کل یک پروژه بر اساس نوع و مساحت.",
        _carbon_seq_wrapper,
        [
            ParamSpec(
                "project_type",
                "نوع پروژه (afforestation/reforestation/agroforestry)",
                "",
                kind="str",
            ),
            ParamSpec("area_ha", "مساحت", "ha"),
            ParamSpec("duration_years", "مدت", "year", 10, kind="int"),
            ParamSpec("region", "منطقه (temperate/tropical)", "", "temperate", kind="str"),
        ],
    ),
    ModelSpec(
        "soil_health_index",
        "شاخص سلامت خاک",
        "Soil health index",
        "soil",
        "simplified",
        "FAO soil health",
        "شاخص سلامت خاک از pH، ماده آلی، N، P و K.",
        calculate_soil_health_index,
        [
            ParamSpec("ph", "pH", ""),
            ParamSpec("organic_matter", "ماده آلی", "%"),
            ParamSpec("nitrogen", "نیتروژن", "mg/kg"),
            ParamSpec("phosphorus", "فسفر", "mg/kg"),
            ParamSpec("potassium", "پتاسیم", "mg/kg"),
            # The engine's SOIL_HEALTH route requires the cation exchange
            # capacity and the soil texture as well; they were not declared,
            # so the model failed validation on every call.
            ParamSpec("cec", "ظرفیت تبادل کاتیونی", "cmol(+)/kg"),
            ParamSpec("texture", "بافت خاک (sand/loam/clay)", "", kind="str"),
        ],
    ),
    ModelSpec(
        "soil_pedotransfer",
        "توابع انتقالی خاک",
        "Pedotransfer functions",
        "soil",
        "official",
        "Saxton & Rawls PTF",
        "تخمین پارامترهای هیدرولیکی خاک از بافت (شن/رس/ماده آلی).",
        estimate_soil_parameters,
        [
            ParamSpec("sand_pct", "شن", "%"),
            ParamSpec("clay_pct", "رس", "%"),
            ParamSpec("om_pct", "ماده آلی", "%", 1.0),
        ],
    ),
    ModelSpec(
        "salinity_class",
        "طبقهبندی شوری خاک",
        "Soil salinity class",
        "soil",
        "official",
        "FAO salinity classes",
        "کلاس شوری بر اساس هدایت الکتریکی (EC dS/m).",
        classify_salinity,
        [ParamSpec("ec", "EC خاک", "dS/m")],
    ),
    ModelSpec(
        "leaching_requirement",
        "نیاز آبشویی",
        "Leaching requirement",
        "soil",
        "official",
        "FAO 29",
        "نیاز آبشویی برای کنترل شوری (LR).",
        calculate_leaching_requirement,
        [
            ParamSpec("ec_soil", "EC خاک", "dS/m"),
            ParamSpec("ec_water", "EC آب آبیاری", "dS/m"),
        ],
    ),
    ModelSpec(
        "van_genuchten_theta",
        "منحنی نگهداشت آب (van Genuchten)",
        "van Genuchten water retention",
        "soil",
        "official",
        "van Genuchten 1980",
        "رطوبت حجمی در پتانسیل ماتریک مشخص.",
        van_genuchten_theta,
        [
            ParamSpec("matric_potential", "پتانسیل ماتریک", "cm"),
            ParamSpec("theta_r", "رطوبت پسماند", "cm³/cm³"),
            ParamSpec("theta_s", "رطوبت اشباع", "cm³/cm³"),
            ParamSpec("alpha", "α", "1/cm"),
            ParamSpec("n", "n", ""),
        ],
    ),
    ModelSpec(
        "soil_water_retention",
        "ظرفیت آب قابل استفاده",
        "Available water capacity",
        "soil",
        "official",
        "Soil texture AWC classes",
        "ظرفیت آب قابل استفاده خاک بر اساس بافت (mm/m).",
        available_water_capacity,
        [ParamSpec("texture_class", "بافت خاک (sand/loam/clay/...)", "", kind="str")],
    ),
    ModelSpec(
        "erosion_usle",
        "فرسایش خاک (RUSLE)",
        "Soil erosion (RUSLE)",
        "soil",
        "official",
        "RUSLE/USLE",
        "هدررفت خاک سالانه با معادله جهانی فرسایش.",
        compute_erosion,
        [
            # The parameter names must match ``compute_erosion``'s signature
            # exactly: it takes ``slope_length`` and ``annual_rainfall``.
            # Declaring ``slope_length_m`` / ``annual_rainfall_mm`` made the
            # model unrunnable (TypeError on every call).
            ParamSpec("slope_length", "طول شیب", "m"),
            ParamSpec("slope_percent", "شیب", "%"),
            ParamSpec("annual_rainfall", "بارش سالانه", "mm"),
            ParamSpec("texture", "بافت (sand/silt/clay/loam)", "", "loam", kind="str"),
            ParamSpec("c_factor", "عامل پوشش C", "", 0.5),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Model cards (Phase 7): validity domain + limitations (honest science)
# ---------------------------------------------------------------------------

MODEL_CARDS: dict[str, dict[str, str]] = {
    "et0_hargreaves": {
        "validity": "روزانه، مناطق نیمه‌خشک؛ Ra از جدول FAO-56",
        "limitations": "برآورد تقریبی ET0؛ در شرایط باد شدید و رطوبت بالا خطای بیشتر",
    },
    "runoff_volume": {
        "validity": "حوضه‌های کوچک (< چند هکتار) با ضریب رواناب منطقی",
        "limitations": "روش ساده؛ سیلاب‌های طراحی نیازمند SCS-CN با داده بارش بلندمدت",
    },
    "check_dam_design": {
        "validity": "آبخیزهای کوچک با شیب ۵ تا ۳۰ درصد",
        "limitations": "ابعاد پیشنهادی مقدماتی؛ طراحی نهایی نیازمند بررسی زمین‌شناسی و هیدرولیک",
    },
    "contour_trench_design": {
        "validity": "شیب‌های ۵ تا ۳۰ درصد، بارش سالانه تا ~۳۰۰mm",
        "limitations": "پیش‌طراحی؛ فاصله و عمق نهایی به بافت خاک بستگی دارد",
    },
    "half_moon_design": {
        "validity": "مناطق خشک با بارش کم، شیب ملایم",
        "limitations": "پیش‌طراحی؛ نیازمند بازدید میدانی",
    },
    "crop_yield": {
        "validity": "محصولات پایه (گندم/جو/ذرت/برنج/…)؛ دما ۱۰ تا ۳۵°C",
        "limitations": "ساده‌سازی AquaCrop؛ آفات/بیماری/مدیریت در نظر گرفته نشده",
    },
    "compare_crops": {
        "validity": "مقایسه نسبی در شرایط یکسان",
        "limitations": "قیمت‌ها ایستا و تقریبی‌اند",
    },
    "climate_projection": {
        "validity": "افق‌های ۲۰۵۰/۲۱۰۰؛ سناریوهای SSP",
        "limitations": "دلتاهای ساده‌شده؛ عدم قطعیت مدل‌های GCM لحاظ نشده",
    },
    "apply_climate_change": {
        "validity": "سناریوهای SSP برای افق‌های ۲۰۵۰/۲۱۰۰",
        "limitations": "تغییرات خطی فرض شده؛ برای برنامه‌ریزی دقیق به داده CMIP6 مراجعه شود",
    },
    "biomass_aboveground": {
        "validity": "درختان ۵ تا ۵۰cm قطر؛ جنگل‌های گرمسیری/معتدل",
        "limitations": "معادله منطقه‌ای؛ چگالی چوب پیش‌فرض ممکن است متفاوت باشد",
    },
    "biomass_belowground": {
        "validity": "نسبت ریشه به ساقه IPCC",
        "limitations": "مقدار ثابت منطقه‌ای؛ خاک‌های خاص متفاوت‌اند",
    },
    "rothc_pools": {
        "validity": "خاک‌های غیراشباع؛ دما ۰ تا ۳۰°C؛ ۰ تا ۶۰ درصد رس",
        "limitations": "پارامترهای تعدیل ساده‌شده؛ کربن معدنی و تالاب لحاظ نشده",
    },
    "farquhar_photosynthesis": {
        "validity": "برگ‌های C3؛ PAR 0 تا ۲۰۰۰؛ دما ۱۰ تا ۴۰°C",
        "limitations": "پارامترهای وابسته به گونه؛ روزنه و تنش آبی لحاظ نشده",
    },
    "quantum_efficiency": {
        "validity": "محدوده آزمایشگاهی",
        "limitations": "تجربی؛ نیازمند اعتبارسنجی میدانی",
    },
    "carbon_sequestration": {
        "validity": "پروژه‌های جنگل‌کاری/احیای جنگل/کشاورزی‌جنگلی؛ نرخ‌های منطقه‌ای",
        "limitations": "ساده‌سازی VM0042؛ baseline و leakage نیازمند محاسبه کامل",
    },
    "soil_health_index": {
        "validity": "شاخص ترکیبی ۰ تا ۱۰۰ برای خاک‌های زراعی",
        "limitations": "وزن‌دهی ثابت؛ بافت و اقلیم می‌توانند تفسیر را تغییر دهند",
    },
    "soil_pedotransfer": {
        "validity": "خاک‌های معدنی؛ شن ۵ تا ۷۰٪ و رس ۵ تا ۶۰٪",
        "limitations": "خاک‌های آلی/آتشفشانی خارج از دامنه",
    },
    "salinity_class": {
        "validity": "طبقات FAO (غیرشور تا بسیارشور)",
        "limitations": "EC عصاره اشباع؛ EC آب زیرزمینی جداگانه ارزیابی شود",
    },
    "leaching_requirement": {
        "validity": "روش FAO 29؛ EC آب آبیاری و خاک مشخص",
        "limitations": "حساسیت گیاهی (آستانه EC) باید از جدول محصولات گرفته شود",
    },
    "van_genuchten_theta": {
        "validity": "پارامترهای van Genuchten معتبر (θr<θs، n>1)",
        "limitations": "پارامترها از منحنی بافت؛ خاک‌های خاص نیازمند اندازه‌گیری",
    },
    "soil_water_retention": {
        "validity": "کلاس‌های بافت استاندارد",
        "limitations": "مقادیر میانگین کلاسی؛ تراکم و ماده آلی می‌توانند تغییر دهند",
    },
    "erosion_usle": {
        "validity": "دیم‌زارها و اراضی شیب‌دار؛ بارش سالانه مشخص",
        "limitations": "عوامل R/K/LS منطقه‌ای؛ فرسایش آبکند و بادی لحاظ نشده",
    },
}


def model_card(slug: str) -> dict[str, str]:
    return MODEL_CARDS.get(slug, {"validity": "", "limitations": ""})


def list_models() -> list[dict[str, Any]]:
    """Registry metadata for the API (no execution)."""
    return [
        {
            "slug": m.slug,
            "name_fa": m.name_fa,
            "name_en": m.name_en,
            "domain": m.domain,
            "fidelity": m.fidelity,
            "reference": m.reference,
            "description": m.description,
            "validity": model_card(m.slug)["validity"],
            "limitations": model_card(m.slug)["limitations"],
            "params": [
                {
                    "name": p.name,
                    "label": p.label,
                    "unit": p.unit,
                    "default": p.default,
                    "kind": p.kind,
                }
                for p in m.params
            ],
        }
        for m in REGISTRY
    ]


def get_model(slug: str) -> ModelSpec | None:
    for m in REGISTRY:
        if m.slug == slug:
            return m
    return None


def run_model(slug: str, params: dict[str, Any]) -> dict[str, Any]:
    """Validate and execute a model. Raises ValueError on bad input."""
    model = get_model(slug)
    if model is None:
        raise ValueError(f"unknown model slug: {slug}")
    kwargs: dict[str, Any] = {}
    for spec in model.params:
        if spec.name in params and params[spec.name] is not None:
            raw = params[spec.name]
            if spec.kind == "str":
                kwargs[spec.name] = str(raw)
            elif spec.kind == "int":
                kwargs[spec.name] = int(raw)
            else:
                kwargs[spec.name] = float(raw)
        elif spec.default is not None:
            kwargs[spec.name] = spec.default
        else:
            raise ValueError(f"missing required parameter: {spec.name} ({spec.label})")
    started = time.time()
    result = model.run(**kwargs)
    return {
        "slug": model.slug,
        "fidelity": model.fidelity,
        "result": result,
        "executed_ms": round((time.time() - started) * 1000, 2),
    }
