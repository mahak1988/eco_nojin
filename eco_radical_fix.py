#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_radical_fix.py
==================

رویکرد رادیکال: بازنویسی کامل resource_manager.py با dict lowercase

استراتژی:
    1. بازنویسی کامل resource_manager.py با 'dict' به جای 'Dict'
    2. تأیید فوری data_connector.py
    3. تست فوری

Python 3.9+ از 'dict' lowercase به عنوان type hint پشتیبانی می‌کند
بدون نیاز به import از typing
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


def backup(file_path: Path):
    if file_path.exists():
        bak = file_path.with_suffix(file_path.suffix + ".radical.bak")
        if not bak.exists():
            shutil.copy2(file_path, bak)
            log(f"  📦 Backup: {bak.name}", "SUCCESS")


# ==============================================================================
# FIX 1: بازنویسی کامل resource_manager.py با dict lowercase
# ==============================================================================

def rewrite_resource_manager() -> bool:
    """بازنویسی کامل با dict lowercase (Python 3.9+ standard)"""
    log("🔧 بازنویسی کامل resource_manager.py با dict lowercase...", "INFO")

    file_path = PROJECT_ROOT / "engine" / "resource_manager.py"
    backup(file_path)

    # محتوای کامل با dict lowercase - بدون نیاز به import Dict
    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.resource_manager
=======================

Resource management with automatic cleanup for Eco Nojin.

Uses Python 3.9+ lowercase type hints (dict, list, optional)
to avoid import dependencies.

Usage:
    from engine.resource_manager import managed_connection

    # Auto-closed connection
    with managed_connection("master") as conn:
        result = conn.execute("SELECT 1")

Author: Eco Nojin Architecture Team
Version: 3.0.1 (Python 3.9+ compatible)
"""

import gc
import logging
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger(__name__)


@contextmanager
def managed_connection(database: str = "master", pooled: bool = True):
    """
    Context manager for DuckDB connections.

    Automatically returns connection to pool (or closes it) on exit.

    Args:
        database: "master" or "analytics"
        pooled: Whether to use connection pooling

    Usage:
        with managed_connection("master") as conn:
            result = conn.execute("SELECT * FROM weather_daily")
        # Connection automatically returned to pool here
    """
    from database.hub import hub

    conn = None
    try:
        if pooled and hasattr(hub, "get_duckdb_pooled"):
            conn = hub.get_duckdb_pooled(database)
            try:
                yield conn
            finally:
                hub.return_duckdb_pooled(conn, database)
        else:
            conn = hub.get_duckdb(database)
            try:
                yield conn
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error in managed connection: {e}")
        raise


@contextmanager
def managed_session():
    """Context manager for SQLAlchemy sessions."""
    from database.hub import hub

    with hub.get_session() as session:
        yield session


def cleanup_resources() -> dict:
    """
    Force cleanup of all resources.

    Returns:
        dict with cleanup statistics
    """
    from database.hub import hub

    stats: dict = {
        "gc_collected": 0,
        "connections_closed": 0,
        "sessions_closed": 0,
    }

    # Force garbage collection (3 rounds)
    for _ in range(3):
        stats["gc_collected"] += gc.collect()

    # Close all connections
    try:
        hub.close_all()
        stats["connections_closed"] = 1
    except Exception as e:
        logger.warning(f"Error closing hub connections: {e}")

    logger.info(f"Resource cleanup: {stats}")
    return stats


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0
    except Exception:
        return 0.0


__all__ = [
    "managed_connection",
    "managed_session",
    "cleanup_resources",
    "get_memory_usage_mb",
]
'''

    # compile check قبل از نوشتن
    try:
        compile(content, file_path, "exec")
    except SyntaxError as e:
        log(f"  ❌ Syntax error in generated content: {e}", "ERROR")
        return False

    # نوشتن
    file_path.write_text(content, encoding="utf-8")
    log("  ✅ resource_manager.py completely rewritten", "SUCCESS")
    log("  💡 Key change: 'Dict' -> 'dict' (Python 3.9+ standard)", "INFO")
    return True


# ==============================================================================
# FIX 2: تأیید و اصلاح data_connector.py
# ==============================================================================

def verify_and_fix_data_connector() -> bool:
    """تأیید data_connector.py و اصلاح اگر لازم باشد"""
    log("🔧 بررسی و اصلاح data_connector.py...", "INFO")

    file_path = PROJECT_ROOT / "engine" / "data_connector.py"
    if not file_path.exists():
        log(f"  ❌ File not found", "ERROR")
        return False

    original = file_path.read_text(encoding="utf-8")
    content = original
    changes = []

    # بررسی 1: import re
    if 'import re' not in content:
        content = 'import re\n' + content
        changes.append("import re")

    # بررسی 2: _sanitize_sql method
    if 'def _sanitize_sql(self' not in content:
        # پیدا کردن کلاس DataConnector
        class_idx = content.find('class DataConnector')
        if class_idx >= 0:
            # پیدا کردن اولین def در کلاس
            first_def_idx = content.find('\n    def ', class_idx)
            if first_def_idx > 0:
                sanitize_code = '''
    def _sanitize_sql(self, query: str) -> str:
        """Sanitize SQL - only SELECT/WITH allowed."""
        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        q = query.upper().strip()

        # Dangerous keywords
        dangerous = ['DROP ', 'DELETE ', 'UPDATE ', 'INSERT ',
                    'ALTER ', 'TRUNCATE', 'CREATE ', 'GRANT ',
                    'REVOKE ', 'EXEC(', 'UNION SELECT']
        for kw in dangerous:
            if kw in q:
                raise ValueError(f"Dangerous SQL blocked: {kw.strip()}")

        # Block comments and semicolons
        if '--' in query or '/*' in query:
            raise ValueError("SQL comments blocked")
        if ';' in query and ';' not in query.split("'")[0]:
            raise ValueError("Semicolons blocked")

        if not (q.startswith('SELECT') or q.startswith('WITH')):
            raise ValueError(f"Only SELECT/WITH allowed")

        return query

'''
                content = content[:first_def_idx] + sanitize_code + content[first_def_idx:]
                changes.append("_sanitize_sql method")

    # بررسی 3: فراخوانی sanitizer در execute_analytics_query
    if 'self._sanitize_sql(query)' not in content:
        # پیدا کردن execute_analytics_query
        exec_idx = content.find('def execute_analytics_query(')
        if exec_idx >= 0:
            # پیدا کردن end of docstring
            docstring_end = content.find('"""', exec_idx + 100)
            if docstring_end > 0:
                docstring_end = content.find('"""', docstring_end + 3)
                if docstring_end > 0:
                    docstring_end += 3
                    # پیدا کردن اولین statement
                    next_line = content.find('\n', docstring_end)
                    if next_line > 0:
                        sanitize_call = '\n        query = self._sanitize_sql(query)\n'
                        content = content[:next_line] + sanitize_call + content[next_line:]
                        changes.append("sanitize call in execute_analytics_query")

    # نوشتن اگر تغییری بود
    if content != original:
        try:
            compile(content, file_path, "exec")
            file_path.write_text(content, encoding="utf-8")
            log(f"  ✅ data_connector.py updated: {', '.join(changes)}", "SUCCESS")
            return True
        except SyntaxError as e:
            log(f"  ❌ Syntax error: {e}", "ERROR")
            file_path.write_text(original, encoding="utf-8")
            return False
    else:
        log("  ℹ️  No changes needed", "INFO")
        return True


