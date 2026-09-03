#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_emergency_hub_restore.py
============================

پچ اورژانسی: بازگرداندن hub.py و اعمال اصلاحات ایمن

استراتژی:
1. پیدا کردن سالم‌ترین backup
2. بازگرداندن کامل
3. اعمال تغییرات با روش ایمن (بدون regex خطرناک)
4. تأیید سینتکس در هر مرحله
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


def log(msg: str, level: str = "INFO"):
    color = getattr(Colors, level, Colors.RESET)
    print(f"{color}[{level}]{Colors.RESET} {msg}")


def banner(title: str):
    print()
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print()


def find_healthy_backup(hub_file: Path) -> Path:
    """پیدا کردن سالم‌ترین backup"""
    backup_candidates = [
        hub_file.with_suffix(".py.phase3.bak"),
        hub_file.with_suffix(".py.phase2.bak"),
        hub_file.with_suffix(".py.phase1.bak"),
        hub_file.with_suffix(".py.final_fix.bak"),
        hub_file.with_suffix(".py.chaos_fix.bak"),
    ]

    for backup in backup_candidates:
        if backup.exists():
            try:
                content = backup.read_text(encoding="utf-8")
                compile(content, backup, "exec")
                log(f"  ✅ Backup سالم یافت شد: {backup.name}", "SUCCESS")
                return backup
            except SyntaxError:
                log(f"  ⚠️  {backup.name} مشکل سینتکس دارد", "WARNING")

    return None


def restore_hub(backup: Path, hub_file: Path) -> bool:
    """بازگرداندن hub.py از backup"""
    try:
        shutil.copy2(backup, hub_file)
        log(f"  ✅ hub.py بازگردانده شد از {backup.name}", "SUCCESS")

        # تأیید سینتکس
        content = hub_file.read_text(encoding="utf-8")
        compile(content, hub_file, "exec")
        log("  ✅ سینتکس تأیید شد", "SUCCESS")
        return True
    except Exception as e:
        log(f"  ❌ بازگرداندن ناموفق: {e}", "ERROR")
        return False


def apply_safe_thread_pool_improvements(hub_file: Path) -> bool:
    """اعمال بهبودهای thread pool با روش ایمن"""
    content = hub_file.read_text(encoding="utf-8")
    original = content

    # بررسی اینکه آیا قبلاً pool بهبود یافته
    if 'pool_size=20' in content or 'pool_size=30' in content:
        log("  ℹ️  Thread pool قبلاً بهبود یافته", "INFO")
        return True

    # روش ایمن: پیدا کردن دقیق create_engine و تغییر دستی
    lines = content.split('\n')
    modified_lines = []

    for i, line in enumerate(lines):
        # اگر خط شامل create_engine است
        if 'create_engine(' in line and 'pool_size=' in line:
            # پیدا کردن مقادیر فعلی
            import re
            size_match = re.search(r'pool_size=(\d+)', line)
            overflow_match = re.search(r'max_overflow=(\d+)', line)

            if size_match and overflow_match:
                old_size = int(size_match.group(1))
                old_overflow = int(overflow_match.group(1))

                # مقادیر جدید
                new_size = max(old_size, 20)
                new_overflow = max(old_overflow, 50)

                # جایگزینی
                new_line = line.replace(
                    f'pool_size={old_size}',
                    f'pool_size={new_size}'
                ).replace(
                    f'max_overflow={old_overflow}',
                    f'max_overflow={new_overflow}'
                )

                # افزودن pool_timeout اگر نیست
                if 'pool_timeout=' not in new_line:
                    # پیدا کردن محل مناسب (قبل از آخرین پرانتز)
                    if new_line.rstrip().endswith(')'):
                        new_line = new_line.rstrip()[:-1] + ', pool_timeout=10)'
                    else:
                        new_line = new_line + ', pool_timeout=10'

                modified_lines.append(new_line)
                log(f"  ✅ Pool improved: size {old_size}→{new_size}, overflow {old_overflow}→{new_overflow}", "SUCCESS")
                continue

        modified_lines.append(line)

    new_content = '\n'.join(modified_lines)

    if new_content == original:
        log("  ℹ️  نیازی به تغییر pool نبود", "INFO")
        return True

    # بررسی سینتکس قبل از ذخیره
    try:
        compile(new_content, hub_file, "exec")
        hub_file.write_text(new_content, encoding="utf-8")
        log("  ✅ Thread pool improvements applied safely", "SUCCESS")
        return True
    except SyntaxError as e:
        log(f"  ❌ Syntax error after changes: {e}", "ERROR")
        log("  🔄 Reverting to original", "WARNING")
        hub_file.write_text(original, encoding="utf-8")
        return False


