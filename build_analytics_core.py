import duckdb
import pandas as pd
from pathlib import Path
import time

# ==========================================
# تنظیمات تیم تحقیقاتی خودکار (Ingestion Pipeline)
# ==========================================
PROJECT_ROOT = Path(__file__).parent.resolve()
MANUAL_DATA_DIR = PROJECT_ROOT / "دیتا دستی اکسل"
OUTPUT_DB = PROJECT_ROOT / "data" / "eco_nojin_analytics.duckdb"

# تضمین وجود پوشه data
OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)

def build_analytics_core():
    print(f"🚀 شروع به کار تیم تحقیقاتی خودکار...")
    print(f"📂 در حال اسکن پوشه: {MANUAL_DATA_DIR}")
    
    # اتصال به DuckDB (فایل محور - بدون نیاز به سرور)
    # اگر فایل از قبل وجود دارد، آن را بازنویسی می‌کنیم تا داده‌ها تازه بمانند
    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()
        
    con = duckdb.connect(str(OUTPUT_DB))
    
    ingested_tables = []
    start_time = time.time()
    
    # ۱. پردازش فایل‌های CSV (با استفاده از موتور C++ داخلی DuckDB برای سرعت حداکثری)
    csv_files = list(MANUAL_DATA_DIR.glob("*.csv"))
    for csv_file in csv_files:
        table_name = csv_file.stem.replace(" ", "_").replace("-", "_").lower()
        print(f"  📥 در حال بلعیدن CSV: {csv_file.name} -> جدول: {table_name}")
        
        try:
            # DuckDB مستقیماً CSV را می‌خواند و جدول را می‌سازد (Zero-Copy در صورت امکان)
            con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{str(csv_file)}', header=true, ignore_errors=true);
            """)
            ingested_tables.append(table_name)
        except Exception as e:
            print(f"    ❌ خطا در خواندن {csv_file.name}: {e}")

    # ۲. پردازش فایل‌های Excel (با استفاده از Pandas به عنوان واسط)
    xlsx_files = list(MANUAL_DATA_DIR.glob("*.xlsx"))
    for xlsx_file in xlsx_files:
        base_name = xlsx_file.stem.replace(" ", "_").replace("-", "_").lower()
        print(f"  📥 در حال بلعیدن Excel: {xlsx_file.name}")
        
        try:
            # خواندن تمام شیت‌های اکسل
            xls = pd.ExcelFile(xlsx_file)
            for sheet_name in xls.sheet_names:
                # پاکسازی نام شیت برای استفاده به عنوان نام جدول SQL
                clean_sheet = "".join(c for c in sheet_name if c.isalnum() or c == '_').lower()
                table_name = f"{base_name}__{clean_sheet}" if clean_sheet else base_name
                
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if not df.empty:
                    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
                    ingested_tables.append(table_name)
        except Exception as e:
            print(f"    ❌ خطا در خواندن {xlsx_file.name}: {e}")

    # ۳. تولید گزارش نهایی و ایندکس‌گذاری
    print("\n📊 در حال ایجاد ایندکس‌های تحلیلی و تولید گزارش...")
    
    # مثال: ایجاد ایندکس روی ستون‌های تاریخ و شناسه سایت برای کوئری‌های سریع موتورهای علمی
    for table in ingested_tables:
        if 'site_id' in [col[0] for col in con.execute(f"PRAGMA table_info('{table}')").fetchall()]:
            con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_site ON {table}(site_id)")
        if 'date' in [col[0] for col in con.execute(f"PRAGMA table_info('{table}')").fetchall()]:
            con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table}(date)")

    # محاسبه حجم نهایی دیتابیس
    db_size_mb = OUTPUT_DB.stat().st_size / (1024 * 1024)
    
    con.close()
    
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("✅ عملیات تیم تحقیقاتی با موفقیت پایان یافت!")
    print(f"🔹 تعداد جداول ایجاد شده: {len(ingested_tables)}")
    print(f"🔹 زمان صرف شده: {elapsed:.2f} ثانیه")
    print(f"🔹 حجم پایگاه داده تحلیلی (DuckDB): {db_size_mb:.2f} مگابایت")
    print(f"🔹 مسیر فایل: {OUTPUT_DB}")
    print("="*60)
    print("💡 نکته: موتورهای علمی (AquaCrop, SWAT) اکنون می‌توانند با یک کوئری SQL ساده")
    print("   به تمام داده‌های اقلیمی و زراعی از طریق این فایل واحد دسترسی داشته باشند.")

if __name__ == "__main__":
    if not MANUAL_DATA_DIR.exists():
        print(f"❌ پوشه '{MANUAL_DATA_DIR}' یافت نشد. لطفاً مسیر را بررسی کنید.")
    else:
        build_analytics_core()