#!/usr/bin/env python3
"""
============================================================================
اسکریپت جامع بازنویسی همزمان:
    ۱. crop_database.py  (820 خط → معماری هیبریدی)
    ۲. aquacrop_real.py  (308 خط → اتصال به زیرساخت داده‌ای)
============================================================================
"""

from __future__ import annotations
import shutil
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.resolve()
MOTORS_DIR = PROJECT_ROOT / "services" / "scientific_motors"
BACKUP_DIR = PROJECT_ROOT / "_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

CROP_DB_FILE = MOTORS_DIR / "crop_database.py"
AQUACROP_FILE = MOTORS_DIR / "aquacrop_real.py"


# ============================================================
# بخش ۱: پشتیبان‌گیری
# ============================================================

def backup_files():
    """پشتیبان‌گیری از فایل‌های فعلی"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    for f in [CROP_DB_FILE, AQUACROP_FILE]:
        if f.exists():
            backup = BACKUP_DIR / f.name
            shutil.copy2(f, backup)
            logger.info(f"📦 پشتیبان: {f.name} → {backup}")
    
    return True


# ============================================================
# بخش ۲: خواندن و استخراج داده‌های موجود
# ============================================================

def extract_crop_database_block() -> str:
    """
    استخراج بلوک CROP_DATABASE از فایل فعلی
    تا ۳۰ گونه کارشناسی‌شده حفظ شوند
    """
    if not CROP_DB_FILE.exists():
        return ""
    
    content = CROP_DB_FILE.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # پیدا کردن شروع و پایان بلوک Enums و DataClasses و CROP_DATABASE
    start_idx = 0
    end_idx = len(lines)
    
    # پیدا کردن شروع (بعد از docstring)
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line and not in_docstring:
            in_docstring = True
        elif '"""' in line and in_docstring:
            start_idx = i + 1
            break
    
    # پیدا کردن پایان بلوک CROP_DATABASE (قبل از توابع کوئری)
    for i in range(start_idx, len(lines)):
        if lines[i].strip().startswith("def get_crop_by_id") or \
           lines[i].strip().startswith("# ============================================================") and \
           "Query Functions" in lines[i]:
            end_idx = i
            break
    
    return '\n'.join(lines[start_idx:end_idx])


def extract_aquacrop_logic() -> str:
    """استخراج منطق محاسباتی AquaCrop از فایل فعلی"""
    if not AQUACROP_FILE.exists():
        return ""
    
    content = AQUACROP_FILE.read_text(encoding="utf-8")
    
    # اگر فایل خیلی بزرگ است، فقط کلاس‌ها و توابع اصلی را حفظ کن
    lines = content.split('\n')
    
    # پیدا کردن کلاس اصلی یا توابع محاسباتی
    logic_lines = []
    in_logic = False
    
    for line in lines:
        if any(keyword in line for keyword in [
            'def calculate_', 'def simulate_', 'def run_',
            'class AquaCrop', 'def _calc_'
        ]):
            in_logic = True
        
        if in_logic:
            logic_lines.append(line)
            if line.strip() == '' and len(logic_lines) > 5:
                # بررسی اینکه آیا تابع بعدی شروع شده
                pass
    
    return '\n'.join(logic_lines) if logic_lines else ""


# ============================================================
# بخش ۳: تولید کد جدید crop_database.py
# ============================================================

