#!/usr/bin/env python3
"""
============================================================================
اسکریپت افزودن مدل‌ها و شاخص‌های جامع به پلتفرم eco_nojin
============================================================================
این اسکریپت ۸ دسته مدل و شاخص را به ریپازیتوری و دیتابیس اضافه می‌کند:
    ۱. مدل‌های تصمیم‌گیری (M001-M008)
    ۲. شاخص‌های خشکسالی
    ۳. شاخص‌های پوشش گیاهی
    ۴. شاخص‌های خاک
    ۵. شاخص‌های آب
    ۶. شاخص‌های اقتصادی
    ۷. شاخص‌های پایداری
    ۸. شاخص‌های امنیت غذایی
============================================================================
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json

import duckdb
import polars as pl

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "data" / "eco_nojin_master.duckdb"
TARGET_FILE = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"


# ============================================================
# بخش ۱: تعریف مدل‌ها و شاخص‌ها (Enums & Data Classes)
# ============================================================

class ModelCategory(Enum):
    DECISION = "decision_engine"
    DROUGHT = "drought_indices"
    VEGETATION = "vegetation_indices"
    SOIL = "soil_indices"
    WATER = "water_indices"
    ECONOMIC = "economic_indices"
    SUSTAINABILITY = "sustainability_indices"
    FOOD_SECURITY = "food_security_indices"


class IndexScale(Enum):
    ZERO_TO_ONE = "0-1"
    ZERO_TO_100 = "0-100"
    NEGATIVE_TO_POSITIVE = "-∞ to +∞"
    CATEGORICAL = "categorical"
    PERCENTAGE = "0-100%"


class IndexDirection(Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    OPTIMAL_RANGE = "optimal_range"


@dataclass
class IndexDefinition:
    id: str
    name_fa: str
    name_en: str
    category: ModelCategory
    formula: str
    unit: str
    scale: IndexScale
    direction: IndexDirection
    optimal_range: Optional[tuple] = None
    threshold_critical: Optional[float] = None
    threshold_warning: Optional[float] = None
    data_sources: List[str] = field(default_factory=list)
    description_fa: str = ""
    reference: str = ""


@dataclass
class ModelDefinition:
    id: str
    name_fa: str
    name_en: str
    category: ModelCategory
    output_scale: str
    inputs: List[str]
    weights: Dict[str, float] = field(default_factory=dict)
    logic_note: str = ""
    hard_constraints: List[str] = field(default_factory=list)
    reference: str = ""


# ============================================================
# بخش ۲: تعریف کامل مدل‌های تصمیم‌گیری (M001-M008)
# ============================================================

DECISION_MODELS: List[ModelDefinition] = [
    ModelDefinition(
        id="M001", name_fa="نمره تناسب زراعی", name_en="Crop Suitability Score",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["climate", "soil", "water", "phenology", "management"],
        weights={"climate_fit": 0.25, "soil_fit": 0.25, "water_security": 0.20,
                 "phenology_match": 0.15, "management_fit": 0.15},
        logic_note="Use weighted min/penalty approach; never rely on climate alone",
        hard_constraints=["min_temp", "max_temp", "soil_depth", "salinity"],
        reference="FAO Framework for Land Evaluation"
    ),
    ModelDefinition(
        id="M002", name_fa="نمره دیم‌کاری", name_en="Rainfed Score",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["seasonal_rainfall", "rainfall_cv", "soil_awc", "crop_water_need"],
        weights={"water_balance": 0.40, "rainfall_reliability": 0.25,
                 "soil_moisture_retention": 0.20, "seasonal_distribution": 0.15},
        logic_note="Use growing-season water balance, not annual rainfall",
        reference="FAO Crop Water Simulator"
    ),
    ModelDefinition(
        id="M003", name_fa="اولویت آبیاری", name_en="Irrigation Priority",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["crop_water_deficit", "water_availability", "efficiency", "crop_value"],
        weights={"deficit_severity": 0.35, "water_sustainability": 0.30,
                 "economic_value": 0.20, "efficiency_potential": 0.15},
        logic_note="Prioritize high-value deficit crops only when water sustainability passes",
        hard_constraints=["aquifer_decline_rate", "allocation_limit"],
        reference="AQUASTAT methodology"
    ),
    ModelDefinition(
        id="M004", name_fa="سازگاری اگروفارستری", name_en="Agroforestry Compatibility",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["shade_tolerance", "root_competition", "canopy", "water_niche"],
        weights={"light_complementarity": 0.30, "root_niche": 0.25,
                 "water_complementarity": 0.25, "economic_synergy": 0.20},
        logic_note="Optimize vertical and temporal complementarity",
        reference="USDA-NAC Agroforestry Practices"
    ),
    ModelDefinition(
        id="M005", name_fa="ریسک آفات", name_en="Pest Risk Score",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["temperature", "humidity", "crop_stage", "host_continuity", "natural_enemies"],
        weights={"climate_suitability": 0.30, "host_availability": 0.25,
                 "historical_incidence": 0.20, "biocontrol_potential": 0.15, "management": 0.10},
        logic_note="Use IPM first; pesticide is last-resort",
        reference="EPPO/CABI Pest Risk Analysis"
    ),
    ModelDefinition(
        id="M006", name_fa="جذابیت اقتصادی", name_en="Economic Attractiveness",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["yield", "price", "costs", "risk", "market_access"],
        weights={"net_margin": 0.35, "price_stability": 0.20,
                 "market_access": 0.20, "input_efficiency": 0.15, "risk_adjustment": 0.10},
        logic_note="Include price volatility and market access",
        reference="FAOSTAT Producer Prices"
    ),
    ModelDefinition(
        id="M007", name_fa="نمره تاب‌آوری", name_en="Resilience Score",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["diversity", "drought_tolerance", "frost_tolerance", "water_security", "income_diversity"],
        weights={"system_diversity": 0.25, "climate_tolerance": 0.25,
                 "water_security": 0.20, "income_diversity": 0.15, "soil_health": 0.15},
        logic_note="Reward diversified systems",
        reference="FAO Resilience Framework"
    ),
    ModelDefinition(
        id="M008", name_fa="تخصیص کاربری زمین", name_en="Land Use Allocation",
        category=ModelCategory.DECISION, output_scale="0-100",
        inputs=["suitability", "water_budget", "labor", "market", "ecological_constraints"],
        weights={"biophysical_suitability": 0.30, "water_budget": 0.25,
                 "socioeconomic_fit": 0.20, "ecological_constraint": 0.15, "policy": 0.10},
        logic_note="Allocate hectares subject to hard constraints",
        reference="GAEZ Land Use Planning"
    ),
]


# ============================================================
# بخش ۳: تعریف شاخص‌های خشکسالی
# ============================================================

DROUGHT_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="DI001", name_fa="شاخص بارش استاندارد شده", name_en="SPI",
        category=ModelCategory.DROUGHT,
        formula="SPI = (P - μ) / σ",
        unit="standard deviations", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(0.5, 2.0), threshold_warning=-1.0, threshold_critical=-2.0,
        data_sources=["data_weather_daily", "data_weather_history_annual"],
        description_fa="شاخص خشکسالی بر اساس بارش در بازه‌های ۱ تا ۴۸ ماهه",
        reference="McKee et al. 1993, WMO No. 1090"
    ),
    IndexDefinition(
        id="DI002", name_fa="شاخص تبخیر و تعرق بارندگی", name_en="SPEI",
        category=ModelCategory.DROUGHT,
        formula="SPEI = (P - PET - μ) / σ",
        unit="standard deviations", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(0.5, 2.0), threshold_warning=-1.0, threshold_critical=-2.0,
        data_sources=["data_weather_daily", "data_weather_history_annual"],
        description_fa="SPI با احتساب تبخیر و تعرق پتانسیل (حساس به تغییر اقلیم)",
        reference="Vicente-Serrano et al. 2010"
    ),
    IndexDefinition(
        id="DI003", name_fa="شاخص شدت خشکسالی پالمر", name_en="PDSI",
        category=ModelCategory.DROUGHT,
        formula="PDSI = f(moisture anomaly, CAFEC precipitation)",
        unit="dimensionless", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(2.0, 4.0), threshold_warning=-2.0, threshold_critical=-4.0,
        data_sources=["data_weather_daily", "ref_soils"],
        description_fa="شاخص بلندمدت خشکسالی با احتراق رطوبت خاک",
        reference="Palmer 1965, Palmer Drought Severity Index"
    ),
    IndexDefinition(
        id="DI004", name_fa="شاخص رطوبت خاک", name_en="SSI",
        category=ModelCategory.DROUGHT,
        formula="SSI = (θ - θ_wilt) / (θ_fc - θ_wilt)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(0.6, 1.0), threshold_warning=0.3, threshold_critical=0.1,
        data_sources=["ref_soils", "data_weather_daily"],
        description_fa="شاخص رطوبت خاک نسبی به ظرفیت مزرعه",
        reference="Narasimhan & Srinivasan 2005"
    ),
    IndexDefinition(
        id="DI005", name_fa="شاخص خشکسالی آب سطحی", name_en="SWSI",
        category=ModelCategory.DROUGHT,
        formula="SWSI = Σ(P_i × C_i)",
        unit="-8 to +8", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(2, 8), threshold_warning=-2, threshold_critical=-4,
        data_sources=["data_weather_daily", "ref_water"],
        description_fa="شاخص یکپارچه خشکسالی آب سطحی (بارش، برف، رواناب، مخازن)",
        reference="Shafer & Dezman 1982"
    ),
    IndexDefinition(
        id="DI006", name_fa="شاخص خشکسالی تبخیر و تعرق", name_en="ETDI",
        category=ModelCategory.DROUGHT,
        formula="ETDI = (ET_actual - ET_mean) / ET_std",
        unit="standard deviations", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["data_weather_daily"],
        description_fa="شاخص خشکسالی بر اساس تبخیر و تعرق واقعی",
        reference="Anderson et al. 2011"
    ),
]


# ============================================================
# بخش ۴: شاخص‌های پوشش گیاهی
# ============================================================

VEGETATION_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="VI001", name_fa="شاخص پوشش گیاهی تفاوت نرمال", name_en="NDVI",
        category=ModelCategory.VEGETATION,
        formula="NDVI = (NIR - Red) / (NIR + Red)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(0.6, 0.9), threshold_warning=0.3, threshold_critical=0.1,
        data_sources=["sentinel2_bands", "landsat_bands"],
        description_fa="شاخص استاندارد پوشش گیاهی از تصاویر ماهواره‌ای",
        reference="Rouse et al. 1974"
    ),
    IndexDefinition(
        id="VI002", name_fa="شاخص پوشش گیاهی بهبود یافته", name_en="EVI",
        category=ModelCategory.VEGETATION,
        formula="EVI = G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(0.5, 0.8),
        data_sources=["sentinel2_bands"],
        description_fa="نسخه بهبود یافته NDVI با حذف اثرات اتمسفر و خاک",
        reference="Huete et al. 2002"
    ),
    IndexDefinition(
        id="VI003", name_fa="شاخص پوشش گیاهی تنظیم‌شده خاک", name_en="SAVI",
        category=ModelCategory.VEGETATION,
        formula="SAVI = ((NIR - Red) / (NIR + Red + L)) × (1 + L)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["sentinel2_bands"],
        description_fa="مناسب برای مناطق خشک با پوشش گیاهی کم",
        reference="Huete 1988"
    ),
    IndexDefinition(
        id="VI004", name_fa="شاخص سطح برگ", name_en="LAI",
        category=ModelCategory.VEGETATION,
        formula="LAI = leaf_area / ground_area",
        unit="m²/m²", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(3.0, 6.0),
        data_sources=["sentinel2_bands", "field_measurement"],
        description_fa="سطح برگ به ازای واحد سطح زمین",
        reference="Chen & Black 1992"
    ),
    IndexDefinition(
        id="VI005", name_fa="کسر جذب فتوسنتزی فعال", name_en="FPAR",
        category=ModelCategory.VEGETATION,
        formula="FPAR = f(NDVI, biome_type)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["sentinel2_bands"],
        description_fa="کسر تابش فتوسنتزی فعال جذب شده توسط پوشش گیاهی",
        reference="Myneni et al. 1997"
    ),
    IndexDefinition(
        id="VI006", name_fa="تولید ناخالص اولیه", name_en="GPP",
        category=ModelCategory.VEGETATION,
        formula="GPP = APAR × LUE",
        unit="g C/m²/day", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["sentinel2_bands", "meteorological"],
        description_fa="میزان کل کربن تثبیت شده توسط فتوسنتز",
        reference="Monteith 1972"
    ),
]


# ============================================================
# بخش ۵: شاخص‌های خاک
# ============================================================

SOIL_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="SI001", name_fa="شاخص کیفیت خاک", name_en="SQR",
        category=ModelCategory.SOIL,
        formula="SQR = Σ(w_i × s_i) [weighted sum of soil indicators]",
        unit="score", scale=IndexScale.ZERO_TO_100,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(70, 100), threshold_warning=50, threshold_critical=30,
        data_sources=["ref_soils", "field_measurement"],
        description_fa="شاخص ترکیبی کیفیت خاک بر اساس پارامترهای فیزیکی، شیمیایی و بیولوژیکی",
        reference="Andrews et al. 2004, Soil Management Assessment Framework"
    ),
    IndexDefinition(
        id="SI002", name_fa="موجودی کربن آلی خاک", name_en="SOC Stock",
        category=ModelCategory.SOIL,
        formula="SOC_stock = SOC_content × bulk_density × depth × (1-coarse_fragment)",
        unit="t C/ha", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(50, 150),
        data_sources=["ref_soils", "lab_analysis"],
        description_fa="موجودی کربن آلی خاک در عمق مشخص",
        reference="IPCC 2019 Guidelines, Tier 2"
    ),
    IndexDefinition(
        id="SI003", name_fa="ظرفیت نگهداشت آب خاک", name_en="AWC",
        category=ModelCategory.SOIL,
        formula="AWC = (θ_fc - θ_wilt) × depth",
        unit="mm", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(100, 200),
        data_sources=["ref_soils"],
        description_fa="مقدار آب قابل دسترس گیاه در پروفیل خاک",
        reference="FAO HWSD methodology"
    ),
    IndexDefinition(
        id="SI004", name_fa="هدایت هیدرولیکی اشباع", name_en="Ksat",
        category=ModelCategory.SOIL,
        formula="Ksat = f(texture, structure, organic_matter)",
        unit="mm/h", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.OPTIMAL_RANGE,
        optimal_range=(10, 50),
        data_sources=["ref_soils"],
        description_fa="سرعت نفوذ آب در خاک اشباع",
        reference="Saxton & Rawls 2006"
    ),
    IndexDefinition(
        id="SI005", name_fa="نرخ فرسایش خاک", name_en="Erosion Rate",
        category=ModelCategory.SOIL,
        formula="A = R × K × LS × C × P (RUSLE)",
        unit="t/ha/year", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.LOWER_BETTER,
        optimal_range=(0, 5), threshold_warning=10, threshold_critical=25,
        data_sources=["rainfall_raster", "dem_raster", "landcover_raster"],
        description_fa="نرخ فرسایش آبی خاک بر اساس مدل RUSLE",
        reference="Renard et al. 1997, RUSLE"
    ),
]


# ============================================================
# بخش ۶: شاخص‌های آب
# ============================================================

WATER_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="WI001", name_fa="شاخص فقر آب", name_en="WPI",
        category=ModelCategory.WATER,
        formula="WPI = f(access, use, capacity, resources, environment)",
        unit="score", scale=IndexScale.ZERO_TO_100,
        direction=IndexDirection.LOWER_BETTER,
        optimal_range=(0, 30), threshold_warning=50, threshold_critical=70,
        data_sources=["ref_water", "ref_sites"],
        description_fa="شاخص ترکیبی فقر آب (دسترسی، استفاده، ظرفیت، منابع، محیط)",
        reference="Sullivan et al. 2003"
    ),
    IndexDefinition(
        id="WI002", name_fa="شاخص تنش آبی", name_en="WSI",
        category=ModelCategory.WATER,
        formula="WSI = water_withdrawal / total_renewable_water",
        unit="percentage", scale=IndexScale.PERCENTAGE,
        direction=IndexDirection.LOWER_BETTER,
        optimal_range=(0, 25), threshold_warning=40, threshold_critical=60,
        data_sources=["ref_water", "ref_sites"],
        description_fa="نسبت برداشت آب به کل منابع تجدیدپذیر",
        reference="UN SDG 6.4.2"
    ),
    IndexDefinition(
        id="WI003", name_fa="بهره‌وری مصرف آب", name_en="WUE",
        category=ModelCategory.WATER,
        formula="WUE = yield / water_consumed",
        unit="kg/m³", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["ref_economics", "irrigation_records"],
        description_fa="میزان تولید به ازای واحد آب مصرفی",
        reference="FAO AquaCrop framework"
    ),
    IndexDefinition(
        id="WI004", name_fa="نرخ تغذیه آبخوان", name_en="Recharge Rate",
        category=ModelCategory.WATER,
        formula="R = P - ET - Runoff - ΔS",
        unit="mm/year", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["data_weather_daily", "ref_soils", "dem_raster"],
        description_fa="نرخ تغذیه سالانه آبخوان از بارش",
        reference="WetSpass-M / SWAT methodology"
    ),
    IndexDefinition(
        id="WI005", name_fa="شاخص جریان پایه", name_en="BFI",
        category=ModelCategory.WATER,
        formula="BFI = baseflow / total_streamflow",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["streamflow_data"],
        description_fa="نسبت جریان پایه به کل جریان رودخانه (نشانگر تغذیه آبخوان)",
        reference="Nathan & McMahon 1990"
    ),
]


# ============================================================
# بخش ۷: شاخص‌های اقتصادی
# ============================================================

ECONOMIC_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="EI001", name_fa="بازگشت سرمایه", name_en="ROI",
        category=ModelCategory.ECONOMIC,
        formula="ROI = (Net Profit / Investment Cost) × 100",
        unit="percentage", scale=IndexScale.PERCENTAGE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(15, 50),
        data_sources=["ref_economics"],
        description_fa="نسبت سود خالص به سرمایه‌گذاری اولیه",
        reference="Standard financial metric"
    ),
    IndexDefinition(
        id="EI002", name_fa="نسبت سود به هزینه", name_en="BCR",
        category=ModelCategory.ECONOMIC,
        formula="BCR = PV(Benefits) / PV(Costs)",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(1.5, 3.0), threshold_warning=1.0,
        data_sources=["ref_economics"],
        description_fa="نسبت ارزش فعلی منافع به ارزش فعلی هزینه‌ها",
        reference="World Bank Project Appraisal"
    ),
    IndexDefinition(
        id="EI003", name_fa="ارزش خالص فعلی", name_en="NPV",
        category=ModelCategory.ECONOMIC,
        formula="NPV = Σ(CF_t / (1+r)^t) - Initial Investment",
        unit="currency", scale=IndexScale.NEGATIVE_TO_POSITIVE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["ref_economics"],
        description_fa="ارزش خالص فعلی جریان‌های نقدی با نرخ تنزیل",
        reference="Standard DCF methodology"
    ),
    IndexDefinition(
        id="EI004", name_fa="نرخ بازده داخلی", name_en="IRR",
        category=ModelCategory.ECONOMIC,
        formula="IRR: NPV = 0",
        unit="percentage", scale=IndexScale.PERCENTAGE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(12, 30),
        data_sources=["ref_economics"],
        description_fa="نرخ تنزیلی که در آن NPV صفر می‌شود",
        reference="Standard financial metric"
    ),
    IndexDefinition(
        id="EI005", name_fa="دوره بازگشت سرمایه", name_en="Payback Period",
        category=ModelCategory.ECONOMIC,
        formula="PP = Initial Investment / Annual Cash Flow",
        unit="years", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.LOWER_BETTER,
        optimal_range=(2, 5), threshold_warning=7,
        data_sources=["ref_economics"],
        description_fa="مدت زمان لازم برای بازگشت سرمایه اولیه",
        reference="Standard financial metric"
    ),
]


# ============================================================
# بخش ۸: شاخص‌های پایداری
# ============================================================

SUSTAINABILITY_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="SU001", name_fa="ردپای کربن", name_en="Carbon Footprint",
        category=ModelCategory.SUSTAINABILITY,
        formula="CF = Σ(emission_i × GWP_i)",
        unit="kg CO₂e/ha", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.LOWER_BETTER,
        data_sources=["ref_fertilizers", "energy_data", "machinery_data"],
        description_fa="مجموع انتشار گازهای گلخانه‌ای به معادل CO₂",
        reference="IPCC 2019, PAS 2050"
    ),
    IndexDefinition(
        id="SU002", name_fa="ردپای آب", name_en="Water Footprint",
        category=ModelCategory.SUSTAINABILITY,
        formula="WF = WF_green + WF_blue + WF_grey",
        unit="m³/ton", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.LOWER_BETTER,
        data_sources=["data_weather_daily", "irrigation_records"],
        description_fa="مجموع آب سبز، آبی و خاکستری مصرف شده",
        reference="Hoekstra et al. 2011, Water Footprint Network"
    ),
    IndexDefinition(
        id="SU003", name_fa="شاخص تنوع زیستی", name_en="Biodiversity Index",
        category=ModelCategory.SUSTAINABILITY,
        formula="BDI = Shannon_H × Evenness × Richness_factor",
        unit="score", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["field_survey", "landcover_raster"],
        description_fa="شاخص ترکیبی تنوع زیستی بر اساس شاخص شانون",
        reference="Magurran 2004"
    ),
    IndexDefinition(
        id="SU004", name_fa="تراز انرژی", name_en="Energy Balance",
        category=ModelCategory.SUSTAINABILITY,
        formula="EB = Energy_output / Energy_input",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(2.0, 10.0),
        data_sources=["machinery_data", "fertilizer_data"],
        description_fa="نسبت انرژی خروجی (محصول) به انرژی ورودی (نهاده‌ها)",
        reference="Pimentel et al. methodology"
    ),
]


# ============================================================
# بخش ۹: شاخص‌های امنیت غذایی
# ============================================================

FOOD_SECURITY_INDICES: List[IndexDefinition] = [
    IndexDefinition(
        id="FS001", name_fa="شاخص امنیت غذایی", name_en="FSI",
        category=ModelCategory.FOOD_SECURITY,
        formula="FSI = f(availability, access, utilization, stability)",
        unit="score", scale=IndexScale.ZERO_TO_100,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(70, 100), threshold_warning=50, threshold_critical=30,
        data_sources=["ref_economics", "ref_yield_benchmarks"],
        description_fa="شاخص ترکیبی امنیت غذایی (دسترسی، فراوانی، بهره‌برداری، پایداری)",
        reference="FAO Global Food Security Index"
    ),
    IndexDefinition(
        id="FS002", name_fa="شکاف عملکرد", name_en="Yield Gap",
        category=ModelCategory.FOOD_SECURITY,
        formula="YG = (Y_potential - Y_actual) / Y_potential × 100",
        unit="percentage", scale=IndexScale.PERCENTAGE,
        direction=IndexDirection.LOWER_BETTER,
        optimal_range=(0, 20), threshold_warning=40,
        data_sources=["ref_yield_benchmarks", "field_data"],
        description_fa="فاصله بین عملکرد پتانسیل و عملکرد واقعی",
        reference="van Ittersum et al. 2013, Yield Gap Analysis"
    ),
    IndexDefinition(
        id="FS003", name_fa="شاخص تنوع تولید", name_en="Diversity Index",
        category=ModelCategory.FOOD_SECURITY,
        formula="DI = 1 - Σ(p_i²) [Simpson]",
        unit="ratio", scale=IndexScale.ZERO_TO_ONE,
        direction=IndexDirection.HIGHER_BETTER,
        data_sources=["ref_species", "ref_economics"],
        description_fa="شاخص تنوع محصولات در یک منطقه (سیمپسون معکوس)",
        reference="Simpson 1949"
    ),
    IndexDefinition(
        id="FS004", name_fa="کفایت کالری", name_en="Caloric Adequacy",
        category=ModelCategory.FOOD_SECURITY,
        formula="CA = (calories_produced / calories_required) × 100",
        unit="percentage", scale=IndexScale.PERCENTAGE,
        direction=IndexDirection.HIGHER_BETTER,
        optimal_range=(100, 130),
        data_sources=["ref_yield_benchmarks", "population_data"],
        description_fa="نسبت کالری تولید شده به کالری مورد نیاز جمعیت",
        reference="FAO Food Balance Sheets"
    ),
]


# ============================================================
# بخش ۱۰: ادغام و تزریق به دیتابیس
# ============================================================

def inject_to_duckdb():
    """تزریق تمام مدل‌ها و شاخص‌ها به دیتابیس DuckDB"""
    print("🔧 در حال تزریق مدل‌ها و شاخص‌ها به دیتابیس...")
    
    conn = duckdb.connect(str(DB_PATH))
    
    # --- جدول مدل‌ها ---
    conn.execute("""
        CREATE OR REPLACE TABLE ref_models_registry (
            model_id VARCHAR PRIMARY KEY,
            name_fa VARCHAR,
            name_en VARCHAR,
            category VARCHAR,
            output_scale VARCHAR,
            inputs JSON,
            weights JSON,
            logic_note VARCHAR,
            hard_constraints JSON,
            reference VARCHAR
        )
    """)
    
    for m in DECISION_MODELS:
        conn.execute("""
            INSERT OR REPLACE INTO ref_models_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            m.id, m.name_fa, m.name_en, m.category.value, m.output_scale,
            json.dumps(m.inputs), json.dumps(m.weights), m.logic_note,
            json.dumps(m.hard_constraints), m.reference
        ])
    
    # --- جدول شاخص‌ها ---
    conn.execute("""
        CREATE OR REPLACE TABLE ref_indices_registry (
            index_id VARCHAR PRIMARY KEY,
            name_fa VARCHAR,
            name_en VARCHAR,
            category VARCHAR,
            formula VARCHAR,
            unit VARCHAR,
            scale VARCHAR,
            direction VARCHAR,
            optimal_range JSON,
            threshold_warning DOUBLE,
            threshold_critical DOUBLE,
            data_sources JSON,
            description_fa VARCHAR,
            reference VARCHAR
        )
    """)
    
    all_indices = (DROUGHT_INDICES + VEGETATION_INDICES + SOIL_INDICES + 
                   WATER_INDICES + ECONOMIC_INDICES + SUSTAINABILITY_INDICES + 
                   FOOD_SECURITY_INDICES)
    
    for idx in all_indices:
        conn.execute("""
            INSERT OR REPLACE INTO ref_indices_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx.id, idx.name_fa, idx.name_en, idx.category.value,
            idx.formula, idx.unit, idx.scale.value, idx.direction.value,
            json.dumps(idx.optimal_range) if idx.optimal_range else None,
            idx.threshold_warning, idx.threshold_critical,
            json.dumps(idx.data_sources), idx.description_fa, idx.reference
        ])
    
    # --- ایجاد View برای دسترسی سریع ---
    conn.execute("""
        CREATE OR REPLACE VIEW v_all_indices AS
        SELECT * FROM ref_indices_registry ORDER BY category, index_id
    """)
    
    conn.execute("""
        CREATE OR REPLACE VIEW v_decision_models AS
        SELECT * FROM ref_models_registry WHERE category = 'decision_engine' ORDER BY model_id
    """)
    
    conn.execute("""
        CREATE OR REPLACE VIEW v_drought_indices AS
        SELECT * FROM ref_indices_registry WHERE category = 'drought_indices' ORDER BY index_id
    """)
    
    conn.execute("CHECKPOINT;")
    
    # آمار
    models_count = conn.execute("SELECT COUNT(*) FROM ref_models_registry").fetchone()[0]
    indices_count = conn.execute("SELECT COUNT(*) FROM ref_indices_registry").fetchone()[0]
    
    conn.close()
    
    print(f"   ✅ {models_count} مدل تصمیم‌گیری تزریق شد.")
    print(f"   ✅ {indices_count} شاخص علمی تزریق شد.")
    print(f"   ✅ ۳ View تحلیلی ایجاد شد.")


def generate_repository_extension():
    """تولید کد الحاقی به ریپازیتوری"""
    
    extension_code = '''

    # ========================================================================
    # بخش جدید: مدل‌ها و شاخص‌های جامع
    # ========================================================================

    def get_all_models(self) -> pl.DataFrame:
        """دریافت تمام مدل‌های تصمیم‌گیری (M001-M008)"""
        return self._conn.execute("SELECT * FROM ref_models_registry ORDER BY model_id").pl()

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """دریافت یک مدل خاص"""
        df = self._conn.execute(
            "SELECT * FROM ref_models_registry WHERE model_id = ?", [model_id]
        ).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_all_indices(self) -> pl.DataFrame:
        """دریافت تمام شاخص‌های علمی"""
        return self._conn.execute("SELECT * FROM v_all_indices").pl()

    def get_indices_by_category(self, category: str) -> pl.DataFrame:
        """دریافت شاخص‌ها بر اساس دسته"""
        return self._conn.execute(
            "SELECT * FROM ref_indices_registry WHERE category = ? ORDER BY index_id",
            [category]
        ).pl()

    def get_drought_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های خشکسالی"""
        return self._conn.execute("SELECT * FROM v_drought_indices").pl()

    def get_vegetation_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های پوشش گیاهی"""
        return self.get_indices_by_category("vegetation_indices")

    def get_soil_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های خاک"""
        return self.get_indices_by_category("soil_indices")

    def get_water_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های آب"""
        return self.get_indices_by_category("water_indices")

    def get_economic_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های اقتصادی"""
        return self.get_indices_by_category("economic_indices")

    def get_sustainability_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های پایداری"""
        return self.get_indices_by_category("sustainability_indices")

    def get_food_security_indices(self) -> pl.DataFrame:
        """دریافت شاخص‌های امنیت غذایی"""
        return self.get_indices_by_category("food_security_indices")

    def calculate_spi(self, site_id: str, window_months: int = 3) -> pl.DataFrame:
        """محاسبه شاخص خشکسالی SPI"""
        return self.calculate_spi_index(site_id, window_months)

    def calculate_ndvi(self, red_band: float, nir_band: float) -> float:
        """محاسبه شاخص پوشش گیاهی NDVI"""
        if (nir_band + red_band) == 0:
            return 0.0
        return (nir_band - red_band) / (nir_band + red_band)

    def calculate_wue(self, yield_kg: float, water_m3: float) -> float:
        """محاسبه بهره‌وری مصرف آب"""
        if water_m3 == 0:
            return 0.0
        return yield_kg / water_m3

    def calculate_roi(self, net_profit: float, investment: float) -> float:
        """محاسبه بازگشت سرمایه"""
        if investment == 0:
            return 0.0
        return (net_profit / investment) * 100

    def calculate_yield_gap(self, potential: float, actual: float) -> float:
        """محاسبه شکاف عملکرد"""
        if potential == 0:
            return 0.0
        return ((potential - actual) / potential) * 100

    def get_index_definition(self, index_id: str) -> Optional[Dict[str, Any]]:
        """دریافت تعریف کامل یک شاخص"""
        df = self._conn.execute(
            "SELECT * FROM ref_indices_registry WHERE index_id = ?", [index_id]
        ).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_models_and_indices_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه جامع مدل‌ها و شاخص‌ها"""
        models = self._conn.execute("SELECT COUNT(*) FROM ref_models_registry").fetchone()[0]
        indices = self._conn.execute("SELECT COUNT(*) FROM ref_indices_registry").fetchone()[0]
        categories = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM ref_indices_registry GROUP BY category"
        ).pl()
        
        return {
            "total_models": models,
            "total_indices": indices,
            "by_category": {row["category"]: row["cnt"] for row in categories.iter_rows(named=True)}
        }
