"""
Phase 1: Scientific Core Activation
هدف: ایجاد دامنه‌های گمشده و پیاده‌سازی واقعی موتورهای علمی
پروتکل ایمنی: AST-based validation + Dry-run mode
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
HYDROMA_ROOT = PROJECT_ROOT / "engine" / "hydroma"

class SafeFileWriter:
    """کلاس امن برای نوشتن فایل با اعتبارسنجی AST"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes: List[Dict[str, Any]] = []
    
    def write(self, file_path: Path, content: str, description: str) -> bool:
        """
        نوشتن فایل با اعتبارسنجی AST.
        اگر dry_run=True، فقط گزارش می‌دهد.
        """
        try:
            # اعتبارسنجی AST قبل از نوشتن
            ast.parse(content)
        except SyntaxError as e:
            print(f"❌ خطای نحوی در محتوای تولیدشده: {e}")
            return False
        
        change = {
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "description": description,
            "lines": len(content.split('\n')),
            "valid_ast": True
        }
        self.changes.append(change)
        
        if self.dry_run:
            print(f"🔍 [DRY-RUN] ایجاد می‌شود: {change['file']} ({change['lines']} خط)")
            return True
        
        # ایجاد دایرکتوری در صورت نیاز
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # نوشتن واقعی
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ ایجاد شد: {change['file']}")
        return True
    
    def summary(self):
        print(f"\n📊 خلاصه: {len(self.changes)} فایل {'ایجاد می‌شود' if self.dry_run else 'ایجاد شد'}")

def create_missing_domains(writer: SafeFileWriter):
    """ایجاد دامنه‌های گمشده: irrigation, infrastructure, economics"""
    from datetime import timezone
    
    domains_config = {
        "irrigation": {
            "description": "موتور طراحی سیستم‌های آبیاری",
            "init_content": '"""Irrigation Design Engine - Drip, Sprinkler, Pivot, Surface"""\n',
            "scheduler_content": '''"""
Irrigation Scheduler
منبع: FAO-56 + Keller & Bliesner (1990)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class IrrigationEvent:
    date: str
    depth_mm: float
    method: str
    efficiency: float  # 0.0 to 1.0
    duration_hours: float

def calculate_interval(etc_mm_per_day: float, raw_mm: float, allowable_depletion: float) -> int:
    """محاسبه دور آبیاری (روز)"""
    if etc_mm_per_day <= 0:
        return 0
    interval = (raw_mm * allowable_depletion) / etc_mm_per_day
    return max(1, int(round(interval)))

def calculate_application_depth(etc_mm: float, efficiency: float, effective_rain_mm: float) -> float:
    """محاسبه عمق آبیاری مورد نیاز"""
    net_need = max(0, etc_mm - effective_rain_mm)
    return net_need / efficiency if efficiency > 0 else 0.0
'''
        },
        "infrastructure": {
            "description": "طراحی زیرساخت‌های مزرعه",
            "init_content": '"""Infrastructure Design Engine - Reservoirs, Canals, Ponds"""\n',
            "earthwork_content": '''"""
Earthwork & Infrastructure Calculator
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class PondDesign:
    volume_m3: float
    surface_area_m2: float
    depth_m: float
    embankment_volume_m3: float

def design_storage_pond(daily_demand_m3: float, autonomy_days: int, evaporation_mm_day: float, surface_area_m2: float) -> PondDesign:
    """طراحی استخر ذخیره آب"""
    storage = daily_demand_m3 * autonomy_days
    evaporation_loss = (evaporation_mm_day / 1000) * surface_area_m2 * autonomy_days
    total_volume = storage + evaporation_loss
    depth = total_volume / surface_area_m2 if surface_area_m2 > 0 else 0
    return PondDesign(
        volume_m3=total_volume,
        surface_area_m2=surface_area_m2,
        depth_m=depth,
        embankment_volume_m3=surface_area_m2 * depth * 0.3  # تخمین ساده
    )
'''
        },
        "economics": {
            "description": "موتور تحلیل اقتصادی پروژه",
            "init_content": '"""Economic Analysis Engine - CAPEX, OPEX, NPV, IRR"""\n',
            "analysis_content": '''"""
Economic Analysis for Agricultural Projects
منبع: FAO Investment Centre methodology
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class EconomicResult:
    npv: float
    irr: Optional[float]
    payback_years: float
    gross_margin: float
    net_margin: float
    roi: float

def calculate_npv(cashflows: List[float], discount_rate: float) -> float:
    """محاسبه NPV (Net Present Value)"""
    return sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cashflows))

def calculate_payback(cashflows: List[float]) -> float:
    """محاسبه دوره بازگشت سرمایه (سال)"""
    cumulative = 0.0
    for year, cf in enumerate(cashflows, 1):
        cumulative += cf
        if cumulative >= 0:
            return year
    return float("inf")
'''
        }
    }
    
    for domain_name, config in domains_config.items():
        domain_path = HYDROMA_ROOT / domain_name
        writer.write(
            domain_path / "__init__.py",
            config["init_content"],
            f"Init file for {config['description']}"
        )
        
        # ایجاد فایل اصلی هر دامنه
        if domain_name == "irrigation":
            writer.write(domain_path / "scheduler.py", config["scheduler_content"], "Irrigation scheduling logic")
        elif domain_name == "infrastructure":
            writer.write(domain_path / "earthwork.py", config["earthwork_content"], "Pond & infrastructure design")
        elif domain_name == "economics":
            writer.write(domain_path / "analysis.py", config["analysis_content"], "NPV, IRR, payback analysis")

