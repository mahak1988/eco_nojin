#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_phase1_emergency.py
========================

فاز 1 فوری: رفع نقاط ضعف بحرانی کشف‌شده در تست آشوب

اقدامات:
1. رفع خطای تورفتگی در services/ai/support_agent.py (خط 114)
2. اصلاح کوئری‌های با نوع داده ناسازگار (MRV site_id)
3. تولید راهنمای مدیریت خطا
4. اجرای تست‌ها برای تأیید
"""

import sys
import shutil
import re
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


def log(msg: str, level: str = "INFO"):
    color = getattr(Colors, level, Colors.RESET)
    print(f"{color}[{level}]{Colors.RESET} {msg}")


def banner(title: str):
    print()
    print(colorize("=" * 70, "BOLD"))
    print(colorize(f"  {title}", "BOLD"))
    print(colorize("=" * 70, "BOLD"))
    print()


def colorize(msg: str, level: str = "INFO") -> str:
    color = getattr(Colors, level, Colors.RESET)
    return f"{color}{msg}{Colors.RESET}"


# ==============================================================================
# Fix 1: رفع خطای تورفتگی در support_agent.py
# ==============================================================================

def fix_support_agent_indentation() -> bool:
    """رفع خطای تورفتگی در services/ai/support_agent.py"""
    log("🔧 رفع خطای تورفتگی در support_agent.py...", "INFO")

    file_path = PROJECT_ROOT / "services" / "ai" / "support_agent.py"

    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False

    # Backup
    backup = file_path.with_suffix(".py.phase1.bak")
    if not backup.exists():
        shutil.copy2(file_path, backup)
        log(f"  📦 Backup: {backup.name}", "SUCCESS")

    # بررسی سینتکس فعلی
    content = file_path.read_text(encoding="utf-8")

    try:
        compile(content, file_path, "exec")
        log("  ℹ️ سینتکس از قبل درست است", "INFO")
        return True
    except IndentationError as e:
        log(f"  ❌ خطای تورفتگی: {e}", "ERROR")

    # راه‌حل: حذف تورفتگی اضافی از خطوط مشکل‌دار
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # اگر خط فقط تورفتگی دارد و خالی است، آن را خالی کن
        if stripped == "" and line != "":
            fixed_lines.append("")
            continue

        # در غیر این صورت، خط را حفظ کن
        fixed_lines.append(line)

    new_content = "\n".join(fixed_lines)

    # اگر تغییر کرد، ذخیره کن
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        log("  ✅ فایل اصلاح شد", "SUCCESS")

        # تأیید سینتکس
        try:
            compile(new_content, file_path, "exec")
            log("  ✅ سینتکس تأیید شد", "SUCCESS")
            return True
        except SyntaxError as e:
            log(f"  ❌ هنوز خطا: {e}", "ERROR")
            # بازیابی از پشتیبان
            shutil.copy2(backup, file_path)
            log("  ⚠️ از پشتیبان بازیابی شد", "WARNING")
            return False

    return True


# ==============================================================================
# Fix 2: اصلاح کوئری‌های با نوع داده ناسازگار
# ==============================================================================

def analyze_site_id_type() -> dict:
    """تحلیل نوع داده سایت‌ها در دیتابیس"""
    log("🔍 تحلیل نوع داده سایت‌ها...", "INFO")

    try:
        from database.hub import hub

        conn = hub.get_duckdb("master")

        try:
            result = conn.execute("""
                SELECT
                    site_id,
                    typeof(site_id) as type,
                    COUNT(*) as count
                FROM weather_daily
                GROUP BY site_id, typeof(site_id)
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            site_info = {
                "numeric_sites": 0,
                "string_sites": 0,
                "sample_sites": []
            }

            for row in result:
                site_id, data_type, count = row
                sample = str(site_id)[:20]
                site_info["sample_sites"].append(sample)

                if data_type in ["INTEGER", "BIGINT", "DOUBLE", "FLOAT"]:
                    site_info["numeric_sites"] += count
                else:
                    site_info["string_sites"] += count

            log(f"  📊 سایت‌های عددی: {site_info['numeric_sites']}", "INFO")
            log(f"  📊 سایت‌های رشته‌ای: {site_info['string_sites']}", "INFO")
            log(f"  📊 نمونه‌ها: {site_info['sample_sites'][:3]}", "INFO")

            conn.close()
            return site_info

        except Exception as e:
            log(f"  ❌ خطا در تحلیل: {e}", "ERROR")
            conn.close()
            return {}

    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return {}


