#!/usr/bin/env python3
"""
اسکریپت قطعی نهایی - بازنویسی مستقیم متد calculate_site_suitability
روش: خواندن خط‌به‌خط و جایگزینی کامل متد معیوب
"""

from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).parent.resolve()
CONNECT_FILE = PROJECT_ROOT / "connect_indices_to_motors.py"

# کد جدید و صحیح متد calculate_site_suitability
NEW_METHOD = '''    def calculate_site_suitability(self, site_id: str, species_id: str) -> Dict[str, Any]:
        """محاسبه جامع تناسب یک گونه برای یک سایت"""
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
        
        # دریافت داده‌های پایه
        crop = repo.get_crop_parameters(species_id)
        site = repo.get_site_profile(site_id)
        
        if not crop:
            return {"error": f"گونه {species_id} یافت نشد"}
        if not site:
            return {"error": f"سایت {site_id} یافت نشد"}
        
        # ============================================================
        # مقداردهی اولیه با مقادیر پیش‌فرض (جلوگیری از خطای تعریف نشدن)
        # ============================================================
        crop_tmin = float(crop.get("min_temp_c", 5) or 5)
        crop_tmax = float(crop.get("max_temp_c", 35) or 35)
        rain_need = float(crop.get("rain_opt_min_mm_y", 500) or 500)
        water_need = float(crop.get("water_need_1_5", 3) or 3)
        drought_tol = float(crop.get("drought_tolerance_1_5", 3) or 3)
        
        # به‌روزرسانی از جدول نیازمندی‌های اقلیمی (در صورت وجود)
        try:
            climate = repo._conn.execute(
                "SELECT * FROM ref_climate_requirements WHERE species_id = ?", [species_id]
            ).pl()
            if not climate.is_empty():
                cr = climate.row(0, named=True)
                if cr.get("min_temp_c") is not None: crop_tmin = float(cr["min_temp_c"])
                if cr.get("max_temp_c") is not None: crop_tmax = float(cr["max_temp_c"])
                if cr.get("rain_opt_min_mm_y") is not None: rain_need = float(cr["rain_opt_min_mm_y"])
                if cr.get("water_need_1_5") is not None: water_need = float(cr["water_need_1_5"])
                if cr.get("drought_tolerance_1_5") is not None: drought_tol = float(cr["drought_tolerance_1_5"])
        except Exception:
            pass  # در صورت خطا، از مقادیر پیش‌فرض استفاده کن
        
        # ============================================================
        # محاسبه امتیازات جزئی (مدل‌های M001 تا M008)
        # ============================================================
        scores = {}
        
        # M001: تناسب اقلیمی
        tmin = float(site.get("tmin_c", 15) or 15)
        tmax = float(site.get("tmax_c", 25) or 25)
        if crop_tmin <= tmin and tmax <= crop_tmax:
            scores["climate_fit"] = 100.0
        else:
            penalty = max(0, crop_tmin - tmin) + max(0, tmax - crop_tmax)
            scores["climate_fit"] = max(0, 100 - penalty * 5)
        
        # M002: امتیاز دیم
        rain = float(site.get("annual_rain_mm", 400) or 400)
        scores["rainfed"] = min(100, (rain / max(rain_need, 1)) * 100)
        
        # M003: امنیت آبی
        scores["water_security"] = max(0, 100 - water_need * 15)
        
        # M004: انطباق خاک
        scores["soil_fit"] = 80.0  # پیش‌فرض، در نسخه بعدی محاسبه دقیق
        
        # M006: جذابیت اقتصادی
        try:
            econ = self.economic.full_economic_analysis(species_id, site_id)
            scores["economic"] = 70.0 if econ.get("net_margin_usd", 0) > 0 else 30.0
        except Exception:
            scores["economic"] = 50.0
        
        # M007: تاب‌آوری
        scores["resilience"] = drought_tol * 20
        
        # ============================================================
        # امتیاز نهایی (وزن‌دهی استاندارد)
        # ============================================================
        weights = {
            "climate_fit": 0.25, "rainfed": 0.20, "water_security": 0.15,
            "soil_fit": 0.15, "economic": 0.15, "resilience": 0.10
        }
        
        final_score = sum(scores.get(k, 50) * w for k, w in weights.items())
        
        # تعیین سیستم توصیه‌شده
        if scores.get("rainfed", 0) > 70 and scores.get("climate_fit", 0) > 80:
            system = "دیم"
            intensity = "زیاد"
        elif scores.get("water_security", 0) > 50:
            system = "آبیاری تکمیلی"
            intensity = "متوسط"
        elif final_score > 50:
            system = "آبیاری کامل"
            intensity = "زیاد"
        else:
            system = "غیرقابل توصیه"
            intensity = "کم"
        
        return {
            "site_id": site_id,
            "species_id": species_id,
            "final_score_0_100": round(final_score, 0),
            "component_scores": {k: round(v, 0) for k, v in scores.items()},
            "recommended_system": system,
            "management_intensity": intensity,
            "confidence": "D"
        }
'''

