#!/usr/bin/env python3
"""
Patch fix_pnpm_v11.py
=====================
اصلاح دو مشکل:
1. افزودن DIM و UNDERLINE به کلاس Colors
2. idempotent کردن cleanup_package_json
"""

import structlog

logger = structlog.get_logger()
import re
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "fix_pnpm_v11.py"


def patch_colors_class(text: str) -> str:
    """افزودن DIM و UNDERLINE به کلاس Colors"""
    # اگر DIM قبلاً وجود دارد، نیازی نیست
    if "DIM = " in text and "UNDERLINE = " in text:
        logger.info("  ℹ کلاس Colors قبلاً کامل است")
        return text

    # افزودن DIM و UNDERLINE بعد از BOLD
    pattern = r'(    BOLD = "\\033\[1m"\n)'
    replacement = r'\1    DIM = "\\033[2m"\n    UNDERLINE = "\\033[4m"\n'

    new_text, count = re.subn(pattern, replacement, text, count=1)

    if count == 0:
        logger.info("  ✗ الگوی BOLD یافت نشد")
        return text

    logger.info("  ✓ DIM و UNDERLINE به کلاس Colors اضافه شد")
    return new_text


def patch_cleanup_idempotent(text: str) -> str:
    """idempotent کردن cleanup_package_json"""
    # تغییر "return len(cleaned) > 0" به return True
    old_return = "return len(cleaned) > 0"
    new_return = "return True  # idempotent: success even if already clean"

    if old_return not in text:
        # بررسی اینکه آیا قبلاً پچ شده
        if "idempotent" in text:
            logger.info("  ℹ cleanup_package_json قبلاً idempotent است")
            return text
        logger.info("  ⚠ الگوی مورد انتظار یافت نشد")
        return text

    new_text = text.replace(old_return, new_return, 1)
    logger.info("  ✓ cleanup_package_json idempotent شد")
    return new_text


def main() -> int:
    logger.info("=" * 70)
    logger.info("  🔧 Patch fix_pnpm_v11.py")
    logger.info("=" * 70)
    logger.info()

    if not SCRIPT.exists():
        logger.info(f"✗ فایل یافت نشد: {SCRIPT}")
        return 1

    logger.info(f"📄 فایل هدف: {SCRIPT}")
    logger.info()

    # خواندن محتوای فعلی
    try:
        text = SCRIPT.read_text(encoding="utf-8")
    except Exception as e:
        logger.info(f"✗ خطا در خواندن فایل: {e}")
        return 1

    original_size = len(text)
    logger.info(f"  حجم اولیه: {original_size:,} کاراکتر")
    logger.info()

    # اعمال پچ‌ها
    logger.info("گام ۱: اصلاح کلاس Colors")
    text = patch_colors_class(text)
    logger.info()

    logger.info("گام ۲: idempotent کردن cleanup_package_json")
    text = patch_cleanup_idempotent(text)
    logger.info()

    # ذخیره
    try:
        SCRIPT.write_text(text, encoding="utf-8")
        new_size = len(text)
        logger.info(f"  حجم نهایی: {new_size:,} کاراکتر")
        logger.info(f"  تغییر: +{new_size - original_size} کاراکتر")
    except Exception as e:
        logger.info(f"✗ خطا در ذخیره فایل: {e}")
        return 1

    logger.info()
    logger.info("=" * 70)
    logger.info("  ✅ Patch با موفقیت اعمال شد!")
    logger.info("=" * 70)
    logger.info()
    logger.info("  حالا اجرا کنید:")
    logger.info(f"    python {SCRIPT.relative_to(Path.cwd())}")
    logger.info()

    return 0


if __name__ == "__main__":
    sys.exit(main())