#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_diagnose_indent.py
======================

تشخیص دقیق و رفع قطعی خطای تورفتگی در support_agent.py

این اسکریپت:
1. فایل را خط به خط تحلیل می‌کند
2. مشکل دقیق خط 114 را شناسایی می‌کند
3. راه‌حل قطعی اعمال می‌کند
"""

import sys
import shutil
import subprocess
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
    banner("تشخیص و رفع قطعی خطای تورفتگی")

    file_path = PROJECT_ROOT / "services" / "ai" / "support_agent.py"

    if not file_path.exists():
        log("❌ فایل یافت نشد", "ERROR")
        return 1

    # خواندن محتوا
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # =========================================================================
    # مرحله 1: تشخیص مشکل
    # =========================================================================
    log("=" * 70, "INFO")
    log("مرحله 1: تشخیص مشکل", "BOLD")
    log("=" * 70, "INFO")

    log(f"📄 فایل: {file_path.relative_to(PROJECT_ROOT)}", "INFO")
    log(f"📊 تعداد کل خطوط: {len(lines)}", "INFO")

    # بررسی سینتکس فعلی
    try:
        compile(content, file_path, "exec")
        log("✅ سینتکس از قبل درست است!", "SUCCESS")
        return 0
    except IndentationError as e:
        error_line = e.lineno
        log(f"❌ خطای سینتکس: {e}", "ERROR")
        log(f"📍 خط مشکل‌دار: {error_line}", "WARNING")

    # نمایش خطوط اطراف خط مشکل‌دار
    log("\n📋 نمایش خطوط اطراف خط مشکل‌دار:", "INFO")
    start = max(0, error_line - 5)
    end = min(len(lines), error_line + 5)

    for i in range(start, end):
        line_num = i + 1
        marker = " ← مشکل" if line_num == error_line else ""
        indent = len(lines[i]) - len(lines[i].lstrip())
        display = lines[i].replace("\t", "→")[:80]
        log(f"  {line_num:4d} (indent={indent}): {display}{marker}", 
            "ERROR" if line_num == error_line else "INFO")

    # تحلیل عمیق‌تر: بررسی ساختار بلاک‌ها
    log("\n🔍 تحلیل ساختار بلاک‌ها:", "INFO")

    # پیدا کردن آخرین خط غیر خالی قبل از خط مشکل‌دار
    prev_non_empty = None
    for i in range(error_line - 2, -1, -1):
        if lines[i].strip():
            prev_non_empty = i
            break

    if prev_non_empty is not None:
        prev_indent = len(lines[prev_non_empty]) - len(lines[prev_non_empty].lstrip())
        prev_line = lines[prev_non_empty].strip()
        log(f"  آخرین خط غیر خالی قبل: خط {prev_non_empty + 1}", "INFO")
        log(f"  محتوا: {prev_line[:60]}", "INFO")
        log(f"  تورفتگی: {prev_indent}", "INFO")

        # اگر خط قبلی با ':' تمام شده، انتظار تورفتگی بیشتر داریم
        if prev_line.endswith(":"):
            log("  ⚠️ خط قبلی با ':' تمام شده - انتظار تورفتگی بیشتر داریم", "WARNING")
        else:
            log("  ⚠️ خط قبلی با ':' تمام نشده - انتظار تورفتگی یکسان داریم", "WARNING")

    # بررسی تورفتگی خط مشکل‌دار
    error_line_content = lines[error_line - 1]
    error_indent = len(error_line_content) - len(error_line_content.lstrip())
    error_stripped = error_line_content.strip()

    log(f"\n📋 خط مشکل‌دار ({error_line}):", "INFO")
    log(f"  محتوا: {error_stripped[:60]}", "INFO")
    log(f"  تورفتگی: {error_indent}", "INFO")

    # =========================================================================
    # مرحله 2: اعمال راه‌حل
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 2: اعمال راه‌حل", "BOLD")
    log("=" * 70, "INFO")

    # پشتیبان
    backup = file_path.with_suffix(".py.diagnose.bak")
    if not backup.exists():
        shutil.copy2(file_path, backup)
        log(f"📦 Backup: {backup.name}", "SUCCESS")

    # استراتژی رفع: حذف تورفتگی اضافی
    # اگر خط مشکل‌دار تورفتگی بیشتری از حد انتظار دارد، آن را کم کن

    if prev_non_empty is not None:
        prev_indent = len(lines[prev_non_empty]) - len(lines[prev_non_empty].lstrip())
        prev_stripped = lines[prev_non_empty].strip()

        # تعیین تورفتگی مورد انتظار
        if prev_stripped.endswith(":"):
            # بعد از ':' انتظار 4 فاصله بیشتر داریم
            expected_indent = prev_indent + 4
        else:
            # در غیر این صورت، انتظار تورفتگی یکسان داریم
            expected_indent = prev_indent

        log(f"  تورفتگی فعلی: {error_indent}", "INFO")
        log(f"  تورفتگی مورد انتظار: {expected_indent}", "INFO")

        if error_indent != expected_indent:
            # اصلاح تورفتگی
            new_line = " " * expected_indent + error_stripped
            lines[error_line - 1] = new_line
            log(f"  ✅ تورفتگی اصلاح شد: {error_indent} → {expected_indent}", "SUCCESS")
        else:
            # اگر تورفتگی درست است، شاید مشکل از خط قبلی است
            log("  ⚠️ تورفتگی درست به نظر می‌رسد، بررسی خط قبلی...", "WARNING")

            # شاید خط قبلی تورفتگی اشتباه دارد
            # بررسی خطوط قبل‌تر
            for check_line in range(error_line - 2, max(0, error_line - 10), -1):
                if lines[check_line].strip():
                    check_indent = len(lines[check_line]) - len(lines[check_line].lstrip())
                    check_stripped = lines[check_line].strip()

                    # اگر این خط هم تورفتگی غیرمنتظره دارد
                    if check_indent > 0 and not check_stripped.startswith(("#", "def ", "class ", "if ", "else", "elif ", "for ", "while ", "try:", "except", "finally:", "with ", "return ", "yield ", "raise ", "continue", "break", "pass", "import ", "from ", "global ", "nonlocal ", "assert ", "del ", "lambda ", "@")):
                        # شاید این خط باید تورفتگی کمتری داشته باشد
                        log(f"  ⚠️ خط {check_line + 1} هم تورفتگی غیرمنتظره دارد", "WARNING")

    # =========================================================================
    # مرحله 3: تلاش‌های جایگزین
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 3: تلاش‌های جایگزین", "BOLD")
    log("=" * 70, "INFO")

    # اگر هنوز خطا داریم، از روش‌های جایگزین استفاده کن
    try:
        new_content = "\n".join(lines)
        compile(new_content, file_path, "exec")
        log("✅ سینتکس درست شد!", "SUCCESS")
    except IndentationError:
        log("⚠️ هنوز خطا داریم، استفاده از روش جایگزین...", "WARNING")

        # روش جایگزین: حذف کامل تورفتگی از خطوط مشکل‌دار
        # و بازسازی بر اساس ساختار

        # خواندن مجدد
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # حذف تورفتگی از خطوطی که فقط تورفتگی دارند
        for i in range(len(lines)):
            if lines[i].strip() == "" and lines[i] != "":
                lines[i] = ""

        new_content = "\n".join(lines)

        try:
            compile(new_content, file_path, "exec")
            log("✅ روش جایگزین موفق بود!", "SUCCESS")
        except IndentationError:
            log("❌ روش جایگزین هم موفق نبود", "ERROR")
            log("💡 پیشنهاد: فایل را دستی بررسی کنید", "WARNING")
            return 1

    # ذخیره
    file_path.write_text(new_content, encoding="utf-8")
    log(f"✅ فایل ذخیره شد", "SUCCESS")

    # =========================================================================
    # مرحله 4: تأیید نهایی
    # =========================================================================
    log("\n" + "=" * 70, "INFO")
    log("مرحله 4: تأیید نهایی", "BOLD")
    log("=" * 70, "INFO")

    # بررسی سینتکس
    try:
        final_content = file_path.read_text(encoding="utf-8")
        compile(final_content, file_path, "exec")
        log("✅ سینتکس نهایی درست است!", "SUCCESS")
        syntax_ok = True
    except SyntaxError as e:
        log(f"❌ سینتکس نهایی: {e}", "ERROR")
        syntax_ok = False

    # اجرای تست‌ها
    if syntax_ok:
        log("\n🧪 اجرای تست‌ها...", "INFO")
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
            log(f"⚠️ برخی تست‌ها شکست خوردند", "WARNING")
            tests_ok = False

    # =========================================================================
    # خلاصه
    # =========================================================================
    banner("خلاصه")

    log("نتایج:", "INFO")
    log(f"  {'✅' if syntax_ok else '❌'} سینتکس", "SUCCESS" if syntax_ok else "ERROR")
    if syntax_ok:
        log(f"  {'✅' if tests_ok else '⚠️ '} تست‌ها", "SUCCESS" if tests_ok else "WARNING")

    if syntax_ok:
        log("\n🎉 خطای تورفتگی با موفقیت رفع شد!", "SUCCESS")
        log("\nاقدام بعدی:", "INFO")
        log("  python eco_chaos_test.py --services --quick", "INFO")
        return 0
    else:
        log("\n⚠️ نیاز به بررسی دستی است", "WARNING")
        log("\nلطفاً محتوای خطوط 110-120 فایل زیر را ارسال کنید:", "INFO")
        log(f"  {file_path.relative_to(PROJECT_ROOT)}", "INFO")
        return 1


if __name__ == "__main__":
    sys.exit(main())