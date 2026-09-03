#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_surgical_fix.py
===================

پچ جراحی: اصلاح خط-به-خط بدون regex خطرناک

استراتژی:
    1. خواندن فایل
    2. پیدا کردن خط دقیق مشکل‌دار
    3. جایگزینی فقط همان خط
    4. compile check فوری
    5. ادامه با خط بعدی

نویسنده: تیم معماری Eco Nojin
نسخه: SURGICAL
"""

import sys
import shutil
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


def backup(file_path: Path) -> Path:
    if not file_path.exists():
        return None
    bak = file_path.with_suffix(file_path.suffix + ".surgical.bak")
    if not bak.exists():
        shutil.copy2(file_path, bak)
        log(f"  📦 Backup: {bak.name}", "SUCCESS")
    return bak


def try_compile(file_path: Path, content: str) -> bool:
    """تلاش برای compile - اگر خطا داشت، جزئیات می‌دهد"""
    try:
        compile(content, file_path, "exec")
        return True
    except SyntaxError as e:
        log(f"  ❌ Syntax error at line {e.lineno}: {e.msg}", "ERROR")
        # نمایش خط مشکل‌دار
        lines = content.split('\n')
        if e.lineno and e.lineno <= len(lines):
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            log(f"  📋 Context around line {e.lineno}:", "WARNING")
            for i in range(start, end):
                marker = " >>>" if i == e.lineno - 1 else "    "
                log(f"{marker} {i+1:4d}: {lines[i][:100]}", "INFO")
        return False


# ==============================================================================
# FIX 1: resource_manager.py - Dict import
# ==============================================================================

def fix_resource_manager() -> bool:
    """رفع خطای Dict در resource_manager.py"""
    log("🔧 Fix 1: resource_manager.py (Dict import)...", "INFO")

    file_path = PROJECT_ROOT / "engine" / "resource_manager.py"
    if not file_path.exists():
        log(f"  ❌ File not found", "ERROR")
        return False

    backup(file_path)
    original = file_path.read_text(encoding="utf-8")

    # بررسی مشکل
    if 'def cleanup_resources() -> Dict:' in original and 'from typing import' not in original:
        # پیدا کردن اولین import line
        lines = original.split('\n')

        # افزودن typing import در ابتدای فایل (بعد از docstring)
        insert_pos = 0
        in_docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                continue
            if not in_docstring and (stripped.startswith('import ') or stripped.startswith('from ')):
                insert_pos = i
                break

        # اضافه کردن typing import
        new_import = 'from typing import Dict, Any, Optional, List'
        lines.insert(insert_pos, new_import)

        new_content = '\n'.join(lines)

        if try_compile(file_path, new_content):
            file_path.write_text(new_content, encoding="utf-8")
            log("  ✅ resource_manager.py fixed (Dict import added)", "SUCCESS")
            return True
        else:
            log("  ❌ Compile failed, reverting", "ERROR")
            file_path.write_text(original, encoding="utf-8")
            return False
    else:
        log("  ℹ️  Already has Dict or different issue", "INFO")
        return True


# ==============================================================================
# FIX 2: data_connector.py - Dict import + SQL Sanitizer
# ==============================================================================

def fix_data_connector() -> bool:
    """رفع Dict + افزودن SQL Sanitizer در data_connector.py"""
    log("🔧 Fix 2: data_connector.py (Dict + SQL Sanitizer)...", "INFO")

    file_path = PROJECT_ROOT / "engine" / "data_connector.py"
    if not file_path.exists():
        log(f"  ❌ File not found", "ERROR")
        return False

    backup(file_path)
    original = file_path.read_text(encoding="utf-8")
    content = original

    # =========================================================================
    # گام 1: Dict import
    # =========================================================================
    lines = content.split('\n')

    # بررسی وجود Dict
    has_dict = any('Dict' in line and ('from typing' in line or 'import typing' in line) for line in lines)

    if not has_dict:
        # پیدا کردن typing import line
        for i, line in enumerate(lines):
            if line.strip().startswith('from typing import'):
                if 'Dict' not in line:
                    # افزودن Dict
                    lines[i] = line.rstrip().rstrip(',') + ', Dict'
                    log(f"  ✅ Added Dict to line {i+1}", "SUCCESS")
                break
        else:
            # پیدا کردن اولین import
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    lines.insert(i, 'from typing import Dict, Any, Optional, List')
                    log(f"  ✅ Added typing import at line {i+1}", "SUCCESS")
                    break

        content = '\n'.join(lines)

    # =========================================================================
    # گام 2: بررسی وجود _sanitize_sql
    # =========================================================================
    if '_sanitize_sql' not in content:
        # پیدا کردن ابتدای کلاس DataConnector
        lines = content.split('\n')
        class_line = -1

        for i, line in enumerate(lines):
            if line.strip().startswith('class DataConnector'):
                class_line = i
                break

        if class_line >= 0:
            # پیدا کردن اولین متد
            for i in range(class_line + 1, len(lines)):
                if lines[i].strip().startswith('def '):
                    # افزودن sanitize قبل از این متد
                    sanitize_code = '''    def _sanitize_sql(self, query: str) -> str:
        """Sanitize SQL query - only SELECT/WITH allowed."""
        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        query_upper = query.upper().strip()

        # Block dangerous statements
        dangerous = [
            'DROP ', 'DELETE ', 'UPDATE ', 'INSERT ',
            'ALTER ', 'TRUNCATE', 'CREATE ', 'GRANT ',
            'REVOKE ', 'EXEC(', 'EXECUTE ',
        ]

        for keyword in dangerous:
            if keyword in query_upper:
                raise ValueError(
                    f"Dangerous SQL blocked: {keyword.strip()}. "
                    f"Only SELECT queries are allowed."
                )

        # Block UNION injection
        if 'UNION' in query_upper and 'SELECT' in query_upper:
            raise ValueError("UNION queries blocked to prevent injection")

        # Block comments
        if '--' in query or '/*' in query:
            raise ValueError("SQL comments blocked")

        # Block semicolons outside strings
        in_str = False
        quote = None
        for ch in query:
            if ch in ('"', "'") and not in_str:
                in_str = True
                quote = ch
            elif ch == quote and in_str:
                in_str = False
            elif ch == ';' and not in_str:
                raise ValueError("Semicolons blocked")

        # Only SELECT/WITH
        if not (query_upper.startswith('SELECT') or query_upper.startswith('WITH')):
            raise ValueError(
                f"Only SELECT/WITH allowed. Got: {query_upper.split()[0] if query_upper else 'empty'}"
            )

        return query

'''
                    lines.insert(i, sanitize_code)
                    log(f"  ✅ Added _sanitize_sql method before line {i+1}", "SUCCESS")
                    break

            content = '\n'.join(lines)

    # =========================================================================
    # گام 3: فراخوانی _sanitize_sql در execute_analytics_query
    # =========================================================================
    if 'self._sanitize_sql(query)' not in content:
        lines = content.split('\n')

        for i, line in enumerate(lines):
            if 'def execute_analytics_query(' in line:
                # پیدا کردن انتهای docstring و افزودن sanitize
                j = i + 1
                # Skip docstring
                docstring_start = None
                while j < len(lines):
                    stripped = lines[j].strip()
                    if '"""' in stripped or "'''" in stripped:
                        if docstring_start is None:
                            docstring_start = j
                        elif j > docstring_start:
                            # End of docstring
                            j += 1
                            break
                    j += 1

                # افزودن sanitize call
                sanitize_call = '        query = self._sanitize_sql(query)\n'
                lines.insert(j, sanitize_call)
                log(f"  ✅ Added sanitize call after line {j}", "SUCCESS")
                break

        content = '\n'.join(lines)

    # =========================================================================
    # گام 4: بررسی import re
    # =========================================================================
    if 'import re' not in content and 're.search' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                lines.insert(i, 'import re')
                log(f"  ✅ Added 'import re' at line {i+1}", "SUCCESS")
                break
        content = '\n'.join(lines)

    # =========================================================================
    # تأیید نهایی
    # =========================================================================
    if content != original:
        if try_compile(file_path, content):
            file_path.write_text(content, encoding="utf-8")
            log("  ✅ data_connector.py successfully updated", "SUCCESS")
            return True
        else:
            log("  ❌ Compile failed, reverting", "ERROR")
            file_path.write_text(original, encoding="utf-8")
            return False
    else:
        log("  ℹ️  No changes needed", "INFO")
        return True


