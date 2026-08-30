#!/usr/bin/env python3
"""
اسکریپت پچ نهایی نسخه ۲ - اصلاح ۲ مشکل باقی‌مانده
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET_FILE = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"

def apply_final_patch_v2():
    print("🔧 شروع اعمال پچ نهایی نسخه ۲...")
    print("="*70)
    
    if not TARGET_FILE.exists():
        print(f"❌ فایل ریپازیتوری یافت نشد: {TARGET_FILE}")
        return
    
    content = TARGET_FILE.read_text(encoding="utf-8")
    original_content = content
    
    # ==========================================
    # پچ ۱: اصلاح متد get_fertilizer_profile
    # خطا: ۳ پارامتر ? ولی فقط ۲ مقدار ارسال می‌شود
    # ==========================================
    
    # جستجوی الگوی معیوب
    old_fert_pattern = r'''    @lru_cache\(maxsize=128\)
    def get_fertilizer_profile\(self, fertilizer_query: str\) -> Optional\[Dict\[str, Any\]\]:
        """دریافت مشخصات کامل یک کود"""
        query = """
            SELECT \* FROM ref_fertilizers
            WHERE fert_id = \? OR material ILIKE \? OR type ILIKE \?
        """
        df = self\._conn\.execute\(
            query, 
            \[fertilizer_query, f"%\{fertilizer_query\}%"\]
        \)\.pl\(\)
        return df\.row\(0, named=True\) if not df\.is_empty\(\) else None'''
    
    new_fert_method = '''    @lru_cache(maxsize=128)
    def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:
        """دریافت مشخصات کامل یک کود"""
        query = """
            SELECT * FROM ref_fertilizers
            WHERE fert_id = ? OR material ILIKE ? OR type ILIKE ?
        """
        df = self._conn.execute(
            query, 
            [fertilizer_query, f"%{fertilizer_query}%", f"%{fertilizer_query}%"]
        ).pl()
        return df.row(0, named=True) if not df.is_empty() else None'''
    
    # جستجوی ساده‌تر (بدون الگوی پیچیده)
    if 'WHERE fert_id = ? OR material ILIKE ? OR type ILIKE ?' in content:
        # پیدا کردن بخش مربوطه و اصلاح پارامترها
        lines = content.split('\n')
        new_lines = []
        in_fert_method = False
        
        for i, line in enumerate(lines):
            if 'def get_fertilizer_profile' in line:
                in_fert_method = True
            
            if in_fert_method and 'fertilizer_query, f"%{fertilizer_query}%"])' in line:
                # اصلاح خط پارامترها
                line = line.replace(
                    '[fertilizer_query, f"%{fertilizer_query}%"])',
                    '[fertilizer_query, f"%{fertilizer_query}%", f"%{fertilizer_query}%"])'
                )
                in_fert_method = False
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        print("   ✅ متد 'get_fertilizer_profile' اصلاح شد (۳ پارامتر).")
    
    # ==========================================
    # پچ ۲: اصلاح تست ماتریس تصمیم‌گیری
    # مشکل: SITE076 در ماتریس تصمیم نیست
    # ==========================================
    
    # تغییر سایت تست از SITE076 به SITE037
    content = content.replace('"SITE076"', '"SITE037"')
    content = content.replace("'SITE076'", "'SITE037'")
    print("   ✅ سایت تست ماتریس تصمیم به SITE037 تغییر یافت.")
    
    # ==========================================
    # پچ ۳: بهبود متد get_decision_engine_matrix
    # ==========================================
    
    # اگر متد هنوز از ستون اشتباهی استفاده می‌کند، اصلاح کن
    if 'ORDER BY suitability_0_100 DESC, final_score_0_100 DESC' not in content:
        old_decision = '''    def get_decision_engine_matrix(self, site_id: str) -> pl.DataFrame:
        """دریافت ماتریس تصمیم‌گیری برای یک سایت"""
        query = f"""
            SELECT * FROM ref_decision_engine
            WHERE site_id = ?
            ORDER BY {{self.DECISION_SCORE_COL}} DESC
        """
        return self._conn.execute(query, [site_id]).pl()'''
        
        new_decision = '''    def get_decision_engine_matrix(self, site_id: str) -> pl.DataFrame:
        """دریافت ماتریس تصمیم‌گیری برای یک سایت"""
        query = """
            SELECT * FROM ref_decision_engine
            WHERE site_id = ?
            ORDER BY suitability_0_100 DESC, final_score_0_100 DESC
        """
        return self._conn.execute(query, [site_id]).pl()'''
        
        if old_decision in content:
            content = content.replace(old_decision, new_decision)
            print("   ✅ متد 'get_decision_engine_matrix' اصلاح شد.")
    
    # ذخیره فایل
    if content != original_content:
        TARGET_FILE.write_text(content, encoding="utf-8")
        print(f"\n✅ پچ نهایی نسخه ۲ با موفقیت اعمال شد.")
    else:
        print("\n⚠️ هیچ تغییری لازم نبود.")
    
    # ==========================================
    # تست سریع نهایی
    # ==========================================
    print("\n" + "="*70)
    print("🧪 تست سریع نهایی...")
    print("="*70)
    
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # بارگذاری مجدد ماژول
        import importlib
        if 'services.scientific_motors.data_repository' in sys.modules:
            del sys.modules['services.scientific_motors.data_repository']
        
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
        
        # تست کود
        fert = repo.get_fertilizer_profile("FRT001")
        if fert:
            print(f"   ✅ کود FRT001: {fert.get('material', 'N/A')} ({fert.get('type', 'N/A')})")
        else:
            # تلاش با نام
            fert2 = repo.get_fertilizer_profile("اوره")
            if fert2:
                print(f"   ✅ کود 'اوره': {fert2.get('material', 'N/A')}")
            else:
                print(f"   ⚠️ کود یافت نشد")
        
        # تست ماتریس تصمیم
        sites = repo.get_all_decision_sites()
        if not sites.is_empty():
            sample_site = sites["site_id"][0]
            matrix = repo.get_decision_engine_matrix(sample_site)
            print(f"   ✅ ماتریس تصمیم ({sample_site}): {len(matrix)} رکورد")
        
        # تست قوانین
        rules = repo.get_critical_plain_rules()
        print(f"   ✅ قوانین بحرانی: {len(rules)} رکورد")
        
        print("\n🎉 پچ نهایی نسخه ۲ با موفقیت اعمال شد!")
        print("📋 گام بعدی: لطفاً تست جامع را اجرا کنید:")
        print("   python test_repository_full.py")
        
    except Exception as e:
        print(f"\n❌ خطا در تست سریع: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_final_patch_v2()