def implement_climate_engine(writer: SafeFileWriter):
    """پیاده‌سازی موتور واقعی FAO-56"""
    climate_path = HYDROMA_ROOT / "climate"
    
    et_code = '''"""
Climate Engine: FAO-56 Reference Evapotranspiration (ET0)
منبع: Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). 
        FAO Irrigation and Drainage Paper 56.
        
Implemented methods:
- Hargreaves-Samani (when only temperature data available)
- Penman-Monteith (full standard, when all data available)
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClimateData:
    tmin: float          # °C
    tmax: float          # °C
    rh_min: Optional[float] = None   # %
    rh_max: Optional[float] = None   # %
    wind_speed: Optional[float] = None  # m/s at 2m
    solar_radiation: Optional[float] = None  # MJ/m2/day
    elevation: float = 0.0  # m
    latitude: float = 0.0   # degrees (positive = North)
    doy: int = 1  # day of year

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

def calc_et0_hargreaves(data: ClimateData) -> float:
    """
    محاسبه ET0 با روش Hargreaves-Samani
    مناسب برای مناطق فاقد داده کامل هواشناسی
    معادله 50 و 52 FAO-56
    """
    tmean = (data.tmax + data.tmin) / 2
    # محاسبه Ra (تابش فرازمینی) ساده‌سازی شده
    phi = math.radians(data.latitude)
    dr = 1 + 0.033 * math.cos(2 * math.pi * data.doy / 365)
    delta_sun = 0.409 * math.sin(2 * math.pi * data.doy / 365 - 1.39)
    ws = math.acos(-math.tan(phi) * math.tan(delta_sun)) if abs(math.tan(phi) * math.tan(delta_sun)) < 1 else 0
    gsc = 0.0820  # MJ/m2/min
    ra = (24 * 60 / math.pi) * gsc * dr * (
        ws * math.sin(phi) * math.sin(delta_sun) +
        math.cos(phi) * math.cos(delta_sun) * math.sin(ws)
    )
    # تبدیل Ra از MJ/m2/day به mm/day (تقریباً 0.408)
    ra_mm = ra * 0.408
    et0 = 0.0023 * (tmean + 17.8) * math.sqrt(max(0, data.tmax - data.tmin)) * ra_mm
    return max(0.0, et0)

def calc_et0_penman_monteith(data: ClimateData) -> float:
    """
    محاسبه ET0 با روش Penman-Monteith (استاندارد جهانی فائو)
    معادله 39 FAO-56
    
    نیازمند همه پارامترها: tmin, tmax, rh_min, rh_max, wind_speed, solar_radiation
    """
    if None in (data.rh_min, data.rh_max, data.wind_speed, data.solar_radiation):
        raise ValueError("داده‌های ناقص. برای Penman-Monteith به همه پارامترها نیاز است.")
    
    tmean = (data.tmax + data.tmin) / 2
    delta = calc_delta(tmean)
    gamma = calc_psychrometric(data.elevation)
    
    # فشار بخار واقعی (ea) - معادله 17 FAO-56
    es_tmax = calc_saturation_vapor_pressure(data.tmax)
    es_tmin = calc_saturation_vapor_pressure(data.tmin)
    ea = (es_tmin * (data.rh_max / 100) + es_tmax * (data.rh_min / 100)) / 2
    
    # تابش خالص (Rn) - ساده‌سازی شده
    rn = data.solar_radiation * 0.77  # albedo grass = 0.23
    
    # معادله نهایی PM
    numerator = 0.408 * delta * rn + gamma * (900 / (tmean + 273)) * data.wind_speed * (es_tmax - ea)
    denominator = delta + gamma * (1 + 0.34 * data.wind_speed)
    et0 = numerator / denominator
    return max(0.0, et0)

def calc_et0(data: ClimateData) -> float:
    """
    انتخاب خودکار روش بر اساس داده‌های موجود
    اگر همه داده‌ها موجود باشد → Penman-Monteith
    در غیر این صورت → Hargreaves
    """
    try:
        return calc_et0_penman_monteith(data)
    except ValueError:
        return calc_et0_hargreaves(data)
'''
    
    writer.write(
        climate_path / "et_calculator.py",
        et_code,
        "FAO-56 ET0 engine (replacing STUB)"
    )

def main():
    import sys
    dry_run = "--dry-run" in sys.argv
    
    print(f"🚀 شروع فاز ۱: توسعه هسته علمی (Mode: {'DRY-RUN' if dry_run else 'EXECUTION'})\n")
    
    writer = SafeFileWriter(dry_run=dry_run)
    
    # مرحله 1: ایجاد دامنه‌های گمشده
    print("📦 گام ۱: ایجاد دامنه‌های گمشده (irrigation, infrastructure, economics)")
    create_missing_domains(writer)
    
    # مرحله 2: پیاده‌سازی موتور اقلیم
    print("\n🌡️ گام ۲: پیاده‌سازی موتور FAO-56")
    implement_climate_engine(writer)
    
    writer.summary()
    
    if dry_run:
        print("\n" + "="*60)
        print("👆 این یک DRY-RUN بود. هیچ فایلی تغییر نکرد.")
        print("💡 برای اجرای واقعی، اسکریپت را بدون --dry-run اجرا کنید:")
        print("   python sandbox\\phase1_scientific_core.py")

if __name__ == "__main__":
    main()