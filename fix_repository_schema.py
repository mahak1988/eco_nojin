#!/usr/bin/env python3
"""
اسکریپت اصلاح خودکار کوئری‌های ScientificDataRepository
بر اساس اسکیمای زنده دیتابیس DuckDB
"""

import duckdb
import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "data" / "eco_nojin_master.duckdb"
REPO_PATH = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"

def get_table_columns(conn: duckdb.DuckDBPyConnection, table_name: str) -> list[str]:
    """دریافت لیست ستون‌های یک جدول از دیتابیس"""
    try:
        result = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        return [row[1] for row in result]  # row[1] نام ستون است
    except Exception as e:
        print(f"⚠️ جدول '{table_name}' یافت نشد: {e}")
        return []

def detect_id_column(columns: list[str], table_name: str) -> str:
    """تشخیص هوشمند نام ستون شناسه برای هر جدول"""
    # اولویت‌های نام‌گذاری بر اساس استاندارد فایل اکسل شما
    priority_names = [
        "site_id", "fert_id", "fertilizer_id", "pest_id", "ipm_id", 
        "species_id", "soil_id", "water_id", "rule_id", "econ_id",
        "id", "key", "code"
    ]
    
    # بررسی نام‌های اولویت‌دار
    for name in priority_names:
        if name in columns:
            return name
            
    # اگر هیچکدام نبود، اولین ستون را به عنوان شناسه در نظر بگیر
    if columns:
        print(f"⚠️ هشدار: ستون شناسه استاندارد برای '{table_name}' یافت نشد. از '{columns[0]}' استفاده می‌شود.")
        return columns[0]
        
    return "id"

def fix_repository():
    print("🔍 شروع تحلیل اسکیمای زنده دیتابیس...")
    
    if not DB_PATH.exists():
        print(f"❌ دیتابیس یافت نشد: {DB_PATH}")
        sys.exit(1)
        
    if not REPO_PATH.exists():
        print(f"❌ فایل ریپازیتوری یافت نشد: {REPO_PATH}")
        sys.exit(1)
        
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ۱. تحلیل جداول کلیدی
    tables_to_check = {
        "ref_sites": None,
        "ref_fertilizers": None,
        "ref_species": None,
        "ref_pests_database": None,
        "ref_ipm_pests": None,
        "ref_rules": None,
        "ref_soils": None
    }
    
    for table in tables_to_check.keys():
        cols = get_table_columns(conn, table)
        if cols:
            id_col = detect_id_column(cols, table)
            tables_to_check[table] = id_col
            print(f"✅ جدول '{table}' -> ستون شناسه: '{id_col}'")
    
    conn.close()
    
    # ۲. خواندن محتوای فایل ریپازیتوری
    print("\n📝 در حال اصلاح کوئری‌ها در فایل دیتا ریپازیتوری...")
    content = REPO_PATH.read_text(encoding="utf-8")
    original_content = content  # برای مقایسه
    
    # ۳. اصلاح کوئری‌های مربوط به سایت‌ها (ref_sites)
    if tables_to_check.get("ref_sites"):
        site_id = tables_to_check["ref_sites"]
        # اصلاح کوئری در متد get_site_profile
        content = re.sub(
            r'WHERE id = \?',
            f'WHERE {site_id} = ?',
            content
        )
        # اصلاح کوئری در متد get_all_sites
        content = re.sub(
            r'ORDER BY id',
            f'ORDER BY {site_id}',
            content
        )
        print(f"   🔧 کوئری‌های 'ref_sites' با ستون '{site_id}' اصلاح شدند.")

    # ۴. اصلاح کوئری‌های مربوط به کودها (ref_fertilizers)
    if tables_to_check.get("ref_fertilizers"):
        fert_id = tables_to_check["ref_fertilizers"]
        # اصلاح کوئری در متد get_fertilizer_profile
        content = re.sub(
            r'WHERE id = \? OR name_fa ILIKE \?',
            f'WHERE {fert_id} = ? OR name_fa ILIKE ?',
            content
        )
        print(f"   🔧 کوئری‌های 'ref_fertilizers' با ستون '{fert_id}' اصلاح شدند.")

    # ۵. اصلاح کوئری‌های مربوط به آفات (ref_pests_database و ref_ipm_pests)
    if tables_to_check.get("ref_pests_database"):
        pest_id = tables_to_check["ref_pests_database"]
        content = re.sub(
            r'WHERE pest_id = \?',
            f'WHERE {pest_id} = ?',
            content
        )
        
    if tables_to_check.get("ref_ipm_pests"):
        ipm_id = tables_to_check["ref_ipm_pests"]
        content = re.sub(
            r'WHERE pest_id = \? OR pest_or_disease ILIKE \?',
            f'WHERE {ipm_id} = ? OR pest_or_disease ILIKE ?',
            content
        )

    # ۶. ذخیره فایل اصلاح‌شده
    if content != original_content:
        REPO_PATH.write_text(content, encoding="utf-8")
        print("\n✅ فایل data_repository.py با موفقیت اصلاح و ذخیره شد.")
    else:
        print("\n⚠️ هیچ تغییری لازم نبود (فایل از قبل صحیح است).")
        
    print("\n" + "="*60)
    print("🎉 عملیات اصلاح اسکیمایی به پایان رسید.")
    print("💡 اکنون می‌توانید تست کامل را اجرا کنید:")
    print("   python test_repository_full.py")
    print("="*60)

if __name__ == "__main__":
    fix_repository()