def generate_crop_database(existing_block: str) -> str:
    """تولید کد جدید فایل crop_database.py"""
    
    # اگر بلوک موجود خالی است، از نسخه پیش‌فرض استفاده کن
    if not existing_block.strip():
        existing_block = '''
# بلوک داده‌های کارشناسی (۳۰ گونه) در نسخه پشتیبان حفظ شده است
# در صورت نیاز، از فایل پشتیبان بازیابی شود
CROP_DATABASE: dict[str, "CropProfile"] = {}
'''
    
    code = f'''"""
Hydroma Nojin - Global Crop Database (Hybrid Architecture)
===========================================================
لایه ۱: ۳۰ گونه کارشناسی‌شده با جزئیات کامل (CropProfile)
لایه ۲: ۵۰۰۰ گونه مرجع از پایگاه داده مرکزی (DuckDB)

نسخه ۲.۰ - بازنویسی خودکار توسط اسکریپت جامع
سازگاری کامل با نسخه قبلی حفظ شده است.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# ============================================================
# Enums & Data Classes (بدون تغییر - سازگاری کامل)
# ============================================================

class KoppenClimate(Enum):
    Af = "Tropical rainforest"
    Am = "Tropical monsoon"
    Aw = "Tropical savanna"
    BWh = "Hot desert"
    BWk = "Cold desert"
    BSh = "Hot semi-arid (steppe)"
    BSk = "Cold semi-arid (steppe)"
    Csa = "Hot-summer Mediterranean"
    Csb = "Warm-summer Mediterranean"
    Csc = "Cold-summer Mediterranean"
    Cfa = "Humid subtropical"
    Cfb = "Oceanic (temperate)"
    Cfc = "Subpolar oceanic"
    Cwa = "Dry-winter humid subtropical"
    Cwb = "Dry-winter subtropical highland"
    Cwc = "Dry-winter cold subtropical"
    Dsa = "Hot-summer Mediterranean continental"
    Dsb = "Warm-summer Mediterranean continental"
    Dsc = "Dry cold-summer continental"
    Dsd = "Very cold dry-winter continental"
    Dfa = "Hot-summer humid continental"
    Dfb = "Warm-summer humid continental"
    Dfc = "Subarctic"
    Dfd = "Extremely cold subarctic"
    Dwa = "Dry-winter hot continental"
    Dwb = "Dry-winter warm continental"
    Dwc = "Dry-winter subarctic"
    Dwd = "Dry-winter extremely cold"
    ET = "Tundra"
    EF = "Ice cap"


class CropFamily(Enum):
    CEREAL = "Cereals / غلات"
    LEGUME = "Legumes / حبوبات"
    VEGETABLE = "Vegetables / سبزیجات"
    FRUIT = "Fruits / میوه‌ها"
    INDUSTRIAL = "Industrial / صنعتی"
    OILSEED = "Oilseeds / دانه‌های روغنی"
    MEDICINAL = "Medicinal & Aromatic / دارویی"
    FORAGE = "Forage / علوفه"
    NUT = "Tree nuts / آجیل"
    TUBER = "Tubers / غده‌ای"
    FLOWER = "Ornamental / زینتی"
    BEVERAGE = "Beverage / نوشیدنی"


class WaterTolerance(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SalinityTolerance(Enum):
    SENSITIVE = "sensitive"
    MODERATE = "moderate"
    TOLERANT = "tolerant"
    HIGHLY_TOLERANT = "highly_tolerant"


@dataclass
class WaterRequirement:
    min_mm: float
    opt_mm: float
    max_mm: float
    drought_tolerance: WaterTolerance


@dataclass
class SoilRequirement:
    ph_min: float
    ph_opt_min: float
    ph_opt_max: float
    ph_max: float
    preferred_texture: list[int]
    salinity_tolerance: SalinityTolerance
    min_depth_cm: float


@dataclass
class TemperatureRequirement:
    min_c: float
    opt_min_c: float
    opt_max_c: float
    max_c: float
    chilling_hours: int
    frost_tolerance: bool


@dataclass
class EconomicData:
    yield_ton_ha: float
    market_price_per_kg_usd: float
    production_cost_per_ha_usd: float
    labor_days_per_ha: float


@dataclass
class CropProfile:
    id: str
    name_fa: str
    name_en: str
    scientific_name: str
    family: CropFamily
    growing_days: int
    planting_months: list[int]
    water: WaterRequirement
    soil: SoilRequirement
    temperature: TemperatureRequirement
    suitable_climates: list[KoppenClimate]
    max_slope_percent: float
    suitable_lcc_classes: list[int]
    altitude_range_m: tuple
    economics: EconomicData
    rotation_compatible: list[str]
    major_producers: list[str]
    uses: list[str]
    shelf_life_days: int
    notes: str = ""


# ============================================================
# لایه ۱: پایگاه داده ۳۰ گونه کارشناسی‌شده
# ============================================================

{existing_block}


# ============================================================
# لایه ۲: سرویس یکپارچه (DuckDB + Curated)
# ============================================================

class CropDatabaseService:
    """
    سرویس یکپارچه دسترسی به داده‌های زراعی
    
    اولویت جستجو:
        1. پایگاه داده کارشناسی (۳۰ گونه با جزئیات کامل)
        2. پایگاه داده مرکزی DuckDB (۵۰۰۰ گونه)
    
    مثال استفاده:
        >>> svc = CropDatabaseService()
        >>> wheat = svc.get_crop("wheat")        # لایه کارشناسی
        >>> durum = svc.get_species_data("W001") # لایه دیتابیس
        >>> results = svc.search_species("گندم") # جستجوی هر دو
    """
    
    _instance: Optional[CropDatabaseService] = None
    _repo = None
    
    def __new__(cls) -> CropDatabaseService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                from services.scientific_motors.data_repository import ScientificDataRepository
                cls._instance._repo = ScientificDataRepository()
                logger.info("✅ CropDatabaseService: DuckDB connected.")
            except Exception as e:
                logger.warning(f"⚠️ DuckDB unavailable, curated-only mode: {{e}}")
        return cls._instance
    
    # ----------------------------------------------------------
    # API اصلی: دسترسی به داده‌های گونه
    # ----------------------------------------------------------
    
    def get_crop(self, crop_id: str) -> Optional[CropProfile]:
        """دریافت پروفایل کامل از لایه کارشناسی"""
        return CROP_DATABASE.get(crop_id)
    
    def get_species_data(self, species_id: str) -> Optional[Dict[str, Any]]:
        """دریافت داده‌های هر گونه از هر دو لایه"""
        # اولویت ۱: لایه کارشناسی
        if species_id in CROP_DATABASE:
            return self._profile_to_dict(CROP_DATABASE[species_id])
        
        # اولویت ۲: لایه DuckDB
        if self._repo:
            data = self._repo.get_crop_parameters(species_id)
            if data:
                return data
        
        return None
    
    def get_climate_requirements(self, species_id: str) -> Optional[Dict[str, Any]]:
        """دریافت نیازمندی‌های اقلیمی"""
        if self._repo:
            df = self._repo.get_crop_climate_matrix(species_id)
            if not df.is_empty():
                return df.row(0, named=True)
        return None
    
    def get_growth_stages(self, species_id: str):
        """دریافت مراحل رشد بر اساس درجه-روز"""
        if self._repo:
            return self._repo.get_growth_stages(species_id)
        return None
    
    def get_yield_benchmark(self, species_id: str):
        """دریافت بنچمارک عملکرد"""
        if self._repo:
            return self._repo.get_yield_benchmarks(species_id)
        return None
    
    def get_crop_calendar(self, species_id: str, site_id: str):
        """دریافت تقویم زراعی"""
        if self._repo:
            return self._repo.get_crop_calendar(species_id, site_id)
        return None
    
    def get_economic_data(self, species_id: str) -> Optional[Dict[str, Any]]:
        """دریافت داده‌های اقتصادی"""
        if self._repo:
            return self._repo.get_economic_parameters(species_id)
        return None
    
    # ----------------------------------------------------------
    # جستجو و فیلتر
    # ----------------------------------------------------------
    
    def search_species(self, query: str) -> List[Dict[str, Any]]:
        """جستجوی گونه در هر دو لایه"""
        results = []
        q = query.lower()
        
        # جستجو در لایه کارشناسی
        for cid, profile in CROP_DATABASE.items():
            if (q in profile.name_fa.lower() or 
                q in profile.name_en.lower() or 
                q in profile.scientific_name.lower()):
                results.append({{
                    "source": "curated", "id": cid,
                    "name_fa": profile.name_fa,
                    "scientific_name": profile.scientific_name,
                    "data": profile
                }})
        
        # جستجو در لایه دیتابیس
        if self._repo:
            try:
                df = self._repo._conn.execute("""
                    SELECT id, name_fa, scientific_name, category 
                    FROM ref_species 
                    WHERE name_fa ILIKE ? OR scientific_name ILIKE ? OR id = ?
                    LIMIT 50
                """, [f"%{{query}}%", f"%{{query}}%", query.upper()]).pl()
                
                for row in df.iter_rows(named=True):
                    results.append({{
                        "source": "database",
                        "id": row["id"],
                        "name_fa": row.get("name_fa", ""),
                        "scientific_name": row.get("scientific_name", ""),
                        "data": row
                    }})
            except Exception as e:
                logger.warning(f"Search failed: {{e}}")
        
        return results
    
    def get_all_species_ids(self) -> List[str]:
        """دریافت لیست تمام شناسه‌های گونه"""
        ids = set(CROP_DATABASE.keys())
        if self._repo:
            try:
                df = self._repo._conn.execute("SELECT id FROM ref_species").pl()
                ids.update(df["id"].to_list())
            except Exception:
                pass
        return sorted(ids)
    
    def get_statistics(self) -> Dict[str, Any]:
        """آمار جامع پایگاه داده"""
        stats = get_crop_statistics()
        if self._repo:
            try:
                total = self._repo._conn.execute(
                    "SELECT COUNT(*) FROM ref_species"
                ).fetchone()[0]
                stats["database_total"] = total
                stats["curated_total"] = len(CROP_DATABASE)
            except Exception:
                pass
        return stats
    
    # ----------------------------------------------------------
    # تبدیل و سازگاری
    # ----------------------------------------------------------
    
    def _profile_to_dict(self, p: CropProfile) -> Dict[str, Any]:
        """تبدیل CropProfile به دیکشنری سازگار با خروجی دیتابیس"""
        return {{
            "species_id": p.id,
            "name_fa": p.name_fa,
            "scientific_name": p.scientific_name,
            "category": p.family.value,
            "min_temp_c": p.temperature.min_c,
            "opt_temp_min_c": p.temperature.opt_min_c,
            "opt_temp_max_c": p.temperature.opt_max_c,
            "max_temp_c": p.temperature.max_c,
            "rain_min_mm_y": p.water.min_mm,
            "rain_opt_min_mm_y": p.water.opt_mm,
            "rain_max_mm_y": p.water.max_mm,
            "soil_depth_cm": p.soil.min_depth_cm,
            "ph_min": p.soil.ph_min,
            "ph_max": p.soil.ph_max,
            "drought_tolerance_1_5": self._tolerance_scale(p.water.drought_tolerance),
            "water_need_1_5": self._water_scale(p.water),
            "growing_days": p.growing_days,
            "planting_months": p.planting_months,
            "source": "curated",
        }}
    
    @staticmethod
    def _tolerance_scale(t: WaterTolerance) -> int:
        return {{WaterTolerance.LOW: 1, WaterTolerance.MEDIUM: 3,
                WaterTolerance.HIGH: 4, WaterTolerance.VERY_HIGH: 5}}[t]
    
    @staticmethod
    def _water_scale(w: WaterRequirement) -> int:
        if w.opt_mm < 350: return 2
        if w.opt_mm < 600: return 3
        if w.opt_mm < 900: return 4
        return 5


# ============================================================
# توابع سازگار با نسخه قبلی (Backward Compatibility)
# ============================================================

_service: Optional[CropDatabaseService] = None

def get_service() -> CropDatabaseService:
    """دریافت نمونه سرویس یکپارچه"""
    global _service
    if _service is None:
        _service = CropDatabaseService()
    return _service

def get_crop_by_id(crop_id: str) -> CropProfile | None:
    return CROP_DATABASE.get(crop_id)

def get_all_crops() -> list[CropProfile]:
    return list(CROP_DATABASE.values())

def filter_by_climate(climate: KoppenClimate) -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values() if climate in c.suitable_climates]

def filter_by_family(family: CropFamily) -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values() if c.family == family]

def filter_drought_tolerant() -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values()
            if c.water.drought_tolerance in (WaterTolerance.HIGH, WaterTolerance.VERY_HIGH)]

def filter_salinity_tolerant() -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values()
            if c.soil.salinity_tolerance in (SalinityTolerance.TOLERANT, SalinityTolerance.HIGHLY_TOLERANT)]

def get_crop_statistics() -> dict:
    crops = list(CROP_DATABASE.values())
    return {{
        "total_crops": len(crops),
        "by_family": {{f.value: len([c for c in crops if c.family == f]) for f in CropFamily}},
        "drought_tolerant": len(filter_drought_tolerant()),
        "salinity_tolerant": len(filter_salinity_tolerant()),
        "annual_crops": len([c for c in crops if c.growing_days < 365]),
        "perennial_crops": len([c for c in crops if c.growing_days >= 365]),
    }}

def climate_description(code: KoppenClimate) -> str:
    descriptions = {{
        KoppenClimate.Af: "Hot, humid year-round. No dry season. Rainforest.",
        KoppenClimate.Am: "Tropical with short dry season. Monsoon-driven.",
        KoppenClimate.Aw: "Distinct wet/dry seasons. Tropical savanna.",
        KoppenClimate.BWh: "Hot desert. <250mm rain. Extreme heat.",
        KoppenClimate.BWk: "Cold desert. <250mm rain. Cold winters.",
        KoppenClimate.BSh: "Hot semi-arid. 250-500mm. Steppe grasslands.",
        KoppenClimate.BSk: "Cold semi-arid. 250-500mm. Cold winters.",
        KoppenClimate.Csa: "Mediterranean. Hot dry summer, mild wet winter.",
        KoppenClimate.Csb: "Cool Mediterranean. Cooler summers.",
        KoppenClimate.Cfa: "Humid subtropical. Hot summer, year-round rain.",
        KoppenClimate.Cfb: "Oceanic. Mild year-round, even rain.",
        KoppenClimate.Cwa: "Subtropical with dry winter. Monsoon-influenced.",
        KoppenClimate.Cwb: "Subtropical highland. Dry winter, mild.",
        KoppenClimate.Dfa: "Humid continental. Hot summer. Great Plains USA.",
        KoppenClimate.Dfb: "Humid continental. Warm summer. N Europe.",
        KoppenClimate.Dfc: "Subarctic. Short cool summer. Boreal forest.",
        KoppenClimate.ET: "Tundra. No month >10°C. Permafrost.",
        KoppenClimate.EF: "Ice cap. All months <0°C. Antarctica.",
    }}
    return descriptions.get(code, "Unknown")
'''
    return code


