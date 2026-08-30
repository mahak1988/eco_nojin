#!/usr/bin/env python3
"""
Fix Vite Config Warning
========================
جایگزینی __dirname با import.meta.dirname در vite.config.ts
"""

import sys
from pathlib import Path

VITE_CONFIG = Path(__file__).parent.parent.parent / "frontend" / "vite.config.ts"


def main() -> int:
    print("=" * 70)
    print("  🔧 اصلاح vite.config.ts")
    print("=" * 70)
    print()

    if not VITE_CONFIG.exists():
        print(f"✗ فایل یافت نشد: {VITE_CONFIG}")
        return 1

    text = VITE_CONFIG.read_text(encoding="utf-8")

    # شمارش تعداد __dirname
    count = text.count("__dirname")
    print(f"  تعداد __dirname یافت شده: {count}")

    if count == 0:
        print("  ℹ هیچ __dirname یافت نشد - فایل مدرن است")
        return 0

    # پشتیبان‌گیری
    backup = VITE_CONFIG.with_suffix(".ts.dirname-backup")
    backup.write_text(text, encoding="utf-8")
    print(f"  ✓ پشتیبان: {backup.name}")

    # جایگزینی
    new_text = text.replace("__dirname", "import.meta.dirname")
    VITE_CONFIG.write_text(new_text, encoding="utf-8")

    print(f"  ✓ جایگزین شد: __dirname → import.meta.dirname")
    print(f"  ✓ فایل ذخیره شد: {VITE_CONFIG}")
    print()
    print("  💡 حالا warning Vite رفع شده است")
    return 0


if __name__ == "__main__":
    sys.exit(main())