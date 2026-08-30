#!/usr/bin/env python3
"""
Bootstrap Script - Phase 0
==========================
نقطه شروع همه اسکریپت‌های پروژه.
این فایل ابتدا utils و سپس ساختار پوشه‌ها را ایجاد می‌کند.
"""

import os
import sys
from pathlib import Path

# مسیر ریشه پروژه
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
UTILS_DIR = SCRIPTS_DIR / "utils"
PHASE0_DIR = SCRIPTS_DIR / "phase0"

def create_directory(path: Path) -> None:
    """ایجاد پوشه اگر وجود نداشته باشد"""
    path.mkdir(parents=True, exist_ok=True)
    print(f"✓ پوشه ایجاد/تأیید شد: {path}")

def create_file(path: Path, content: str) -> None:
    """ایجاد فایل با محتوای مشخص"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"✓ فایل ایجاد شد: {path}")

def main() -> int:
    print("=" * 70)
    print("  eco_nojin Bootstrap - ایجاد ساختار اسکریپت‌ها")
    print("=" * 70)
    
    # ایجاد ساختار پوشه‌ها
    create_directory(UTILS_DIR)
    create_directory(PHASE0_DIR)
    
    # ایجاد __init__.py ها
    for d in [SCRIPTS_DIR, UTILS_DIR, PHASE0_DIR]:
        init_file = d / "__init__.py"
        if not init_file.exists():
            create_file(init_file, '"""Script package."""\n')
    
    print("\n" + "=" * 70)
    print("  ساختار پایه ایجاد شد. حالا utils را ایجاد می‌کنیم...")
    print("=" * 70 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())