# ============================================================
# بخش ۴: تولید کد جدید aquacrop_real.py
# ============================================================

def generate_aquacrop_real() -> str:
    """تولید کد جدید فایل aquacrop_real.py"""
    
    return '''"""
Hydroma Nojin - AquaCrop Real Simulation Engine
=================================================
مدل شبیه‌سازی رشد محصول بر اساس چارچوب AquaCrop فائو

نسخه ۲.۰ - اتصال کامل به زیرساخت داده‌ای:
    - CropDatabaseService: پارامترهای گیاه
    - ScientificDataRepository: داده‌های اقلیمی، خاک، تقویم زراعی
    - DroughtIndexEngine: پایش خشکسالی در طول شبیه‌سازی

مراجع:
    - FAO AquaCrop Version 7.0
    - Steduto et al. (2012), FAO Irrigation and Drainage Paper 66
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

import polars as pl

logger = logging.getLogger(__name__)


# ============================================================
# ساختارهای داده
# ============================================================

@dataclass
class AquaCropConfig:
    """پیکربندی شبیه‌سازی AquaCrop"""
    species_id: str
    site_id: str
    planting_date: Optional[str] = None  # ISO format
    simulation_days: int = 365
    irrigation_mode: str = "rainfed"  # rainfed, full, deficit, supplementary
    co2_ppm: float = 420.0  # غلظت CO2 اتمسفر
    
    # پارامترهای گیاهی (از دیتابیس خوانده می‌شوند)
    kc_max: float = 1.10
    kc_seedling: float = 0.30
    root_depth_max_cm: float = 100.0
    growing_days: int = 150
    harvest_index: float = 0.45
    stress_sensitivity: Dict[str, float] = field(default_factory=lambda: {
        "water": 0.7, "temperature": 0.5, "salinity": 0.3
    })
    
    # پارامترهای خاک (از دیتابیس خوانده می‌شوند)
    soil_awc_mm_m: float = 150.0  # آب قابل دسترس
    soil_depth_cm: float = 100.0
    soil_k_sat_mm_h: float = 20.0  # هدایت هیدرولیکی اشباع
    
    # پارامترهای اقلیمی (از دیتابیس خوانده می‌شوند)
    et0_daily: Optional[List[float]] = None  # تبخیر و تعرق مرجع روزانه
    rainfall_daily: Optional[List[float]] = None  # بارش روزانه
    tmin_daily: Optional[List[float]] = None
    tmax_daily: Optional[List[float]] = None


@dataclass
class AquaCropResult:
    """نتایج شبیه‌سازی"""
    species_id: str
    site_id: str
    
    # خروجی‌های اصلی
    yield_t_ha: float = 0.0
    biomass_t_ha: float = 0.0
    harvest_index: float = 0.0
    
    # مصرف آب
    total_et_mm: float = 0.0
    total_rain_mm: float = 0.0
    irrigation_mm: float = 0.0
    water_productivity_kg_m3: float = 0.0
    
    # تنش‌ها
    water_stress_days: int = 0
    max_stress_index: float = 0.0
    mean_stress_index: float = 0.0
    
    # تقویم
    emergence_day: int = 0
    harvest_day: int = 0
    growing_days_actual: int = 0
    
    # متادیتا
    confidence: str = "D"
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "species_id": self.species_id,
            "site_id": self.site_id,
            "yield_t_ha": round(self.yield_t_ha, 2),
            "biomass_t_ha": round(self.biomass_t_ha, 2),
            "harvest_index": round(self.harvest_index, 3),
            "total_et_mm": round(self.total_et_mm, 1),
            "total_rain_mm": round(self.total_rain_mm, 1),
            "irrigation_mm": round(self.irrigation_mm, 1),
            "water_productivity_kg_m3": round(self.water_productivity_kg_m3, 3),
            "water_stress_days": self.water_stress_days,
            "growing_days_actual": self.growing_days_actual,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


# ============================================================
# موتور شبیه‌سازی اصلی
# ============================================================

class AquaCropSimulator:
    """
    موتور شبیه‌سازی رشد محصول بر اساس AquaCrop
    
    فرآیند:
        1. بارگذاری پارامترها از دیتابیس
        2. شبیه‌سازی روزانه رشد
        3. محاسبه تنش آبی و عملکرد
        4. تولید گزارش خروجی
    """
    
    def __init__(self):
        from services.scientific_motors.data_repository import ScientificDataRepository
        from services.scientific_motors.crop_database import CropDatabaseService
        
        self.repo = ScientificDataRepository()
        self.crop_db = CropDatabaseService()
    
    # ----------------------------------------------------------
    # مرحله ۱: بارگذاری پارامترها
    # ----------------------------------------------------------
    
    def load_config(self, species_id: str, site_id: str,
                    irrigation_mode: str = "rainfed") -> Optional[AquaCropConfig]:
        """
        بارگذاری خودکار پیکربندی از دیتابیس
        
        این متد تمام پارامترهای مورد نیاز را از زیرساخت داده‌ای می‌خواند:
            - پارامترهای گیاه از CropDatabaseService
            - داده‌های اقلیمی از ScientificDataRepository
            - پارامترهای خاک از ref_soils
        """
        config = AquaCropConfig(
            species_id=species_id,
            site_id=site_id,
            irrigation_mode=irrigation_mode
        )
        
        # ۱. پارامترهای گیاه
        crop_data = self.crop_db.get_species_data(species_id)
        if crop_data:
            config.growing_days = int(crop_data.get("growing_days", 150))
            config.kc_max = self._estimate_kc_max(crop_data)
            config.root_depth_max_cm = float(crop_data.get("soil_depth_cm", 100))
            
            # تخمین شاخص برداشت بر اساس دسته محصول
            category = str(crop_data.get("category", ""))
            config.harvest_index = self._estimate_harvest_index(category)
        
        # ۲. نیازمندی‌های اقلیمی
        climate = self.crop_db.get_climate_requirements(species_id)
        if climate:
            # پارامترهای تنش
            drought_tol = float(climate.get("drought_tolerance_1_5", 3))
            config.stress_sensitivity["water"] = max(0.1, 1.0 - drought_tol / 6.0)
        
        # ۳. داده‌های خاک
        site = self.repo.get_site_profile(site_id)
        if site:
            soil_id = site.get("soil_id", "")
            if soil_id:
                soil = self.repo._conn.execute(
                    "SELECT * FROM ref_soils WHERE soil_id = ?", [soil_id]
                ).pl()
                if not soil.is_empty():
                    soil_row = soil.row(0, named=True)
                    config.soil_awc_mm_m = float(soil_row.get("AWC_mm_m", 150) or 150)
                    config.soil_depth_cm = 100.0  # پیش‌فرض
        
        # ۴. داده‌های اقلیمی روزانه
        weather = self.repo.get_weather_daily(site_id)
        if not weather.is_empty():
            config.simulation_days = min(len(weather), 365)
            
            # استخراج بارش و دما
            if "precip_mm" in weather.columns:
                config.rainfall_daily = weather["precip_mm"].to_list()[:config.simulation_days]
            if "tmin_c" in weather.columns:
                config.tmin_daily = weather["tmin_c"].to_list()[:config.simulation_days]
            if "tmax_c" in weather.columns:
                config.tmax_daily = weather["tmax_c"].to_list()[:config.simulation_days]
            
            # محاسبه ET0 با فرمول ساده هارگریو
            config.et0_daily = self._calculate_et0(
                config.tmin_daily, config.tmax_daily,
                site.get("lat", 30.0) if site else 30.0
            )
        
        logger.info(f"✅ Config loaded: {species_id} @ {site_id} ({irrigation_mode})")
        return config
    
    # ----------------------------------------------------------
    # مرحله ۲: شبیه‌سازی روزانه
    # ----------------------------------------------------------
    
    def simulate(self, config: AquaCropConfig) -> AquaCropResult:
        """اجرای شبیه‌سازی روزانه"""
        result = AquaCropResult(
            species_id=config.species_id,
            site_id=config.site_id
        )
        
        # بررسی داده‌های ورودی
        if not config.rainfall_daily:
            result.warnings.append("داده بارش موجود نیست؛ از مقدار پیش‌فرض استفاده می‌شود")
            config.rainfall_daily = [3.0] * config.simulation_days
        
        if not config.et0_daily:
            result.warnings.append("ET0 محاسبه نشد؛ از مقدار پیش‌فرض ۵ میلی‌متر استفاده می‌شود")
            config.et0_daily = [5.0] * config.simulation_days
        
        # متغیرهای حالت
        soil_water = config.soil_awc_mm_m * (config.soil_depth_cm / 100.0) * 0.5  # ۵۰٪ ظرفیت
        canopy_cover = 0.0
        biomass_cum = 0.0
        stress_days = 0
        stress_values = []
        
        growing_days = config.growing_days
        if growing_days > config.simulation_days:
            growing_days = config.simulation_days
            result.warnings.append(f"دوره رشد به {config.simulation_days} روز محدود شد")
        
        # شبیه‌سازی روزانه
        for day in range(growing_days):
            # پارامترهای روز
            rain = config.rainfall_daily[day] if day < len(config.rainfall_daily) else 0
            et0 = config.et0_daily[day] if day < len(config.et0_daily) else 5.0
            
            # رشد پوشش گیاهی (منحنی لجستیک)
            growth_fraction = day / max(growing_days, 1)
            if growth_fraction < 0.15:
                canopy_cover = config.kc_seedling / config.kc_max * growth_fraction / 0.15
            elif growth_fraction < 0.7:
                progress = (growth_fraction - 0.15) / 0.55
                canopy_cover = min(1.0, config.kc_seedling / config.kc_max + 
                                   (1.0 - config.kc_seedling / config.kc_max) * progress)
            else:
                # فاز پیری
                decline = (growth_fraction - 0.7) / 0.3
                canopy_cover = max(0.3, 1.0 - decline * 0.5)
            
            # نیاز آبی گیاه
            kc = config.kc_seedling + (config.kc_max - config.kc_seedling) * min(canopy_cover, 1.0)
            crop_et = et0 * kc
            
            # بارندگی مؤثر (۸۰٪ بارش)
            effective_rain = rain * 0.8
            
            # تراز آب خاک
            soil_water += effective_rain - crop_et
            
            # آبیاری (در صورت نیاز)
            irrigation = 0.0
            if config.irrigation_mode in ("full", "supplementary"):
                depletion_threshold = config.soil_awc_mm_m * (config.soil_depth_cm / 100.0) * 0.5
                if soil_water < depletion_threshold:
                    irrigation = depletion_threshold - soil_water
                    soil_water += irrigation
            
            # محدود کردن آب خاک
            max_water = config.soil_awc_mm_m * (config.soil_depth_cm / 100.0)
            soil_water = max(0, min(soil_water, max_water))
            
            # محاسبه تنش آبی
            if soil_water < config.soil_awc_mm_m * (config.soil_depth_cm / 100.0) * 0.3:
                stress = 1.0 - (soil_water / (config.soil_awc_mm_m * (config.soil_depth_cm / 100.0) * 0.3))
                stress = min(1.0, stress * config.stress_sensitivity.get("water", 0.7))
                stress_days += 1
                stress_values.append(stress)
            else:
                stress = 0.0
                stress_values.append(0.0)
            
            # رشد بیوماس
            wp = 15.0  # بهره‌وری آب (g/m²/mm)
            biomass_increment = crop_et * wp * (1 - stress) * canopy_cover / 1000.0  # kg/ha
            biomass_cum += biomass_increment
        
        # محاسبه نتایج نهایی
        result.biomass_t_ha = biomass_cum / 1000.0
        result.harvest_index = config.harvest_index
        result.yield_t_ha = result.biomass_t_ha * config.harvest_index
        result.total_et_mm = sum(config.et0_daily[:growing_days]) if config.et0_daily else 0
        result.total_rain_mm = sum(config.rainfall_daily[:growing_days]) if config.rainfall_daily else 0
        result.irrigation_mm = irrigation
        result.water_stress_days = stress_days
        result.max_stress_index = max(stress_values) if stress_values else 0
        result.mean_stress_index = sum(stress_values) / len(stress_values) if stress_values else 0
        result.growing_days_actual = growing_days
        
        # بهره‌وری آب
        total_water = result.total_et_mm + result.irrigation_mm
        if total_water > 0:
            result.water_productivity_kg_m3 = (result.yield_t_ha * 1000) / total_water
        
        # تعیین سطح اطمینان
        if result.water_stress_days > growing_days * 0.5:
            result.confidence = "C"
            result.warnings.append("تنش آبی شدید؛ نتیجه با عدم قطعیت بالا")
        else:
            result.confidence = "B"
        
        return result
    
    # ----------------------------------------------------------
    # مرحله ۳: اجرای کامل با بارگذاری خودکار
    # ----------------------------------------------------------
    
    def run(self, species_id: str, site_id: str,
            irrigation_mode: str = "rainfed") -> AquaCropResult:
        """اجرای کامل شبیه‌سازی (بارگذاری + شبیه‌سازی)"""
        config = self.load_config(species_id, site_id, irrigation_mode)
        if not config:
            result = AquaCropResult(species_id=species_id, site_id=site_id)
            result.warnings.append("امکان بارگذاری پیکربندی وجود نداشت")
            return result
        
        return self.simulate(config)
    
    # ----------------------------------------------------------
    # توابع کمکی
    # ----------------------------------------------------------
    
    def _calculate_et0(self, tmin: Optional[List[float]], 
                       tmax: Optional[List[float]],
                       lat: float) -> Optional[List[float]]:
        """محاسبه تبخیر و تعرق مرجع با فرمول هارگریو"""
        if not tmin or not tmax:
            return None
        
        et0_list = []
        for i in range(len(tmin)):
            t_mean = (tmin[i] + tmax[i]) / 2
            t_range = max(0.1, tmax[i] - tmin[i])
            
            # فرمول هارگریو: ET0 = 0.0023 × Ra × (T+17.8) × √TR
            ra = 15.0 + lat * 0.1  # تخمین ساده تابش
            et0 = 0.0023 * ra * (t_mean + 17.8) * math.sqrt(t_range)
            et0_list.append(max(0.5, min(12.0, et0)))
        
        return et0_list
    
    def _estimate_kc_max(self, crop_data: Dict) -> float:
        """تخمین ضریب گیاهی حداکثر بر اساس دسته محصول"""
        category = str(crop_data.get("category", "")).lower()
        
        kc_map = {
            "دانه‌ای": 1.15,
            "حبوبات": 1.10,
            "صیفی": 1.20,
            "درختی": 0.95,
            "علوفه‌ای": 1.05,
            "غده‌ای": 1.10,
            "دارویی": 0.90,
        }
        
        for key, value in kc_map.items():
            if key in category:
                return value
        return 1.10
    
    def _estimate_harvest_index(self, category: str) -> float:
        """تخمین شاخص برداشت بر اساس دسته محصول"""
        category = category.lower()
        
        if "دانه" in category or "غلات" in category:
            return 0.45
        elif "حبوب" in category or "legume" in category:
            return 0.40
        elif "صیفی" in category or "سبزی" in category:
            return 0.60
        elif "غده" in category or "ریشه" in category:
            return 0.75
        elif "علوفه" in category:
            return 0.85
        elif "درختی" in category or "میوه" in category:
            return 0.30
        elif "دارویی" in category:
            return 0.35
        else:
            return 0.45
    
    # ----------------------------------------------------------
    # تحلیل سناریو
    # ----------------------------------------------------------
    
    def compare_irrigation_scenarios(self, species_id: str, site_id: str) -> Dict[str, Any]:
        """مقایسه سناریوهای مختلف آبیاری"""
        scenarios = {}
        
        for mode in ["rainfed", "supplementary", "full"]:
            result = self.run(species_id, site_id, mode)
            scenarios[mode] = result.to_dict()
        
        # محاسبه ارزش افزوده آبیاری
        if scenarios.get("rainfed") and scenarios.get("full"):
            rainfed_yield = scenarios["rainfed"]["yield_t_ha"]
            full_yield = scenarios["full"]["yield_t_ha"]
            irrigation_mm = scenarios["full"]["irrigation_mm"]
            
            if irrigation_mm > 0:
                marginal_wp = ((full_yield - rainfed_yield) * 1000) / irrigation_mm
                scenarios["analysis"] = {
                    "yield_increase_percent": round((full_yield / max(rainfed_yield, 0.01) - 1) * 100, 1),
                    "marginal_water_productivity_kg_m3": round(marginal_wp, 3),
                    "irrigation_justified": marginal_wp > 0.5,
                }
        
        return scenarios


# ============================================================
# توابع سازگار با نسخه قبلی
# ============================================================

_simulator: Optional[AquaCropSimulator] = None

def get_simulator() -> AquaCropSimulator:
    global _simulator
    if _simulator is None:
        _simulator = AquaCropSimulator()
    return _simulator

def run_aquacrop(species_id: str, site_id: str, 
                 irrigation_mode: str = "rainfed") -> Dict[str, Any]:
    """تابع اصلی برای اجرای شبیه‌سازی"""
    sim = get_simulator()
    result = sim.run(species_id, site_id, irrigation_mode)
    return result.to_dict()

def compare_irrigation(species_id: str, site_id: str) -> Dict[str, Any]:
    """مقایسه سناریوهای آبیاری"""
    sim = get_simulator()
    return sim.compare_irrigation_scenarios(species_id, site_id)
'''


