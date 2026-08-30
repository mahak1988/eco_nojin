#!/usr/bin/env python3
"""
اسکریپت اصلاح ۲ خطای باقی‌مانده در اتصال شاخص‌ها به موتورها
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.resolve()
CONNECT_FILE = PROJECT_ROOT / "connect_indices_to_motors.py"
REPO_FILE = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"

def fix_food_security_engine():
    """اصلاح موتور امنیت غذایی: get_yield_benchmark -> get_yield_benchmarks"""
    content = CONNECT_FILE.read_text(encoding="utf-8")
    
    # اصلاح نام متد
    content = content.replace(
        "benchmarks = self.repo.get_yield_benchmark(species_id)",
        "benchmarks = self.repo.get_yield_benchmarks(species_id)"
    )
    
    CONNECT_FILE.write_text(content, encoding="utf-8")
    print("   ✅ موتور امنیت غذایی اصلاح شد (get_yield_benchmarks)")

def fix_decision_engine():
    """اصلاح موتور تصمیم یکپارچه: ستون species_id در View"""
    content = CONNECT_FILE.read_text(encoding="utf-8")
    
    # اصلاح کوئری در متد calculate_site_suitability
    # مشکل: در v_crop_climate_matrix ستون id است نه species_id
    old_pattern = r'crop = repo\.get_crop_parameters\(species_id\)'
    new_code = '''crop = repo.get_crop_parameters(species_id)
        
        # اگر گونه در لایه کارشناسی نبود، از دیتابیس بخوان
        if not crop:
            df = repo._conn.execute(
                "SELECT * FROM ref_species WHERE id = ?", [species_id]
            ).pl()
            if df.is_empty():
                return {"error": f"گونه {species_id} یافت نشد"}
            crop = df.row(0, named=True)'''
    
    content = re.sub(old_pattern, new_code, content)
    
    # اصلاح کوئری آب و هوا
    old_climate = r'crop_tmin = crop\.get\("min_temp_c", 5\)'
    new_climate = '''# دریافت نیازمندی‌های اقلیمی از جدول جداگانه
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
    
    # جایگزینی بخش محاسبه امتیازات
    old_scores = '''        # محاسبه امتیازات جزئی
        scores = {}
        
        # M001: تناسب اقلیمی
        tmin = site.get("tmin_c", 15)
        tmax = site.get("tmax_c", 25)
        crop_tmin = crop.get("min_temp_c", 5)
        crop_tmax = crop.get("max_temp_c", 35)'''
    
    new_scores = '''        # محاسبه امتیازات جزئی
        scores = {}
        
        # M001: تناسب اقلیمی
        tmin = site.get("tmin_c", 15)
        tmax = site.get("tmax_c", 25)'''
    
    content = content.replace(old_scores, new_scores)
    
    # اصلاح بخش بارندگی
    old_rain = '''        # M002: امتیاز دیم
        rain = site.get("annual_rain_mm", 400)
        rain_need = crop.get("rain_opt_min_mm_y", 500)'''
    
    new_rain = '''        # M002: امتیاز دیم
        rain = site.get("annual_rain_mm", 400)'''
    
    content = content.replace(old_rain, new_rain)
    
    # اصلاح بخش آب
    old_water = '''        # M003: امنیت آبی
        water_need = crop.get("water_need_1_5", 3)'''
    
    new_water = '''        # M003: امنیت آبی'''
    
    content = content.replace(old_water, new_water)
    
    # اصلاح بخش تاب‌آوری
    old_res = '''        # M007: تاب‌آوری
        drought_tol = crop.get("drought_tolerance_1_5", 3)'''
    
    new_res = '''        # M007: تاب‌آوری'''
    
    content = content.replace(old_res, new_res)
    
    CONNECT_FILE.write_text(content, encoding="utf-8")
    print("   ✅ موتور تصمیم یکپارچه اصلاح شد (کوئری ref_climate_requirements)")

def add_missing_method_to_repo():
    """افزودن متد get_yield_benchmark به ریپازیتوری (برای سازگاری)"""
    content = REPO_FILE.read_text(encoding="utf-8")
    
    # بررسی وجود متد
    if "def get_yield_benchmark(" not in content:
        # پیدا کردن متد get_yield_benchmarks و افزودن نسخه بدون s
        marker = "    def get_yield_benchmarks(self, species_id: str) -> pl.DataFrame:"
        if marker in content:
            # متد را پیدا کن و بعد از آن یک wrapper اضافه کن
            new_method = '''
    def get_yield_benchmark(self, species_id: str) -> pl.DataFrame:
        """دریافت بنچمارک عملکرد (نام جایگزین برای سازگاری)"""
        return self.get_yield_benchmarks(species_id)
'''
            # پیدا کردن انتهای متد get_yield_benchmarks
            lines = content.split('\n')
            insert_pos = -1
            in_method = False
            
            for i, line in enumerate(lines):
                if 'def get_yield_benchmarks' in line:
                    in_method = True
                elif in_method and line.strip() and not line.startswith('        ') and not line.startswith('    def get_yield_benchmark'):
                    insert_pos = i
                    break
            
            if insert_pos > 0:
                lines.insert(insert_pos, new_method)
                content = '\n'.join(lines)
                REPO_FILE.write_text(content, encoding="utf-8")
                print("   ✅ متد get_yield_benchmark به ریپازیتوری اضافه شد")
            else:
                print("   ⚠️ امکان افزودن متد وجود نداشت")
        else:
            print("   ⚠️ متد get_yield_benchmarks یافت نشد")
    else:
        print("   ℹ️ متد get_yield_benchmark از قبل وجود دارد")

def main():
    print("🔧 شروع اصلاح ۲ خطای باقی‌مانده...")
    print("="*70)
    
    # اصلاح ۱: موتور امنیت غذایی
    fix_food_security_engine()
    
    # اصلاح ۲: موتور تصمیم یکپارچه
    fix_decision_engine()
    
    # اصلاح ۳: افزودن متد به ریپازیتوری
    add_missing_method_to_repo()
    
    # تست سریع
    print("\n" + "="*70)
    print("🧪 تست سریع...")
    
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # حذف ماژول‌های کش‌شده
        modules_to_remove = [k for k in sys.modules if 'data_repository' in k or 'connect_indices' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
        
        # تست بنچمارک عملکرد
        benchmarks = repo.get_yield_benchmarks("W001")
        print(f"   ✅ بنچمارک عملکرد: {len(benchmarks)} ردیف")
        
        # تست گونه
        crop = repo.get_crop_parameters("W001")
        if crop:
            print(f"   ✅ گونه W001: {crop.get('name_fa', 'N/A')}")
        
        # تست نیازمندی‌های اقلیمی
        climate = repo._conn.execute(
            "SELECT * FROM ref_climate_requirements WHERE species_id = ?", ["W001"]
        ).pl()
        print(f"   ✅ نیازمندی‌های اقلیمی: {len(climate)} ردیف")
        
        print("\n🎉 اصلاحات با موفقیت اعمال شد!")
        print("📋 لطفاً اسکریپت اتصال را مجدداً اجرا کنید:")
        print("   python connect_indices_to_motors.py")
        
    except Exception as e:
        print(f"\n❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()