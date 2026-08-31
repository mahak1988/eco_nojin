#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
رفع مشکل مقادیر بدون محدودیت در توابع استرس
باید همه مقادیر استرس در بازه [0, 1] باشند
============================================================================
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE_FILE = ROOT / "engine" / "hydroma" / "climate_adaptation" / "multi_stress_engine.py"


def fix_unbounded_values():
    """رفع مقادیر بدون محدودیت در همه توابع استرس"""
    
    print("=" * 70)
    print("رفع مقادیر بدون محدودیت در توابع استرس")
    print("=" * 70)
    
    if not ENGINE_FILE.exists():
        print(f"\n❌ فایل یافت نشد: {ENGINE_FILE}")
        return False
    
    content = ENGINE_FILE.read_text(encoding="utf-8")
    original = content
    
    fixes_applied = 0
    
    # ---------------------------------------------------------------
    # اصلاح ۱: تابع سالینیتی
    # ---------------------------------------------------------------
    # فرمول قدیمی (بدون محدودیت):
    #   salinity_stress = max(0.0, (ec - 4) / 16) if ec > 4 else 0.0
    # فرمول جدید (با محدودیت به [0,1]):
    #   salinity_stress = min(1.0, max(0.0, (ec - 4) / 16)) if ec > 4 else 0.0
    
    old_pattern = "salinity_stress = max(0.0, (ec - 4) / 16) if ec > 4 else 0.0"
    new_pattern = "salinity_stress = min(1.0, max(0.0, (ec - 4) / 16)) if ec > 4 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع شوری: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۲: تابع قلیائیت
    # ---------------------------------------------------------------
    old_pattern = "alkalinity_stress = max(0.0, (ph - 8.5) / 5.5) if ph > 8.5 else 0.0"
    new_pattern = "alkalinity_stress = min(1.0, max(0.0, (ph - 8.5) / 5.5)) if ph > 8.5 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع قلیائیت: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۳: ریسک سدیمی شدن
    # ---------------------------------------------------------------
    old_pattern = "sodification_risk = salinity_stress * alkalinity_stress"
    new_pattern = "sodification_risk = min(1.0, salinity_stress * alkalinity_stress)"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ ریسک سدیمی شدن: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۴: تابع خشکسالی (برای اطمینان)
    # ---------------------------------------------------------------
    old_pattern = "drought_stress = max(0.0, (50 - rain) / 50) if rain < 50 else 0.0"
    new_pattern = "drought_stress = min(1.0, max(0.0, (50 - rain) / 50)) if rain < 50 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع خشکسالی: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۵: تابع گرما (برای اطمینان)
    # ---------------------------------------------------------------
    old_pattern = "heat_stress = max(0.0, (temp - 35) / 15) if temp > 35 else 0.0"
    new_pattern = "heat_stress = min(1.0, max(0.0, (temp - 35) / 15)) if temp > 35 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع گرما: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۶: سیل و شیب
    # ---------------------------------------------------------------
    old_pattern = "flood_risk = max(0.0, (rain - 500) / 2000) if rain > 500 else 0.0"
    new_pattern = "flood_risk = min(1.0, max(0.0, (rain - 500) / 2000)) if rain > 500 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع سیل: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # اصلاح ۷: یخبندان
    # ---------------------------------------------------------------
    old_pattern = "frost_stress = max(0.0, (-temp) / 40) if temp < 0 else 0.0"
    new_pattern = "frost_stress = min(1.0, max(0.0, (-temp) / 40)) if temp < 0 else 0.0"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        fixes_applied += 1
        print("✅ تابع یخبندان: محدودیت به [0,1] اضافه شد")
    
    # ---------------------------------------------------------------
    # ذخیره فایل
    # ---------------------------------------------------------------
    if content != original:
        ENGINE_FILE.write_text(content, encoding="utf-8")
        print(f"\n💾 فایل ذخیره شد: {fixes_applied} اصلاح اعمال شد")
        return True
    else:
        print("\nℹ️ تغییری لازم نبود")
        return True


def verify_fix():
    """بررسی صحت اصلاح"""
    print("\n" + "=" * 70)
    print("بررسی صحت اصلاح")
    print("=" * 70)
    
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        
        # حذف کش ماژول
        modules_to_remove = [k for k in list(sys.modules.keys()) if 'multi_stress' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        from engine.hydroma.climate_adaptation.multi_stress_engine import (
            salinity_ph_stress
        )
        
        # تست شوری ارومیه (۳۰۰)
        result = salinity_ph_stress(ec=300, ph=9.2)
        
        print(f"\n🧪 تست شوری ارومیه (EC=300, pH=9.2):")
        print(f"   salinity_stress = {result['salinity_stress']} (باید <= 1.0)")
        print(f"   alkalinity_stress = {result['alkalinity_stress']} (باید <= 1.0)")
        print(f"   sodification_risk = {result['sodification_risk']} (باید <= 1.0)")
        print(f"   severity = {result['severity']}")
        
        # بررسی موفقیت
        success = (
            result['salinity_stress'] <= 1.0 and
            result['alkalinity_stress'] <= 1.0 and
            result['sodification_risk'] <= 1.0
        )
        
        if success:
            print("\n🎉 همه مقادیر در بازه [0, 1] هستند")
        else:
            print("\n❌ هنوز مقادیر خارج از بازه وجود دارد")
        
        return success
        
    except Exception as e:
        print(f"\n❌ خطا در بررسی: {e}")
        return False


def main():
    fixed = fix_unbounded_values()
    verified = verify_fix()
    
    print("\n" + "=" * 70)
    if fixed and verified:
        print("🎉 خطا با موفقیت رفع شد")
        print("\n📋 گام بعدی:")
        print("   python behavioral_stress_test.py")
        print("   (انتظار: 16/16 تست موفق - 100%)")
    else:
        print("⚠️ نیاز به بررسی بیشتر")
    print("=" * 70)


if __name__ == "__main__":
    main()