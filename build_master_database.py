import duckdb
import pandas as pd
import re
from pathlib import Path
import shutil
import time
import sys

# ==========================================
# تنظیمات معماری Master Database
# ==========================================
PROJECT_ROOT = Path(__file__).parent.resolve()
MANUAL_DATA_DIR = PROJECT_ROOT / "دیتا دستی اکسل"
MASTER_DB = PROJECT_ROOT / "data" / "eco_nojin_master.duckdb"
ARCHIVE_DIR = PROJECT_ROOT / "data" / "_archived_excel_data"

# فایل قلب تپنده پروژه (دارای 30 شیت و 5000 گونه)
CORE_EXCEL_FILE = "global_agri_simulator_database_v2.0.xlsx"

def sanitize_table_name(raw_name: str, prefix: str = "tbl") -> str:
    """
    موتور پاکسازی نام‌ها برای انطباق با استاندارد SQL
    - حذف کاراکترهای غیرمجاز
    - جلوگیری از شروع نام با عدد
    """
    name = Path(raw_name).stem
    # جایگزینی کاراکترهای غیر الفبایی (به جز _) با _
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # حذف _ های متوالی
    name = re.sub(r'_+', '_', name).strip('_')
    
    # اگر نام با عدد شروع شد یا خالی بود، پیشوند اضافه کن
    if not name or name[0].isdigit():
        name = f"{prefix}_{name}"
        
    return name.lower()