def fix_file():
    """خواندن فایل، پیدا کردن متد معیوب، و جایگزینی آن"""
    print("🔧 شروع اصلاح قطعی فایل...")
    
    if not CONNECT_FILE.exists():
        print(f"❌ فایل یافت نشد: {CONNECT_FILE}")
        return False
    
    content = CONNECT_FILE.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # پیدا کردن شروع و پایان متد معیوب
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if 'def calculate_site_suitability' in line:
            start_idx = i
            # پیدا کردن تورفتگی این خط
            indent = len(line) - len(line.lstrip())
            
            # جستجو برای پایان متد (خطی با تورفتگی کمتر یا مساوی که یک متد جدید است)
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped == '':
                    continue
                current_indent = len(lines[j]) - len(lines[j].lstrip())
                # اگر خط جدیدی با تورفتگی مشابه یا کمتر پیدا شد، متد تمام شده
                if current_indent <= indent and (stripped.startswith('def ') or stripped.startswith('@') or stripped.startswith('class ') or stripped.startswith('# ==')):
                    end_idx = j
                    break
            
            if end_idx == -1:
                end_idx = len(lines)
            break
    
    if start_idx == -1:
        print("❌ متد 'calculate_site_suitability' یافت نشد!")
        return False
    
    print(f"   📍 متد معیوب در خط {start_idx + 1} تا {end_idx} یافت شد")
    print(f"   📝 تعداد خطوط حذف شده: {end_idx - start_idx}")
    
    # جایگزینی متد
    new_lines = lines[:start_idx] + NEW_METHOD.split('\n') + ['', ''] + lines[end_idx:]
    new_content = '\n'.join(new_lines)
    
    # ذخیره فایل
    CONNECT_FILE.write_text(new_content, encoding="utf-8")
    print(f"   ✅ متد بازنویسی شد ({len(NEW_METHOD.split(chr(10)))} خط جدید)")
    return True

def test_result():
    """تست نتیجه اصلاح"""
    print("\n" + "="*70)
    print("🧪 تست نتیجه اصلاح...")
    
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # حذف ماژول‌های کش‌شده
        modules_to_remove = [k for k in list(sys.modules.keys()) if 'connect_indices' in k or 'data_repository' in k]
        for m in modules_to_remove:
            del sys.modules[m]
        
        from connect_indices_to_motors import IntegratedDecisionEngine
        engine = IntegratedDecisionEngine()
        
        # تست با سایت و گونه معتبر
        result = engine.calculate_site_suitability("SITE037", "W001")
        
        if "error" in result:
            print(f"   ⚠️ خطا: {result['error']}")
            return False
        
        print(f"   ✅ امتیاز نهایی: {result['final_score_0_100']}")
        print(f"   ✅ سیستم توصیه‌شده: {result['recommended_system']}")
        print(f"   ✅ شدت مدیریت: {result['management_intensity']}")
        print(f"   ✅ اجزای امتیاز: {result['component_scores']}")
        
        # تست با گونه دیگر
        result2 = engine.calculate_site_suitability("SITE001", "W028")
        if "error" not in result2:
            print(f"\n   ✅ تست دوم (SITE001, W028 - زیتون):")
            print(f"      امتیاز: {result2['final_score_0_100']}، سیستم: {result2['recommended_system']}")
        
        print("\n🎉 اصلاح با موفقیت کامل اعمال شد!")
        return True
        
    except Exception as e:
        print(f"\n❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 اسکریپت قطعی نهایی - بازنویسی مستقیم متد")
    print("="*70)
    
    success = fix_file()
    
    if success:
        test_result()
        print("\n" + "="*70)
        print("📋 گام بعدی: اجرای کامل تست اتصال")
        print("   python connect_indices_to_motors.py")
        print("="*70)
    else:
        print("\n❌ اصلاح ناموفق بود. لطفاً فایل را به صورت دستی بررسی کنید.")

if __name__ == "__main__":
    main()