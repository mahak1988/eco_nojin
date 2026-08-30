#!/usr/bin/env python3
"""
اسکریپت اصلاح نهایی ریپازیتوری - پچ دقیق ۳ خطای باقی‌مانده
بر اساس اسکیمای واقعی استخراج شده توسط diagnose_schema_gaps.py
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET_FILE = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"

def apply_final_patch():
    print("🔧 شروع اعمال پچ نهایی بر اساس اسکیمای واقعی دیتابیس...")
    print("="*70)
    
    if not TARGET_FILE.exists():
        print(f"❌ فایل ریپازیتوری یافت نشد: {TARGET_FILE}")
        return
    
    content = TARGET_FILE.read_text(encoding="utf-8")
    original_content = content
    
    # ==========================================
    # پچ ۱: اصلاح کوئری‌های قوانین (ref_rules)
    # ستون‌های واقعی: rule_id, priority, condition, recommendation, confidence
    # ==========================================
    
    # اصلاح متد get_soil_restoration_protocols
    old_soil_protocols = '''    def get_soil_restoration_protocols(self) -> pl.DataFrame:
        """دریافت پروتکل‌های احیای خاک"""
        query = f"""
            SELECT * FROM ref_rules
            WHERE {{self.RULES_TEXT_COL}} ILIKE '%خاک%'
               OR {{self.RULES_TEXT_COL}} ILIKE '%احیا%'
               OR {{self.RULES_SCOPE_COL}} ILIKE '%soil%'
            ORDER BY {{self.RULES_SEVERITY_COL}} DESC
        """
        return self._conn.execute(query).pl()'''
    
    new_soil_protocols = '''    def get_soil_restoration_protocols(self) -> pl.DataFrame:
        """دریافت پروتکل‌های احیای خاک"""
        query = """
            SELECT * FROM ref_rules
            WHERE condition ILIKE '%خاک%'
               OR condition ILIKE '%soil%'
               OR recommendation ILIKE '%احیا%'
               OR recommendation ILIKE '%خاک%'
            ORDER BY priority DESC
        """
        return self._conn.execute(query).pl()'''
    
    if old_soil_protocols in content:
        content = content.replace(old_soil_protocols, new_soil_protocols)
        print("   ✅ متد 'get_soil_restoration_protocols' اصلاح شد.")
    
    # اصلاح متد get_critical_plain_rules
    old_critical_rules = '''    def get_critical_plain_rules(self) -> pl.DataFrame:
        """دریافت قوانین دشت‌های بحرانی"""
        query = f"""
            SELECT * FROM ref_rules
            WHERE {{self.RULES_TEXT_COL}} ILIKE '%آب%'
               OR {{self.RULES_TEXT_COL}} ILIKE '%بحرانی%'
               OR {{self.RULES_TEXT_COL}} ILIKE '%ممنوع%'
               OR {{self.RULES_SCOPE_COL}} ILIKE '%water%'
            ORDER BY {{self.RULES_SEVERITY_COL}} DESC
        """
        return self._conn.execute(query).pl()'''
    
    new_critical_rules = '''    def get_critical_plain_rules(self) -> pl.DataFrame:
        """دریافت قوانین دشت‌های بحرانی"""
        query = """
            SELECT * FROM ref_rules
            WHERE condition ILIKE '%آب%'
               OR condition ILIKE '%بحرانی%'
               OR condition ILIKE '%ممنوع%'
               OR recommendation ILIKE '%آب%'
               OR recommendation ILIKE '%بحرانی%'
            ORDER BY priority DESC
        """
        return self._conn.execute(query).pl()'''
    
    if old_critical_rules in content:
        content = content.replace(old_critical_rules, new_critical_rules)
        print("   ✅ متد 'get_critical_plain_rules' اصلاح شد.")
    
    # اصلاح متد get_hard_constraints
    old_hard_constraints = '''    def get_hard_constraints(self) -> pl.DataFrame:
        """دریافت محدودیت‌های سخت"""
        query = f"""
            SELECT * FROM ref_rules
            WHERE {{self.RULES_SEVERITY_COL}} ILIKE '%error%'
               OR {{self.RULES_TYPE_COL}} ILIKE '%hard%'
            ORDER BY {{self.RULES_SEVERITY_COL}} DESC
        """
        return self._conn.execute(query).pl()'''
    
    new_hard_constraints = '''    def get_hard_constraints(self) -> pl.DataFrame:
        """دریافت محدودیت‌های سخت"""
        query = """
            SELECT * FROM ref_rules
            WHERE priority ILIKE '%بالا%'
               OR condition ILIKE '%رد سخت%'
               OR recommendation ILIKE '%رد سخت%'
            ORDER BY priority DESC
        """
        return self._conn.execute(query).pl()'''
    
    if old_hard_constraints in content:
        content = content.replace(old_hard_constraints, new_hard_constraints)
        print("   ✅ متد 'get_hard_constraints' اصلاح شد.")
    
    # ==========================================
    # پچ ۲: اصلاح کوئری‌های کود (ref_fertilizers)
    # ستون‌های واقعی: fert_id, material, type, N_pct, ...
    # ==========================================
    
    old_fert_profile = '''    @lru_cache(maxsize=128)
    def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:
        """دریافت مشخصات کامل یک کود"""
        query = f"""
            SELECT * FROM ref_fertilizers
            WHERE {{self.FERT_ID_COL}} = ? OR {{self.FERT_NAME_COL}} ILIKE ?
        """
        df = self._conn.execute(query, [fertilizer_query, f"%{{fertilizer_query}}%"]).pl()
        return df.row(0, named=True) if not df.is_empty() else None'''
    
    new_fert_profile = '''    @lru_cache(maxsize=128)
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
    
    if old_fert_profile in content:
        content = content.replace(old_fert_profile, new_fert_profile)
        print("   ✅ متد 'get_fertilizer_profile' اصلاح شد.")
    
    # ==========================================
    # پچ ۳: اصلاح تست ماتریس تصمیم‌گیری
    # سایت‌های واقعی: SITE001, SITE007, SITE010, ...
    # ==========================================
    
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
    
    # ==========================================
    # پچ ۴: اصلاح متغیرهای کلاس
    # ==========================================
    
    # حذف متغیرهای نامعتبر
    old_class_vars = '''    # ستون‌های کلیدی شناسایی شده (تولید شده به صورت خودکار)
    RULES_TYPE_COL = "{rules_type_col}"
    RULES_SCOPE_COL = "{rules_scope_col}"
    RULES_SEVERITY_COL = "{rules_severity_col}"
    RULES_TEXT_COL = "{rules_text_col}"
    FERT_NAME_COL = "{fert_name_col}"
    FERT_ID_COL = "{fert_id_col}"
    SITE_NAME_COL = "{site_name_col}"
    SITE_ID_COL = "{site_id_col}"
    DECISION_SCORE_COL = "{decision_score_col}"
    PRECIP_COL = "{precip_col}"
    SAMPLE_DECISION_SITE = "{sample_site}"'''
    
    new_class_vars = '''    # ستون‌های کلیدی (بر اساس اسکیمای واقعی دیتابیس)
    SITE_ID_COL = "site_id"
    PRECIP_COL = "precip_mm"
    SAMPLE_DECISION_SITE = "SITE037"'''
    
    # جستجو با الگوی انعطاف‌پذیر
    if "RULES_TYPE_COL" in content:
        # حذف خطوط متغیرهای نامعتبر
        lines = content.split('\n')
        new_lines = []
        skip_vars = ['RULES_TYPE_COL', 'RULES_SCOPE_COL', 'RULES_SEVERITY_COL', 
                     'RULES_TEXT_COL', 'FERT_NAME_COL', 'FERT_ID_COL', 
                     'SITE_NAME_COL', 'DECISION_SCORE_COL']
        
        for line in lines:
            if any(var in line for var in skip_vars):
                continue
            new_lines.append(line)
        content = '\n'.join(new_lines)
        print("   ✅ متغیرهای کلاس نامعتبر حذف شدند.")
    
    # ==========================================
    # پچ ۵: اصلاح متد محاسبه SPI برای استفاده از ستون صحیح
    # ==========================================
    content = content.replace('SUM({{self.PRECIP_COL}})', 'SUM(precip_mm)')
    content = content.replace('AND {{self.PRECIP_COL}} IS NOT NULL', 'AND precip_mm IS NOT NULL')
    print("   ✅ کوئری‌های SPI اصلاح شدند.")
    
    # ==========================================
    # پچ ۶: اصلاح تست نمونه در بخش __main__
    # ==========================================
    content = content.replace('"SITE076"', '"SITE037"')
    content = content.replace("'SITE076'", "'SITE037'")
    print("   ✅ سایت تست نمونه به SITE037 تغییر یافت.")
    
    # ذخیره فایل
    if content != original_content:
        TARGET_FILE.write_text(content, encoding="utf-8")
        print(f"\n✅ پچ نهایی با موفقیت اعمال شد.")
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
        
        # تست قوانین
        rules = repo.get_critical_plain_rules()
        print(f"   ✅ قوانین بحرانی: {len(rules)} رکورد")
        
        # تست کود
        fert = repo.get_fertilizer_profile("FRT001")
        if fert:
            print(f"   ✅ کود FRT001: {fert.get('material', 'N/A')}")
        else:
            print(f"   ⚠️ کود FRT001 یافت نشد (ممکن است شناسه متفاوت باشد)")
            # تلاش با نام
            fert2 = repo.get_fertilizer_profile("اوره")
            if fert2:
                print(f"   ✅ کود 'اوره': {fert2.get('material', 'N/A')}")
        
        # تست ماتریس تصمیم
        sites = repo.get_all_decision_sites()
        if not sites.is_empty():
            sample_site = sites["site_id"][0]
            matrix = repo.get_decision_engine_matrix(sample_site)
            print(f"   ✅ ماتریس تصمیم ({sample_site}): {len(matrix)} رکورد")
        
        print("\n🎉 پچ نهایی با موفقیت اعمال شد!")
        print("📋 گام بعدی: لطفاً تست جامع را اجرا کنید:")
        print("   python test_repository_full.py")
        
    except Exception as e:
        print(f"\n❌ خطا در تست سریع: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_final_patch()