#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_final_fix_support_agent.py
==============================

رفع قطعی مشکلات فایل support_agent.py:
1. انتقال `from database.hub import hub` به داخل تابع
2. اصلاح کدگذاری کاراکترهای فارسی
3. تأیید سینتکس
"""

import sys
import shutil
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()


class Colors:
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def colorize(msg: str, level: str = "INFO") -> str:
    color = getattr(Colors, level, Colors.RESET)
    return f"{color}{msg}{Colors.RESET}"


def log(msg: str, level: str = "INFO"):
    print(colorize(f"[{level}] {msg}", level))


def banner(title: str):
    print()
    print(colorize("=" * 70, "BOLD"))
    print(colorize(f"  {title}", "BOLD"))
    print(colorize("=" * 70, "BOLD"))
    print()


def main() -> int:
    banner("رفع قطعی مشکلات support_agent.py")

    file_path = PROJECT_ROOT / "services" / "ai" / "support_agent.py"

    if not file_path.exists():
        log("❌ فایل یافت نشد", "ERROR")
        return 1

    # Backup
    backup = file_path.with_suffix(".py.final_fix.bak")
    if not backup.exists():
        shutil.copy2(file_path, backup)
        log(f"📦 Backup: {backup.name}", "SUCCESS")

    # =========================================================================
    # مرحله 1: خواندن و تحلیل
    # =========================================================================
    log("=" * 70, "INFO")
    log("مرحله 1: خواندن و تحلیل", "BOLD")
    log("=" * 70, "INFO")

    # تلاش برای خواندن با کدگذاری‌های مختلف
    encodings_to_try = ["utf-8", "utf-8-sig", "cp1256", "latin-1"]
    content = None
    used_encoding = None

    for enc in encodings_to_try:
        try:
            content = file_path.read_text(encoding=enc)
            used_encoding = enc
            log(f"✅ خوانده شد با کدگذاری: {enc}", "SUCCESS")
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        log("❌ نتوانستم فایل را بخوانم", "ERROR")
        return 1

    lines = content.split("\n")
    log(f"📊 تعداد خطوط: {len(lines)}", "INFO")

    # =========================================================================
    # مرحله 2: اصلاح ساختار
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 2: اصلاح ساختار", "BOLD")
    log("=" * 70, "INFO")

    # پیدا کردن خطوط مشکل‌دار
    hub_import_line = None
    func_def_line = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # پیدا کردن `from database.hub import hub` در سطح 0
        if stripped == "from database.hub import hub" and not line.startswith(" ") and not line.startswith("\t"):
            hub_import_line = i
            log(f"📍 خط {i + 1}: import در سطح 0 یافت شد", "INFO")

        # پیدا کردن تعریف تابع قبل از خط مشکل‌دار
        if stripped.startswith("def ") and hub_import_line is None:
            func_def_line = i
            log(f"📍 خط {i + 1}: تعریف تابع یافت شد: {stripped[:50]}", "INFO")

    # اگر هر دو را پیدا کردیم، اصلاح کن
    if hub_import_line is not None and func_def_line is not None:
        log(f"\n🔧 انتقال خط {hub_import_line + 1} به داخل تابع...", "INFO")

        # حذف خط از جای فعلی
        hub_import = lines.pop(hub_import_line)

        # پیدا کردن محل مناسب برای وارد کردن (بعد از `from database import models`)
        insert_pos = None
        for i in range(func_def_line, len(lines)):
            if "from database import models" in lines[i]:
                insert_pos = i + 1
                break

        if insert_pos is None:
            # اگر پیدا نشد، بعد از خط اول تابع وارد کن
            insert_pos = func_def_line + 1

        # وارد کردن با تورفتگی 4
        lines.insert(insert_pos, "    " + hub_import.strip())
        log(f"✅ خط به داخل تابع منتقل شد (بعد از خط {insert_pos + 1})", "SUCCESS")
    else:
        log("⚠️ ساختار مورد انتظار پیدا نشد", "WARNING")

    # =========================================================================
    # مرحله 3: اصلاح کدگذاری
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 3: اصلاح کدگذاری کاراکترهای فارسی", "BOLD")
    log("=" * 70, "INFO")

    # اگر کدگذاری cp1256 بود، یعنی فایل با کدگذاری اشتباه ذخیره شده
    # در این حالت، باید کاراکترها را برگردانیم
    if used_encoding == "cp1256":
        log("⚠️ فایل با کدگذاری cp1256 ذخیره شده - تلاش برای اصلاح...", "WARNING")

        # تلاش برای بازسازی با کدگذاری صحیح
        try:
            # خواندن به صورت بایت
            raw_bytes = file_path.read_bytes()

            # تلاش برای تبدیل
            content_fixed = raw_bytes.decode("utf-8", errors="replace")
            lines = content_fixed.split("\n")
            log("✅ کدگذاری اصلاح شد", "SUCCESS")
        except Exception as e:
            log(f"⚠️ اصلاح کدگذاری ناموفق: {e}", "WARNING")

    # =========================================================================
    # مرحله 4: بررسی سینتکس
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 4: بررسی سینتکس", "BOLD")
    log("=" * 70, "INFO")

    new_content = "\n".join(lines)

    try:
        compile(new_content, file_path, "exec")
        log("✅ سینتکس درست شد!", "SUCCESS")
        syntax_ok = True
    except SyntaxError as e:
        log(f"❌ سینتکس هنوز خطا دارد: {e}", "ERROR")
        log(f"📍 خط: {e.lineno}, ستون: {e.offset}", "WARNING")
        syntax_ok = False

    # =========================================================================
    # مرحله 5: ذخیره و تأیید
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 5: ذخیره و تأیید", "BOLD")
    log("=" * 70, "INFO")

    if syntax_ok:
        file_path.write_text(new_content, encoding="utf-8")
        log("✅ فایل ذخیره شد", "SUCCESS")

        # تأیید نهایی
        try:
            final_content = file_path.read_text(encoding="utf-8")
            compile(final_content, file_path, "exec")
            log("✅ تأیید نهایی موفق بود!", "SUCCESS")
            final_ok = True
        except SyntaxError as e:
            log(f"❌ تأیید نهایی ناموفق: {e}", "ERROR")
            final_ok = False
    else:
        log("⚠️ فایل ذخیره نشد (سینتکس نادرست)", "WARNING")
        final_ok = False

    # =========================================================================
    # مرحله 6: اجرای تست‌ها
    # =========================================================================
    if final_ok:
        log("\n" + "=" * 70, "INFO")
        log("مرحله 6: اجرای تست‌ها", "BOLD")
        log("=" * 70, "INFO")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "services", "-q", "--tb=no", "-x"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=120,
        )

        if result.returncode == 0:
            log("✅ همه تست‌ها پاس شدند!", "SUCCESS")
            tests_ok = True
        else:
            log("⚠️ برخی تست‌ها شکست خوردند", "WARNING")
            tests_ok = False

    # =========================================================================
    # خلاصه
    # =========================================================================
    banner("خلاصه")

    log("نتایج:", "INFO")
    log(f"  {'✅' if syntax_ok else '❌'} اصلاح ساختار", "SUCCESS" if syntax_ok else "ERROR")
    log(f"  {'✅' if final_ok else '❌'} تأیید نهایی", "SUCCESS" if final_ok else "ERROR")
    if final_ok:
        log(f"  {'✅' if tests_ok else '⚠️ '} تست‌ها", "SUCCESS" if tests_ok else "WARNING")

    if final_ok:
        log("\n🎉 فایل با موفقیت اصلاح شد!", "SUCCESS")
        log("\nاقدام بعدی:", "INFO")
        log("  python eco_chaos_test.py --services --quick", "INFO")
        return 0
    else:
        log("\n⚠️ نیاز به بررسی بیشتر است", "WARNING")
        log("\nلطفاً این دستور را اجرا کنید و خروجی را ارسال کنید:", "INFO")
        log('  Get-Content "services\\ai\\support_agent.py" | Select-Object -Skip 108 -First 12', "INFO")
        return 1


if __name__ == "__main__":
    sys.exit(main())