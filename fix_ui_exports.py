#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""رفع خطای export در ui/index.ts"""

from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")

def fix_ui_index():
    """اضافه کردن exports به ui/index.ts"""
    print("\n" + "=" * 70)
    print("  🔧 رفع خطای export در ui/index.ts")
    print("=" * 70 + "\n")
    
    index_path = FRONTEND_ROOT / 'src' / 'components' / 'ui' / 'index.ts'
    
    if not index_path.exists():
        log("ui/index.ts یافت نشد!", "X")
        return False
    
    content = index_path.read_text(encoding='utf-8')
    
    # لیست exports که باید اضافه شوند
    new_exports = [
        "Modal",
        "Tabs", 
        "ProgressRing",
    ]
    
    # اضافه کردن exports جدید
    for export_name in new_exports:
        if export_name not in content:
            content += f"\nexport {{ {export_name} }} from './{export_name}';\n"
            log(f"اضافه شد: export {{ {export_name} }}", "+")
        else:
            log(f"از قبل وجود دارد: {export_name}", "✓")
    
    # ذخیره فایل
    index_path.write_text(content, encoding='utf-8')
    
    print("\n" + "=" * 70)
    print("  ✅ ui/index.ts به‌روزرسانی شد")
    print("=" * 70)
    print("\n  🚀 اجرا:")
    print("     cd frontend")
    print("     pnpm run dev")
    print("\n  📊 تست:")
    print("     http://localhost:5173/simulator")
    
    return True

if __name__ == "__main__":
    import sys
    success = fix_ui_index()
    sys.exit(0 if success else 1)