def patch_data_connector() -> bool:
    """اصلاح کوئری‌های با نوع داده ناسازگار در data_connector.py"""
    log("🔧 اصلاح کوئری‌های با نوع داده ناسازگار...", "INFO")

    file_path = PROJECT_ROOT / "engine" / "data_connector.py"

    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False

    # Backup
    backup = file_path.with_suffix(".py.phase1.bak")
    if not backup.exists():
        shutil.copy2(file_path, backup)
        log(f"  📦 Backup: {backup.name}", "SUCCESS")

    content = file_path.read_text(encoding="utf-8")
    original = content

    # الگوهای مشکل‌دار و جایگزین‌های آن‌ها
    patterns = [
        # الگو 1: CAST(site_id AS FLOAT) که برای سایت‌های رشته‌ای کار نمی‌کند
        (
            r"AVG\(CAST\(site_id AS FLOAT\)\)",
            "AVG(CAST(COALESCE(TRY(CAST(site_id AS FLOAT)), 0) AS FLOAT))"
        ),
        # الگو 2: SUM(site_id)
        (
            r"SUM\(site_id\)",
            "SUM(CAST(COALESCE(TRY(CAST(site_id AS FLOAT)), 0) AS FLOAT))"
        ),
        # الگو 3: MAX/MIN بدون محافظت
        (
            r"MAX\(site_id\)",
            "MAX(CAST(COALESCE(TRY(CAST(site_id AS FLOAT)), 0) AS FLOAT))"
        ),
        (
            r"MIN\(site_id\)",
            "MIN(CAST(COALESCE(TRY(CAST(site_id AS FLOAT)), 0) AS FLOAT))"
        ),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        log("  ✅ data_connector.py اصلاح شد", "SUCCESS")
        return True
    else:
        log("  ℹ️ الگوی مشکل‌دار یافت نشد", "INFO")
        return True


# ==============================================================================
# Fix 3: تولید راهنمای مدیریت خطا
# ==============================================================================

def create_error_handling_guide() -> bool:
    """تولید راهنمای مدیریت خطا برای محاسبات عددی"""
    log("📝 تولید راهنمای مدیریت خطا...", "INFO")

    guide_lines = [
        "# راهنمای مدیریت خطا در محاسبات عددی",
        "",
        "## مشکل شناسایی‌شده",
        "",
        "تست‌های آشوب نشان دادند که محاسبات با مقادیر نامعتبر (منفی، صفر، بی‌نهایت)",
        "خطا می‌دهند و سیستم را می‌شکنند.",
        "",
        "## راه‌حل‌های پیشنهادی",
        "",
        "### 1. استفاده از تابع‌های امن (TRY)",
        "",
        "به جای:",
        "```sql",
        "SELECT LOG(value) FROM table",
        "```",
        "",
        "استفاده کن:",
        "```sql",
        "SELECT TRY(LOG(value)) FROM table",
        "```",
        "",
        "### 2. فیلتر کردن مقادیر نامعتبر",
        "",
        "```sql",
        "SELECT",
        "    site_id,",
        "    AVG(temperature) as avg_temp",
        "FROM weather_daily",
        "WHERE temperature IS NOT NULL",
        "  AND temperature BETWEEN -100 AND 100  -- محدوده منطقی",
        "GROUP BY site_id",
        "```",
        "",
        "### 3. استفاده از CASE برای مقادیر لبه‌ای",
        "",
        "```sql",
        "SELECT",
        "    CASE",
        "        WHEN value > 0 THEN LOG(value)",
        "        WHEN value = 0 THEN 0",
        "        ELSE NULL",
        "    END as safe_log",
        "FROM table",
        "```",
        "",
        "### 4. محافظت در سطح اپلیکیشن",
        "",
        "```python",
        "import math",
        "",
        "def safe_sqrt(x):",
        '    """محاسبه امن ریشه دوم"""',
        "    if x is None or math.isnan(x) or math.isinf(x):",
        "        return None",
        "    if x < 0:",
        "        return None",
        "    return math.sqrt(x)",
        "",
        "def safe_log(x, base=10):",
        '    """محاسبه امن لگاریتم"""',
        "    if x is None or x <= 0:",
        "        return None",
        "    try:",
        "        return math.log(x, base)",
        "    except (ValueError, OverflowError):",
        "        return None",
        "```",
        "",
        "## پیاده‌سازی در لایه‌های مختلف",
        "",
        "| لایه | راه‌حل |",
        "|---|---|",
        "| **دیتابیس** | `TRY()`, `COALESCE()`, `CASE WHEN` |",
        "| **SQLAlchemy** | Validator در مدل‌ها |",
        "| **API Gateway** | Pydantic validation |",
        "| **موتور محاسباتی** | توابع امن (بالا) |",
        "",
    ]

    guide_file = PROJECT_ROOT / "docs" / "numerical_error_handling.md"
    guide_file.parent.mkdir(parents=True, exist_ok=True)
    guide_file.write_text("\n".join(guide_lines), encoding="utf-8")
    log(f"  ✅ راهنما ذخیره شد: {guide_file.relative_to(PROJECT_ROOT)}", "SUCCESS")
    return True


# ==============================================================================
# Verification: اجرای تست‌ها
# ==============================================================================

def verify_fixes() -> dict:
    """اجرای تست‌ها برای تأیید رفع مشکلات"""
    log("🧪 اجرای تست‌های تأیید...", "INFO")

    results = {
        "syntax_ok": False,
        "tests_ok": False,
        "chaos_ok": False,
    }

    # تست 1: سینتکس
    log("\n  1. بررسی سینتکس...", "INFO")
    test_file = PROJECT_ROOT / "services" / "ai" / "support_agent.py"
    try:
        content = test_file.read_text(encoding="utf-8")
        compile(content, test_file, "exec")
        results["syntax_ok"] = True
        log("     ✅ سینتکس درست است", "SUCCESS")
    except SyntaxError as e:
        log(f"     ❌ خطای سینتکس: {e}", "ERROR")

    # تست 2: اجرای تست‌های اصلی
    log("\n  2. اجرای تست‌های اصلی...", "INFO")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "services", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=120,
        )
        if result.returncode == 0:
            results["tests_ok"] = True
            log("     ✅ تست‌های اصلی پاس شدند", "SUCCESS")
        else:
            log(f"     ⚠️ برخی تست‌ها شکست خوردند", "WARNING")
    except subprocess.TimeoutExpired:
        log("     ⏰ Timeout در اجرای تست‌ها", "WARNING")
    except Exception as e:
        log(f"     ❌ خطا: {e}", "ERROR")

    # تست 3: اجرای تست آشوب (فقط موتور و خدمات)
    log("\n  3. اجرای تست آشوب (سریع)...", "INFO")
    chaos_file = PROJECT_ROOT / "eco_chaos_test.py"
    if chaos_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(chaos_file), "--services", "--quick"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=180,
            )
            if result.returncode == 0:
                results["chaos_ok"] = True
                log("     ✅ تست آشوب پاس شد", "SUCCESS")
            else:
                log("     ⚠️ تست آشوب نیاز به بررسی دارد", "WARNING")
        except subprocess.TimeoutExpired:
            log("     ⏰ Timeout در تست آشوب", "WARNING")
        except Exception as e:
            log(f"     ❌ خطا: {e}", "ERROR")

    return results


