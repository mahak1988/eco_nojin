#!/usr/bin/env python3
# ============================================================================
# نصب‌کننده فاز ۲: موتور فنولوژی تطبیقی اقلیمی
# الگوریتم‌ها: H05 فنولوژی پویا | H06 خشکسالی ناگهانی | H07 ساعات سرمایی | H24 تصحیح بلادرنگ
# خروجی: ماژول + تست + اتصال به planting_calendar.py + به‌روزرسانی رجیستری
# ============================================================================
import json
import shutil
import subprocess
import sys
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
CAP_DIR = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation"
PLANTING_CAL = PROJECT_ROOT / "services" / "scientific_motors" / "planting_calendar.py"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_climate_adaptive_phenology.py"
REGISTRY = PROJECT_ROOT / "docs" / "hydroma" / "innovation_registry.json"

# ----------------------------------------------------------------------------
# کد ماژول فنولوژی تطبیقی
# ----------------------------------------------------------------------------
CAP_CODE = '''# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Climate Adaptive Phenology Engine - Phase 2
# Algorithms: H05 Dynamic Planting | H06 Flash Drought Warning
#             H07 Chilling Hours   | H24 Real-time Correction
# References: Modest et al. 2022 (phenology shift)
#             Yuan et al. 2023 (flash drought)
#             Luedeling et al. 2011 (chilling hours)
# ============================================================================
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

__version__ = "1.0.0"

# ------------------------------------------------------------------ ثابت‌ها
DAY_MS = 86400000  # میلی‌ثانیه در روز


@dataclass
class PhenologyConfig:
    frost_buffer_days: int = 14          # فاصله ایمن پس از آخرین یخبندان
    soil_temp_threshold_c: float = 10.0  # آستانه دمای خاک برای جوانه‌زنی
    soil_temp_window_days: int = 7       # بازه پایش دمای خاک
    rain_onset_threshold_mm: float = 10.0  # حداقل بارش برای شروع دیم
    rain_window_days: int = 30           # بازه جستجوی شروع بارش
    flash_drought_vpd_trend: float = 0.5  # آستانه روند فشار بخار
    flash_drought_sm_trend: float = -0.3  # آستانه روند رطوبت خاک
    flash_drought_horizon_days: int = 14  # افق هشدار
    chilling_model: str = "utah"         # مدل ساعات سرمایی


# ------------------------------------------------------------------ ابزارها
def safe_mean(values: Sequence[float]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def slope_per_day(values: Sequence[float]) -> float:
    # شیب خطی (رگرسیون ساده) بر واحد روز
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n < 3:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = safe_mean(vals)
    num = sum((i - x_mean) * (vals[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


# ============================================================================
class ClimateAdaptivePhenology:
    # ------------------------------------------------------------------ init
    def __init__(self, config: Optional[PhenologyConfig] = None):
        self.cfg = config or PhenologyConfig()

    # ------------------------------------------------------------------- H05
    def h05_dynamic_planting_day(self,
                                 last_frost_day_of_year: int,
                                 soil_temp_series: Sequence[float],
                                 rain_onset_day_of_year: Optional[int] = None,
                                 target_day_of_year: Optional[int] = None) -> Dict:
        """
        تعیین تاریخ کاشت پویا بر اساس:
        1. آخرین یخبندان + فاصله ایمن
        2. رسیدن دمای خاک به آستانه جوانه‌زنی
        3. همزمانی با شروع فصل بارش (برای دیم)
        خروجی: روز سال کاشت + دلایل
        """
        reasons = []
        candidate = target_day_of_year or 280  # پیش‌فرض: اواسط پاییز

        # 1. فاصله ایمن از یخبندان
        if last_frost_day_of_year:
            frost_safe = last_frost_day_of_year + self.cfg.frost_buffer_days
            if candidate < frost_safe:
                candidate = frost_safe
                reasons.append("تنظیم بر اساس آخرین یخبندان + %d روز ایمن"
                               % self.cfg.frost_buffer_days)

        # 2. دمای خاک
        if soil_temp_series and len(soil_temp_series) >= 3:
            mean_soil = safe_mean(soil_temp_series[-self.cfg.soil_temp_window_days:])
            if mean_soil < self.cfg.soil_temp_threshold_c:
                deficit = self.cfg.soil_temp_threshold_c - mean_soil
                delay_days = int(math.ceil(deficit * 3))  # تقریب 3 روز به ازای هر درجه
                candidate += delay_days
                reasons.append("تأخیر %d روزه برای رسیدن دمای خاک به %.1f درجه"
                               % (delay_days, self.cfg.soil_temp_threshold_c))
            else:
                reasons.append("دمای خاک مناسب است (%.1f درجه)" % mean_soil)

        # 3. همزمانی با شروع بارش (برای دیم)
        if rain_onset_day_of_year:
            gap = abs(candidate - rain_onset_day_of_year)
            if gap > self.cfg.rain_window_days:
                reasons.append("هشدار: فاصله %d روزه از شروع بارش؛ ریسک دیم بالا" % gap)
            else:
                reasons.append("همزمانی مناسب با شروع بارش (%d روز)" % gap)

        return {
            "planting_day_of_year": candidate,
            "reasons": reasons,
            "frost_risk_reduced": bool(reasons and "یخبندان" in reasons[0]),
            "confidence": "B" if len(reasons) >= 2 else "C",
        }

    # ------------------------------------------------------------------- H06
    def h06_flash_drought_risk(self,
                               vpd_last_7d: Sequence[float],
                               soil_moisture_fraction_last_14d: Sequence[float],
                               forecast_rain_mm_next_14d: float) -> Dict:
        """
        ریسک خشکسالی ناگهانی بر اساس:
        - روند فشار بخار (افزایش = تنش)
        - روند رطوبت خاک (کاهش = تنش)
        - پیش‌بینی بارش (کاهش = تشدید)
        خروجی: ریسک 0 تا 1 + سطح هشدار
        """
        vpd_slope = slope_per_day(vpd_last_7d)
        sm_slope = slope_per_day(soil_moisture_fraction_last_14d)

        risk = 0.0
        drivers = []

        if vpd_slope > self.cfg.flash_drought_vpd_trend:
            risk += 0.35
            drivers.append("افزایش سریع فشار بخار (%.2f/روز)" % vpd_slope)

        if sm_slope < self.cfg.flash_drought_sm_trend:
            risk += 0.35
            drivers.append("کاهش سریع رطوبت خاک (%.2f/روز)" % sm_slope)

        if forecast_rain_mm_next_14d < 5.0:
            risk += 0.20
            drivers.append("پیش‌بینی بارش ناچیز (%.1f میلی‌متر در ۱۴ روز)"
                           % forecast_rain_mm_next_14d)

        # نرمال‌سازی
        risk = min(1.0, risk)

        if risk >= 0.7:
            level = "بحرانی"
            action = "آبیاری اضطراری + پایش روزانه"
        elif risk >= 0.4:
            level = "هشدار"
            action = "افزایش دور آبیاری + مالچ‌پاشی"
        elif risk >= 0.2:
            level = "پایش"
            action = "پایش هفتگی"
        else:
            level = "عادی"
            action = "روال عادی"

        return {
            "risk_0_1": round(risk, 2),
            "level": level,
            "action": action,
            "drivers": drivers,
            "horizon_days": self.cfg.flash_drought_horizon_days,
            "vpd_slope_per_day": round(vpd_slope, 3),
            "sm_slope_per_day": round(sm_slope, 3),
        }

    # ------------------------------------------------------------------- H07
    def h07_chilling_hours(self,
                           hourly_temps_c: Sequence[float]) -> Dict:
        """
        محاسبه ساعات سرمایی مؤثر با مدل یوتا:
        0-2.4: 1 واحد | 2.5-9.1: 0.5 | 9.2-12.4: 0 | 12.5-15.9: -0.5 | >=16: -1
        خروجی: مجموع واحدها + تفسیر
        """
        units = 0.0
        for t in hourly_temps_c:
            if t is None:
                continue
            if t <= 2.4:
                units += 1.0
            elif t <= 9.1:
                units += 0.5
            elif t <= 12.4:
                units += 0.0
            elif t <= 15.9:
                units -= 0.5
            else:
                units -= 1.0
        units = max(0.0, units)

        if units >= 1000:
            status = "کافی برای اکثر درختان معتدل"
        elif units >= 700:
            status = "کافی برای ارقام کم‌نیاز"
        elif units >= 400:
            status = "مرزی؛ ریسک خزان‌شکنی ناقص"
        else:
            status = "ناکافی؛ نیاز به ارقام کم‌سرمایی یا جبران"

        return {
            "chilling_units": round(units, 0),
            "status": status,
            "model": self.cfg.chilling_model,
            "hours_analyzed": len(hourly_temps_c),
        }

    # ------------------------------------------------------------------- H24
    def h24_realtime_correction(self,
                                ndvi_actual: float,
                                ndvi_predicted: float) -> Dict:
        """
        تصحیح بلادرنگ بر اساس تفاوت شاخص گیاهی مشاهده‌شده و پیش‌بینی‌شده
        خروجی: ضریب تصحیح عملکرد (0.5 تا 1.5)
        """
        if ndvi_predicted <= 0:
            return {"correction_factor": 1.0, "note": "پیش‌بینی نامعتبر"}
        ratio = ndvi_actual / ndvi_predicted
        factor = max(0.5, min(1.5, ratio))
        note = ""
        if factor < 0.85:
            note = "عملکرد واقعی کمتر از پیش‌بینی؛ تنش فعال"
        elif factor > 1.10:
            note = "عملکرد واقعی بهتر از پیش‌بینی"
        else:
            note = "تطابق مناسب"
        return {
            "correction_factor": round(factor, 2),
            "ndvi_ratio": round(ratio, 2),
            "note": note,
        }

    # -------------------------------------------------- گزارش فصلی یکپارچه
    def generate_season_advisory(self,
                                 last_frost_day: int,
                                 soil_temp_series: Sequence[float],
                                 vpd_7d: Sequence[float],
                                 sm_14d: Sequence[float],
                                 forecast_rain: float,
                                 winter_temps: Optional[Sequence[float]] = None) -> Dict:
        """تولید توصیه‌نامه فصلی کامل با ترکیب هر چهار الگوریتم"""
        advisory = {}
        advisory["planting"] = self.h05_dynamic_planting_day(
            last_frost_day, soil_temp_series)
        advisory["flash_drought"] = self.h06_flash_drought_risk(
            vpd_7d, sm_14d, forecast_rain)
        if winter_temps:
            advisory["chilling"] = self.h07_chilling_hours(winter_temps)
        advisory["generated_by"] = "ClimateAdaptivePhenology v%s" % __version__
        return advisory
'''