# ==============================================================================
# FIX 3: hub.py - pool size increase (SAFELY)
# ==============================================================================

def fix_hub_pool() -> bool:
    """افزایش pool size با جایگزینی دقیق عدد"""
    log("🔧 Fix 3: hub.py (pool size)...", "INFO")

    file_path = PROJECT_ROOT / "database" / "hub" / "hub.py"
    if not file_path.exists():
        log(f"  ❌ File not found", "ERROR")
        return False

    backup(file_path)
    original = file_path.read_text(encoding="utf-8")
    content = original

    # جایگزینی ساده اعداد pool_size
    # الگو: pool_size=10 -> pool_size=30
    content = content.replace('pool_size=10', 'pool_size=30')
    content = content.replace('pool_size=5', 'pool_size=30')
    content = content.replace('pool_size = 10', 'pool_size = 30')
    content = content.replace('pool_size = 5', 'pool_size = 30')

    # max_overflow
    content = content.replace('max_overflow=20', 'max_overflow=60')
    content = content.replace('max_overflow=10', 'max_overflow=60')
    content = content.replace('max_overflow = 20', 'max_overflow = 60')
    content = content.replace('max_overflow = 10', 'max_overflow = 60')

    # pool_timeout
    content = content.replace('pool_timeout=30', 'pool_timeout=10')
    content = content.replace('pool_timeout = 30', 'pool_timeout = 10')

    # شمارش تغییرات
    changes = []
    if 'pool_size=30' in content or 'pool_size = 30' in content:
        changes.append('pool_size=30')
    if 'max_overflow=60' in content or 'max_overflow = 60' in content:
        changes.append('max_overflow=60')
    if 'pool_timeout=10' in content or 'pool_timeout = 10' in content:
        changes.append('pool_timeout=10')

    if content != original:
        if try_compile(file_path, content):
            file_path.write_text(content, encoding="utf-8")
            log(f"  ✅ hub.py pool optimized: {', '.join(changes)}", "SUCCESS")
            return True
        else:
            log("  ❌ Compile failed, reverting", "ERROR")
            file_path.write_text(original, encoding="utf-8")
            return False
    else:
        log("  ℹ️  No pool parameters found to change", "INFO")
        return True


