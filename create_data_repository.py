#!/usr/bin/env python3
"""
اسکریپت ایجاد مخزن داده‌های علمی (ScientificDataRepository)
برای پلتفرم eco_nojin

این اسکریپت به صورت خودکار فایل زیر را ایجاد می‌کند:
    services/scientific_motors/data_repository.py
"""

from pathlib import Path
import sys
import textwrap

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET_DIR = PROJECT_ROOT / "services" / "scientific_motors"
TARGET_FILE = TARGET_DIR / "data_repository.py"

REPOSITORY_CODE = textwrap.dedent('''
    """
    ============================================================================
    ScientificDataRepository - مخزن مرکزی داده‌های علمی پلتفرم eco_nojin
    ============================================================================
    این ماژول به عنوان «منبع یگانه حقیقت» (Single Source of Truth) برای
    تمام موتورهای علمی پلتفرم عمل می‌کند.
    
    معماری:
        - الگوی طراحی: Singleton (یک نمونه برای کل اپلیکیشن)
        - اتصال: DuckDB در حالت Read-Only (برای جلوگیری از قفل شدن)
        - خروجی: Polars DataFrame (برای سازگاری با C++ و Numba)
        
    حوزه‌های تحت پوشش:
        1. رشد محصول و AquaCrop
        2. خاک، احیای خاک و پدوترانسفر
        3. کود زیستی و شیمیایی
        4. منابع آب زیرزمینی و دشت‌های بحرانی
        5. اقلیم و هواشناسی
        6. آفات و مدیریت تلفیقی (IPM)
        7. اقتصاد کشاورزی
        8. تقویم زراعی و موتور تصمیم‌گیری
        
    نویسنده: تیم معماری داده‌ی اکوژین
    نسخه: 1.0.0
    ============================================================================
    """

    from __future__ import annotations

    import logging
    from functools import lru_cache
    from pathlib import Path
    from typing import Any, Dict, List, Optional

    import duckdb
    import polars as pl

    logger = logging.getLogger(__name__)


    class ScientificDataRepository:
        """
        مخزن مرکزی داده‌های علمی برای موتورهای شبیه‌ساز اکوژین.
        
        این کلاس به صورت Singleton پیاده‌سازی شده تا از ایجاد اتصالات
        متعدد به فایل دیتابیس جلوگیری شود.
        
        مثال استفاده:
            >>> repo = ScientificDataRepository()
            >>> crop_params = repo.get_crop_parameters("W001")
            >>> soil_data = repo.get_soil_profile("Gleysol")
        """

        _instance: Optional[ScientificDataRepository] = None
        _conn: Optional[duckdb.DuckDBPyConnection] = None
        _db_path: Path = Path(__file__).parent.parent.parent / "data" / "eco_nojin_master.duckdb"

        def __new__(cls) -> ScientificDataRepository:
            """ایجاد نمونه یکتا از کلاس و برقراری اتصال به دیتابیس"""
            if cls._instance is None:
                cls._instance = super(ScientificDataRepository, cls).__new__(cls)
                
                if not cls._db_path.exists():
                    raise FileNotFoundError(
                        f"پایگاه داده مادر یافت نشد: {cls._db_path}\\n"
                        f"لطفاً ابتدا اسکریپت 'build_master_database.py' را اجرا کنید."
                    )
                
                # اتصال فقط خواندنی برای کارایی بالا و جلوگیری از قفل شدن
                cls._conn = duckdb.connect(str(cls._db_path), read_only=True)
                logger.info("✅ ScientificDataRepository initialized (DuckDB Read-Only).")
                
            return cls._instance

        def __del__(self):
            """بستن اتصال در زمان تخریب آبجکت"""
            if self._conn is not None:
                self._conn.close()
                logger.info("🔒 ScientificDataRepository connection closed.")

        # ========================================================================
        # ۱. حوزه رشد محصول و AquaCrop
        # ========================================================================

        @lru_cache(maxsize=512)
        def get_crop_parameters(self, species_id: str) -> Optional[Dict[str, Any]]:
            """
            دریافت پارامترهای کامل یک گونه گیاهی برای موتورهای رشد.
            
            جایگزین دیکشنری‌های ۸۰۰ خطی در فایل‌های قبلی می‌شود.
            
            Args:
                species_id: شناسه گونه (مانند "W001" برای گندم دوروم)
                
            Returns:
                دیکشنری شامل تمام پارامترهای اقلیمی و زراعی، یا None در صورت عدم یافتن.
            """
            query = """
                SELECT * FROM v_crop_climate_matrix 
                WHERE species_id = ?
            """
            df = self._conn.execute(query, [species_id]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ گونه با شناسه '{species_id}' در دیتابیس یافت نشد.")
                return None
            return df.row(0, named=True)

        def get_crop_climate_matrix(self, species_id: str) -> pl.DataFrame:
            """
            دریافت ماتریس کامل اقلیمی برای یک گونه (شامل تمام محدودیت‌ها).
            
            این متد برای موتور Decision Engine حیاتی است.
            """
            query = """
                SELECT 
                    s.id AS species_id,
                    s.name_fa,
                    s.scientific_name,
                    s.category,
                    s.primary_climate,
                    s.dryland_class,
                    c.min_temp_c,
                    c.opt_temp_min_c,
                    c.opt_temp_max_c,
                    c.max_temp_c,
                    c.rain_min_mm_y,
                    c.rain_opt_min_mm_y,
                    c.rain_max_mm_y,
                    c.soil_depth_cm,
                    c.drought_tolerance_1_5,
                    c.water_need_1_5,
                    c.rainfed_suitability_1_5
                FROM ref_species s
                LEFT JOIN ref_climate_requirements c ON s.id = c.species_id
                WHERE s.id = ?
            """
            return self._conn.execute(query, [species_id]).pl()

        @lru_cache(maxsize=256)
        def get_growth_stages(self, species_id: str) -> pl.DataFrame:
            """
            دریافت مراحل فنولوژیک (رشد) یک گیاه بر اساس درجه-روز (GDD).
            
            خوراک اصلی موتورهای `hpheno.py` و `irrigation_scheduler.py`.
            
            Returns:
                جدول شامل: نام مرحله، درجه-روز تجمعی، نیاز آبی، حساسیت به تنش.
            """
            query = """
                SELECT * FROM ref_growth_stages
                WHERE species_or_group = ? OR species_or_group ILIKE 'General%'
                ORDER BY gdd_cumulative ASC
            """
            return self._conn.execute(query, [species_id]).pl()

        def get_yield_benchmarks(self, species_id: str) -> pl.DataFrame:
            """
            دریافت عملکردهای مرجع برای یک گونه در شرایط مختلف (دیم، آبی، مطلوب).
            
            خوراک موتورهای اقتصادی و مقایسه عملکرد.
            """
            query = """
                SELECT * FROM ref_yield_benchmarks
                WHERE species_id = ?
            """
            return self._conn.execute(query, [species_id]).pl()

        # ========================================================================
        # ۲. حوزه خاک و احیای خاک
        # ========================================================================

        @lru_cache(maxsize=128)
        def get_soil_profile(self, wrb_group: str) -> Optional[Dict[str, Any]]:
            """
            دریافت پروفیل کامل خاک بر اساس گروه‌بندی جهانی (WRB4).
            
            خوراک موتورهای `engine/land/reference/data.py` و `soil_integrator.py`.
            
            Args:
                wrb_group: نام گروه خاک (مانند "Gleysol", "Calcisol", "Regosol")
                
            Returns:
                دیکشنری شامل پارامترهای هیدرولیکی، شیمیایی و فیزیکی خاک.
            """
            query = """
                SELECT 
                    soil_id,
                    WRB_group,
                    USDA_texture,
                    AWC_mm_m,
                    bulk_density,
                    organic_carbon_pct,
                    pH,
                    infiltration_rate_mm_h,
                    erodibility_factor_K
                FROM ref_soils
                WHERE WRB_group ILIKE ?
            """
            df = self._conn.execute(query, [f"%{wrb_group}%"]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ گروه خاک '{wrb_group}' در دیتابیس یافت نشد.")
                return None
            return df.row(0, named=True)

        def get_all_soil_groups(self) -> pl.DataFrame:
            """دریافت تمام گروه‌های خاک موجود در دیتابیس مرجع"""
            return self._conn.execute("SELECT * FROM ref_soils ORDER BY WRB_group").pl()

        def get_soil_restoration_protocols(self) -> pl.DataFrame:
            """
            دریافت پروتکل‌های احیای خاک و اصلاح شوری/سدیمی بودن.
            
            خوراک موتورهای `services/scientific_motors/land_capability.py`.
            """
            query = """
                SELECT * FROM ref_rules
                WHERE rule_type ILIKE '%soil%' 
                   OR rule_type ILIKE '%restoration%'
                   OR rule_type ILIKE '%salinity%'
                ORDER BY priority DESC
            """
            return self._conn.execute(query).pl()

        # ========================================================================
        # ۳. حوزه کود زیستی و شیمیایی
        # ========================================================================

        @lru_cache(maxsize=128)
        def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:
            """
            دریافت مشخصات کامل یک کود (شیمیایی یا زیستی).
            
            جایگزین دیتاست‌های داخلی در `engine/hydroma/biofertilizer/data/materials_data.py`.
            
            Args:
                fertilizer_query: شناسه یا نام کود (مانند "F001" یا "کود زیستی ازتوباکتر")
                
            Returns:
                دیکشنری شامل درصد عناصر، ریسک‌ها و سازگاری‌ها.
            """
            query = """
                SELECT * FROM ref_fertilizers
                WHERE id = ? OR name_fa ILIKE ?
            """
            df = self._conn.execute(query, [fertilizer_query, f"%{fertilizer_query}%"]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ کود '{fertilizer_query}' در دیتابیس یافت نشد.")
                return None
            return df.row(0, named=True)

        def get_fertilizer_compatibility_matrix(self) -> pl.DataFrame:
            """
            دریافت ماتریس سازگاری کودها برای جلوگیری از ترکیبات خطرناک.
            
            خوراک موتور `advanced_calculator.py` برای هشدار تداخلات شیمیایی.
            """
            query = """
                SELECT 
                    f1.name_fa AS fertilizer_1,
                    f2.name_fa AS fertilizer_2,
                    compatibility_status
                FROM ref_fertilizers f1
                CROSS JOIN ref_fertilizers f2
                WHERE f1.compatibility ILIKE '%' || f2.name_fa || '%'
                  AND f1.id != f2.id
            """
            return self._conn.execute(query).pl()

        def get_biofertilizer_recommendations(self, soil_type: str, crop_category: str) -> pl.DataFrame:
            """
            دریافت توصیه‌های کود زیستی بر اساس نوع خاک و دسته محصول.
            
            این متد از داده‌های `ref_fertilizers` و `ref_soils` برای تولید
            توصیه‌های هوشمند استفاده می‌کند.
            """
            query = """
                SELECT 
                    f.name_fa AS biofertilizer,
                    f.N_pct,
                    f.P2O5_pct,
                    f.K2O_pct,
                    f.organic_matter_pct,
                    f.notes AS recommendation_notes
                FROM ref_fertilizers f
                WHERE f.category ILIKE '%زیستی%' OR f.category ILIKE '%bio%'
                  AND f.target_soil ILIKE ?
                  AND f.target_crop ILIKE ?
                ORDER BY f.efficiency_score DESC
            """
            return self._conn.execute(query, [f"%{soil_type}%", f"%{crop_category}%"]).pl()

        # ========================================================================
        # ۴. حوزه منابع آب زیرزمینی و دشت‌های بحرانی
        # ========================================================================

        def get_site_climate_history(self, site_id: str) -> pl.DataFrame:
            """
            دریافت داده‌های تاریخی اقلیمی یک سایت (بارش سالانه، دما).
            
            خوراک موتورهای `groundwater_model.py` و `drought_motor.py`
            برای محاسبه شاخص‌های خشکسالی و تغذیه آبخوان.
            """
            query = """
                SELECT * FROM data_weather_history_annual
                WHERE site_id = ?
                ORDER BY year ASC
            """
            return self._conn.execute(query, [site_id]).pl()

        def get_weather_daily(self, site_id: str, start_date: Optional[str] = None, 
                              end_date: Optional[str] = None) -> pl.DataFrame:
            """
            دریافت داده‌های روزانه هواشناسی برای یک سایت.
            
            خوراک اصلی موتورهای `aquacrop_real.py` و `irrigation_scheduler.py`.
            
            Args:
                site_id: شناسه سایت (مانند "SITE076")
                start_date: تاریخ شروع (فرمت: "2000-01-01")
                end_date: تاریخ پایان (فرمت: "2024-12-31")
            """
            query = "SELECT * FROM data_weather_daily WHERE site_id = ?"
            params: List[Any] = [site_id]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " ORDER BY date ASC"
            return self._conn.execute(query, params).pl()

        def get_critical_plain_rules(self) -> pl.DataFrame:
            """
            دریافت قوانین سخت‌گیرانه (Hard Constraints) برای دشت‌های ممنوعه/بحرانی.
            
            خوراک موتورهای تصمیم‌گیری برای وتوی خودکار کشت‌های پرآب‌بر.
            
            Returns:
                جدول قوانین شامل: نوع قانون، شرط، اقدام، شدت.
            """
            query = """
                SELECT * FROM ref_rules
                WHERE rule_type ILIKE '%groundwater%' 
                   OR rule_type ILIKE '%critical%' 
                   OR rule_type ILIKE '%aquifer%'
                   OR rule_type ILIKE '%drought%'
                ORDER BY priority DESC
            """
            return self._conn.execute(query).pl()

        def get_water_sources(self) -> pl.DataFrame:
            """دریافت منابع آب موجود (چاه، قنات، رودخانه، سد) و ظرفیت آن‌ها"""
            return self._conn.execute("SELECT * FROM ref_water").pl()

        def calculate_spi_index(self, site_id: str, window_months: int = 3) -> pl.DataFrame:
            """
            محاسبه شاخص بارش استاندارد شده (SPI) برای پایش خشکسالی.
            
            این متد با استفاده از Polars، محاسبات آماری را مستقیماً
            روی داده‌های دیتابیس انجام می‌دهد (بسیار سریع‌تر از پانداس).
            
            Args:
                site_id: شناسه سایت
                window_months: بازه زمانی محاسبه (۳، ۶، یا ۱۲ ماهه)
                
            Returns:
                جدول شامل تاریخ، بارش تجمعی، و مقدار شاخص SPI.
            """
            query = f"""
                WITH monthly_rain AS (
                    SELECT 
                        date_trunc('month', date) AS month,
                        SUM(precipitation_mm) AS monthly_precip
                    FROM data_weather_daily
                    WHERE site_id = ?
                    GROUP BY date_trunc('month', date)
                ),
                rolling_stats AS (
                    SELECT 
                        month,
                        monthly_precip,
                        AVG(monthly_precip) OVER (
                            ORDER BY month 
                            ROWS BETWEEN {window_months - 1} PRECEDING AND CURRENT ROW
                        ) AS rolling_mean,
                        STDDEV(monthly_precip) OVER (
                            ORDER BY month 
                            ROWS BETWEEN {window_months - 1} PRECEDING AND CURRENT ROW
                        ) AS rolling_std
                    FROM monthly_rain
                )
                SELECT 
                    month,
                    monthly_precip,
                    rolling_mean,
                    CASE 
                        WHEN rolling_std = 0 THEN 0
                        ELSE (monthly_precip - rolling_mean) / rolling_std
                    END AS spi_value
                FROM rolling_stats
                ORDER BY month ASC
            """
            return self._conn.execute(query, [site_id]).pl()

        # ========================================================================
        # ۵. حوزه آفات و مدیریت تلفیقی (IPM)
        # ========================================================================

        def get_pests_for_crop(self, species_id: str) -> pl.DataFrame:
            """دریافت لیست آفات و بیماری‌های مرتبط با یک گونه گیاهی"""
            query = """
                SELECT * FROM ref_pests_database
                WHERE host_species_id = ? OR host_species_id IS NULL
                ORDER BY severity_score DESC
            """
            return self._conn.execute(query, [species_id]).pl()

        @lru_cache(maxsize=128)
        def get_ipm_protocol(self, pest_id: str) -> Optional[Dict[str, Any]]:
            """
            دریافت پروتکل کامل مدیریت تلفیقی برای یک آفت خاص.
            
            خوراک موتورهای `services/scientific_motors/crop_advisor.py`.
            """
            query = """
                SELECT * FROM ref_ipm_pests
                WHERE pest_id = ? OR pest_or_disease ILIKE ?
            """
            df = self._conn.execute(query, [pest_id, f"%{pest_id}%"]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ پروتکل آفت '{pest_id}' یافت نشد.")
                return None
            return df.row(0, named=True)

        # ========================================================================
        # ۶. حوزه اقتصاد کشاورزی و بازار
        # ========================================================================

        @lru_cache(maxsize=256)
        def get_economic_parameters(self, species_id: str) -> Optional[Dict[str, Any]]:
            """
            دریافت پارامترهای اقتصادی یک محصول (قیمت، هزینه، سود).
            
            خوراک موتورهای `engine/hydroma/economics/roi.py` و `costing.py`.
            """
            query = """
                SELECT * FROM ref_economics
                WHERE species_id = ? OR species_or_system = ?
            """
            df = self._conn.execute(query, [species_id, species_id]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ داده‌های اقتصادی برای '{species_id}' یافت نشد.")
                return None
            return df.row(0, named=True)

        # ========================================================================
        # ۷. تقویم زراعی و موتور تصمیم‌گیری
        # ========================================================================

        def get_crop_calendar(self, species_id: str, site_id: str) -> pl.DataFrame:
            """دریافت تقویم زراعی بهینه برای یک گونه در یک سایت خاص"""
            query = """
                SELECT * FROM ref_crop_calendar
                WHERE species_id = ? AND site_id = ?
                ORDER BY start_month ASC
            """
            return self._conn.execute(query, [species_id, site_id]).pl()

        def get_decision_engine_matrix(self, site_id: str) -> pl.DataFrame:
            """
            دریافت ماتریس امتیازدهی موتور تصمیم‌گیری برای یک سایت.
            
            این ماتریس شامل امتیازهای زیر است:
                - قابلیت خاک، امنیت آبی، ریسک اقتصادی، تاب‌آوری، آگروفارستری.
            """
            query = """
                SELECT * FROM ref_decision_engine
                WHERE site_id = ?
                ORDER BY final_weighted_score DESC
            """
            return self._conn.execute(query, [site_id]).pl()

        def get_hard_constraints(self) -> pl.DataFrame:
            """
            دریافت تمام محدودیت‌های سخت (Hard Constraints) سیستم.
            
            این قوانین در مرحله اول تصمیم‌گیری اعمال می‌شوند و در صورت
            نقض، گزینه‌های کشت به طور کامل حذف می‌شوند (نه فقط کاهش امتیاز).
            """
            query = """
                SELECT * FROM ref_rules
                WHERE rule_type ILIKE '%hard%' OR constraint_type ILIKE '%hard%'
                ORDER BY priority DESC
            """
            return self._conn.execute(query).pl()

        # ========================================================================
        # ۸. حوزه سایت‌ها و مکان‌یابی
        # ========================================================================

        @lru_cache(maxsize=512)
        def get_site_profile(self, site_id: str) -> Optional[Dict[str, Any]]:
            """دریافت پروفایل کامل یک سایت (مختصات، ارتفاع، وضعیت دشت)"""
            query = """
                SELECT * FROM ref_sites
                WHERE id = ?
            """
            df = self._conn.execute(query, [site_id]).pl()
            if df.is_empty():
                logger.warning(f"⚠️ سایت '{site_id}' در دیتابیس یافت نشد.")
                return None
            return df.row(0, named=True)

        def get_all_sites(self) -> pl.DataFrame:
            """دریافت لیست تمام سایت‌های موجود در دیتابیس"""
            return self._conn.execute("SELECT * FROM ref_sites ORDER BY id").pl()

        def get_sites_in_critical_plains(self) -> pl.DataFrame:
            """دریافت سایت‌هایی که در دشت‌های بحرانی یا ممنوعه قرار دارند"""
            query = """
                SELECT * FROM ref_sites
                WHERE critical_plain_status ILIKE '%بحرانی%' 
                   OR critical_plain_status ILIKE '%ممنوعه%'
                   OR critical_plain_status ILIKE '%prohibited%'
                ORDER BY critical_plain_severity DESC
            """
            return self._conn.execute(query).pl()


    # ========================================================================
    # توابع کمکی برای تست و استفاده در اسکریپت‌های پایتون
    # ========================================================================

    def create_repository() -> ScientificDataRepository:
        """تابع کارخانه برای ایجاد نمونه ریپازیتوری"""
        return ScientificDataRepository()


    if __name__ == "__main__":
        # تست سریع عملکرد ریپازیتوری
        print("🔍 در حال تست عملکرد ScientificDataRepository...")
        try:
            repo = ScientificDataRepository()
            
            # تست ۱: دریافت پارامترهای گندم دوروم (W001)
            crop = repo.get_crop_parameters("W001")
            if crop:
                print(f"✅ تست گونه: {crop.get('name_fa', 'N/A')} ({crop.get('scientific_name', 'N/A')})")
            
            # تست ۲: دریافت گروه‌های خاک
            soils = repo.get_all_soil_groups()
            print(f"✅ تست خاک: {len(soils)} گروه خاک یافت شد.")
            
            # تست ۳: دریافت قوانین دشت بحرانی
            rules = repo.get_critical_plain_rules()
            print(f"✅ تست قوانین: {len(rules)} قانون بحرانی یافت شد.")
            
            print("\\n🎉 تمام تست‌ها با موفقیت انجام شد.")
            
        except Exception as e:
            print(f"❌ خطا در تست ریپازیتوری: {e}")
''').strip()

