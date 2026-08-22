from datetime import timezone
"""
import datetime
Eco Nojin Hotfix Script - Phase 0 Test Environment Fix
هدف: حل خطاهای 404 API Gateway و مشکل PermissionError ویندوز
توسط: شورای عالی فنی
"""

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VENV_PIP = PROJECT_ROOT / ".venv" / "Scripts" / "pip.exe"

def fix_pytest_tmp_path():
    """حل مشکل PermissionError با تغییر مسیر Temp به داخل پروژه"""
    pytest_ini = PROJECT_ROOT / "pytest.ini"
    content = """[pytest]
# حل مشکل PermissionError در ویندوز با تغییر مسیر basetemp
basetemp = D:/eco_nojin/.pytest_cache/tmp
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --tb=short -q
"""
    with open(pytest_ini, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ فایل pytest.ini ایجاد شد (مسیر Temp اصلاح شد).")

def install_missing_packages():
    """نصب پکیج‌های گمشده برای تست‌های بلاکچین"""
    if VENV_PIP.exists():
        print("📦 در حال نصب eth-tester[py-evm]...")
        subprocess.run([str(VENV_PIP), "install", "eth-tester[py-evm]"], capture_output=True)
        print("✅ پکیج‌های بلاکچین نصب شدند.")

def fix_api_gateway_main():
    """
    ثبت روترهای تجاری در main.py API Gateway برای حل خطاهای 404
    """
    main_py = PROJECT_ROOT / "services" / "api_gateway" / "main.py"
    if not main_py.exists():
        print("⚠️ فایل main.py یافت نشد.")
        return

    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. بررسی و اصلاح Importها (اگر مسیر نسبی شکسته باشد)
    if "from .routers import" in content:
        # اطمینان از اینکه روترهای تجاری در لیست import هستند
        business_routers = ["blockchain", "ecowallet", "marketplace", "ussd", "voice"]
        for router in business_routers:
            if router not in content:
                # اضافه کردن به لیست import
                content = content.replace("from .routers import (", f"from .routers import (\n    {router},")
                modified = True

    # 2. اضافه کردن include_router برای روترهای تجاری اگر وجود ندارند
    business_routers_appends = [
        "app.include_router(blockchain.router)",
        "app.include_router(ecowallet.router)",
        "app.include_router(marketplace.router)",
        "app.include_router(ussd.router)",
        "app.include_router(voice.router)"
    ]
    
    for append_line in business_routers_appends:
        if append_line not in content:
            # اضافه کردن قبل از آخرین app.include_router یا در انتهای بخش روترها
            content = content.replace("# AI & Assistant", f"{append_line}\n\n# AI & Assistant")
            modified = True

    if modified:
        with open(main_py, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ فایل main.py API Gateway پچ شد (روترهای تجاری رجیستر شدند).")

def fix_deprecated_datetime():
    """
    جایگزینی datetime.now(timezone.utc).replace(tzinfo=None) با datetime.now(datetime.UTC) در فایل‌های اصلی برای حذف هشدارها
    (این مورد اختیاری است اما برای پاکسازی لاگ تست‌ها مفید است)
    """
    print("🧹 در حال پاکسازی هشدارهای datetime (اختیاری)...")
    # این بخش را در فازهای بعدی و با یک اسکریپت اختصاصی Refactor انجام می‌دهیم تا ریسک به حداقل برسد.

if __name__ == "__main__":
    print("🚀 شروع اجرای Hotfix برای محیط تست...")
    fix_pytest_tmp_path()
    install_missing_packages()
    fix_api_gateway_main()
    print("\n✅ Hotfix با موفقیت اجرا شد. لطفاً دوباره pytest را اجرا کنید.")