'''
    
    # الحاق به فایل ریپازیتوری
    content = TARGET_FILE.read_text(encoding="utf-8")
    
    # پیدا کردن آخرین متد کلاس و اضافه کردن بعد از آن
    # ساده‌ترین روش: قبل از آخرین خط کلاس اضافه کن
    if "def get_models_and_indices_summary" not in content:
        # پیدا کردن نقطه درج (قبل از توابع خارج از کلاس)
        insert_marker = "\n\n# ============================================================================\n# توابع سازگار"
        if insert_marker in content:
            content = content.replace(insert_marker, extension_code + insert_marker)
        else:
            # اگر marker نبود، قبل از آخرین `def` خارج از کلاس
            lines = content.split('\n')
            # پیدا کردن آخرین خطی که با `def` شروع می‌شود و در سطح کلاس نیست
            insert_pos = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith('def ') and not lines[i].startswith('    '):
                    insert_pos = i
                    break
            
            extension_lines = extension_code.split('\n')
            lines = lines[:insert_pos] + extension_lines + ['', ''] + lines[insert_pos:]
            content = '\n'.join(lines)
        
        TARGET_FILE.write_text(content, encoding="utf-8")
        print("✅ متدهای جدید به ریپازیتوری اضافه شدند.")
    else:
        print("⚠️ متدها از قبل وجود دارند.")


# ============================================================
# بخش ۱۱: اجرای اصلی
# ============================================================

def main():
    print("🚀 شروع افزودن مدل‌ها و شاخص‌های جامع به پلتفرم eco_nojin")
    print("="*70)
    
    # فاز ۱: تزریق به دیتابیس
    inject_to_duckdb()
    
    # فاز ۲: الحاق به ریپازیتوری
    generate_repository_extension()
    
    # فاز ۳: تست سریع
    print("\n" + "="*70)
    print("🧪 تست سریع...")
    
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        
        modules_to_remove = [k for k in sys.modules if 'data_repository' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
        
        # تست مدل‌ها
        models = repo.get_all_models()
        print(f"   ✅ مدل‌های تصمیم‌گیری: {len(models)} مدل")
        
        # تست شاخص‌ها
        indices = repo.get_all_indices()
        print(f"   ✅ شاخص‌های علمی: {len(indices)} شاخص")
        
        # تست دسته‌بندی
        summary = repo.get_models_and_indices_summary()
        print(f"   ✅ خلاصه: {summary['total_models']} مدل، {summary['total_indices']} شاخص")
        for cat, cnt in summary['by_category'].items():
            print(f"      - {cat}: {cnt}")
        
        # تست محاسبات
        ndvi = repo.calculate_ndvi(0.4, 0.7)
        print(f"   ✅ NDVI نمونه: {ndvi:.3f}")
        
        spi = repo.calculate_spi("SITE076", 3)
        print(f"   ✅ SPI برای SITE076: {len(spi)} ماه")
        
        print("\n🎉 تمام مدل‌ها و شاخص‌ها با موفقیت اضافه شدند!")
        
    except Exception as e:
        print(f"\n❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("📋 خلاصه نهایی:")
    print("   ✅ ۸ مدل تصمیم‌گیری (M001-M008)")
    print("   ✅ ۶ شاخص خشکسالی (SPI, SPEI, PDSI, SSI, SWSI, ETDI)")
    print("   ✅ ۶ شاخص پوشش گیاهی (NDVI, EVI, SAVI, LAI, FPAR, GPP)")
    print("   ✅ ۵ شاخص خاک (SQR, SOC, AWC, Ksat, Erosion)")
    print("   ✅ ۵ شاخص آب (WPI, WSI, WUE, Recharge, BFI)")
    print("   ✅ ۵ شاخص اقتصادی (ROI, BCR, NPV, IRR, Payback)")
    print("   ✅ ۴ شاخص پایداری (Carbon, Water Footprint, Biodiversity, Energy)")
    print("   ✅ ۴ شاخص امنیت غذایی (FSI, Yield Gap, Diversity, Caloric)")
    print("="*70)


if __name__ == "__main__":
    main()