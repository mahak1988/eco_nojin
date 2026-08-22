"""
Eco Nojin Refactoring Script - Phase 0.5
هدف: جداسازی ماژول‌های کسب‌وکاری از موتور علمی (HyDroMa)
توسط: شورای عالی فنی
وضعیت: آماده اجرا (با قابلیت به‌روزرسانی خودکار Importها)
"""

import os
import shutil
import re
from pathlib import Path
from datetime import datetime

# ==============================================================================
# 1. پیکربندی (Configuration)
# ==============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
HYDROMA_ROOT = PROJECT_ROOT / "engine" / "hydroma"
BUSINESS_ROOT = PROJECT_ROOT / "services" / "business_modules"

# ماژول‌هایی که باید منتقل شوند
TARGET_MODULES = [
    "blockchain", "ecowallet", "insurance", 
    "marketplace", "ussd", "voice"
]

LOG_FILE = PROJECT_ROOT / "sandbox" / "audit_reports" / f"refactor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

# ==============================================================================
# 2. توابع جابجایی و به‌روزرسانی (Migration & Update Logic)
# ==============================================================================

def move_modules():
    """جابجایی فیزیکی دایرکتوری‌ها"""
    if not BUSINESS_ROOT.exists():
        BUSINESS_ROOT.mkdir(parents=True, exist_ok=True)
        log(f"✅ دایرکتوری مقصد ساخته شد: {BUSINESS_ROOT}")

    for module in TARGET_MODULES:
        src = HYDROMA_ROOT / module
        dst = BUSINESS_ROOT / module
        
        if src.exists() and src.is_dir():
            try:
                shutil.move(str(src), str(dst))
                log(f"📦 ماژول '{module}' با موفقیت از موتور علمی به لایه کسب‌وکار منتقل شد.")
            except Exception as e:
                log(f"❌ خطا در انتقال '{module}': {e}")
        else:
            log(f"⚠️ ماژول '{module}' در مسیر مبدأ یافت نشد.")

    # ایجاد فایل __init__.py برای اینکه دایرکتوری جدید به عنوان پکیج پایتون شناخته شود
    init_file = BUSINESS_ROOT / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def update_imports():
    """جستجو و جایگزینی هوشمند در تمام فایل‌های پایتون پروژه"""
    log("🔍 شروع اسکن کل پروژه برای به‌روزرسانی Importها...")
    
    # الگوهای جستجو و جایگزینی
    # مثال: from services.business_modules.blockchain import X -> from services.business_modules.blockchain import X
    replacements = {
        module: f"services.business_modules.{module}" for module in TARGET_MODULES
    }
    
    files_updated = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # نادیده گرفتن فایل‌های داخل محیط مجازی و پوشه‌های پنهان
        if ".venv" in str(py_file) or "__pycache__" in str(py_file) or ".git" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            new_content = content
            modified = False
            
            for module, new_path in replacements.items():
                # الگوی 1: from engine.hydroma.module import ...
                pattern1 = rf"from\s+engine\.hydroma\.{module}\s+import"
                if re.search(pattern1, new_content):
                    new_content = re.sub(pattern1, f"from {new_path} import", new_content)
                    modified = True
                
                # الگوی 2: import engine.hydroma.module
                pattern2 = rf"import\s+engine\.hydroma\.{module}"
                if re.search(pattern2, new_content):
                    new_content = re.sub(pattern2, f"import {new_path}", new_content)
                    modified = True
                    
                # الگوی 3: از روت پروژه (اگر به صورت نسبی باشد ممکن است نیاز به بررسی دستی داشته باشد)
                if f"engine.hydroma.{module}" in new_content:
                    new_content = new_content.replace(f"engine.hydroma.{module}", new_path)
                    modified = True

            if modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_updated += 1
                log(f"🔄 فایل '{py_file.relative_to(PROJECT_ROOT)}' به‌روزرسانی شد.")
                
        except Exception as e:
            log(f"⚠️ خطا در پردازش فایل '{py_file}': {e}")
            
    log(f"✅ به‌روزرسانی تمام شد. تعداد {files_updated} فایل اصلاح شد.")

# ==============================================================================
# 3. اجرای اصلی (Main Execution)
# ==============================================================================

if __name__ == "__main__":
    print("🚀 شروع عملیات جداسازی معماری (Phase 0.5)...")
    print("⚠️ هشدار: لطفاً مطمئن شوید که تغییرات در Git ثبت شده است.")
    
    # اجرای جابجایی
    move_modules()
    
    # اجرای به‌روزرسانی ارجاعات
    update_imports()
    
    print("\n✅ عملیات جداسازی با موفقیت به پایان رسید.")
    print(f"📄 گزارش کامل ذخیره شد در: {LOG_FILE}")
    print("👉 گام بعدی: اجرای تست‌های پایه برای اطمینان از عدم شکستن کدها.")