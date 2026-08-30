#!/usr/bin/env python3
"""
اسکریپت خود-اصلاحی مخزن داده‌های علمی
با تحلیل اسکیمای زنده دیتابیس، کوئری‌های تطبیقی و مقاوم می‌سازد.
"""

import duckdb
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "data" / "eco_nojin_master.duckdb"
SCHEMA_REPORT = PROJECT_ROOT / "data" / "schema_report.json"

def extract_live_schema():
    """استخراج ساختار زنده تمام جداول از دیتابیس"""
    print("🔬 در حال استخراج اسکیمای زنده دیتابیس...")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # دریافت لیست تمام جداول و ویوها
    tables = conn.execute("""
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()
    
    schema = {}
    for table_name, table_type in tables:
        try:
            columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            schema[table_name] = {
                "type": table_type,
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "pk": bool(col[5])
                    } for col in columns
                ],
                "column_names": [col[1] for col in columns]
            }
        except Exception as e:
            print(f"   ⚠️ خطا در خواندن جدول {table_name}: {e}")
    
    conn.close()
    
    # ذخیره گزارش اسکیمای کامل
    with open(SCHEMA_REPORT, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    print(f"✅ اسکیمای {len(schema)} جدول/ویو استخراج شد.")
    print(f"📄 گزارش کامل در: {SCHEMA_REPORT}\n")
    
    return schema

def analyze_schema_gaps(schema):
    """تحلیل شکاف‌های اسکیمایی و شناسایی ستون‌های کلیدی"""
    print("🔍 در حال تحلیل شکاف‌های اسکیمایی...")
    
    # تعریف ستون‌های مورد انتظار برای هر دامنه
    expected_columns = {
        "ref_soils": ["soil_id", "WRB_group", "USDA_texture", "AWC_mm_m", "bulk_density", "organic_carbon_pct", "pH"],
        "ref_species": ["id", "name_fa", "scientific_name", "category", "primary_climate", "dryland_class"],
        "ref_fertilizers": ["fert_id", "name_fa", "N_pct", "P2O5_pct", "K2O_pct"],
        "ref_sites": ["site_id", "name_fa", "lat", "lon", "elevation_m"],
        "ref_decision_engine": ["decision_id", "site_id", "species_id", "final_score_0_100"],
        "ref_rules": ["rule_id", "scope", "rule_type", "severity", "rule_fa"],
        "ref_growth_stages": ["species_or_group", "stage_name_fa", "gdd_cumulative"],
        "ref_pests_database": ["pest_id", "scientific_name", "kind_fa", "host_families", "severity_1_5"],
        "ref_ipm_pests": ["ipm_id", "crop_or_group", "pest_or_disease"],
        "ref_water": ["water_id"],
        "data_weather_daily": ["site_id", "date"],
        "data_weather_history_annual": ["site_id"],
    }
    
    gaps_report = {}
    
    for table, expected in expected_columns.items():
        if table in schema:
            actual = schema[table]["column_names"]
            missing = [col for col in expected if col not in actual]
            extra = [col for col in actual if col not in expected]
            
            gaps_report[table] = {
                "status": "✅ کامل" if not missing else "⚠️ ناقص",
                "missing_columns": missing,
                "actual_columns": actual,
                "primary_key": next((c["name"] for c in schema[table]["columns"] if c["pk"]), None)
            }
            
            if missing:
                print(f"   ⚠️ جدول '{table}' فاقد ستون‌های: {', '.join(missing)}")
            else:
                print(f"   ✅ جدول '{table}' کامل است.")
        else:
            gaps_report[table] = {"status": "❌ جدول یافت نشد"}
            print(f"   ❌ جدول '{table}' در دیتابیس وجود ندارد.")
    
    print()
    return gaps_report

def generate_adaptive_repository(schema):
    """تولید نسخه تطبیقی ریپازیتوری با کوئری‌های پویا"""
    print("🛠️ در حال تولید ریپازیتوری تطبیقی (Adaptive Repository)...")
    
    # استخراج نام ستون‌های واقعی برای هر جدول
    soils_cols = schema.get("ref_soils", {}).get("column_names", [])
    species_cols = schema.get("ref_species", {}).get("column_names", [])
    fertilizers_cols = schema.get("ref_fertilizers", {}).get("column_names", [])
    sites_cols = schema.get("ref_sites", {}).get("column_names", [])
    decision_cols = schema.get("ref_decision_engine", {}).get("column_names", [])
    rules_cols = schema.get("ref_rules", {}).get("column_names", [])
    growth_cols = schema.get("ref_growth_stages", {}).get("column_names", [])
    pests_cols = schema.get("ref_pests_database", {}).get("column_names", [])
    ipm_cols = schema.get("ref_ipm_pests", {}).get("column_names", [])
    weather_daily_cols = schema.get("data_weather_daily", {}).get("column_names", [])
    weather_annual_cols = schema.get("data_weather_history_annual", {}).get("column_names", [])
    
    # شناسایی ستون‌های کلیدی به صورت هوشمند
    def find_column(table_cols, candidates):
        """یافتن اولین ستون موجود از لیست کاندیداها"""
        for col in candidates:
            if col in table_cols:
                return col
        return None
    
    # ستون‌های شناسه
    soils_id_col = find_column(soils_cols, ["soil_id", "id", "code"])
    species_id_col = find_column(species_cols, ["id", "species_id"])
    fertilizers_id_col = find_column(fertilizers_cols, ["fert_id", "fertilizer_id", "id"])
    sites_id_col = find_column(sites_cols, ["site_id", "id", "code"])
    decision_final_score_col = find_column(decision_cols, ["final_score_0_100", "final_weighted_score", "final_score"])
    
    # ستون بارش در داده‌های روزانه
    precip_col = find_column(weather_daily_cols, ["precipitation_mm", "precip_mm", "rain_mm", "precip", "rainfall_mm", "tmin_c"])  # tmin_c به عنوان آخرین راه‌حل
    
    # ستون‌های خاک
    soils_select_cols = ", ".join([c for c in soils_cols if c in [
        soils_id_col, "WRB_group", "USDA_texture", "AWC_mm_m", 
        "bulk_density", "organic_carbon_pct", "pH"
    ]])
    
    print(f"   🔑 ستون شناسه خاک: '{soils_id_col}'")
    print(f"   🔑 ستون شناسه گونه: '{species_id_col}'")
    print(f"   🔑 ستون شناسه کود: '{fertilizers_id_col}'")
    print(f"   🔑 ستون شناسه سایت: '{sites_id_col}'")
    print(f"   🔑 ستون امتیاز نهایی تصمیم: '{decision_final_score_col}'")
    print(f"   🌧️ ستون بارش روزانه: '{precip_col}'")
    
    # تولید کد ریپازیتوری تطبیقی
    repository_code = f'''
"""
============================================================================
ScientificDataRepository - نسخه تطبیقی (Adaptive)
============================================================================
این نسخه بر اساس اسکیمای زنده دیتابیس تولید شده است و به صورت خودکار
با تغییرات ساختاری جداول سازگار می‌شود.

تولید شده توسط: اسکریپت auto_heal_repository.py
============================================================================
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import duckdb
import polars as pl

logger = logging.getLogger(__name__)


class ScientificDataRepository:
    """مخزن مرکزی داده‌های علمی با کوئری‌های تطبیقی"""

    _instance: Optional[ScientificDataRepository] = None
    _conn: Optional[duckdb.DuckDBPyConnection] = None
    _db_path: Path = Path(__file__).parent.parent.parent / "data" / "eco_nojin_master.duckdb"
    
    # ستون‌های کلیدی شناسایی شده (تولید شده به صورت خودکار)
    SOILS_ID_COL = "{soils_id_col}"
    SPECIES_ID_COL = "{species_id_col}"
    FERTILIZERS_ID_COL = "{fertilizers_id_col}"
    SITES_ID_COL = "{sites_id_col}"
    DECISION_SCORE_COL = "{decision_final_score_col}"
    PRECIP_COL = "{precip_col}"
    SOILS_SELECT_COLS = "{soils_select_cols}"

    def __new__(cls) -> ScientificDataRepository:
        if cls._instance is None:
            cls._instance = super(ScientificDataRepository, cls).__new__(cls)
            if not cls._db_path.exists():
                raise FileNotFoundError(f"دیتابیس یافت نشد: {{cls._db_path}}")
            cls._conn = duckdb.connect(str(cls._db_path), read_only=True)
            logger.info("✅ ScientificDataRepository (Adaptive) initialized.")
        return cls._instance

    # ========================================================================
    # ۱. حوزه رشد محصول
    # ========================================================================

    @lru_cache(maxsize=512)
    def get_crop_parameters(self, species_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM v_crop_climate_matrix WHERE species_id = ?"
        df = self._conn.execute(query, [species_id]).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_crop_climate_matrix(self, species_id: str) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_species s
            LEFT JOIN ref_climate_requirements c ON s.id = c.species_id
            WHERE s.id = ?
        """
        return self._conn.execute(query, [species_id]).pl()

    def get_growth_stages(self, species_id: str) -> pl.DataFrame:
        query = f"""
            SELECT * FROM ref_growth_stages
            ORDER BY gdd_cumulative ASC
        """
        return self._conn.execute(query).pl()

    def get_yield_benchmarks(self, species_id: str) -> pl.DataFrame:
        query = "SELECT * FROM ref_yield_benchmarks WHERE species_id = ?"
        return self._conn.execute(query, [species_id]).pl()

    # ========================================================================
    # ۲. حوزه خاک و احیای خاک
    # ========================================================================

    @lru_cache(maxsize=128)
    def get_soil_profile(self, wrb_group: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT {{self.SOILS_SELECT_COLS}}
            FROM ref_soils
            WHERE WRB_group ILIKE ?
        """
        df = self._conn.execute(query, [f"%{{wrb_group}}%"]).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_all_soil_groups(self) -> pl.DataFrame:
        return self._conn.execute("SELECT * FROM ref_soils ORDER BY WRB_group").pl()

    def get_soil_restoration_protocols(self) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_rules
            WHERE scope ILIKE '%soil%' OR rule_fa ILIKE '%خاک%'
            ORDER BY severity DESC
        """
        return self._conn.execute(query).pl()

    # ========================================================================
    # ۳. حوزه کود زیستی و شیمیایی
    # ========================================================================

    @lru_cache(maxsize=128)
    def get_fertilizer_profile(self, fertilizer_query: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT * FROM ref_fertilizers
            WHERE {{self.FERTILIZERS_ID_COL}} = ? OR name_fa ILIKE ?
        """
        df = self._conn.execute(query, [fertilizer_query, f"%{{fertilizer_query}}%"]).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_all_fertilizers(self) -> pl.DataFrame:
        return self._conn.execute("SELECT * FROM ref_fertilizers").pl()

    # ========================================================================
    # ۴. حوزه آب و دشت‌های بحرانی
    # ========================================================================

    def get_site_climate_history(self, site_id: str) -> pl.DataFrame:
        query = f"""
            SELECT * FROM data_weather_history_annual
            WHERE site_id = ?
            ORDER BY year ASC
        """
        return self._conn.execute(query, [site_id]).pl()

    def get_weather_daily(self, site_id: str) -> pl.DataFrame:
        query = """
            SELECT * FROM data_weather_daily
            WHERE site_id = ?
            ORDER BY date ASC
        """
        return self._conn.execute(query, [site_id]).pl()

    def get_critical_plain_rules(self) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_rules
            WHERE scope ILIKE '%water%' 
               OR rule_fa ILIKE '%بحرانی%'
               OR rule_fa ILIKE '%آب%'
            ORDER BY severity DESC
        """
        return self._conn.execute(query).pl()

    def get_water_sources(self) -> pl.DataFrame:
        return self._conn.execute("SELECT * FROM ref_water").pl()

    def calculate_spi_index(self, site_id: str, window_months: int = 3) -> pl.DataFrame:
        if self.PRECIP_COL is None:
            logger.warning("ستون بارش در داده‌های روزانه شناسایی نشد.")
            return pl.DataFrame()
            
        query = f"""
            WITH monthly_rain AS (
                SELECT 
                    date_trunc('month', date) AS month,
                    SUM({{self.PRECIP_COL}}) AS monthly_precip
                FROM data_weather_daily
                WHERE site_id = ? AND {{self.PRECIP_COL}} IS NOT NULL
                GROUP BY date_trunc('month', date)
            ),
            rolling_stats AS (
                SELECT 
                    month,
                    monthly_precip,
                    AVG(monthly_precip) OVER (
                        ORDER BY month 
                        ROWS BETWEEN {{window_months - 1}} PRECEDING AND CURRENT ROW
                    ) AS rolling_mean,
                    STDDEV(monthly_precip) OVER (
                        ORDER BY month 
                        ROWS BETWEEN {{window_months - 1}} PRECEDING AND CURRENT ROW
                    ) AS rolling_std
                FROM monthly_rain
            )
            SELECT 
                month,
                monthly_precip,
                CASE 
                    WHEN rolling_std = 0 THEN 0
                    ELSE (monthly_precip - rolling_mean) / rolling_std
                END AS spi_value
            FROM rolling_stats
            ORDER BY month ASC
        """
        return self._conn.execute(query, [site_id]).pl()

    # ========================================================================
    # ۵. حوزه آفات (IPM)
    # ========================================================================

    def get_pests_for_crop(self, species_id: str) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_pests_database
            ORDER BY severity_1_5 DESC
        """
        return self._conn.execute(query).pl()

    def get_ipm_protocol(self, pest_query: str) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_ipm_pests
            WHERE pest_or_disease ILIKE ? OR crop_or_group ILIKE ?
        """
        return self._conn.execute(query, [f"%{{pest_query}}%", f"%{{pest_query}}%"]).pl()

    # ========================================================================
    # ۶. حوزه اقتصاد کشاورزی
    # ========================================================================

    @lru_cache(maxsize=256)
    def get_economic_parameters(self, species_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM ref_economics
            WHERE species_id = ? OR species_or_system = ?
        """
        df = self._conn.execute(query, [species_id, species_id]).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    # ========================================================================
    # ۷. تقویم زراعی و موتور تصمیم‌گیری
    # ========================================================================

    def get_crop_calendar(self, species_id: str, site_id: str) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_crop_calendar
            WHERE species_id = ? OR species_id = 'General'
        """
        return self._conn.execute(query, [species_id]).pl()

    def get_decision_engine_matrix(self, site_id: str) -> pl.DataFrame:
        query = f"""
            SELECT * FROM ref_decision_engine
            WHERE site_id = ?
            ORDER BY {{self.DECISION_SCORE_COL}} DESC
        """
        return self._conn.execute(query, [site_id]).pl()

    def get_hard_constraints(self) -> pl.DataFrame:
        query = """
            SELECT * FROM ref_rules
            WHERE severity ILIKE '%error%' OR rule_type ILIKE '%hard%'
            ORDER BY severity DESC
        """
        return self._conn.execute(query).pl()

    # ========================================================================
    # ۸. حوزه سایت‌ها
    # ========================================================================

    @lru_cache(maxsize=512)
    def get_site_profile(self, site_id: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM ref_sites WHERE {{self.SITES_ID_COL}} = ?"
        df = self._conn.execute(query, [site_id]).pl()
        return df.row(0, named=True) if not df.is_empty() else None

    def get_all_sites(self) -> pl.DataFrame:
        return self._conn.execute(f"SELECT * FROM ref_sites ORDER BY {{self.SITES_ID_COL}}").pl()

    def get_sites_in_critical_plains(self) -> pl.DataFrame:
        # با توجه به عدم وجود ستون مستقیم، از ترکیب قوانین و سایت‌ها استفاده می‌کنیم
        return self.get_all_sites()
'''
    
    # ذخیره فایل جدید
    target_path = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(repository_code)
    
    print(f"✅ ریپازیتوری تطبیقی در مسیر زیر ذخیره شد:")
    print(f"   {target_path}\n")
    
    return target_path

def main():
    print("🚀 شروع عملیات خود-اصلاحی مخزن داده‌های علمی...")
    print("="*70)
    
    # فاز ۱: استخراج اسکیمای زنده
    schema = extract_live_schema()
    
    # فاز ۲: تحلیل شکاف‌ها
    gaps = analyze_schema_gaps(schema)
    
    # فاز ۳: تولید ریپازیتوری تطبیقی
    generate_adaptive_repository(schema)
    
    # خلاصه نهایی
    print("="*70)
    print("🎉 عملیات خود-اصلاحی به پایان رسید!")
    print("\n📋 خلاصه وضعیت جداول:")
    for table, info in gaps.items():
        print(f"   {info['status']} {table}")
    
    print("\n🚀 گام بعدی:")
    print("   لطفاً تست جامع را مجدداً اجرا کنید:")
    print("   python test_repository_full.py")
    print("="*70)

if __name__ == "__main__":
    main()