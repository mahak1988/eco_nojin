#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_final_sql_fix.py
====================

تشخیص و رفع مشکل SQL Injection
استراتژی: بررسی مستقیم execute_analytics_query و افزودن فراخوانی sanitize
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

def log(msg: str, level: str = "INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "WARNING": "\033[93m",
              "ERROR": "\033[91m", "BOLD": "\033[1m", "RESET": "\033[0m"}
    color = colors.get(level, colors["RESET"])
    print(f"{color}[{level}]{colors['RESET']} {msg}")

def banner(title: str):
    print(f"\n\033[1m{'=' * 70}\033[0m")
    print(f"\033[1m  {title}\033[0m")
    print(f"\033[1m{'=' * 70}\033[0m\n")


def diagnose_sql_injection():
    """تشخیص اینکه آیا sanitize فراخوانی می‌شود"""
    banner("🔬 تشخیص SQL Injection")
    
    file_path = PROJECT_ROOT / "engine" / "data_connector.py"
    content = file_path.read_text(encoding="utf-8")
    
    # بررسی 1: وجود _sanitize_sql
    has_sanitize = 'def _sanitize_sql(self' in content
    log(f"  {'✅' if has_sanitize else '❌'} _sanitize_sql method exists: {has_sanitize}",
        "SUCCESS" if has_sanitize else "ERROR")
    
    # بررسی 2: فراخوانی _sanitize_sql
    calls_sanitize = 'self._sanitize_sql(query)' in content
    log(f"  {'✅' if calls_sanitize else '❌'} _sanitize_sql is called: {calls_sanitize}",
        "SUCCESS" if calls_sanitize else "ERROR")
    
    # بررسی 3: موقعیت execute_analytics_query
    exec_match = re.search(r'def execute_analytics_query\(self[^)]*\)[^:]*:', content)
    if exec_match:
        log(f"  ✅ execute_analytics_query found at position {exec_match.start()}", "SUCCESS")
        
        # نمایش ۵۰ خط اول متد
        start = exec_match.start()
        lines = content[start:start+2000].split('\n')
        log("\n  📋 First 15 lines of execute_analytics_query:", "INFO")
        for i, line in enumerate(lines[:15], 1):
            print(f"    {i:2d}: {line}")
    else:
        log("  ❌ execute_analytics_query not found", "ERROR")
    
    return has_sanitize, calls_sanitize


def fix_sql_sanitizer_call():
    """افزودن فراخوانی _sanitize_sql به execute_analytics_query"""
    banner("🔧 Fix: افزودن فراخوانی sanitize")
    
    file_path = PROJECT_ROOT / "engine" / "data_connector.py"
    original = file_path.read_text(encoding="utf-8")
    content = original
    
    # اگر قبلاً فراخوانی می‌شود، رد کن
    if 'self._sanitize_sql(query)' in content:
        log("  ℹ️  Sanitize already called, skipping", "INFO")
        return True
    
    # پیدا کردن execute_analytics_query و افزودن sanitize call
    # استراتژی: پیدا کردن اولین خط بعد از docstring
    
    # روش 1: پیدا کردن "def execute_analytics_query" و عبور از docstring
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if 'def execute_analytics_query(' in line:
            # پیدا کردن انتهای docstring
            j = i + 1
            in_docstring = False
            docstring_char = None
            
            while j < len(lines):
                stripped = lines[j].strip()
                
                # شروع docstring
                if not in_docstring:
                    if '"""' in stripped:
                        count = stripped.count('"""')
                        if count == 2:  # """...""" on one line
                            j += 1
                            break
                        else:
                            in_docstring = True
                            docstring_char = '"""'
                    elif "'''" in stripped:
                        count = stripped.count("'''")
                        if count == 2:
                            j += 1
                            break
                        else:
                            in_docstring = True
                            docstring_char = "'''"
                else:
                    # پایان docstring
                    if docstring_char in stripped:
                        j += 1
                        break
                
                j += 1
            
            # جی الان باید اولین خط بعد از docstring باشد
            # افزودن sanitize call
            indent = '        '  # 8 spaces (method body)
            sanitize_lines = [
                '',
                indent + '# SQL Injection Protection',
                indent + 'query = self._sanitize_sql(query)',
            ]
            
            # درج بعد از docstring
            lines = lines[:j] + sanitize_lines + lines[j:]
            modified = True
            log(f"  ✅ Added sanitize call after line {j}", "SUCCESS")
            break
    
    if not modified:
        # روش 2: استفاده از regex برای یافتن و جایگزینی
        pattern = r'(def execute_analytics_query\(self[^)]*\)[^:]*:\s*(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\')\s*)'
        
        match = re.search(pattern, content)
        if match:
            insertion = match.group(1) + '\n        # SQL Injection Protection\n        query = self._sanitize_sql(query)\n'
            content = content[:match.start()] + insertion + content[match.end():]
            modified = True
            log("  ✅ Added sanitize call (regex method)", "SUCCESS")
    
    if modified:
        new_content = '\n'.join(lines) if 'lines' in locals() else content
        
        # Verify syntax
        try:
            compile(new_content, file_path, "exec")
            file_path.write_text(new_content, encoding="utf-8")
            log("  ✅ data_connector.py updated and verified", "SUCCESS")
            return True
        except SyntaxError as e:
            log(f"  ❌ Syntax error: {e}", "ERROR")
            file_path.write_text(original, encoding="utf-8")
            return False
    
    log("  ⚠️  Could not find insertion point", "WARNING")
    return False


def test_sql_injection():
    """تست SQL Injection protection"""
    banner("🧪 تست SQL Injection")
    
    try:
        from engine.data_connector import connector
        log("  ✅ connector imported", "SUCCESS")
    except Exception as e:
        log(f"  ❌ Import failed: {e}", "ERROR")
        return False
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: SELECT should work
    tests_total += 1
    try:
        connector.execute_analytics_query("SELECT 1 as test")
        log("  ✅ SELECT query works", "SUCCESS")
        tests_passed += 1
    except Exception as e:
        log(f"  ❌ SELECT failed: {e}", "ERROR")
    
    # Test 2: DROP should be blocked
    tests_total += 1
    try:
        connector.execute_analytics_query("DROP TABLE users")
        log("  ❌ DROP was NOT blocked!", "ERROR")
    except ValueError as e:
        if "blocked" in str(e).lower() or "dangerous" in str(e).lower():
            log(f"  ✅ DROP blocked correctly: {e}", "SUCCESS")
            tests_passed += 1
        else:
            log(f"  ⚠️  DROP raised ValueError but unexpected: {e}", "WARNING")
    except Exception as e:
        log(f"  ⚠️  DROP raised {type(e).__name__}: {e}", "WARNING")
    
    # Test 3: DELETE should be blocked
    tests_total += 1
    try:
        connector.execute_analytics_query("DELETE FROM users WHERE 1=1")
        log("  ❌ DELETE was NOT blocked!", "ERROR")
    except ValueError as e:
        if "blocked" in str(e).lower() or "dangerous" in str(e).lower():
            log(f"  ✅ DELETE blocked correctly", "SUCCESS")
            tests_passed += 1
        else:
            log(f"  ⚠️  DELETE raised ValueError but unexpected: {e}", "WARNING")
    except Exception as e:
        log(f"  ⚠️  DELETE raised {type(e).__name__}: {e}", "WARNING")
    
    # Test 4: Semicolon injection should be blocked
    tests_total += 1
    try:
        connector.execute_analytics_query("SELECT 1; DROP TABLE users")
        log("  ❌ Semicolon injection was NOT blocked!", "ERROR")
    except ValueError as e:
        if "blocked" in str(e).lower() or "semicolon" in str(e).lower():
            log(f"  ✅ Semicolon injection blocked correctly", "SUCCESS")
            tests_passed += 1
        else:
            log(f"  ⚠️  Semicolon raised ValueError but unexpected: {e}", "WARNING")
    except Exception as e:
        log(f"  ⚠️  Semicolon raised {type(e).__name__}: {e}", "WARNING")
    
    log(f"\n  📊 Results: {tests_passed}/{tests_total} tests passed",
        "SUCCESS" if tests_passed == tests_total else "WARNING")
    
    return tests_passed == tests_total


def main():
    banner("🎯 پچ نهایی SQL Injection")
    
    log("استراتژی:", "INFO")
    log("  1. تشخیص اینکه آیا _sanitize_sql فراخوانی می‌شود", "INFO")
    log("  2. افزودن فراخوانی در execute_analytics_query", "INFO")
    log("  3. تست SQL Injection protection", "INFO")
    
    # مرحله 1: تشخیص
    has_sanitize, calls_sanitize = diagnose_sql_injection()
    
    # مرحله 2: Fix
    if has_sanitize and not calls_sanitize:
        fix_sql_sanitizer_call()
    
    # مرحله 3: تست
    success = test_sql_injection()
    
    banner("📊 خلاصه")
    
    if success:
        log("✅ SQL Injection protection فعال شد!", "SUCCESS")
        log("\n📋 Commit و Push:", "INFO")
        log("  git add -A", "INFO")
        log("  git commit -m 'fix: activate SQL sanitizer in execute_analytics_query'", "INFO")
        log("  git push origin main", "INFO")
    else:
        log("⚠️  SQL Injection protection نیاز به بررسی دستی دارد", "WARNING")
        log("\n📋 بررسی دستی:", "INFO")
        log("  کد data_connector.py را باز کنید", "INFO")
        log("  مطمئن شوید self._sanitize_sql(query) در execute_analytics_query فراخوانی می‌شود", "INFO")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())