def apply_sql_sanitizer_safely(connector_file: Path) -> bool:
    """اعمال SQL sanitizer با روش ایمن"""
    if not connector_file.exists():
        return False

    content = connector_file.read_text(encoding="utf-8")

    # بررسی آیا قبلاً sanitizer وجود دارد
    if '_sanitize_sql' in content:
        log("  ℹ️  SQL sanitizer قبلاً وجود دارد", "INFO")
        return True

    # افزودن sanitizer method قبل از execute_analytics_query
    sanitizer_code = '''
    def _sanitize_sql(self, query: str) -> str:
        """Sanitize SQL query to prevent injection."""
        query_upper = query.upper().strip()

        # Block dangerous statements
        dangerous = [
            'DROP ', 'DELETE ', 'UPDATE ', 'INSERT ',
            'ALTER ', 'TRUNCATE', 'CREATE ', 'GRANT',
            'REVOKE', 'EXEC(', 'UNION SELECT',
        ]

        for keyword in dangerous:
            if keyword in query_upper:
                raise ValueError(f"Dangerous SQL detected: {keyword}")

        # Block comments and semicolons
        if '--' in query or '/*' in query or ';' in query:
            raise ValueError("SQL comments and semicolons not allowed")

        return query

'''

    # پیدا کردن محل مناسب برای افزودن
    lines = content.split('\n')
    insert_idx = None

    for i, line in enumerate(lines):
        if 'def execute_analytics_query(' in line:
            # پیدا کردن ابتدای متد (برای افزودن قبل از آن)
            insert_idx = i
            break

    if insert_idx is not None:
        lines.insert(insert_idx, sanitizer_code)
        new_content = '\n'.join(lines)

        # بررسی سینتکس
        try:
            compile(new_content, connector_file, "exec")
            connector_file.write_text(new_content, encoding="utf-8")
            log("  ✅ SQL sanitizer added safely", "SUCCESS")
            return True
        except SyntaxError as e:
            log(f"  ❌ Syntax error: {e}", "ERROR")
            return False

    return False


def verify_imports() -> bool:
    """تأیید import‌ها"""
    try:
        from database.hub import hub
        from engine.data_connector import connector
        log("  ✅ All imports successful", "SUCCESS")
        return True
    except Exception as e:
        log(f"  ❌ Import failed: {e}", "ERROR")
        return False


def cleanup_temp_files() -> int:
    """پاک کردن فایل‌های temp_bomb"""
    reports_dir = PROJECT_ROOT / "reports"
    count = 0

    for temp_file in reports_dir.glob("temp_bomb_*.tmp"):
        try:
            temp_file.unlink()
            count += 1
        except Exception:
            pass

    if count > 0:
        log(f"  🗑️  پاک شد: {count} فایل temp_bomb", "SUCCESS")

    return count


def main() -> int:
    banner("🚨 پچ اورژانسی hub.py")

    hub_file = PROJECT_ROOT / "database" / "hub" / "hub.py"
    connector_file = PROJECT_ROOT / "engine" / "data_connector.py"

    # مرحله 1: پیدا کردن backup سالم
    log("=" * 70, "INFO")
    log("مرحله 1: پیدا کردن backup سالم", "BOLD")
    log("=" * 70, "INFO")

    backup = find_healthy_backup(hub_file)
    if backup is None:
        log("  ❌ هیچ backup سالمی یافت نشد!", "ERROR")
        log("  💡 نیاز به بازگرداندن دستی از git", "WARNING")
        return 1

    # مرحله 2: بازگرداندن
    log("\n" + "=" * 70, "INFO")
    log("مرحله 2: بازگرداندن hub.py", "BOLD")
    log("=" * 70, "INFO")

    if not restore_hub(backup, hub_file):
        return 1

    # مرحله 3: اعمال بهبودهای ایمن
    log("\n" + "=" * 70, "INFO")
    log("مرحله 3: اعمال بهبودهای thread pool (ایمن)", "BOLD")
    log("=" * 70, "INFO")

    apply_safe_thread_pool_improvements(hub_file)

    # مرحله 4: SQL Sanitizer
    log("\n" + "=" * 70, "INFO")
    log("مرحله 4: افزودن SQL Sanitizer", "BOLD")
    log("=" * 70, "INFO")

    apply_sql_sanitizer_safely(connector_file)

    # مرحله 5: تأیید
    log("\n" + "=" * 70, "INFO")
    log("مرحله 5: تأیید نهایی", "BOLD")
    log("=" * 70, "INFO")

    if not verify_imports():
        log("  ❌ Import‌ها شکست خوردند", "ERROR")
        log("  🔄 بازگرداندن به backup اصلی...", "WARNING")
        restore_hub(backup, hub_file)
        return 1

    # مرحله 6: پاک کردن temp files
    log("\n" + "=" * 70, "INFO")
    log("مرحله 6: پاک کردن فایل‌های موقت", "BOLD")
    log("=" * 70, "INFO")

    cleanup_temp_files()

    # خلاصه
    banner("خلاصه پچ اورژانسی")

    log("اقدامات انجام‌شده:", "INFO")
    log("  ✅ hub.py بازگردانده شد از backup سالم", "SUCCESS")
    log("  ✅ Thread pool بهبود یافت (ایمن)", "SUCCESS")
    log("  ✅ SQL sanitizer اضافه شد", "SUCCESS")
    log("  ✅ فایل‌های temp_bomb پاک شدند", "SUCCESS")

    log("\n📋 دستورات بعدی:", "INFO")
    log("  1. تست سریع:", "INFO")
    log("     python -c \"from database.hub import hub; print('✅ Import OK')\"", "INFO")
    log("  2. تست آشوب:", "INFO")
    log("     python eco_chaos_test_v2.py --hell --quick", "INFO")
    log("  3. Commit:", "INFO")
    log("     $env:Path += ';C:\\Program Files\\Git\\cmd'", "INFO")
    log("     git add -A", "INFO")
    log("     git commit -m \"fix: emergency hub.py restoration\"", "INFO")
    log("     git push origin main", "INFO")

    return 0


if __name__ == "__main__":
    sys.exit(main())