#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_fix_chaos.py
================

پچ برای رفع مشکل daemon thread در eco_chaos_test.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
chaos_file = PROJECT_ROOT / "eco_chaos_test.py"

if not chaos_file.exists():
    print("❌ eco_chaos_test.py not found")
    exit(1)

content = chaos_file.read_text(encoding="utf-8")

# Backup
backup = chaos_file.with_suffix(".py.chaos_fix.bak")
if not backup.exists():
    import shutil
    shutil.copy2(chaos_file, backup)
    print(f"📦 Backup: {backup.name}")

# Fix 1: Set daemon BEFORE start
old_code = """        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=timeout)

        elapsed = (time.perf_counter() - start) * 1000
        mem_after = ChaosMetrics.get_process_memory_mb()

        if thread.is_alive():
            # Timeout - تست fail شد
            passed = False
            error_type = "TimeoutError"
            error_msg = f"Test exceeded {timeout}s timeout"
            failure_point = "timeout"
            print(f"  ⏰ TIMEOUT after {timeout}s - سیستم هنگ کرد ✅")
            # Force kill
            thread.daemon = True"""

new_code = """        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        elapsed = (time.perf_counter() - start) * 1000
        mem_after = ChaosMetrics.get_process_memory_mb()

        if thread.is_alive():
            # Timeout - تست fail شد
            passed = False
            error_type = "TimeoutError"
            error_msg = f"Test exceeded {timeout}s timeout"
            failure_point = "timeout"
            print(f"  ⏰ TIMEOUT after {timeout}s - سیستم هنگ کرد ✅")
            # Thread will die with process (daemon=True was set before start)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fixed daemon thread issue")
else:
    print("ℹ️  Code already fixed or different structure")

chaos_file.write_text(content, encoding="utf-8")
print("💾 File saved")

# Additional improvements
print("\n📝 Additional improvements:")

# Fix 2: Add better cleanup mechanism
if "import signal" not in content:
    content = content.replace(
        "import sys\nimport os",
        "import sys\nimport os\nimport signal"
    )
    print("  ✅ Added signal import")

# Fix 3: Add force timeout mechanism
if "def force_kill_on_timeout" not in content:
    force_kill_code = '''

def force_kill_on_timeout(thread, timeout):
    """Force kill thread if it exceeds timeout"""
    import ctypes
    
    def _async_raise(tid, exc_type):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid),
            ctypes.py_object(exc_type)
        )
        if res == 0:
            raise ValueError("Invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(tid), None
            )
            raise SystemError("PyThreadState_SetAsyncExc failed")
    
    thread.join(timeout=timeout)
    if thread.is_alive():
        try:
            _async_raise(thread.ident, SystemExit)
            print(f"  🔪 Force killed stuck thread")
        except Exception:
            pass
'''
    # Insert before ChaosOrchestrator class
    insert_pos = content.find("class ChaosOrchestrator:")
    if insert_pos > 0:
        content = content[:insert_pos] + force_kill_code + "\n" + content[insert_pos:]
        print("  ✅ Added force_kill_on_timeout function")

chaos_file.write_text(content, encoding="utf-8")
print("\n🎯 Patch complete! Run: python eco_chaos_test.py --all")