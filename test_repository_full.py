#!/usr/bin/env python3
"""
تست جامع عملکرد تمامی متدهای ScientificDataRepository
نسخه 2.0 - بدون وابستگی به کتابخانه‌های جانبی
"""

import sys
from pathlib import Path

# افزودن ریشه پروژه به مسیر پایتون
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

def print_table(headers: list, rows: list):
    """چاپ جدول ساده بدون نیاز به کتابخانه خارجی"""
    # محاسبه عرض هر ستون
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # چاپ هدر
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)
    
    print(f"\n{header_line}")
    print(separator)
    
    # چاپ ردیف‌ها
    for row in rows:
        line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(line)
    print()

def run_full_test():
    print("🚀 شروع تست جامع مخزن داده‌های علمی...")
    print("="*70)
    
    try:
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
    except Exception as e:
        print(f"❌ خطا در ایجاد ریپازیتوری: {e}")
        return
        
    test_results = []
    
    # ==========================================
    # لیست کامل تست‌ها (۱۸ تست استراتژیک)
    # ==========================================
    tests = [
        # حوزه رشد محصول
        ("۱. پارامترهای گونه (W001)", lambda: repo.get_crop_parameters("W001")),
        ("۲. ماتریس اقلیمی گونه", lambda: repo.get_crop_climate_matrix("W001")),
        ("۳. مراحل رشد فنولوژیک", lambda: repo.get_growth_stages("W001")),
        ("۴. بنچمارک عملکرد", lambda: repo.get_yield_benchmarks("W001")),
        
        # حوزه خاک و احیای خاک
        ("۵. پروفایل خاک (Calcisol)", lambda: repo.get_soil_profile("Calcisol")),
        ("۶. تمام گروه‌های خاک", lambda: repo.get_all_soil_groups()),
        ("۷. پروتکل‌های احیای خاک", lambda: repo.get_soil_restoration_protocols()),
        
        # حوزه کود زیستی و شیمیایی
        ("۸. پروفایل کود (F001)", lambda: repo.get_fertilizer_profile("FRT001")),
        ("۹. ماتریس سازگاری کودها", lambda: repo.get_fertilizer_compatibility_matrix()),
        ("۱۰. توصیه کود زیستی", lambda: repo.get_biofertilizer_recommendations("Calcisol", "زراعی")),
        
        # حوزه آب و دشت‌های بحرانی
        ("۱۱. تاریخچه اقلیمی سایت", lambda: repo.get_site_climate_history("SITE037")),
        ("۱۲. داده‌های روزانه هواشناسی", lambda: repo.get_weather_daily("SITE076")),
        ("۱۳. قوانین دشت بحرانی", lambda: repo.get_critical_plain_rules()),
        ("۱۴. محاسبه شاخص SPI", lambda: repo.calculate_spi_index("SITE076", 3)),
        
        # حوزه آفات (IPM)
        ("۱۵. آفات محصول گندم", lambda: repo.get_pests_for_crop("W001")),
        
        # حوزه سایت و تصمیم‌گیری
        ("۱۶. پروفایل سایت (SITE037)", lambda: repo.get_site_profile("SITE037")),
        ("۱۷. ماتریس تصمیم‌گیری", lambda: repo.get_decision_engine_matrix("SITE037")),
        ("۱۸. سایت‌های بحرانی", lambda: repo.get_sites_in_critical_plains()),
    ]
    
    # ==========================================
    # اجرای تست‌ها و جمع‌آوری نتایج
    # ==========================================
    for test_name, test_func in tests:
        try:
            result = test_func()
            
            # تحلیل نوع نتیجه
            if result is None:
                status = "⚠️ خالی"
                detail = "داده‌ای یافت نشد"
            elif hasattr(result, 'is_empty'):  # Polars DataFrame
                row_count = len(result)
                status = "✅ موفق" if row_count > 0 else "⚠️ خالی"
                detail = f"{row_count} ردیف"
            elif isinstance(result, dict):
                status = "✅ موفق" if result else "⚠️ خالی"
                detail = f"{len(result)} فیلد"
            else:
                status = "✅ موفق"
                detail = str(type(result).__name__)
                
            test_results.append([test_name, status, detail])
            
        except Exception as e:
            error_msg = str(e).split('\n')[0][:60]
            test_results.append([test_name, "❌ خطا", error_msg])
    
    # ==========================================
    # چاپ نتایج در قالب جدول
    # ==========================================
    print_table(["نام تست", "وضعیت", "جزئیات"], test_results)
    
    # ==========================================
    # خلاصه آماری نتایج
    # ==========================================
    success_count = sum(1 for r in test_results if "✅" in r[1])
    warning_count = sum(1 for r in test_results if "⚠️" in r[1])
    error_count = sum(1 for r in test_results if "❌" in r[1])
    
    print("="*70)
    print("📊 خلاصه آماری تست جامع:")
    print(f"   ✅ موفق:            {success_count} تست")
    print(f"   ⚠️ هشدار (خالی):    {warning_count} تست")
    print(f"   ❌ خطا:             {error_count} تست")
    print(f"   📈 درصد موفقیت:     {(success_count/len(test_results)*100):.1f}%")
    print("="*70)
    
    if error_count == 0:
        print("\n🎉 تمام تست‌ها با موفقیت پاس شدند!")
        print("💡 ریپازیتوری آماده اتصال به موتورهای علمی است.")
        print("\n🚀 گام بعدی پیشنهادی:")
        print("   بازنویسی فایل crop_database.py (۸۲۰ خط) برای استفاده از این ریپازیتوری.")
    else:
        print("\n⚠️ برخی متدها خطا دارند. لطفاً جدول بالا را بررسی کنید.")
        
    # ==========================================
    # نمایش نمونه‌ای از داده‌های واقعی
    # ==========================================
    print("\n" + "="*70)
    print("🔬 نمونه‌ای از داده‌های واقعی بازیابی شده:")
    print("="*70)
    
    try:
        # نمونه ۱: پارامترهای گندم دوروم
        crop = repo.get_crop_parameters("W001")
        if crop:
            print("\n📌 گونه: گندم دوروم (Triticum durum)")
            print(f"   🌡️ محدوده دمایی مطلوب: {crop.get('opt_temp_min_c', '?')}°C تا {crop.get('opt_temp_max_c', '?')}°C")
            print(f"   💧 تحمل خشکی: {crop.get('drought_tolerance_1_5', '?')} از ۵")
            print(f"   🌧️ نیاز بارش: {crop.get('rain_opt_min_mm_y', '?')} تا {crop.get('rain_max_mm_y', '?')} میلی‌متر")
    except Exception as e:
        print(f"   ⚠️ خطا در نمایش نمونه گونه: {e}")
    
    try:
        # نمونه ۲: گروه‌های خاک
        soils = repo.get_all_soil_groups()
        if len(soils) > 0:
            print(f"\n📌 گروه‌های خاک موجود در دیتابیس ({len(soils)} گروه):")
            print("   " + "، ".join(soils["WRB_group"].to_list()[:8]))
    except Exception as e:
        print(f"   ⚠️ خطا در نمایش نمونه خاک: {e}")

if __name__ == "__main__":
    run_full_test()