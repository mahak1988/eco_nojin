#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - رفع نهایی مشکلات فاز ۲
═══════════════════════════════════════════════════════════════════════
این اسکریپت:
1. numpy و pandas را نصب می‌کند (نیاز plugin phoenix)
2. تست‌ها را با subprocess و پارامترهای صحیح اجرا می‌کند
3. plugin phoenix را غیرفعال می‌کند (-p no:phoenix)
4. خروجی کامل pytest را نمایش می‌دهد

اجرا: python final_phase2_fix.py
"""

import subprocess
import sys
import re
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")


def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")


def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════
# گام ۱: نصب numpy و pandas
# ═══════════════════════════════════════════════════════════════

def step1_install_numpy():
    separator("گام ۱: نصب numpy و pandas")
    
    packages = ['numpy', 'pandas']
    
    for pkg in packages:
        log(f"بررسی {pkg}...", "i")
        try:
            __import__(pkg)
            log(f"{pkg} قبلاً نصب است", "+")
        except ImportError:
            log(f"نصب {pkg}...", "i")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                log(f"{pkg} نصب شد", "+")
            else:
                log(f"خطا در نصب {pkg}: {result.stderr[:200]}", "X")
                return False
    return True


# ═══════════════════════════════════════════════════════════════
# گام ۲: اجرای تست‌ها با subprocess + پارامترهای صحیح
# ═══════════════════════════════════════════════════════════════

def step2_run_tests():
    separator("گام ۲: اجرای تست‌ها")
    
    test_files = [
        "services/marketplace/tests/test_integration.py",
        "services/tourism/tests/test_integration.py",
        "services/landscape/tests/test_integration.py",
    ]
    
    results = {}
    
    for test_file in test_files:
        log(f"\nاجرای {test_file}...", "i")
        print("-" * 70)
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_file,
            "-v",
            "--tb=long",
            "-p", "no:phoenix",  # غیرفعال کردن plugin phoenix
            "-p", "no:arize-phoenix-client",  # نام کامل plugin
            "--no-header",
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        # نمایش خروجی کامل (بدون محدودیت)
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print("-" * 70)
        
        if result.returncode == 0:
            match = re.search(r'(\d+) passed', result.stdout)
            count = match.group(1) if match else "?"
            log(f"{test_file} - {count} تست پاس شد", "+")
            results[test_file] = True
        else:
            log(f"{test_file} - شکست خورد (exit={result.returncode})", "X")
            results[test_file] = False
    
    return results


# ═══════════════════════════════════════════════════════════════
# گام ۳: گزارش نهایی
# ═══════════════════════════════════════════════════════════════

def step3_generate_report(results):
    separator("گام ۳: گزارش نهایی")
    
    from datetime import datetime
    
    all_passed = all(results.values())
    
    report = f"""# گزارش نهایی فاز ۲

**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## اقدامات

1. نصب numpy و pandas (برای سازگاری با plugin phoenix)
2. اجرای تست‌ها با `-p no:phoenix` برای جلوگیری از تداخل plugin
3. حل تداخل models.py با models/__init__.py
4. بازسازی conftest.py در ریشه پروژه

## نتایج تست‌ها

"""
    
    for test_file, passed in results.items():
        icon = "✅" if passed else "❌"
        report += f"- {icon} {test_file}\n"
    
    report += f"\n**وضعیت:** {'موفق' if all_passed else 'ناموفق'}\n"
    
    report_file = PROJECT_ROOT / "FINAL_PHASE2_RESULT.md"
    report_file.write_text(report, encoding='utf-8')
    log(f"گزارش: {report_file}", "+")
    
    return all_passed


# ═══════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  Eco Nojin - رفع نهایی مشکلات فاز ۲")
    print("=" * 70)
    
    # گام ۱: نصب numpy
    if not step1_install_numpy():
        log("نصب numpy شکست خورد", "X")
        return 1
    
    # گام ۲: اجرای تست‌ها
    results = step2_run_tests()
    
    # گام ۳: گزارش
    all_passed = step3_generate_report(results)
    
    # خلاصه
    separator("خلاصه نهایی")
    
    for test_file, passed in results.items():
        icon = "+" if passed else "X"
        print(f"  [{icon}] {test_file}")
    
    if all_passed:
        print("\n  +++ فاز ۲ اکنون کامل است! +++")
        print("\n  گام بعدی: commit")
        print("  git add -A && git commit -m 'phase2: consolidate duplicates'")
        return 0
    else:
        print("\n  [!] برخی تست‌ها شکست خوردند")
        print("  [i] خروجی کامل pytest در بالا قابل مشاهده است")
        return 1


if __name__ == "__main__":
    sys.exit(main())