def build_master_database():
    print("🚀 شروع عملیات ساخت پایگاه داده مادر (Master Database)...")
    print(f"📂 مسیر هدف: {MASTER_DB}\n")
    
    # تضمین وجود پوشه‌ها
    MASTER_DB.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # پاکسازی دیتابیس قبلی برای شروع یکپارچه
    if MASTER_DB.exists():
        MASTER_DB.unlink()
        
    con = duckdb.connect(str(MASTER_DB))
    ingested_tables = []
    
    # ==========================================
    # فاز 1: بلعیدن قلب تپنده (فایل v2.0)
    # ==========================================
    core_file_path = MANUAL_DATA_DIR / CORE_EXCEL_FILE
    if core_file_path.exists():
        print(f"💎 در حال پردازش فایل مرجع اصلی: {CORE_EXCEL_FILE}")
        try:
            xls = pd.ExcelFile(core_file_path)
            for sheet_name in xls.sheet_names:
                # شیت‌های مرجع با پیشوند ref_ وارد می‌شوند (مانند ref_species, ref_sites)
                table_name = f"ref_{sanitize_table_name(sheet_name, 'sheet')}"
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                if not df.empty:
                    con.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM df')
                    ingested_tables.append(table_name)
                    print(f"   ✅ شیت '{sheet_name}' -> جدول '{table_name}' ({len(df)} رکورد)")
        except Exception as e:
            print(f"   ❌ خطای بحرانی در خواندن فایل مرجع: {e}")
    else:
        print(f"⚠️ هشدار: فایل مرجع اصلی ({CORE_EXCEL_FILE}) در پوشه دیتا دستی یافت نشد.")

    # ==========================================
    # فاز 2: بلعیدن داده‌های اقلیمی و کمکی (CSV و Excel)
    # ==========================================
    print("\n🌍 در حال پردازش داده‌های اقلیمی و کمکی...")
    
    # پردازش CSVها
    for csv_file in MANUAL_DATA_DIR.glob("*.csv"):
        if csv_file.name == CORE_EXCEL_FILE: continue
        
        # پیشوند data_ برای داده‌های خام اقلیمی و اقتصادی
        table_name = f"data_{sanitize_table_name(csv_file.name, 'csv')}"
        try:
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table_name}" AS 
                SELECT * FROM read_csv_auto('{str(csv_file)}', header=true, ignore_errors=true);
            """)
            count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
            ingested_tables.append(table_name)
            print(f"   ✅ CSV '{csv_file.name}' -> جدول '{table_name}' ({count} رکورد)")
        except Exception as e:
            print(f"   ❌ خطا در {csv_file.name}: {e}")

    # پردازش سایر Excelها
    for xlsx_file in MANUAL_DATA_DIR.glob("*.xlsx"):
        if xlsx_file.name == CORE_EXCEL_FILE: continue
        
        try:
            xls = pd.ExcelFile(xlsx_file)
            for sheet_name in xls.sheet_names:
                table_name = f"data_{sanitize_table_name(xlsx_file.name, 'xlsx')}_{sanitize_table_name(sheet_name, 'sheet')}"
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if not df.empty:
                    con.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM df')
                    ingested_tables.append(table_name)
        except Exception as e:
            print(f"   ❌ خطا در {xlsx_file.name}: {e}")

    # ==========================================
    # فاز 3: ایجاد نمای تحلیلی (Analytical Views) برای موتورهای eco_nojin
    # ==========================================
    print("\n⚙️ در حال ایجاد Viewهای تحلیلی برای موتورهای علمی...")
    try:
        # ایجاد یک View که مشخصات گونه را به نیازهای اقلیمی آن متصل می‌کند
        # این View خوراک اصلی موتورهای AquaCrop و Decision Engine خواهد بود
        con.execute("""
            CREATE OR REPLACE VIEW v_crop_climate_matrix AS
            SELECT 
                s.id AS species_id,
                s.name_fa,
                s.scientific_name,
                s.category,
                s.primary_climate,
                c.min_temp_c,
                c.opt_temp_min_c,
                c.opt_temp_max_c,
                c.max_temp_c,
                c.rain_min_mm_y,
                c.rain_opt_min_mm_y,
                c.rain_max_mm_y,
                c.soil_depth_cm,
                c.drought_tolerance_1_5,
                c.water_need_1_5
            FROM ref_species s
            LEFT JOIN ref_climate_requirements c ON s.id = c.species_id;
        """)
        print("   ✅ View 'v_crop_climate_matrix' برای موتورهای شبیه‌ساز ایجاد شد.")
    except Exception as e:
        print(f"   ⚠️ امکان ایجاد View تحلیلی نبود (شاید جداول مرجع کامل نباشند): {e}")

    # ==========================================
    # فاز 4: بایگانی ایمن فایل‌های اکسل (Safe Archiving)
    # ==========================================
    print("\n📦 در حال انتقال فایل‌های اکسل به بایگانی ایمن...")
    archived_count = 0
    for file in MANUAL_DATA_DIR.iterdir():
        if file.is_file() and file.suffix.lower() in ['.xlsx', '.xls', '.csv']:
            try:
                shutil.move(str(file), str(ARCHIVE_DIR / file.name))
                archived_count += 1
            except Exception as e:
                print(f"   ❌ خطا در انتقال {file.name}: {e}")
    
    # ==========================================
    # گزارش نهایی و بهینه‌سازی
    # ==========================================
    print("\n🧹 در حال فشرده‌سازی و بهینه‌سازی پایگاه داده...")
    con.execute("PRAGMA optimize;")
    db_size_mb = MASTER_DB.stat().st_size / (1024 * 1024)
    
    con.close()
    
    print("\n" + "="*70)
    print("✅ عملیات ساخت Master Database با موفقیت پایان یافت!")
    print(f"🔹 تعداد کل جداول و Viewهای ایجاد شده: {len(ingested_tables)}")
    print(f"🔹 تعداد فایل‌های منتقل شده به بایگانی: {archived_count}")
    print(f"🔹 حجم نهایی پایگاه داده مادر: {db_size_mb:.2f} مگابایت")
    print(f"🔹 مسیر دیتابیس: {MASTER_DB}")
    print(f"🔹 مسیر بایگانی: {ARCHIVE_DIR}")
    print("-" * 70)
    print("💡 استراتژی بعدی:")
    print("   1. فایل‌های اکسل اکنون در پوشه '_archived_excel_data' امن هستند.")
    print("   2. شما می‌توانید آن‌ها را پس از تایید نهایی خروجی‌های پلتفرم، حذف (Delete) کنید.")
    print("   3. موتورهای علمی (AquaCrop, SWAT) اکنون فقط به 'eco_nojin_master.duckdb' متصل می‌شوند.")
    print("="*70)

if __name__ == "__main__":
    if not MANUAL_DATA_DIR.exists():
        print(f"❌ پوشه '{MANUAL_DATA_DIR}' یافت نشد.")
        sys.exit(1)
    build_master_database()