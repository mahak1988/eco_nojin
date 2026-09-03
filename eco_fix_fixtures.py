#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_fix_fixtures.py
===================

افزودن fixture های گمشده به tests/conftest.py:
- datahub_instance
- connector_instance  
- benchmark_timer
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


def banner(title: str):
    print()
    print(colorize("=" * 70, "BOLD"))
    print(colorize(f"  {title}", "BOLD"))
    print(colorize("=" * 70, "BOLD"))
    print()


def log(msg: str, level: str = "INFO"):
    print(colorize(f"[{level}] {msg}", level))


def main() -> int:
    banner("Add Missing Fixtures")

    conftest_file = PROJECT_ROOT / "tests" / "conftest.py"

    if not conftest_file.exists():
        log("❌ tests/conftest.py not found", "ERROR")
        return 1

    # Backup
    backup = conftest_file.with_suffix(".py.fixtures.bak")
    if not backup.exists():
        shutil.copy2(conftest_file, backup)
        log(f"📦 Backup: {backup.name}", "SUCCESS")

    # Read current content
    content = conftest_file.read_text(encoding="utf-8")

    # Fixtures to add (at the end of file)
    fixtures_to_add = '''

# ── Aliases for backward compatibility ─────────────────────────────
@pytest.fixture(scope="session")
def datahub_instance():
    """Alias for datahub fixture (for backward compatibility)."""
    return hub


@pytest.fixture(scope="session")
def connector_instance():
    """Provide DataConnector singleton instance."""
    from engine.data_connector import connector
    return connector


# ── Benchmark timer fixture ────────────────────────────────────────
@pytest.fixture
def benchmark_timer():
    """Context manager for precise timing in benchmarks."""
    import time
    
    class Timer:
        def __init__(self):
            self.start = None
            self.elapsed = None
        
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start
    
    return Timer()
'''

    # Check which fixtures are already present
    needs_datahub_instance = "datahub_instance" not in content or \
                             "def datahub_instance" not in content
    needs_connector_instance = "def connector_instance" not in content
    needs_benchmark_timer = "def benchmark_timer" not in content

    if not (needs_datahub_instance or needs_connector_instance or needs_benchmark_timer):
        log("✅ All fixtures already present", "SUCCESS")
        return 0

    # Append fixtures
    additions = []
    if needs_datahub_instance:
        additions.append("datahub_instance")
    if needs_connector_instance:
        additions.append("connector_instance")
    if needs_benchmark_timer:
        additions.append("benchmark_timer")

    log(f"Adding fixtures: {', '.join(additions)}", "INFO")

    new_content = content.rstrip() + "\n" + fixtures_to_add

    # Write
    conftest_file.write_text(new_content, encoding="utf-8")
    log("✅ tests/conftest.py updated", "SUCCESS")

    # Verify syntax
    try:
        compile(new_content, conftest_file, "exec")
        log("✅ Syntax valid", "SUCCESS")
    except SyntaxError as e:
        log(f"❌ Syntax error: {e}", "ERROR")
        return 1

    # ── Run all tests ──
    banner("Running All Tests")

    # 1) DataHub rigorous
    log("\n" + "=" * 70, "INFO")
    log("1. DataHub rigorous tests", "BOLD")
    log("=" * 70, "INFO")
    r1 = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_database_hub_rigorous.py",
         "-v", "--tb=short", "-q"],
        cwd=PROJECT_ROOT,
    )

    # 2) Connector rigorous
    log("\n" + "=" * 70, "INFO")
    log("2. Connector rigorous tests", "BOLD")
    log("=" * 70, "INFO")
    r2 = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_engine_connector_rigorous.py",
         "-v", "--tb=short", "-q"],
        cwd=PROJECT_ROOT,
    )

    # 3) Benchmarks
    log("\n" + "=" * 70, "INFO")
    log("3. Benchmarks", "BOLD")
    log("=" * 70, "INFO")
    r3 = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/benchmarks/test_db_benchmarks.py",
         "-v", "-s", "--tb=short"],
        cwd=PROJECT_ROOT,
    )

    # 4) Original 79 tests (to ensure no regression)
    log("\n" + "=" * 70, "INFO")
    log("4. Original 79 tests (regression check)", "BOLD")
    log("=" * 70, "INFO")
    r4 = subprocess.run(
        [sys.executable, "-m", "pytest",
         "services", "--tb=short", "-q"],
        cwd=PROJECT_ROOT,
    )

    # Summary
    banner("Final Summary")

    r1_ok = r1.returncode == 0
    r2_ok = r2.returncode == 0
    r3_ok = r3.returncode == 0
    r4_ok = r4.returncode == 0

    log("Test Results:", "INFO")
    log(f"  {'✅' if r1_ok else '⚠️ '} DataHub rigorous: {'PASS' if r1_ok else 'Some failures'}",
        "SUCCESS" if r1_ok else "WARNING")
    log(f"  {'✅' if r2_ok else '⚠️ '} Connector rigorous: {'PASS' if r2_ok else 'Some failures'}",
        "SUCCESS" if r2_ok else "WARNING")
    log(f"  {'✅' if r3_ok else '⚠️ '} Benchmarks: {'PASS' if r3_ok else 'Some failures'}",
        "SUCCESS" if r3_ok else "WARNING")
    log(f"  {'✅' if r4_ok else '⚠️ '} Original 79 tests: {'PASS' if r4_ok else 'Some failures'}",
        "SUCCESS" if r4_ok else "WARNING")

    if all([r1_ok, r2_ok, r3_ok, r4_ok]):
        log("\n🎉 ALL TESTS PASSED!", "SUCCESS")
        return 0
    else:
        total_passed = sum([r1_ok, r2_ok, r3_ok, r4_ok])
        log(f"\n✅ {total_passed}/4 test suites passed", "SUCCESS" if total_passed >= 3 else "WARNING")
        return 0 if r4_ok else 1


if __name__ == "__main__":
    sys.exit(main())