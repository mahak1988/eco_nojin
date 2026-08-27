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

from engine.hydroma.carbon.calculator import (
    CarbonProjectType,
    calculate_carbon_sequestration,
)
from engine.hydroma.climate.et_calculator import calc_et0_hargreaves
from engine.hydroma.scenarios.climate_scenarios import (
    apply_climate_change as _apply_climate_change,
    get_climate_projection,
)
from engine.hydroma.scenarios.crop_scenarios import compare_crops, simulate_crop_yield
from engine.hydroma.soil.health import calculate_soil_health_index
from engine.hydroma.soil.pedotransfer import estimate_soil_parameters
from engine.hydroma.soil.physics import (
    available_water_capacity,
    van_genuchten_theta,
)
from engine.hydroma.soil.salinity import (
    calculate_leaching_requirement,
    classify_salinity,
)
from engine.hydroma.watershed.calculator import (
    calculate_runoff,
    design_check_dam,
    design_contour_trench,
    design_half_moon,
)
from engine.hydroma.wrapper import compute_erosion
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


def _carbon_seq_wrapper(project_type: str, area_ha: float, duration_years: int = 10, region: str = "temperate") -> dict[str, Any]:
    try:
        ptype = CarbonProjectType(project_type)
    except ValueError as exc:
        raise ValueError(
            f"unknown project_type '{project_type}'; use one of "
            f"{[t.value for t in CarbonProjectType]}"
        ) from exc
    return calculate_carbon_sequestration(ptype, area_ha, duration_years, region)


# ---------------------------------------------------------------------------
# The 22 models
# ---------------------------------------------------------------------------