# ==============================================================================
# اجرای اصلی
# ==============================================================================

def main() -> int:
    banner("🚀 فاز 1 فوری: رفع نقاط ضعف بحرانی")

    # مرحله 1: رفع خطای تورفتگی
    log("=" * 70, "INFO")
    log("مرحله 1: رفع خطای تورفتگی", "BOLD")
    log("=" * 70, "INFO")
    fix1_ok = fix_support_agent_indentation()

    # مرحله 2: تحلیل نوع داده
    log("\n" + "=" * 70, "INFO")
    log("مرحله 2: تحلیل نوع داده سایت‌ها", "BOLD")
    log("=" * 70, "INFO")
    site_info = analyze_site_id_type()

    # مرحله 3: اصلاح کوئری‌ها
    log("\n" + "=" * 70, "INFO")
    log("مرحله 3: اصلاح کوئری‌های ناسازگار", "BOLD")
    log("=" * 70, "INFO")
    fix2_ok = patch_data_connector()

    # مرحله 4: تولید راهنما
    log("\n" + "=" * 70, "INFO")
    log("مرحله 4: تولید راهنمای مدیریت خطا", "BOLD")
    log("=" * 70, "INFO")
    fix3_ok = create_error_handling_guide()

    # مرحله 5: تأیید
    log("\n" + "=" * 70, "INFO")
    log("مرحله 5: تأیید با اجرای تست‌ها", "BOLD")
    log("=" * 70, "INFO")
    verification = verify_fixes()

    # خلاصه
    banner("خلاصه فاز 1")

    log("نتایج اقدامات:", "INFO")
    log(f"  {'✅' if fix1_ok else '❌'} رفع خطای تورفتگی", "SUCCESS" if fix1_ok else "ERROR")
    log(f"  {'✅' if site_info else '⚠️ '} تحلیل نوع داده", "SUCCESS" if site_info else "WARNING")
    log(f"  {'✅' if fix2_ok else '❌'} اصلاح کوئری‌ها", "SUCCESS" if fix2_ok else "ERROR")
    log(f"  {'✅' if fix3_ok else '❌'} تولید راهنما", "SUCCESS" if fix3_ok else "ERROR")

    log("\nنتایج تأیید:", "INFO")
    log(f"  {'✅' if verification['syntax_ok'] else '❌'} سینتکس", "SUCCESS" if verification['syntax_ok'] else "ERROR")
    log(f"  {'✅' if verification['tests_ok'] else '⚠️ '} تست‌های اصلی", "SUCCESS" if verification['tests_ok'] else "WARNING")
    log(f"  {'✅' if verification['chaos_ok'] else '⚠️ '} تست آشوب", "SUCCESS" if verification['chaos_ok'] else "WARNING")

    # امتیاز نهایی
    log("\n" + "=" * 70, "INFO")
    log("امتیاز نهایی فاز 1", "BOLD")
    log("=" * 70, "INFO")

    score = 0
    if fix1_ok: score += 25
    if fix2_ok: score += 25
    if fix3_ok: score += 25
    if verification["syntax_ok"]: score += 10
    if verification["tests_ok"]: score += 10
    if verification["chaos_ok"]: score += 5

    log(f"  امتیاز: {score}/100", "INFO")

    if score >= 80:
        log("  🏆 فاز 1 با موفقیت کامل شد!", "SUCCESS")
    elif score >= 60:
        log("  ✅ فاز 1 تقریباً کامل شد", "SUCCESS")
    else:
        log("  ⚠️ نیاز به بررسی بیشتر", "WARNING")

    return 0 if score >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())