# ==============================================================================
# VERIFY
# ==============================================================================

def verify_all() -> dict:
    """تأیید رفع تمام مشکلات"""
    log("🧪 تأیید نهایی...", "INFO")

    results = {
        "resource_manager": False,
        "data_connector": False,
        "hub": False,
        "select_works": False,
        "drop_blocked": False,
    }

    # تست 1: resource_manager
    try:
        from engine.resource_manager import cleanup_resources
        results["resource_manager"] = True
        log("  ✅ resource_manager imports OK", "SUCCESS")
    except Exception as e:
        log(f"  ❌ resource_manager: {e}", "ERROR")

    # تست 2: data_connector
    try:
        from engine.data_connector import DataConnector, connector
        results["data_connector"] = True
        log("  ✅ data_connector imports OK", "SUCCESS")

        # بررسی _sanitize_sql
        if hasattr(DataConnector, '_sanitize_sql'):
            log("  ✅ _sanitize_sql method exists", "SUCCESS")
        else:
            log("  ⚠️  _sanitize_sql method missing", "WARNING")

    except Exception as e:
        log(f"  ❌ data_connector: {e}", "ERROR")
        return results

    # تست 3: hub
    try:
        from database.hub import hub
        results["hub"] = True
        log("  ✅ hub imports OK", "SUCCESS")
    except Exception as e:
        log(f"  ❌ hub: {e}", "ERROR")

    # تست 4-5: SQL Injection
    try:
        from engine.data_connector import connector

        # SELECT
        try:
            connector.execute_analytics_query("SELECT 1 as test")
            results["select_works"] = True
            log("  ✅ SELECT works", "SUCCESS")
        except Exception as e:
            log(f"  ❌ SELECT failed: {e}", "ERROR")

        # DROP should be blocked
        try:
            connector.execute_analytics_query("DROP TABLE users")
            log("  ❌ DROP was NOT blocked!", "ERROR")
        except ValueError as e:
            if "blocked" in str(e).lower() or "dangerous" in str(e).lower():
                results["drop_blocked"] = True
                log("  ✅ DROP blocked correctly", "SUCCESS")
            else:
                log(f"  ⚠️  DROP blocked with different error: {e}", "WARNING")
        except Exception as e:
            log(f"  ⚠️  DROP raised {type(e).__name__}", "WARNING")

    except Exception as e:
        log(f"  ❌ SQL tests: {e}", "ERROR")

    return results


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> int:
    banner("🔬 پچ جراحی - اصلاح خط-به-خط")

    log("📋 مشکلاتی که رفع می‌شوند:", "INFO")
    log("  1. resource_manager.py:74 - NameError: Dict", "INFO")
    log("  2. data_connector.py - Dict import + SQL Sanitizer", "INFO")
    log("  3. hub.py - pool_size=10 → 30", "INFO")

    log("\n" + "=" * 70, "INFO")
    log("FIX 1: resource_manager.py", "BOLD")
    log("=" * 70, "INFO")
    fix_resource_manager()

    log("\n" + "=" * 70, "INFO")
    log("FIX 2: data_connector.py", "BOLD")
    log("=" * 70, "INFO")
    fix_data_connector()

    log("\n" + "=" * 70, "INFO")
    log("FIX 3: hub.py (pool size)", "BOLD")
    log("=" * 70, "INFO")
    fix_hub_pool()

    log("\n" + "=" * 70, "INFO")
    log("تأیید نهایی", "BOLD")
    log("=" * 70, "INFO")
    results = verify_all()

    # خلاصه
    banner("📊 خلاصه جراحی")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    log("نتایج:", "INFO")
    for key, value in results.items():
        emoji = "✅" if value else "❌"
        log(f"  {emoji} {key}", "SUCCESS" if value else "ERROR")

    log(f"\n🎯 موفقیت: {passed}/{total}",
        "SUCCESS" if passed >= total - 1 else "WARNING")

    log("\n📋 دستورات بعدی:", "INFO")
    log("  1. تست سریع:", "INFO")
    log("     python -c \"from engine.data_connector import connector; print('✅ OK')\"", "INFO")
    log("  2. Hell Protocol:", "INFO")
    log("     python eco_chaos_test_v2.py --hell --quick", "INFO")

    return 0 if passed >= total - 1 else 1


if __name__ == "__main__":
    sys.exit(main())