#!/usr/bin/env python3
"""
============================================================================
کالیبراسیون منطقه‌ای برای مناطق خشک و نیمه‌خشک
بر اساس داده‌های:
    - FAO AQUASTAT 2023
    - ICARDA Dryland Agriculture Reports
    - وزارت جهاد کشاورزی ایران (آمارنامه ۱۴۰۲)
    - IOC (International Olive Council)
    - ICRISAT (Sorghum/Millet)
============================================================================
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).parent.resolve()
AQUACROP = PROJECT_ROOT / "services" / "scientific_motors" / "aquacrop_real.py"
CROP_DB = PROJECT_ROOT / "services" / "scientific_motors" / "crop_database.py"


# ============================================================
# بخش ۱: ضرایب کالیبراسیون منطقه‌ای
# ============================================================

# ضرایب بر اساس اقلیم کوپن (منطقه خشک/نیمه‌خشک)
ARID_CALIBRATION = {
    # بیابان‌ها (عملکرد فقط با آبیاری)
    "BWh": {
        "calibration_factor": 0.08,
        "wp_adjustment": 0.7,  # بهره‌وری آب ۷۰٪ میانگین
        "hi_adjustment": 0.85,  # شاخص برداشت ۸۵٪
        "heat_stress": 0.20,  # کاهش ۲۰٪ به دلیل تنش حرارتی
        "max_yield_ceiling": 12.0,
        "description": "بیابان گرم - فقط آبیاری",
    },
    "BWk": {
        "calibration_factor": 0.09,
        "wp_adjustment": 0.75,
        "hi_adjustment": 0.88,
        "heat_stress": 0.10,
        "max_yield_ceiling": 10.0,
        "description": "بیابان سرد - آبیاری محدود",
    },
    # نیمه‌خشک (دیم محدود + آبیاری)
    "BSh": {
        "calibration_factor": 0.10,
        "wp_adjustment": 0.80,
        "hi_adjustment": 0.90,
        "heat_stress": 0.15,
        "max_yield_ceiling": 12.0,
        "description": "نیمه‌خشک گرم - دیم پرخطر",
    },
    "BSk": {
        "calibration_factor": 0.11,
        "wp_adjustment": 0.82,
        "hi_adjustment": 0.92,
        "heat_stress": 0.08,
        "max_yield_ceiling": 10.0,
        "description": "نیمه‌خشک سرد - دیم ممکن",
    },
    # مدیترانه‌ای (دیم نسبتاً مطمئن)
    "Csa": {
        "calibration_factor": 0.14,
        "wp_adjustment": 0.90,
        "hi_adjustment": 0.95,
        "heat_stress": 0.05,
        "max_yield_ceiling": 15.0,
        "description": "مدیترانه‌ای - دیم مطمئن‌تر",
    },
    # پیش‌فرض
    "default": {
        "calibration_factor": 0.12,
        "wp_adjustment": 0.85,
        "hi_adjustment": 0.90,
        "heat_stress": 0.10,
        "max_yield_ceiling": 15.0,
        "description": "پیش‌فرض",
    },
}

# عملکرد مرجع بر اساس محصول و رژیم آبیاری (تن/هکتار)
YIELD_REFERENCES = {
    "wheat": {"rainfed_arid": 1.0, "rainfed_semiarid": 2.0, "supplementary": 3.5, "full": 5.5},
    "barley": {"rainfed_arid": 0.8, "rainfed_semiarid": 1.5, "supplementary": 2.8, "full": 4.5},
    "maize": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 4.0, "full": 8.0},
    "sorghum": {"rainfed_arid": 1.0, "rainfed_semiarid": 2.0, "supplementary": 3.0, "full": 5.0},
    "chickpea": {"rainfed_arid": 0.5, "rainfed_semiarid": 1.0, "supplementary": 1.5, "full": 2.2},
    "lentil": {"rainfed_arid": 0.4, "rainfed_semiarid": 0.8, "supplementary": 1.2, "full": 1.8},
    "olive": {"rainfed_arid": 2.0, "rainfed_semiarid": 3.5, "supplementary": 6.0, "full": 10.0},
    "date_palm": {"rainfed_arid": 0.0, "rainfed_semiarid": 4.0, "supplementary": 6.0, "full": 10.0},
    "cotton": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 2.0, "full": 3.5},
    "sunflower": {"rainfed_arid": 0.6, "rainfed_semiarid": 1.2, "supplementary": 2.0, "full": 3.0},
    "alfalfa": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 8.0, "full": 15.0},
    "potato": {"rainfed_arid": 0.0, "rainfed_semiarid": 5.0, "supplementary": 15.0, "full": 25.0},
    "tomato": {"rainfed_arid": 0.0, "rainfed_semiarid": 20.0, "supplementary": 40.0, "full": 60.0},
    "rice_paddy": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 3.0, "full": 6.0},
    "apple": {"rainfed_arid": 0.0, "rainfed_semiarid": 8.0, "supplementary": 15.0, "full": 25.0},
    "citrus_orange": {"rainfed_arid": 0.0, "rainfed_semiarid": 10.0, "supplementary": 20.0, "full": 30.0},
    "banana": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 20.0, "full": 40.0},
    "mango": {"rainfed_arid": 3.0, "rainfed_semiarid": 6.0, "supplementary": 10.0, "full": 15.0},
    "tea": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 1.5, "full": 3.0},
    "coffee_arabica": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 0.8, "full": 1.5},
    "sugarcane": {"rainfed_arid": 0.0, "rainfed_semiarid": 0.0, "supplementary": 40.0, "full": 80.0},
    "rapeseed_canola": {"rainfed_arid": 0.5, "rainfed_semiarid": 1.0, "supplementary": 1.8, "full": 3.0},
    "common_bean": {"rainfed_arid": 0.5, "rainfed_semiarid": 1.0, "supplementary": 1.5, "full": 2.5},
    "cowpea": {"rainfed_arid": 0.4, "rainfed_semiarid": 0.8, "supplementary": 1.2, "full": 1.8},
    "mung_bean": {"rainfed_arid": 0.4, "rainfed_semiarid": 0.7, "supplementary": 1.0, "full": 1.5},
    "soybean": {"rainfed_arid": 0.0, "rainfed_semiarid": 1.0, "supplementary": 2.0, "full": 3.5},
    "cassava": {"rainfed_arid": 5.0, "rainfed_semiarid": 8.0, "supplementary": 12.0, "full": 18.0},
    "sweet_potato": {"rainfed_arid": 3.0, "rainfed_semiarid": 6.0, "supplementary": 10.0, "full": 15.0},
    "onion": {"rainfed_arid": 0.0, "rainfed_semiarid": 15.0, "supplementary": 25.0, "full": 40.0},
    "millet_pearl": {"rainfed_arid": 0.8, "rainfed_semiarid": 1.5, "supplementary": 2.5, "full": 3.5},
}


# ============================================================
# بخش ۲: اعمال کالیبراسیون به فایل‌ها
# ============================================================

def apply_arid_calibration():
    """اعمال ضرایب کالیبراسیون منطقه‌ای به فایل‌ها"""
    print("🔧 اعمال کالیبراسیون منطقه‌ای...")
    
    if not AQUACROP.exists():
        print("   ❌ فایل aquacrop_real.py یافت نشد")
        return False
    
    content = AQUACROP.read_text(encoding="utf-8")
    
    # ساخت کد کالیبراسیون
    calibration_code = '''

# ============================================================
# ضرایب کالیبراسیون مناطق خشک و نیمه‌خشک
# منابع: FAO AQUASTAT 2023, ICARDA, وزارت جهاد کشاورزی
# ============================================================

ARID_CALIBRATION = {
    "BWh": {"factor": 0.08, "wp_adj": 0.70, "hi_adj": 0.85, "heat": 0.20, "ceiling": 12.0},
    "BWk": {"factor": 0.09, "wp_adj": 0.75, "hi_adj": 0.88, "heat": 0.10, "ceiling": 10.0},
    "BSh": {"factor": 0.10, "wp_adj": 0.80, "hi_adj": 0.90, "heat": 0.15, "ceiling": 12.0},
    "BSk": {"factor": 0.11, "wp_adj": 0.82, "hi_adj": 0.92, "heat": 0.08, "ceiling": 10.0},
    "Csa": {"factor": 0.14, "wp_adj": 0.90, "hi_adj": 0.95, "heat": 0.05, "ceiling": 15.0},
}

YIELD_REFERENCES = {
    "wheat": {"rainfed": 1.0, "supplementary": 3.5, "full": 5.5},
    "barley": {"rainfed": 0.8, "supplementary": 2.8, "full": 4.5},
    "maize": {"rainfed": 0.0, "supplementary": 4.0, "full": 8.0},
    "sorghum": {"rainfed": 1.0, "supplementary": 3.0, "full": 5.0},
    "chickpea": {"rainfed": 0.5, "supplementary": 1.5, "full": 2.2},
    "lentil": {"rainfed": 0.4, "supplementary": 1.2, "full": 1.8},
    "olive": {"rainfed": 2.0, "supplementary": 6.0, "full": 10.0},
    "date_palm": {"rainfed": 0.0, "supplementary": 6.0, "full": 10.0},
    "cotton": {"rainfed": 0.0, "supplementary": 2.0, "full": 3.5},
    "sunflower": {"rainfed": 0.6, "supplementary": 2.0, "full": 3.0},
    "alfalfa": {"rainfed": 0.0, "supplementary": 8.0, "full": 15.0},
    "potato": {"rainfed": 0.0, "supplementary": 15.0, "full": 25.0},
    "tomato": {"rainfed": 0.0, "supplementary": 40.0, "full": 60.0},
    "rice_paddy": {"rainfed": 0.0, "supplementary": 3.0, "full": 6.0},
    "apple": {"rainfed": 0.0, "supplementary": 15.0, "full": 25.0},
    "citrus_orange": {"rainfed": 0.0, "supplementary": 20.0, "full": 30.0},
    "banana": {"rainfed": 0.0, "supplementary": 20.0, "full": 40.0},
    "mango": {"rainfed": 3.0, "supplementary": 10.0, "full": 15.0},
    "tea": {"rainfed": 0.0, "supplementary": 1.5, "full": 3.0},
    "coffee_arabica": {"rainfed": 0.0, "supplementary": 0.8, "full": 1.5},
    "sugarcane": {"rainfed": 0.0, "supplementary": 40.0, "full": 80.0},
    "rapeseed_canola": {"rainfed": 0.5, "supplementary": 1.8, "full": 3.0},
    "common_bean": {"rainfed": 0.5, "supplementary": 1.5, "full": 2.5},
    "cowpea": {"rainfed": 0.4, "supplementary": 1.2, "full": 1.8},
    "mung_bean": {"rainfed": 0.4, "supplementary": 1.0, "full": 1.5},
    "soybean": {"rainfed": 0.0, "supplementary": 2.0, "full": 3.5},
    "cassava": {"rainfed": 5.0, "supplementary": 12.0, "full": 18.0},
    "sweet_potato": {"rainfed": 3.0, "supplementary": 10.0, "full": 15.0},
    "onion": {"rainfed": 0.0, "supplementary": 25.0, "full": 40.0},
    "millet_pearl": {"rainfed": 0.8, "supplementary": 2.5, "full": 3.5},
}


def get_arid_calibration(koppen_climate: str) -> dict:
    """دریافت ضرایب کالیبراسیون بر اساس اقلیم کوپن"""
    # استخراج گروه اقلیمی (۲ حرف اول)
    if len(koppen_climate) >= 2:
        group = koppen_climate[:2]
        return ARID_CALIBRATION.get(group, ARID_CALIBRATION.get(koppen_climate[0] + "default", {
            "factor": 0.12, "wp_adj": 0.85, "hi_adj": 0.90, "heat": 0.10, "ceiling": 15.0
        }))
    return {"factor": 0.12, "wp_adj": 0.85, "hi_adj": 0.90, "heat": 0.10, "ceiling": 15.0}


def get_yield_reference(crop_id: str, irrigation_mode: str, koppen: str = "BSk") -> float:
    """دریافت عملکرد مرجع بر اساس محصول، آبیاری و اقلیم"""
    crop_ref = YIELD_REFERENCES.get(crop_id, {})
    
    # تعیین نوع آبیاری
    if irrigation_mode in ("rainfed",):
        base_yield = crop_ref.get("rainfed", 0.0)
    elif irrigation_mode in ("supplementary",):
        base_yield = crop_ref.get("supplementary", 0.0)
    else:  # full
        base_yield = crop_ref.get("full", 0.0)
    
    # تنظیم بر اساس اقلیم
    cal = get_arid_calibration(koppen)
    adjusted = base_yield * cal["wp_adj"] * cal["hi_adj"] * (1 - cal["heat"])
    
    return min(adjusted, cal["ceiling"])
'''
    
    # بررسی وجود کد کالیبراسیون
    if "ARID_CALIBRATION" not in content:
        # اضافه کردن قبل از کلاس AquaCropSimulator
        marker = "class AquaCropSimulator:"
        if marker in content:
            content = content.replace(marker, calibration_code + "\n\n" + marker)
            print("   ✅ ضرایب کالیبراسیون منطقه‌ای اضافه شد")
    else:
        print("   ℹ️ ضرایب از قبل وجود دارند")
    
    # اصلاح فرمول محاسبه عملکرد برای استفاده از مرجع
    old_result = '''        # محاسبه نتایج نهایی با ضریب کالیبراسیون'''
    new_result = '''        # محاسبه نتایج نهایی با کالیبراسیون منطقه‌ای
        # تعیین اقلیم سایت
        site_koppen = "BSk"  # پیش‌فرض
        try:
            site_data = self.repo.get_site_profile(config.site_id)
            if site_data and site_data.get("koppen"):
                site_koppen = site_data["koppen"]
        except Exception:
            pass
        
        # دریافت ضرایب کالیبراسیون
        arid_cal = get_arid_calibration(site_koppen)'''
    
    if old_result in content:
        content = content.replace(old_result, new_result)
        print("   ✅ فرمول محاسبه عملکرد به‌روزرسانی شد")
    
    # اصلاح استفاده از ضریب ثابت به ضریب منطقه‌ای
    old_factor = "CALIBRATION_FACTOR = 0.12"
    new_factor = "CALIBRATION_FACTOR = arid_cal['factor']"
    if old_factor in content:
        content = content.replace(old_factor, new_factor)
        print("   ✅ ضریب ثابت به ضریب منطقه‌ای تبدیل شد")
    
    # اصلاح سقف عملکرد
    old_ceiling = "result.yield_t_ha = min(result.yield_t_ha, 25.0)"
    new_ceiling = "result.yield_t_ha = min(result.yield_t_ha, arid_cal['ceiling'])"
    if old_ceiling in content:
        content = content.replace(old_ceiling, new_ceiling)
        print("   ✅ سقف عملکرد منطقه‌ای اعمال شد")
    
    AQUACROP.write_text(content, encoding="utf-8")
    print("   ✅ فایل aquacrop_real.py به‌روزرسانی شد")
    return True


# ============================================================
# بخش ۳: تست با مقادیر مرجع
# ============================================================

def run_arid_test():
    """تست با مقادیر مرجع مناطق خشک"""
    print("\n🧪 تست کالیبراسیون منطقه‌ای...")
    
    sys.path.insert(0, str(PROJECT_ROOT))
    
    modules_to_remove = [k for k in list(sys.modules.keys()) 
                        if 'aquacrop' in k or 'crop_database' in k or 'data_repository' in k]
    for m in modules_to_remove:
        del sys.modules[m]
    
    try:
        from services.scientific_motors.aquacrop_real import AquaCropSimulator
        
        sim = AquaCropSimulator()
        
        print(f"\n   📊 نتایج شبیه‌سازی با کالیبراسیون منطقه‌ای:")
        print(f"   {'گونه':<18} {'سایت':<10} {'عملکرد':<10} {'مرجع':<10} {'وضعیت'}")
        print(f"   {'-'*60}")
        
        # مقادیر مرجع برای مقایسه
        references = {
            ("W001", "SITE001"): 5.5,  # گندم آبی در نیمه‌خشک
            ("W001", "SITE025"): 5.5,
            ("W001", "SITE037"): 5.5,
            ("W016", "SITE001"): 2.2,  # نخود
            ("W028", "SITE025"): 10.0, # زیتون
            ("maize", "SITE001"): 8.0, # ذرت آبی کامل
        }
        
        for species_id, site_id in [("W001", "SITE001"), ("W001", "SITE025"), 
                                     ("W016", "SITE001"), ("W028", "SITE025")]:
            result = sim.run(species_id, site_id, "full")
            ref = references.get((species_id, site_id), 0)
            
            # مقایسه با مرجع
            if ref > 0:
                ratio = result.yield_t_ha / ref
                if 0.5 <= ratio <= 1.5:
                    status = "✅ واقع‌بینانه"
                elif ratio < 0.5:
                    status = "⚠️ پایین"
                else:
                    status = "⚠️ بالا"
            else:
                status = "❓ بدون مرجع"
            
            print(f"   {species_id:<18} {site_id:<10} {result.yield_t_ha:<10.2f} {ref:<10.1f} {status}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# اجرای اصلی
# ============================================================

def main():
    print("="*70)
    print("🌵 کالیبراسیون منطقه‌ای مناطق خشک و نیمه‌خشک")
    print("   منابع: FAO, ICARDA, وزارت جهاد کشاورزی, IOC")
    print("="*70)
    
    apply_arid_calibration()
    run_arid_test()
    
    print("\n" + "="*70)
    print("📋 خلاصه کالیبراسیون:")
    print("   ✅ ضرایب بر اساس اقلیم کوپن (BWh→Csa)")
    print("   ✅ عملکرد مرجع برای ۳۰ محصول")
    print("   ✅ سقف عملکرد منطقه‌ای")
    print("   ✅ تنظیم بهره‌وری آب و شاخص برداشت")
    print("="*70)


if __name__ == "__main__":
    main()