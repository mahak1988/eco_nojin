#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - رفع تمام خطاهای Chrome icon
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")

def fix_file(file_path: Path) -> bool:
    """رفع Chrome در یک فایل"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # حذف Chrome از import
        content = re.sub(r'\bChrome,\s*', '', content)
        content = re.sub(r',\s*Chrome\b', '', content)
        content = re.sub(r'\bChrome\b(?=\s*})', '', content)
        
        # جایگزینی استفاده از Chrome
        content = content.replace('<Chrome', '<Globe')
        content = content.replace('Chrome />', 'Globe />')
        content = content.replace('Chrome size=', 'Globe size=')
        content = content.replace('Chrome color=', 'Globe color=')
        
        # اطمینان از وجود Globe در import اگر استفاده شده
        if 'Globe' in content and "from 'lucide-react'" in content:
            if 'Globe,' not in content and ', Globe' not in content:
                content = content.replace(
                    "} from 'lucide-react';",
                    "Globe,\n} from 'lucide-react';"
                )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        log(f"خطا در {file_path}: {e}", "X")
        return False

def clear_vite_cache():
    """پاک کردن cache vite"""
    cache_dirs = [
        FRONTEND_ROOT / "node_modules" / ".vite",
        FRONTEND_ROOT / "node_modules" / ".vite-temp",
    ]
    
    import shutil
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            log(f"Cache پاک شد: {cache_dir}", "+")

def main():
    print("\n" + "=" * 70)
    print("  🔧 رفع تمام خطاهای Chrome icon")
    print("=" * 70 + "\n")
    
    # اسکن تمام فایل‌های TSX
    tsx_files = list(FRONTEND_ROOT.rglob("*.tsx"))
    ts_files = list(FRONTEND_ROOT.rglob("*.ts"))
    all_files = tsx_files + ts_files
    
    fixed_count = 0
    for file_path in all_files:
        # نادیده گرفتن node_modules
        if "node_modules" in str(file_path):
            continue
        
        if fix_file(file_path):
            log(f"اصلاح شد: {file_path.relative_to(FRONTEND_ROOT)}", "+")
            fixed_count += 1
    
    # پاک کردن cache
    clear_vite_cache()
    
    print("\n" + "=" * 70)
    print(f"  ✅ {fixed_count} فایل اصلاح شد")
    print("=" * 70)
    print("\n  🚀 اجرا:")
    print("     cd frontend")
    print("     pnpm run dev")
    print("\n  ⚠️  اگر هنوز صفحه سفید است:")
    print("     1. Ctrl+C برای توقف سرور")
    print("     2. rm -rf node_modules/.vite")
    print("     3. pnpm run dev")
    print("\n  💡 درباره هشدارهای MetaMask:")
    print("     این هشدارها از browser extension هستند، نه از کد شما.")
    print("     می‌توانید آنها را نادیده بگیرید.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())