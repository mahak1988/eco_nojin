#!/usr/bin/env python3
"""
Patch fix_pnpm_v11.py
=====================
اصلاح دو مشکل:
1. افزودن DIM و UNDERLINE به کلاس Colors
2. idempotent کردن cleanup_package_json
"""

import re
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "fix_pnpm_v11.py"


def patch_colors_class(text: str) -> str:
    """افزودن DIM و UNDERLINE به کلاس Colors"""
    # اگر DIM قبلاً وجود دارد، نیازی نیست
    if "DIM = " in text and "UNDERLINE = " in text:
        print("  ℹ کلاس Colors قبلاً کامل است")
        return text

    # افزودن DIM و UNDERLINE بعد از BOLD
    pattern = r'(    BOLD = "\\033\[1m"\n)'
    replacement = r'\1    DIM = "\\033[2m"\n    UNDERLINE = "\\033[4m"\n'

    new_text, count = re.subn(pattern, replacement, text, count=1)

    if count == 0:
        print("  ✗ الگوی BOLD یافت نشد")
        return text

    print("  ✓ DIM و UNDERLINE به کلاس Colors اضافه شد")
    return new_text


def patch_cleanup_idempotent(text: str) -> str:
    """idempotent کردن cleanup_package_json"""
    # تغییر "return len(cleaned) > 0" به return True
    old_return = "return len(cleaned) > 0"
    new_return = "return True  # idempotent: success even if already clean"

    if old_return not in text:
        # بررسی اینکه آیا قبلاً پچ شده
        if "idempotent" in text:
            print("  ℹ cleanup_package_json قبلاً idempotent است")
            return text
        print("  ⚠ الگوی مورد انتظار یافت نشد")
        return text

    new_text = text.replace(old_return, new_return, 1)
    print("  ✓ cleanup_package_json idempotent شد")
    return new_text


def main() -> int:
    print("=" * 70)
    print("  🔧 Patch fix_pnpm_v11.py")
    print("=" * 70)
    print()

    if not SCRIPT.exists():
        print(f"✗ فایل یافت نشد: {SCRIPT}")
        return 1

    print(f"📄 فایل هدف: {SCRIPT}")
    print()

    # خواندن محتوای فعلی
    try:
        text = SCRIPT.read_text(encoding="utf-8")
    except Exception as e:
        print(f"✗ خطا در خواندن فایل: {e}")
        return 1

    original_size = len(text)
    print(f"  حجم اولیه: {original_size:,} کاراکتر")
    print()

    # اعمال پچ‌ها
    print("گام ۱: اصلاح کلاس Colors")
    text = patch_colors_class(text)
    print()

    print("گام ۲: idempotent کردن cleanup_package_json")
    text = patch_cleanup_idempotent(text)
    print()

    # ذخیره
    try:
        SCRIPT.write_text(text, encoding="utf-8")
        new_size = len(text)
        print(f"  حجم نهایی: {new_size:,} کاراکتر")
        print(f"  تغییر: +{new_size - original_size} کاراکتر")
    except Exception as e:
        print(f"✗ خطا در ذخیره فایل: {e}")
        return 1

    print()
    print("=" * 70)
    print("  ✅ Patch با موفقیت اعمال شد!")
    print("=" * 70)
    print()
    print("  حالا اجرا کنید:")
    print(f"    python {SCRIPT.relative_to(Path.cwd())}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())