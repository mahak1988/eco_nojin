#!/usr/bin/env python3
"""
اصلاح خطای بحرانی R13_amazon_rainforest
مشکل: Ksat=10mm/h برای بافت clay غیرواقعی است
راه‌حل: کاهش به 4mm/h (واقع‌بینانه برای Ferralsol رسی)
"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
CHALLENGE_FILE = PROJECT_ROOT / "tests" / "challenge_25_scientists.py"

def fix_r13_ksat():
    print("=" * 70)
    print("اصلاح خطای بحرانی R13_amazon_rainforest")
    print("=" * 70)
    
    if not CHALLENGE_FILE.exists():
        print(f"❌ فایل یافت نشد: {CHALLENGE_FILE}")
        return False
    
    content = CHALLENGE_FILE.read_text(encoding="utf-8")
    
    # الگوی جستجو برای ksat در منطقه R13
    # باید فقط در بلاک R13 تغییر کند
    old_pattern = r'("R13_amazon_rainforest":\s*\{[^}]*"ksat_mm_h":\s*)10\.0'
    new_value = r'\g<1>4.0'
    
    new_content, count = re.subn(old_pattern, new_value, content, flags=re.DOTALL)
    
    if count == 0:
        print("⚠️ الگوی مورد نظر یافت نشد")
        return False
    
    if count > 1:
        print(f"⚠️ {count} مورد یافت شد (باید فقط ۱ مورد باشد)")
        return False
    
    CHALLENGE_FILE.write_text(new_content, encoding="utf-8")
    print("✅ Ksat منطقه R13 از 10.0 به 4.0 mm/h اصلاح شد")
    print("   توجیه: Ferralsol رسی با ساختار aggregate")
    print("=" * 70)
    return True

if __name__ == "__main__":
    if fix_r13_ksat():
        print("\n📋 گام بعدی:")
        print("   python tests/challenge_25_scientists.py")