# ============================================================
# بخش ۵: نوشتن فایل‌ها
# ============================================================

def write_files():
    """نوشتن فایل‌های جدید"""
    
    # خواندن بلوک داده‌های موجود
    logger.info("📖 در حال خواندن داده‌های موجود...")
    existing_block = extract_crop_database_block()
    
    if existing_block:
        logger.info(f"   ✅ بلوک CROP_DATABASE استخراج شد ({len(existing_block.split(chr(10)))} خط)")
    else:
        logger.warning("   ⚠️ بلوک CROP_DATABASE یافت نشد؛ از نسخه خالی استفاده می‌شود")
    
    # نوشتن فایل‌ها
    logger.info("📝 در حال نوشتن فایل‌های جدید...")
    
    crop_db_code = generate_crop_database(existing_block)
    CROP_DB_FILE.write_text(crop_db_code, encoding="utf-8")
    logger.info(f"   ✅ crop_database.py: {len(crop_db_code.split(chr(10)))} خط")
    
    aquacrop_code = generate_aquacrop_real()
    AQUACROP_FILE.write_text(aquacrop_code, encoding="utf-8")
    logger.info(f"   ✅ aquacrop_real.py: {len(aquacrop_code.split(chr(10)))} خط")


# ============================================================
# بخش ۶: تست یکپارچگی
# ============================================================