INIT_APPEND = '''
from .climate_adaptive_phenology import (
    ClimateAdaptivePhenology, PhenologyConfig)
'''

TEST_CODE = '''import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.climate_adaptive_phenology import (
    ClimateAdaptivePhenology)

def main():
    cap = ClimateAdaptivePhenology()

    # H05: فنولوژی پویا
    soil = [8.0, 8.5, 9.0, 9.5]
    r = cap.h05_dynamic_planting_day(280, soil, rain_onset_day_of_year=300)
    assert "planting_day_of_year" in r
    assert r["planting_day_of_year"] >= 280
    assert len(r["reasons"]) > 0

    # H06: خشکسالی ناگهانی
    vpd = [1.0, 1.2, 1.5, 1.9, 2.4, 3.0, 3.7]
    sm = [0.6, 0.55, 0.5, 0.42, 0.35, 0.28, 0.22, 0.17,
          0.13, 0.10, 0.08, 0.06, 0.05, 0.04]
    r2 = cap.h06_flash_drought_risk(vpd, sm, forecast_rain_mm_next_14d=2.0)
    assert 0.0 <= r2["risk_0_1"] <= 1.0
    assert r2["level"] in ("عادی", "پایش", "هشدار", "بحرانی")
    assert r2["risk_0_1"] >= 0.5  # شرایط تنش شدید

    # H07: ساعات سرمایی
    temps = [1.0, 2.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0] * 100
    r3 = cap.h07_chilling_hours(temps)
    assert r3["chilling_units"] >= 0
    assert r3["hours_analyzed"] == 800

    # H24: تصحیح بلادرنگ
    r4 = cap.h24_realtime_correction(0.4, 0.6)
    assert 0.5 <= r4["correction_factor"] <= 1.5
    assert r4["correction_factor"] < 1.0  # عملکرد کمتر از پیش‌بینی

    # گزارش فصلی یکپارچه
    adv = cap.generate_season_advisory(
        last_frost_day=280, soil_temp_series=soil,
        vpd_7d=vpd, sm_14d=sm, forecast_rain=2.0,
        winter_temps=temps)
    assert "planting" in adv and "flash_drought" in adv and "chilling" in adv

    print("ALL CAP TESTS PASSED (H05,H06,H07,H24)")

if __name__ == "__main__":
    main()
'''

