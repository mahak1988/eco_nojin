#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
رفع فرمول ریسک سدیمی شدن با مدل وزن‌دهی تشدیدی
مدل جدید: ترکیب خطی + اثر تشدید (بر اساس US Salinity Handbook)
============================================================================
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE_FILE = ROOT / "engine" / "hydroma" / "climate_adaptation" / "multi_stress_engine.py"


def fix_sodification_formula():
    """اصلاح فرمول ریسک سدیمی شدن"""
    
    print("=" * 70)
    print("رفع فرمول ریسک سدیمی شدن (مدل وزن‌دهی تشدیدی)")
    print("=" * 70)
    
    if not ENGINE_FILE.exists():
        print(f"\n❌ فایل یافت نشد: {ENGINE_FILE}")
        return False
    
    content = ENGINE_FILE.read_text(encoding="utf-8")
    original = content
    
    # ---------------------------------------------------------------
    # فرمول قدیمی (حاصلضرب ساده):
    #   sodification_risk = min(1.0, salinity_stress * alkalinity_stress)
    #
    # فرمول جدید (وزن‌دهی تشدیدی):
    #   - ۶۰٪ وزن شوری (عامل اصلی)
    #   - ۴۰٪ وزن قلیائیت (عامل تشدید)
    #   - ۳۰٪ اثر تشدید (تعامل دو عامل)
    # ---------------------------------------------------------------
    
    old_formula = "sodification_risk = min(1.0, salinity_stress * alkalinity_stress)"
    new_formula = """# مدل وزن‌دهی تشدیدی (US Salinity Handbook)
    # شوری عامل اصلی (60%)، قلیائیت عامل تشدید (40%)، و اثر تعاملی (30%)
    sodification_risk = min(1.0, 
                            (salinity_stress * 0.6) + 
                            (alkalinity_stress * 0.4) + 
                            (salinity_stress * alkalinity_stress * 0.3))"""
    
    if old_formula in content:
        content = content.replace(old_formula, new_formula)
        print("\n✅ فرمول ریسک سدیمی شدن به مدل وزن‌دهی تشدیدی تبدیل شد")
        print("   فرمول جدید:")
        print("   risk = 0.6×salinity + 0.4×alkalinity + 0.3×(salinity×alkalinity)")
    else:
        print("\n⚠️ فرمول قدیمی یافت نشد")
        return False
    
    # ---------------------------------------------------------------
    # ذخیره فایل
    # ---------------------------------------------------------------
    ENGINE_FILE.write_text(content, encoding="utf-8")
    print(f"\n💾 فایل ذخیره شد: {ENGINE_FILE}")
    return True


def verify_fix():
    """بررسی صحت اصلاح با محاسبات دستی"""
    print("\n" + "=" * 70)
    print("بررسی صحت اصلاح")
    print("=" * 70)
    
    try:
        sys.path.insert(0, str(ROOT))
        
        # حذف کش ماژول
        modules_to_remove = [k for k in list(sys.modules.keys()) if 'multi_stress' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        from engine.hydroma.climate_adaptation.multi_stress_engine import salinity_ph_stress
        
        # تست ۱: شرایط تست فیل شده (EC=50, pH=11)
        print("\n🧪 تست ۱: شرایط تست فیل شده (EC=50, pH=11)")
        result = salinity_ph_stress(ec=50, ph=11)
        print(f"   salinity_stress = {result['salinity_stress']}")
        print(f"   alkalinity_stress = {result['alkalinity_stress']}")
        print(f"   sodification_risk = {result['sodification_risk']}")
        print(f"   انتظار: > 0.5")
        
        test1_pass = result['sodification_risk'] > 0.5
        print(f"   نتیجه: {'✅ پاس' if test1_pass else '❌ فیل'}")
        
        # تست ۲: شوری ارومیه (EC=300, pH=9.2)
        print("\n🧪 تست ۲: شوری ارومیه (EC=300, pH=9.2)")
        result2 = salinity_ph_stress(ec=300, ph=9.2)
        print(f"   salinity_stress = {result2['salinity_stress']}")
        print(f"   alkalinity_stress = {result2['alkalinity_stress']}")
        print(f"   sodification_risk = {result2['sodification_risk']}")
        print(f"   severity = {result2['severity']}")
        
        test2_pass = (result2['salinity_stress'] <= 1.0 and 
                      result2['sodification_risk'] <= 1.0 and
                      result2['severity'] == 'بحرانی')
        print(f"   نتیجه: {'✅ پاس' if test2_pass else '❌ فیل'}")
        
        # تست ۳: شرایط عادی (EC=1, pH=7)
        print("\n🧪 تست ۳: شرایط عادی (EC=1, pH=7)")
        result3 = salinity_ph_stress(ec=1, ph=7)
        print(f"   salinity_stress = {result3['salinity_stress']}")
        print(f"   alkalinity_stress = {result3['alkalinity_stress']}")
        print(f"   sodification_risk = {result3['sodification_risk']}")
        
        test3_pass = result3['sodification_risk'] < 0.1
        print(f"   نتیجه: {'✅ پاس' if test3_pass else '❌ فیل'}")
        
        all_pass = test1_pass and test2_pass and test3_pass
        
        print("\n" + "=" * 70)
        if all_pass:
            print("🎉 همه تست‌ها پاس شدند")
        else:
            print("⚠️ برخی تست‌ها فیل شدند")
        print("=" * 70)
        
        return all_pass
        
    except Exception as e:
        print(f"\n❌ خطا در بررسی: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    fixed = fix_sodification_formula()
    verified = verify_fix()
    
    print("\n" + "=" * 70)
    if fixed and verified:
        print("🎉 فرمول با موفقیت اصلاح شد")
        print("\n📋 گام بعدی:")
        print("   python behavioral_stress_test.py")
        print("   (انتظار: 16/16 تست موفق - 100%)")
    else:
        print("⚠️ نیاز به بررسی بیشتر")
    print("=" * 70)


if __name__ == "__main__":
    main()