def run_integration_tests():
    """اجرای تست‌های یکپارچگی"""
    logger.info("🧪 در حال اجرای تست‌های یکپارچگی...")
    
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # حذف ماژول‌های کش‌شده
        modules_to_remove = [k for k in list(sys.modules.keys()) 
                           if 'crop_database' in k or 'aquacrop' in k or 'data_repository' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        # تست ۱: وارد کردن ماژول‌ها
        from services.scientific_motors.crop_database import CropDatabaseService, get_service
        from services.scientific_motors.aquacrop_real import AquaCropSimulator, run_aquacrop
        logger.info("   ✅ ماژول‌ها با موفقیت وارد شدند")
        
        # تست ۲: سرویس پایگاه داده
        svc = get_service()
        stats = svc.get_statistics()
        logger.info(f"   ✅ آمار پایگاه داده: {stats.get('total_crops', 0)} گونه کارشناسی")
        
        # تست ۳: جستجو
        results = svc.search_species("گندم")
        logger.info(f"   ✅ جستجوی 'گندم': {len(results)} نتیجه")
        
        # تست ۴: شبیه‌سازی AquaCrop
        sim = AquaCropSimulator()
        result = sim.run("W001", "SITE037", "rainfed")
        logger.info(f"   ✅ شبیه‌سازی گندم دوروم @ SITE037:")
        logger.info(f"      عملکرد: {result.yield_t_ha:.2f} تن/هکتار")
        logger.info(f"      بیوماس: {result.biomass_t_ha:.2f} تن/هکتار")
        logger.info(f"      روزهای تنش: {result.water_stress_days}")
        logger.info(f"      اطمینان: {result.confidence}")
        
        # تست ۵: مقایسه سناریوهای آبیاری
        scenarios = sim.compare_irrigation_scenarios("W001", "SITE037")
        logger.info(f"   ✅ مقایسه سناریوهای آبیاری:")
        for mode, data in scenarios.items():
            if isinstance(data, dict) and "yield_t_ha" in data:
                logger.info(f"      {mode}: {data['yield_t_ha']} تن/هکتار")
        
        logger.info("\n🎉 تمام تست‌ها با موفقیت پاس شدند!")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# بخش ۷: اجرای اصلی
# ============================================================

def main():
    print("="*70)
    print("🚀 اسکریپت جامع بازنویسی: crop_database.py + aquacrop_real.py")
    print("="*70)
    
    # مرحله ۱: پشتیبان‌گیری
    backup_files()
    
    # مرحله ۲: نوشتن فایل‌های جدید
    write_files()
    
    # مرحله ۳: تست یکپارچگی
    success = run_integration_tests()
    
    # خلاصه نهایی
    print("\n" + "="*70)
    print("📋 خلاصه بازنویسی:")
    print("   ✅ crop_database.py: معماری هیبریدی (کارشناسی + دیتابیس)")
    print("   ✅ aquacrop_real.py: اتصال کامل به زیرساخت داده‌ای")
    print("   ✅ پشتیبان در: " + str(BACKUP_DIR))
    print("="*70)
    
    if success:
        print("\n🎯 گام بعدی پیشنهادی:")
        print("   ۱. اتصال irrigation_scheduler.py به CropDatabaseService")
        print("   ۲. اتصال planting_calendar.py به تقویم زراعی دیتابیس")
        print("   ۳. اتصال economy_motor.py به EconomicIndexEngine")
    else:
        print("\n⚠️ برخی تست‌ها ناموفق بودند. لطفاً لاگ‌ها را بررسی کنید.")


if __name__ == "__main__":
    main()