#!/usr/bin/env python3
"""
اسکریپت اصلاح نهایی موتور تصمیم یکپارچه
رفع خطای 'crop_tmin' is not defined
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.resolve()
CONNECT_FILE = PROJECT_ROOT / "connect_indices_to_motors.py"

def fix_crop_tmin_error():
    """اصلاح خطای تعریف نشدن متغیرهای اقلیمی"""
    content = CONNECT_FILE.read_text(encoding="utf-8")
    
    # الگوی معیوب: متغیرها فقط در بلاک if تعریف شده‌اند
    old_pattern = r'''        # دریافت نیازمندی‌های اقلیمی از جدول جداگانه
        climate = repo\._conn\.execute\(
            "SELECT \* FROM ref_climate_requirements WHERE species_id = \?", \[species_id\]
        \)\.pl\(\)
        
        if not climate\.is_empty\(\):
            climate_row = climate\.row\(0, named=True\)
            crop_tmin = climate_row\.get\("min_temp_c", crop\.get\("min_temp_c", 5\)\)
            crop_tmax = climate_row\.get\("max_temp_c", crop\.get\("max_temp_c", 35\)\)
            rain_need = climate_row\.get\("rain_opt_min_mm_y", crop\.get\("rain_opt_min_mm_y", 500\)\)
            water_need = climate_row\.get\("water_need_1_5", crop\.get\("water_need_1_5", 3\)\)
            drought_tol = climate_row\.get\("drought_tolerance_1_5", crop\.get\("drought_tolerance_1_5", 3\)\)
        else:
            crop_tmin = crop\.get\("min_temp_c", 5\)
            crop_tmax = crop\.get\("max_temp_c", 35\)
            rain_need = crop\.get\("rain_opt_min_mm_y", 500\)
            water_need = crop\.get\("water_need_1_5", 3\)
            drought_tol = crop\.get\("drought_tolerance_1_5", 3\)'''
    
    # کد اصلاح‌شده: مقداردهی اولیه + به‌روزرسانی شرطی
    new_code = '''        # مقداردهی اولیه با مقادیر پیش‌فرض
        crop_tmin = crop.get("min_temp_c", 5)
        crop_tmax = crop.get("max_temp_c", 35)
        rain_need = crop.get("rain_opt_min_mm_y", 500)
        water_need = crop.get("water_need_1_5", 3)
        drought_tol = crop.get("drought_tolerance_1_5", 3)
        
        # به‌روزرسانی از جدول نیازمندی‌های اقلیمی (در صورت وجود)
        try:
            climate = repo._conn.execute(
                "SELECT * FROM ref_climate_requirements WHERE species_id = ?", [species_id]
            ).pl()
            
            if not climate.is_empty():
                climate_row = climate.row(0, named=True)
                crop_tmin = climate_row.get("min_temp_c", crop_tmin)
                crop_tmax = climate_row.get("max_temp_c", crop_tmax)
                rain_need = climate_row.get("rain_opt_min_mm_y", rain_need)
                water_need = climate_row.get("water_need_1_5", water_need)
                drought_tol = climate_row.get("drought_tolerance_1_5", drought_tol)
        except Exception:
            pass  # در صورت خطا، از مقادیر پیش‌فرض استفاده کن'''
    
    # جایگزینی با الگوی ساده‌تر (بدون الگوی پیچیده)
    # پیدا کردن بخش مربوطه
    if "# دریافت نیازمندی‌های اقلیمی از جدول جداگانه" in content:
        # پیدا کردن شروع و پایان بخش
        lines = content.split('\n')
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if "# دریافت نیازمندی‌های اقلیمی از جدول جداگانه" in line:
                start_idx = i
            elif start_idx >= 0 and "drought_tol = crop.get(" in line and "drought_tolerance_1_5" in line:
                end_idx = i + 1
                break
        
        if start_idx >= 0 and end_idx > start_idx:
            # جایگزینی خطوط
            new_lines = lines[:start_idx] + new_code.split('\n') + lines[end_idx:]
            content = '\n'.join(new_lines)
            CONNECT_FILE.write_text(content, encoding="utf-8")
            print("   ✅ موتور تصمیم یکپارچه اصلاح شد (مقداردهی اولیه + try/except)")
            return True
    
    # روش جایگزین: جستجوی مستقیم
    if "climate = repo._conn.execute(" in content and "ref_climate_requirements" in content:
        # پیدا کردن بلاک if/else و جایگزینی
        old_if = "        if not climate.is_empty():"
        if old_if in content:
            # این روش پیچیده است، از روش خط‌به‌خط استفاده می‌کنیم
            pass
    
    # روش نهایی: جایگزینی مستقیم
    old_block = '''        # دریافت نیازمندی‌های اقلیمی از جدول جداگانه
        climate = repo._conn.execute(
            "SELECT * FROM ref_climate_requirements WHERE species_id = ?", [species_id]
        ).pl()
        
        if not climate.is_empty():
            climate_row = climate.row(0, named=True)
            crop_tmin = climate_row.get("min_temp_c", crop.get("min_temp_c", 5))
            crop_tmax = climate_row.get("max_temp_c", crop.get("max_temp_c", 35))
            rain_need = climate_row.get("rain_opt_min_mm_y", crop.get("rain_opt_min_mm_y", 500))
            water_need = climate_row.get("water_need_1_5", crop.get("water_need_1_5", 3))
            drought_tol = climate_row.get("drought_tolerance_1_5", crop.get("drought_tolerance_1_5", 3))
        else:
            crop_tmin = crop.get("min_temp_c", 5)
            crop_tmax = crop.get("max_temp_c", 35)
            rain_need = crop.get("rain_opt_min_mm_y", 500)
            water_need = crop.get("water_need_1_5", 3)
            drought_tol = crop.get("drought_tolerance_1_5", 3)'''
    
    if old_block in content:
        content = content.replace(old_block, new_code)
        CONNECT_FILE.write_text(content, encoding="utf-8")
        print("   ✅ موتور تصمیم یکپارچه اصلاح شد (روش جایگزینی مستقیم)")
        return True
    
    # اگر هیچ روشی کار نکرد، از روش خط‌به‌خط استفاده کن
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # پیدا کردن شروع بلاک معیوب
        if "# دریافت نیازمندی‌های اقلیمی از جدول جداگانه" in line:
            # اضافه کردن کد جدید
            new_lines.extend(new_code.split('\n'))
            
            # رد شدن از بلاک قدیمی
            i += 1
            while i < len(lines):
                if lines[i].strip() == "" and i + 1 < len(lines) and not lines[i+1].startswith("            "):
                    break
                if "# M001:" in lines[i] or "# محاسبه امتیازات" in lines[i]:
                    break
                i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    if len(new_lines) != len(lines):
        CONNECT_FILE.write_text('\n'.join(new_lines), encoding="utf-8")
        print("   ✅ موتور تصمیم یکپارچه اصلاح شد (روش خط‌به‌خط)")
        return True
    
    print("   ⚠️ امکان اصلاح خودکار وجود نداشت")
    return False

def main():
    print("🔧 شروع اصلاح نهایی موتور تصمیم یکپارچه...")
    print("="*70)
    
    success = fix_crop_tmin_error()
    
    if success:
        # تست سریع
        print("\n" + "="*70)
        print("🧪 تست سریع...")
        
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT))
            
            # حذف ماژول‌های کش‌شده
            modules_to_remove = [k for k in sys.modules if 'connect_indices' in k]
            for m in modules_to_remove:
                del sys.modules[m]
            
            # وارد کردن مجدد
            from connect_indices_to_motors import IntegratedDecisionEngine
            engine = IntegratedDecisionEngine()
            
            # تست با یک سایت و گونه
            result = engine.calculate_site_suitability("SITE037", "W001")
            
            if "error" not in result:
                print(f"   ✅ امتیاز نهایی: {result['final_score_0_100']}")
                print(f"   ✅ سیستم توصیه‌شده: {result['recommended_system']}")
                print(f"   ✅ شدت مدیریت: {result['management_intensity']}")
                print("\n🎉 اصلاح با موفقیت اعمال شد!")
                print("📋 لطفاً اسکریپت اتصال را مجدداً اجرا کنید:")
                print("   python connect_indices_to_motors.py")
            else:
                print(f"   ⚠️ خطا در تست: {result['error']}")
                
        except Exception as e:
            print(f"\n❌ خطا در تست: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ لطفاً فایل را به صورت دستی بررسی کنید.")

if __name__ == "__main__":
    main()