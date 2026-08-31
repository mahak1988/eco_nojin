#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
رفع خطای ناسازگاری نام متغیر در multi_stress_engine.py
============================================================================
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE_FILE = ROOT / "engine" / "hydroma" / "climate_adaptation" / "multi_stress_engine.py"


def fix_variable_names():
    """رفع ناسازگاری نام متغیرها"""
    
    print("=" * 70)
    print("رفع خطای ناسازگاری نام متغیر در multi_stress_engine.py")
    print("=" * 70)
    
    if not ENGINE_FILE.exists():
        print(f"\n❌ فایل یافت نشد: {ENGINE_FILE}")
        return False
    
    content = ENGINE_FILE.read_text(encoding="utf-8")
    original_content = content
    
    # رفع خطای اصلی: amplified_stress -> amplified
    if "amplified_stress" in content:
        # بررسی اینکه آیا متغیر به نام 'amplified' تعریف شده است
        if "amplified = min(1.0, combined * 1.5)" in content:
            # متغیر به نام 'amplified' تعریف شده، پس باید در همجا از آن استفاده شود
            content = content.replace('"severity": _severity(amplified_stress),',
                                      '"severity": _severity(amplified),')
            print("\n✅ خطای 'amplified_stress' به 'amplified' اصلاح شد")
        else:
            # متغیر به نام دیگری تعریف شده، بررسی می‌کنیم
            print("\n⚠️ متغیر 'amplified' یافت نشد، بررسی دقیق‌تر لازم است")
    else:
        print("\nℹ️ خطای 'amplified_stress' در فایل وجود ندارد")
    
    # بررسی سایر مشکلات احتمالی
    issues_found = []
    
    # بررسی تابع‌های تعریف‌نشده
    required_functions = ["_severity", "drought_heat_salinity_stress", 
                          "flood_slope_stress", "frost_wind_stress", 
                          "salinity_ph_stress"]
    for func in required_functions:
        if f"def {func}" not in content:
            issues_found.append(f"تابع {func} تعریف نشده است")
    
    # بررسی متغیرهای استفاده‌شده اما تعریف‌نشده
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # بررسی استفاده از متغیرهایی که ممکن است تعریف نشده باشند
        if "_severity(" in line:
            # استخراج نام متغیر داخل پرانتز
            start = line.find("_severity(") + len("_severity(")
            end = line.find(")", start)
            if end > start:
                var_name = line[start:end].strip()
                if var_name and var_name not in ["combined", "amplified", 
                                                   "effective_frost", "max(salinity_stress, sodification_risk)"]:
                    # بررسی اینکه آیا این متغیر در خطوط قبلی تعریف شده است
                    defined = False
                    for prev_line in lines[:i-1]:
                        if f"{var_name} =" in prev_line or f"{var_name}=" in prev_line:
                            defined = True
                            break
                    if not defined and not var_name.startswith("("):
                        issues_found.append(f"خط {i}: متغیر '{var_name}' ممکن است تعریف نشده باشد")
    
    if issues_found:
        print("\n⚠️ مشکلات احتمالی یافت شد:")
        for issue in issues_found:
            print(f"   - {issue}")
    else:
        print("\n✅ مشکل دیگری یافت نشد")
    
    # ذخیره فایل اصلاح‌شده
    if content != original_content:
        ENGINE_FILE.write_text(content, encoding="utf-8")
        print(f"\n💾 فایل اصلاح‌شده ذخیره شد: {ENGINE_FILE}")
        return True
    else:
        print("\nℹ️ تغییری در فایل اعمال نشد")
        return False


def verify_fix():
    """بررسی صحت اصلاح"""
    print("\n" + "=" * 70)
    print("بررسی صحت اصلاح")
    print("=" * 70)
    
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        
        # تلاش برای وارد کردن ماژول
        from engine.hydroma.climate_adaptation.multi_stress_engine import (
            drought_heat_salinity_stress,
            flood_slope_stress,
            frost_wind_stress,
            salinity_ph_stress
        )
        print("\n✅ ماژول با موفقیت وارد شد")
        
        # تست تابع‌ها
        print("\n🧪 تست تابع‌ها:")
        
        # تست ۱: خشکسالی+گرما+شوری
        result = drought_heat_salinity_stress(temp=45, rain=5, ec=30)
        print(f"   ✅ خشکسالی+گرما+شوری: {result['severity']} (استرس: {result['combined_stress']})")
        
        # تست ۲: سیل+شیب
        result = flood_slope_stress(rain=5000, slope=60)
        print(f"   ✅ سیل+شیب: {result['severity']} (استرس: {result['combined_stress']})")
        
        # تست ۳: یخبندان+باد
        result = frost_wind_stress(temp=-40, wind=100)
        print(f"   ✅ یخبندان+باد: {result['severity']} (سرمای موثر: {result['effective_frost_stress']})")
        
        # تست ۴: شوری+قلیائیت
        result = salinity_ph_stress(ec=50, ph=11)
        print(f"   ✅ شوری+قلیائیت: {result['severity']} (ریسک سدیمی: {result['sodification_risk']})")
        
        print("\n🎉 همه تابع‌ها به درستی کار می‌کنند")
        return True
        
    except Exception as e:
        print(f"\n❌ خطا در بررسی: {e}")
        return False


def main():
    fixed = fix_variable_names()
    verified = verify_fix()
    
    print("\n" + "=" * 70)
    if fixed and verified:
        print("🎉 خطا با موفقیت رفع شد")
        print("\n📋 گام بعدی:")
        print("   python behavioral_stress_test.py")
    elif verified:
        print("✅ ماژول به درستی کار می‌کند")
        print("\n📋 گام بعدی:")
        print("   python behavioral_stress_test.py")
    else:
        print("⚠️ نیاز به بررسی بیشتر")
    print("=" * 70)


if __name__ == "__main__":
    main()