# ==============================================================================
# VERIFY
# ==============================================================================

def verify_all() -> dict:
    """تأیید نهایی"""
    log("🧪 تأیید نهایی...", "INFO")

    results = {}

    # تست 1: resource_manager
    try:
        from engine.resource_manager import cleanup_resources
        stats = cleanup_resources()
        results["resource_manager"] = True
        log(f"  ✅ resource_manager OK (cleaned {stats['gc_collected']} objects)", "SUCCESS")
    except Exception as e:
        results["resource_manager"] = False
        log(f"  ❌ resource_manager: {e}", "ERROR")

    # تست 2: data_connector
    try:
        from engine.data_connector import DataConnector, connector
        results["data_connector"] = True
        log("  ✅ data_connector OK", "SUCCESS")

        # تست SELECT
        try:
            connector.execute_analytics_query("SELECT 1 as test")
            results["select_works"] = True
            log("  ✅ SELECT works", "SUCCESS")
        except Exception as e:
            results["select_works"] = False
            log(f"  ❌ SELECT failed: {e}", "ERROR")

        # تست DROP (باید بلاک شود)
        try:
            connector.execute_analytics_query("DROP TABLE users")
            results["drop_blocked"] = False
            log("  ❌ DROP was NOT blocked!", "ERROR")
        except ValueError as e:
            if "blocked" in str(e).lower() or "dangerous" in str(e).lower():
                results["drop_blocked"] = True
                log("  ✅ DROP blocked correctly", "SUCCESS")
            else:
                results["drop_blocked"] = False
                log(f"  ⚠️  Different error: {e}", "WARNING")
        except Exception as e:
            results["drop_blocked"] = False
            log(f"  ⚠️  DROP raised: {type(e).__name__}", "WARNING")

    except Exception as e:
        results["data_connector"] = False
        log(f"  ❌ data_connector: {e}", "ERROR")

    return results


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> int:
    banner("🎯 پچ رادیکال - بازنویسی کامل")

    log("💡 استراتژی:", "INFO")
    log("  • استفاده از 'dict' lowercase به جای 'Dict' (Python 3.9+)", "INFO")
    log("  • بدون نیاز به import از typing", "INFO")
    log("  • بازنویسی کامل resource_manager.py", "INFO")
    log("  • تأیید و اصلاح data_connector.py", "INFO")

    log("\n" + "=" * 70, "INFO")
    log("FIX 1: بازنویسی resource_manager.py", "BOLD")
    log("=" * 70, "INFO")
    if not rewrite_resource_manager():
        return 1

    log("\n" + "=" * 70, "INFO")
    log("FIX 2: بررسی data_connector.py", "BOLD")
    log("=" * 70, "INFO")
    verify_and_fix_data_connector()

    log("\n" + "=" * 70, "INFO")
    log("تأیید نهایی", "BOLD")
    log("=" * 70, "INFO")
    results = verify_all()

    # خلاصه
    banner("📊 خلاصه پچ رادیکال")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    log("نتایج:", "INFO")
    for key, value in results.items():
        emoji = "✅" if value else "❌"
        log(f"  {emoji} {key}", "SUCCESS" if value else "ERROR")

    log(f"\n🎯 موفقیت: {passed}/{total}",
        "SUCCESS" if passed == total else "WARNING")

    if passed == total:
        log("\n🚀 همه تست‌ها پاس شدند!", "SUCCESS")
        log("\n📋 دستورات بعدی:", "INFO")
        log("  1. اجرای Hell Protocol:", "INFO")
        log("     python eco_chaos_test_v2.py --hell --quick", "INFO")
        log("  2. Commit و Push:", "INFO")
        log("     $env:Path += ';C:\\Program Files\\Git\\cmd'", "INFO")
        log("     git add -A", "INFO")
        log("     git commit -m 'fix(radical): rewrite resource_manager with dict lowercase'", "INFO")
        log("     git push origin main", "INFO")
    else:
        log("\n⚠️  برخی تست‌ها ناموفق بودند", "WARNING")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())