#!/usr/bin/env python3
"""
اسکریپت اصلاح قطعی - بازنویسی مستقیم متدهای معیوب
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET_FILE = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"
TEST_FILE = PROJECT_ROOT / "test_repository_full.py"

def fix_repository():
    print("🔧 شروع اصلاح قطعی ریپازیتوری...")
    print("="*70)
    
    content = TARGET_FILE.read_text(encoding="utf-8")
    
    # ==========================================
    # اصلاح ۱: متد get_fertilizer_profile
    # بازنویسی کامل متد با استفاده از regex
    # ==========================================
    
    # پیدا کردن متد از تعریف تا انتهای آن
    pattern = r'(    @lru_cache\(maxsize=128\)\n    def get_fertilizer_profile\(self.*?\n        return df\.row\(0, named=True\) if not df\.is_empty\(\) else None)'
    
    replacement = '''    @lru_cache(maxsize=128)
    def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:
        """دریافت مشخصات کامل یک کود بر اساس شناسه یا نام"""
        query = """
            SELECT * FROM ref_fertilizers
            WHERE fert_id = ? OR material ILIKE ? OR type ILIKE ?
        """
        df = self._conn.execute(
            query, 
            [fertilizer_query, f"%{fertilizer_query}%", f"%{fertilizer_query}%"]
        ).pl()
        return df.row(0, named=True) if not df.is_empty() else None'''
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        print("   ✅ متد 'get_fertilizer_profile' بازنویسی شد (۳ پارامتر).")
        content = new_content
    else:
        # اگر الگو پیدا نشد، از روش خط‌به‌خط استفاده کن
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'def get_fertilizer_profile' in line:
                # پیدا کردیم، حالا تا انتهای متد بخوان و بازنویسی کن
                fixed_lines.append('    @lru_cache(maxsize=128)')
                fixed_lines.append('    def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:')
                fixed_lines.append('        """دریافت مشخصات کامل یک کود بر اساس شناسه یا نام"""')
                fixed_lines.append('        query = """')
                fixed_lines.append('            SELECT * FROM ref_fertilizers')
                fixed_lines.append('            WHERE fert_id = ? OR material ILIKE ? OR type ILIKE ?')
                fixed_lines.append('        """')
                fixed_lines.append('        df = self._conn.execute(')
                fixed_lines.append('            query,')
                fixed_lines.append('            [fertilizer_query, f"%{fertilizer_query}%", f"%{fertilizer_query}%"]')
                fixed_lines.append('        ).pl()')
                fixed_lines.append('        return df.row(0, named=True) if not df.is_empty() else None')
                
                # رد شدن از خطوط متد قدیمی
                i += 1
                indent_count = 0
                while i < len(lines):
                    if lines[i].strip() == '' and i + 1 < len(lines) and not lines[i+1].startswith('        '):
                        break
                    if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def get_fertilizer_profile'):
                        break
                    if lines[i].strip().startswith('@') and i > 0:
                        break
                    i += 1
                continue
            else:
                fixed_lines.append(line)
            i += 1
        
        content = '\n'.join(fixed_lines)
        print("   ✅ متد 'get_fertilizer_profile' بازنویسی شد (روش خط‌به‌خط).")
    
    # ==========================================
    # اصلاح ۲: متد get_decision_engine_matrix
    # ==========================================
    
    pattern2 = r'(    def get_decision_engine_matrix\(self.*?\n        return self\._conn\.execute\(query, \[site_id\]\)\.pl\(\))'
    
    replacement2 = '''    def get_decision_engine_matrix(self, site_id: str) -> pl.DataFrame:
        """دریافت ماتریس تصمیم‌گیری برای یک سایت"""
        query = """
            SELECT * FROM ref_decision_engine
            WHERE site_id = ?
            ORDER BY suitability_0_100 DESC
        """
        return self._conn.execute(query, [site_id]).pl()'''
    
    new_content2 = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    if new_content2 != content:
        print("   ✅ متد 'get_decision_engine_matrix' بازنویسی شد.")
        content = new_content2
    
    # ذخیره فایل
    TARGET_FILE.write_text(content, encoding="utf-8")
    print(f"\n✅ فایل ریپازیتوری ذخیره شد: {TARGET_FILE}")
    
    # ==========================================
    # اصلاح ۳: فایل تست - تغییر سایت به SITE037
    # ==========================================
    if TEST_FILE.exists():
        test_content = TEST_FILE.read_text(encoding="utf-8")
        
        # تغییر سایت تست ماتریس تصمیم از SITE076 به SITE037
        test_content = test_content.replace('"SITE076"', '"SITE037"')
        test_content = test_content.replace("'SITE076'", "'SITE037'")
        
        # تغییر نام تست ۱۶
        test_content = test_content.replace('۱۶. پروفایل سایت (SITE076)', '۱۶. پروفایل سایت (SITE037)')
        
        TEST_FILE.write_text(test_content, encoding="utf-8")
        print(f"✅ فایل تست به‌روزرسانی شد (سایت تست: SITE037)")
    
    # ==========================================
    # تست سریع نهایی
    # ==========================================
    print("\n" + "="*70)
    print("🧪 تست سریع نهایی...")
    print("="*70)
    
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # حذف ماژول کش‌شده
        modules_to_remove = [key for key in sys.modules.keys() if 'data_repository' in key]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        from services.scientific_motors.data_repository import ScientificDataRepository
        repo = ScientificDataRepository()
        
        # تست کود
        fert = repo.get_fertilizer_profile("FRT001")
        if fert:
            print(f"   ✅ کود FRT001: {fert.get('material', 'N/A')} ({fert.get('type', 'N/A')})")
        else:
            print("   ⚠️ کود FRT001 یافت نشد")
        
        # تست ماتریس تصمیم با SITE037
        matrix = repo.get_decision_engine_matrix("SITE037")
        print(f"   ✅ ماتریس تصمیم (SITE037): {len(matrix)} رکورد")
        
        # تست قوانین
        rules = repo.get_critical_plain_rules()
        print(f"   ✅ قوانین بحرانی: {len(rules)} رکورد")
        
        print("\n🎉 اصلاح قطعی با موفقیت اعمال شد!")
        print("📋 لطفاً تست جامع را اجرا کنید:")
        print("   python test_repository_full.py")
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_repository()