def create_repository_file():
    """ایجاد فایل ریپازیتوری در مسیر صحیح پروژه"""
    print("🚀 شروع ایجاد مخزن داده‌های علمی (ScientificDataRepository)...")
    
    # ایجاد پوشه‌ها در صورت عدم وجود
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 مسیر هدف: {TARGET_DIR}")
    
    # نوشتن محتوای فایل
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(REPOSITORY_CODE)
        
    print(f"✅ فایل با موفقیت ایجاد شد: {TARGET_FILE}")
    print(f"📊 حجم فایل: {TARGET_FILE.stat().st_size / 1024:.2f} کیلوبایت")
    
    # بررسی اینکه آیا ماژول قابل ایمپورت است
    print("\n🔍 در حال تست ایمپورت ماژول...")
    try:
        # تغییر موقت به ریشه پروژه برای ایمپورت صحیح
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # تلاش برای ایمپورت ماژول جدید
        from services.scientific_motors.data_repository import ScientificDataRepository
        print("✅ ماژول با موفقیت ایمپورت شد.")
        
        # تست ایجاد نمونه
        repo = ScientificDataRepository()
        print("✅ اتصال به دیتابیس با موفقیت برقرار شد.")
        
        # تست یک کوئری ساده
        sites = repo.get_all_sites()
        print(f"✅ کوئری تست: {len(sites)} سایت در دیتابیس یافت شد.")
        
    except ImportError as e:
        print(f"⚠️ هشدار ایمپورت: {e}")
        print("💡 نکته: ممکن است نیاز باشد `__init__.py` در پوشه‌های مربوطه ایجاد شود.")
    except FileNotFoundError as e:
        print(f"❌ خطا: {e}")
        print("💡 راه‌حل: ابتدا اسکریپت `build_master_database.py` را اجرا کنید.")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")

    print("\n" + "="*70)
    print("📋 راهنمای استفاده در ماژول‌های پلتفرم:")
    print("="*70)
    print("""
    # در فایل‌های دیگر پروژه (مثلاً crop_database.py):
    
    from services.scientific_motors.data_repository import ScientificDataRepository
    
    # ایجاد نمونه (به صورت خودکار Singleton است)
    repo = ScientificDataRepository()
    
    # دریافت پارامترهای گندم
    wheat_params = repo.get_crop_parameters("W001")
    
    # دریافت پروفیل خاک
    soil_data = repo.get_soil_profile("Calcisol")
    
    # دریافت قوانین دشت بحرانی
    critical_rules = repo.get_critical_plain_rules()
    
    # محاسبه شاخص خشکسالی
    spi_df = repo.calculate_spi_index("SITE076", window_months=3)
    """)
    print("="*70)

if __name__ == "__main__":
    create_repository_file()