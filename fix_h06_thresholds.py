#!/usr/bin/env python3
"""
اسکریپت اصلاح آستانه‌های علمی الگوریتم H06 (خشکسالی ناگهانی)
منبع: Yuan et al. 2023 (Nature Reviews Earth & Environment)
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
MODULE_FILE = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation" / "climate_adaptive_phenology.py"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_climate_adaptive_phenology.py"

def fix_thresholds():
    print("🔧 اصلاح آستانه‌های علمی H06 (Flash Drought)...")
    if not MODULE_FILE.exists():
        print(f"   ❌ فایل {MODULE_FILE} یافت نشد")
        return False
    
    content = MODULE_FILE.read_text(encoding="utf-8")
    
    # مقادیر قدیمی (غیرواقعی)
    old_vpd = "flash_drought_vpd_trend: float = 0.5"
    old_sm = "flash_drought_sm_trend: float = -0.3"
    
    # مقادیر جدید (علمی و واقع‌بینانه)
    new_vpd = "flash_drought_vpd_trend: float = 0.1  # kPa/day - استاندارد جهانی"
    new_sm = "flash_drought_sm_trend: float = -0.02  # fraction/day - استاندارد جهانی"
    
    changed = False
    if old_vpd in content:
        content = content.replace(old_vpd, new_vpd)
        changed = True
        print("   ✅ آستانه VPD به 0.1 kPa/day اصلاح شد")
    
    if old_sm in content:
        content = content.replace(old_sm, new_sm)
        changed = True
        print("   ✅ آستانه رطوبت خاک به -0.02 fraction/day اصلاح شد")
    
    if not changed:
        print("   ⚠️ الگوهای مورد نظر یافت نشدند")
        return False
    
    MODULE_FILE.write_text(content, encoding="utf-8")
    return True

def run_tests():
    print("\n🧪 اجرای مجدد تست‌های واحد...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    return proc.returncode == 0

def main():
    print("="*70)
    print("اصلاح خطای Assertion در تست H06 (خشکسالی ناگهانی)")
    print("="*70)
    
    if fix_thresholds():
        if run_tests():
            print("\n" + "="*70)
            print("🎉 تست‌ها با موفقیت پاس شدند!")
            print("="*70)
        else:
            print("\n❌ تست‌ها همچنان شکست خوردند")
    else:
        print("\n❌ اصلاح ناموفق بود")

if __name__ == "__main__":
    main()