REGISTRY: list[ModelSpec] = [
    ModelSpec(
        "et0_hargreaves", "تبخیر و تعرق مرجع (هارگریوز)", "Reference ET0 (Hargreaves)",
        "climate", "simplified", "FAO-56 Hargreaves",
        "محاسبه ET0 روزانه با روش هارگریوز — نیازمند Ra خورشیدی (MJ/m²/day).",
        calc_et0_hargreaves,
        [
            ParamSpec("t_min", "دمای کمینه", "°C"),
            ParamSpec("t_max", "دمای بیشینه", "°C"),
            ParamSpec("t_mean", "دمای میانگین", "°C"),
            ParamSpec("ra_mj", "تابش فرازمینی", "MJ/m²/day"),
        ],
    ),
    ModelSpec(
        "runoff_volume", "حجم رواناب سطحی", "Surface runoff volume",
        "water", "simplified", "SCS-style rational",
        "حجم رواناب از مساحت، بارش و ضریب رواناب (m³).",
        calculate_runoff,
        [
            ParamSpec("area_m2", "مساحت", "m²"),
            ParamSpec("rainfall_mm", "بارش", "mm"),
            ParamSpec("runoff_coefficient", "ضریب رواناب", "", 0.5),
        ],
    ),
    ModelSpec(
        "check_dam_design", "طراحی بند خاکی", "Check dam design",
        "water", "simplified", "Watershed structures",
        "ابعاد پیشنهادی بند خاکی بر اساس شیب، مساحت و بارش.",
        design_check_dam,
        [
            ParamSpec("slope_pct", "شیب", "%"),
            ParamSpec("area_m2", "مساحت آبخیز", "m²"),
            ParamSpec("rainfall_mm", "بارش", "mm", 100),
        ],
    ),
    ModelSpec(
        "contour_trench_design", "طراحی ترانشه کانتوری", "Contour trench design",
        "water", "simplified", "Watershed structures",
        "ابعاد پیشنهادی ترانشه کانتوری برای جمعآوری رواناب.",
        design_contour_trench,
        [
            ParamSpec("slope_pct", "شیب", "%"),
            ParamSpec("area_m2", "مساحت", "m²"),
            ParamSpec("rainfall_mm", "بارش", "mm", 100),
        ],
    ),
    ModelSpec(
        "half_moon_design", "طراحی هلالی آبگیر", "Half-moon catchment design",
        "water", "simplified", "Watershed structures",
        "ابعاد پیشنهادی هلالی آبگیر (banquette).",
        design_half_moon,
        [
            ParamSpec("slope_pct", "شیب", "%"),
            ParamSpec("area_m2", "مساحت", "m²"),
            ParamSpec("rainfall_mm", "بارش", "mm", 100),
        ],
    ),
    ModelSpec(
        "crop_yield", "پیشبینی عملکرد محصول", "Crop yield simulation",
        "crop", "simplified", "AquaCrop-style",
        "شبیهسازی عملکرد (kg/ha) بر اساس آب، دما و CO₂ — رویکرد سادهشده AquaCrop.",
        simulate_crop_yield,
        [
            ParamSpec("crop_type", "محصول", "", kind="str"),
            ParamSpec("available_water", "آب در دسترس", "mm"),
            ParamSpec("mean_temp", "دمای میانگین", "°C"),
            ParamSpec("growing_season_precip", "بارش فصل رشد", "mm", 0),
            ParamSpec("irrigation_efficiency", "راندمان آبیاری", "", 0.6),
            ParamSpec("co2_concentration", "غلظت CO₂", "ppm", 420),
        ],
    ),
    ModelSpec(
        "compare_crops", "مقایسه محصولات", "Compare crops",
        "crop", "simplified", "AquaCrop-style",
        "مقایسه عملکرد و سوددهی چند محصول در شرایط یکسان.",
        compare_crops,
        [
            ParamSpec("available_water", "آب در دسترس", "mm"),
            ParamSpec("mean_temp", "دمای میانگین", "°C"),
            ParamSpec("co2_concentration", "غلظت CO₂", "ppm", 420),
        ],
    ),
    ModelSpec(
        "climate_projection", "پیشبینی اقلیمی", "Climate projection",
        "climate", "simplified", "IPCC-style scenarios",
        "پروژه اقلیمی (دما/بارش/ET0) برای سناریو و افق زمانی مشخص.",
        get_climate_projection,
        [
            ParamSpec("scenario", "سناریو (SSP1/SSP2/SSP3/SSP5)", "", kind="str"),
            ParamSpec("time_horizon", "افق زمانی", "year", kind="int"),
            ParamSpec("baseline_temp", "دمای پایه", "°C", 18.0),
            ParamSpec("baseline_precip", "بارش پایه", "mm", 300.0),
        ],
    ),
    ModelSpec(
        "apply_climate_change", "اثر تغییر اقلیم", "Apply climate change",
        "climate", "simplified", "IPCC-style scenarios",
        "مقادیر اقلیمی جدید پس از اعمال سناریو بر دادههای پایه.",
        _apply_climate_wrapper,
        [
            ParamSpec("scenario", "سناریو", "", kind="str"),
            ParamSpec("time_horizon", "افق زمانی", "year"),
            ParamSpec("baseline_temp", "دمای پایه", "°C", 18.0),
            ParamSpec("baseline_precip", "بارش پایه", "mm", 300.0),
        ],
    ),
    ModelSpec(
        "biomass_aboveground", "زیستتوده هوایی", "Aboveground biomass",
        "carbon", "official", "IPCC allometric (Chave et al.)",
        "زیستتوده هوایی درخت از قطر و ارتفاع.",
        biomass_aboveground,
        [
            ParamSpec("D_cm", "قطر در ارتفاع سینه", "cm"),
            ParamSpec("H_m", "ارتفاع", "m"),
            ParamSpec("wood_density", "چگالی چوب", "g/cm³", 0.55),
        ],
    ),
    ModelSpec(
        "biomass_belowground", "زیستتوده زیرزمینی", "Belowground biomass",
        "carbon", "official", "IPCC root:shoot ratio",
        "زیستتوده ریشه از نسبت ریشه به ساقه.",
        biomass_belowground,
        [ParamSpec("AGB_kg", "زیستتوده هوایی", "kg")],
    ),
    ModelSpec(
        "rothc_pools", "پولهای کربن RothC", "RothC carbon pools",
        "carbon", "official", "RothC 5-pool model",
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
        "farquhar_photosynthesis", "فتوسنتز فارکوهار", "Farquhar photosynthesis",
        "carbon", "official", "Farquhar et al. 1980",
        "نرخ خالص فتوسنتز برگ (A) با مدل بیوشیمیایی فارکوهار.",
        farquhar_photosynthesis,
        [
            ParamSpec("PAR_umol", "تابش فعال فتوسنتزی", "µmol/m²/s", 1500),
            ParamSpec("T_leaf_C", "دمای برگ", "°C", 25.0),
            ParamSpec("CO2_ppm", "CO₂", "ppm", 420.0),
        ],
    ),
    ModelSpec(
        "quantum_efficiency", "بازده کوانتومی", "Quantum efficiency",
        "carbon", "experimental", "Exploratory",
        "بازده کوانتومی فتوسنتز بر اساس دما — تجربی، نیازمند اعتبارسنجی میدانی.",
        quantum_efficiency,
        [ParamSpec("T_C", "دما", "°C", 25.0)],
    ),
    ModelSpec(
        "carbon_sequestration", "ترسیب کربن پروژه", "Project carbon sequestration",
        "carbon", "simplified", "VM0042-aligned",
        "ترسیب کربن سالانه و کل یک پروژه بر اساس نوع و مساحت.",
        _carbon_seq_wrapper,
        [
            ParamSpec("project_type", "نوع پروژه (afforestation/reforestation/agroforestry)", "", kind="str"),
            ParamSpec("area_ha", "مساحت", "ha"),
            ParamSpec("duration_years", "مدت", "year", 10, kind="int"),
            ParamSpec("region", "منطقه (temperate/tropical)", "", "temperate"),
        ],
    ),
    ModelSpec(
        "soil_health_index", "شاخص سلامت خاک", "Soil health index",
        "soil", "simplified", "FAO soil health",
        "شاخص سلامت خاک از pH، ماده آلی، N، P و K.",
        calculate_soil_health_index,
        [
            ParamSpec("ph", "pH", ""),
            ParamSpec("organic_matter", "ماده آلی", "%"),
            ParamSpec("nitrogen", "نیتروژن", "mg/kg"),
            ParamSpec("phosphorus", "فسفر", "mg/kg"),
            ParamSpec("potassium", "پتاسیم", "mg/kg"),
        ],
    ),
    ModelSpec(
        "soil_pedotransfer", "توابع انتقالی خاک", "Pedotransfer functions",
        "soil", "official", "Saxton & Rawls PTF",
        "تخمین پارامترهای هیدرولیکی خاک از بافت (شن/رس/ماده آلی).",
        estimate_soil_parameters,
        [
            ParamSpec("sand_pct", "شن", "%"),
            ParamSpec("clay_pct", "رس", "%"),
            ParamSpec("om_pct", "ماده آلی", "%", 1.0),
        ],
    ),
    ModelSpec(
        "salinity_class", "طبقهبندی شوری خاک", "Soil salinity class",
        "soil", "official", "FAO salinity classes",
        "کلاس شوری بر اساس هدایت الکتریکی (EC dS/m).",
        classify_salinity,
        [ParamSpec("ec", "EC خاک", "dS/m")],
    ),
    ModelSpec(
        "leaching_requirement", "نیاز آبشویی", "Leaching requirement",
        "soil", "official", "FAO 29",
        "نیاز آبشویی برای کنترل شوری (LR).",
        calculate_leaching_requirement,
        [
            ParamSpec("ec_soil", "EC خاک", "dS/m"),
            ParamSpec("ec_water", "EC آب آبیاری", "dS/m"),
        ],
    ),
    ModelSpec(
        "van_genuchten_theta", "منحنی نگهداشت آب (van Genuchten)", "van Genuchten water retention",
        "soil", "official", "van Genuchten 1980",
        "رطوبت حجمی در پتانسیل ماتریک مشخص.",
        van_genuchten_theta,
        [
            ParamSpec("h", "پتانسیل ماتریک", "cm"),
            ParamSpec("theta_r", "رطوبت پسماند", "cm³/cm³"),
            ParamSpec("theta_s", "رطوبت اشباع", "cm³/cm³"),
            ParamSpec("alpha", "α", "1/cm"),
            ParamSpec("n", "n", ""),
        ],
    ),
    ModelSpec(
        "soil_water_retention", "ظرفیت آب قابل استفاده", "Available water capacity",
        "soil", "official", "Soil texture AWC classes",
        "ظرفیت آب قابل استفاده خاک بر اساس بافت (mm/m).",
        available_water_capacity,
        [ParamSpec("texture", "بافت خاک (sand/loam/clay/...)", "", kind="str")],
    ),
    ModelSpec(
        "erosion_usle", "فرسایش خاک (RUSLE)", "Soil erosion (RUSLE)",
        "soil", "official", "RUSLE/USLE",
        "هدررفت خاک سالانه با معادله جهانی فرسایش.",
        compute_erosion,
        [
            ParamSpec("slope_length_m", "طول شیب", "m"),
            ParamSpec("slope_percent", "شیب", "%"),
            ParamSpec("annual_rainfall_mm", "بارش سالانه", "mm"),
            ParamSpec("texture", "بافت (sand/silt/clay/loam)", "", "loam"),
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