IMPORT_BLOCK = '''
# --- Hydroma Climate Adaptive Phenology (auto-installed, Phase 2) ---
try:
    from engine.hydroma.climate_adaptation.climate_adaptive_phenology import (
        ClimateAdaptivePhenology as _CAP_cls)
    _HYDROMA_CAP = _CAP_cls()
except Exception:
    _HYDROMA_CAP = None
'''


# ----------------------------------------------------------------------------
# مراحل نصب
# ----------------------------------------------------------------------------
def install_module():
    print("[1/5] ایجاد ماژول ClimateAdaptivePhenology ...")
    CAP_DIR.mkdir(parents=True, exist_ok=True)
    (CAP_DIR / "climate_adaptive_phenology.py").write_text(CAP_CODE, encoding="utf-8")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
    init_file = CAP_DIR / "__init__.py"
    if init_file.exists():
        current = init_file.read_text(encoding="utf-8")
        if "climate_adaptive_phenology" not in current:
            init_file.write_text(current + INIT_APPEND, encoding="utf-8")
            print("   -> __init__.py به‌روزرسانی شد")
    else:
        init_file.write_text(INIT_APPEND.lstrip(), encoding="utf-8")
    print("   -> engine/hydroma/climate_adaptation/climate_adaptive_phenology.py")
    print("   -> tests/unit/test_climate_adaptive_phenology.py")


