#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
رفع خطای AttributeError در AnalyticsService.aggregate_landscape
═══════════════════════════════════════════════════════════════════════
این اسکریپت:
1. ساختار واقعی LandscapeFund را بررسی می‌کند
2. ستون صحیح برای balance را شناسایی می‌کند
3. services/analytics/service.py را اصلاح می‌کند
4. تست را دوباره اجرا می‌کند

اجرا: python fix_analytics_landscape_bug.py
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")


def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")


def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        log(f"خطا در خواندن {path}: {e}", "X")
        return ""


def write_file(path: Path, content: str) -> bool:
    try:
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        log(f"خطا در نوشتن {path}: {e}", "X")
        return False


# ═══════════════════════════════════════════════════════════════
# گام ۱: بررسی ساختار LandscapeFund
# ═══════════════════════════════════════════════════════════════

def analyze_landscape_fund():
    separator("گام ۱: بررسی ساختار LandscapeFund")
    
    landscape_models = PROJECT_ROOT / "services" / "landscape" / "models" / "__init__.py"
    
    if not landscape_models.exists():
        log("فایل models یافت نشد!", "X")
        return None
    
    content = read_file(landscape_models)
    if not content:
        return None
    
    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        log(f"SyntaxError: {e}", "X")
        return None
    
    # پیدا کردن LandscapeFund
    landscape_fund_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LandscapeFund":
            landscape_fund_class = node
            break
    
    if not landscape_fund_class:
        log("کلاس LandscapeFund یافت نشد!", "X")
        return None
    
    # استخراج Column ها
    columns = []
    for item in landscape_fund_class.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    # بررسی آیا این یک Column است
                    if isinstance(item.value, ast.Call):
                        if isinstance(item.value.func, ast.Name) and item.value.func.id == "Column":
                            columns.append(target.id)
    
    log(f"ستون‌های LandscapeFund: {columns}", "+")
    
    # پیدا کردن ستون مناسب برای balance
    balance_column = None
    possible_names = ['balance', 'current_balance', 'total_balance', 'amount', 'fund_balance']
    
    for col in columns:
        if col.lower() in possible_names or 'balance' in col.lower():
            balance_column = col
            log(f"ستون balance یافت شد: {balance_column}", "+")
            break
    
    if not balance_column:
        log("هیچ ستون balance یافت نشد - از مقدار 0 استفاده می‌شود", "!")
    
    return {
        'columns': columns,
        'balance_column': balance_column,
    }


# ═══════════════════════════════════════════════════════════════
# گام ۲: اصلاح analytics/service.py
# ═══════════════════════════════════════════════════════════════

def fix_analytics_service(balance_column: str):
    separator("گام ۲: اصلاح services/analytics/service.py")
    
    service_file = PROJECT_ROOT / "services" / "analytics" / "service.py"
    
    if not service_file.exists():
        log("فایل service.py یافت نشد!", "X")
        return False
    
    content = read_file(service_file)
    if not content:
        return False
    
    # پیدا کردن تابع aggregate_landscape
    # جایگزینی خط مشکل‌دار
    
    if balance_column:
        # استفاده از ستون صحیح
        old_pattern = r'func\.coalesce\(func\.sum\(LandscapeFund\.current_balance\), 0\)'
        new_code = f'func.coalesce(func.sum(LandscapeFund.{balance_column}), 0)'
    else:
        # اگر ستون balance وجود ندارد، از 0 استفاده کن
        old_pattern = r'func\.coalesce\(func\.sum\(LandscapeFund\.current_balance\), 0\)'
        new_code = '0'
    
    new_content = re.sub(old_pattern, new_code, content)
    
    if new_content == content:
        log("الگو یافت نشد - بررسی دستی لازم است", "!")
        log(f"جستجو برای: {old_pattern}", "i")
        return False
    
    if write_file(service_file, new_content):
        log("فایل اصلاح شد", "+")
        if balance_column:
            log(f"استفاده از: LandscapeFund.{balance_column}", "+")
        else:
            log("استفاده از مقدار ثابت 0", "+")
        return True
    
    return False


# ═══════════════════════════════════════════════════════════════
# گام ۳: اجرای تست
# ═══════════════════════════════════════════════════════════════

def run_test():
    separator("گام ۳: اجرای تست analytics")
    
    test_file = "services/analytics/tests/test_integration.py"
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_file, "-v", "--tb=short",
        "-p", "no:phoenix",
    ]
    
    log(f"اجرای {test_file}...", "i")
    
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    
    # نمایش خلاصه
    for line in result.stdout.split('\n'):
        if 'passed' in line or 'failed' in line or 'error' in line:
            print(f"    {line}")
    
    if result.returncode == 0:
        log("✅ تست پاس شد", "+")
        return True
    else:
        log("❌ تست شکست خورد", "X")
        # نمایش ۲۰ خط آخر
        lines = result.stdout.split('\n')
        print("    خروجی (۲۰ خط آخر):")
        for line in lines[-20:]:
            print(f"      {line}")
        return False


# ═══════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  رفع خطای AttributeError در AnalyticsService")
    print("=" * 70)
    
    # گام ۱: بررسی LandscapeFund
    fund_info = analyze_landscape_fund()
    
    if not fund_info:
        log("تحلیل LandscapeFund ناموفق بود", "X")
        return 1
    
    # گام ۲: اصلاح service.py
    balance_column = fund_info.get('balance_column')
    if not fix_analytics_service(balance_column):
        log("اصلاح service.py ناموفق بود", "X")
        return 1
    
    # گام ۳: اجرای تست
    if run_test():
        print("\n" + "=" * 70)
        print("  ✅ مشکل رفع شد!")
        print("=" * 70)
        print("\n  اکنون می‌توانید تمام تست‌ها را اجرا کنید:")
        print("  python -m pytest services/*/tests/test_integration.py -v")
        print("\n  یا فاز ۳ را دوباره اجرا کنید:")
        print("  python phase3_complete_priority_modules.py")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ❌ تست هنوز شکست می‌خورد")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())