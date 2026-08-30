#!/usr/bin/env python3
"""اسکریپت تشخیص دقیق ستون‌های جداول مشکل‌دار"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "eco_nojin_master.duckdb"

def diagnose():
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # جداولی که خطا دارند
    problem_tables = ["ref_rules", "ref_fertilizers", "ref_sites", "ref_decision_engine"]
    
    print("🔬 تشخیص دقیق ستون‌های جداول مشکل‌دار:")
    print("="*70)
    
    for table in problem_tables:
        try:
            columns = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            col_names = [col[1] for col in columns]
            
            # شمارش رکوردها
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            
            print(f"\n📋 جدول: {table} ({count} رکورد)")
            print(f"   ستون‌ها ({len(col_names)}):")
            for i, col in enumerate(col_names, 1):
                print(f"      {i:2}. {col}")
                
            # نمایش یک نمونه داده
            if count > 0:
                sample = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchdf()
                print(f"\n   📊 نمونه داده:")
                for col in col_names[:5]:  # فقط ۵ ستون اول
                    val = sample[col].iloc[0] if col in sample.columns else "N/A"
                    print(f"      {col}: {val}")
                    
        except Exception as e:
            print(f"\n❌ خطا در جدول {table}: {e}")
    
    # بررسی سایت‌های موجود در ماتریس تصمیم‌گیری
    print("\n" + "="*70)
    print("🌍 سایت‌های موجود در ماتریس تصمیم‌گیری:")
    try:
        sites = conn.execute("""
            SELECT DISTINCT site_id 
            FROM ref_decision_engine 
            ORDER BY site_id 
            LIMIT 20
        """).fetchdf()
        print(f"   {len(sites)} سایت یافت شد:")
        print(f"   {', '.join(sites['site_id'].tolist())}")
    except Exception as e:
        print(f"   ❌ خطا: {e}")
    
    conn.close()

if __name__ == "__main__":
    diagnose()