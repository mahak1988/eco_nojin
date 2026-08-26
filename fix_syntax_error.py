#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""رفع سریع خطای Syntax در فایل‌های Auth"""

import re
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")

def fix_syntax_errors():
    print("\n" + "=" * 70)
    print("  🔧 رفع خطای Syntax در import ها")
    print("=" * 70 + "\n")
    
    # اسکن تمام فایل‌های TSX
    tsx_files = list(FRONTEND_ROOT.rglob("*.tsx"))
    fixed_count = 0
    
    for file_path in tsx_files:
        if "node_modules" in str(file_path):
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            original = content
            
            # الگوی خطا: Wallet Globe (بدون کاما)
            content = re.sub(r'\bWallet\s+Globe\b', 'Wallet, Globe', content)
            
            # الگوهای مشابه دیگر
            content = re.sub(r'\bWallet\s+Mail\b', 'Wallet, Mail', content)
            content = re.sub(r'\bWallet\s+Lock\b', 'Wallet, Lock', content)
            content = re.sub(r'\bWallet\s+Eye\b', 'Wallet, Eye', content)
            content = re.sub(r'\bWallet\s+Loader\b', 'Wallet, Loader', content)
            content = re.sub(r'\bWallet\s+Loader2\b', 'Wallet, Loader2', content)
            content = re.sub(r'\bGlobe\s+Mail\b', 'Globe, Mail', content)
            
            # حذف کاماهای تکراری (اگر ایجاد شد)
            content = re.sub(r',\s*,', ',', content)
            
            # حذف کاما قبل از } (اگر ایجاد شد)
            content = re.sub(r',\s*}', ' }', content)
            
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                log(f"اصلاح شد: {file_path.relative_to(FRONTEND_ROOT)}", "+")
                fixed_count += 1
        except Exception as e:
            log(f"خطا در {file_path}: {e}", "X")
    
    print("\n" + "=" * 70)
    print(f"  ✅ {fixed_count} فایل اصلاح شد")
    print("=" * 70)
    print("\n  🚀 اجرا:")
    print("     cd frontend")
    print("     pnpm run dev")
    
    return fixed_count > 0

if __name__ == "__main__":
    import sys
    fix_syntax_errors()
    sys.exit(0)