def integrate_planting_calendar():
    print("[2/5] اتصال به planting_calendar.py ...")
    if not PLANTING_CAL.exists():
        print("   !! فایل planting_calendar.py یافت نشد؛ اتصال رد شد.")
        return False
    content = PLANTING_CAL.read_text(encoding="utf-8")
    if "_HYDROMA_CAP" in content:
        print("   -> اتصال از قبل موجود است؛ رد شد.")
        return True
    backup = PLANTING_CAL.with_suffix(".py.bak_cap")
    shutil.copy2(PLANTING_CAL, backup)
    markers = ["logger = logging.getLogger(__name__)",
               "from __future__ import annotations"]
    inserted = False
    for marker in markers:
        if marker in content:
            content = content.replace(marker, marker + IMPORT_BLOCK, 1)
            inserted = True
            break
    if not inserted:
        # افزودن در ابتدای فایل
        content = IMPORT_BLOCK.lstrip() + "\n" + content
        inserted = True
    PLANTING_CAL.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(PLANTING_CAL), doraise=True)
        print("   -> اتصال اعمال و سینتکس تأیید شد.")
        return True
    except Exception as exc:
        shutil.copy2(backup, PLANTING_CAL)
        print(f"   !! خطای سینتکس؛ rollback انجام شد: {exc}")
        return False


def run_tests():
    print("[3/5] اجرای تست‌های واحد ...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    return proc.returncode == 0


def update_registry():
    print("[4/5] به‌روزرسانی رجیستری مستندات ...")
    if not REGISTRY.exists():
        print("   !! رجیستری یافت نشد؛ رد شد.")
        return False
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for phase in data.get("phases", []):
            if phase.get("phase") == "فاز 2":
                phase["status"] = "نصب شد"
        data["phase2_installed_at"] = __import__("datetime").datetime.now().isoformat()
        REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print("   -> وضعیت فاز ۲ به «نصب شد» تغییر یافت.")
        return True
    except Exception as exc:
        print(f"   !! خطا در به‌روزرسانی رجیستری: {exc}")
        return False


def demo_advisory():
    print("[5/5] تولید توصیه‌نامه فصلی نمونه ...")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from engine.hydroma.climate_adaptation.climate_adaptive_phenology import (
            ClimateAdaptivePhenology)
        cap = ClimateAdaptivePhenology()
        adv = cap.generate_season_advisory(
            last_frost_day=280,
            soil_temp_series=[8.0, 8.5, 9.0, 9.5],
            vpd_7d=[1.0, 1.2, 1.5, 1.9, 2.4, 3.0, 3.7],
            sm_14d=[0.6, 0.55, 0.5, 0.42, 0.35, 0.28, 0.22, 0.17,
                    0.13, 0.10, 0.08, 0.06, 0.05, 0.04],
            forecast_rain=2.0,
            winter_temps=[1.0, 2.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0] * 100)
        print(f"   تاریخ کاشت پیشنهادی: روز {adv['planting']['planting_day_of_year']} سال")
        print(f"   ریسک خشکسالی ناگهانی: {adv['flash_drought']['risk_0_1']} "
              f"({adv['flash_drought']['level']})")
        if "chilling" in adv:
            print(f"   ساعات سرمایی: {adv['chilling']['chilling_units']} واحد")
        return True
    except Exception as exc:
        print(f"   !! خطا در نمونه: {exc}")
        return False


def main():
    print("=" * 70)
    print("نصب فاز ۲: موتور فنولوژی تطبیقی اقلیمی (H05,H06,H07,H24)")
    print("=" * 70)
    install_module()
    integrated = integrate_planting_calendar()
    tests_ok = run_tests()
    registry_ok = update_registry()
    demo_advisory()
    print("=" * 70)
    print(f"نتیجه: ماژول=OK | تست‌ها={'OK' if tests_ok else 'FAIL'} | "
          f"اتصال={'OK' if integrated else 'SKIP'} | رجیستری={'OK' if registry_ok else 'SKIP'}")
    print("=" * 70)


if __name__ == "__main__":
    main()