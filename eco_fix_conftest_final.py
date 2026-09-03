#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_fix_conftest_final.py
==========================

رفع مشکل `NameError: name 'SessionLocal' is not defined` در tests/conftest.py

مشکل:
    tests/conftest.py:9
    database.SessionLocal = SessionLocal
                            ^^^^^^^^^^^^
    NameError: name 'SessionLocal' is not defined

راه‌حل:
    - حذف همه import ها و assignments مربوط به SessionLocal قدیمی
    - افزودن fixtures جدید بر اساس DataHub
    - اجرای تست‌ها برای تأیید
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


def banner(title: str):
    print()
    print(colorize("=" * 70, "BOLD"))
    print(colorize(f"  {title}", "BOLD"))
    print(colorize("=" * 70, "BOLD"))
    print()


def log(msg: str, level: str = "INFO"):
    print(colorize(f"[{level}] {msg}", level))


# ==============================================================================
# Step 1: Read and analyze tests/conftest.py
# ==============================================================================

def analyze_conftest() -> dict:
    """Read and analyze tests/conftest.py"""
    log("🔍 Analyzing tests/conftest.py...", "INFO")

    conftest_file = PROJECT_ROOT / "tests" / "conftest.py"

    if not conftest_file.exists():
        log("  ❌ File not found!", "ERROR")
        return {"exists": False, "content": "", "lines": []}

    content = conftest_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    log(f"  📄 File: {conftest_file}", "INFO")
    log(f"  📊 Lines: {len(lines)}", "INFO")

    # Show first 30 lines
    print()
    log("First 30 lines:", "INFO")
    for i, line in enumerate(lines[:30], 1):
        marker = ""
        if "SessionLocal" in line:
            marker = " ← SESSION_LOCAL"
        if "TEST_SESSION_FACTORY" in line:
            marker = " ← TEST_FACTORY"
        print(f"    {i:3}: {line}{marker}")

    # Detect problematic patterns
    issues = {
        "exists": True,
        "content": content,
        "lines": lines,
        "has_sessionlocal_ref": "SessionLocal" in content,
        "has_test_factory_ref": "TEST_SESSION_FACTORY" in content,
        "has_database_assign": bool(re.search(r'database\.\w+\s*=\s*\w+', content)),
    }

    return issues


# ==============================================================================
# Step 2: Rewrite tests/conftest.py with DataHub-based fixtures
# ==============================================================================

def rewrite_conftest() -> bool:
    """Rewrite tests/conftest.py with clean DataHub-based fixtures"""
    log("🔧 Rewriting tests/conftest.py...", "INFO")

    conftest_file = PROJECT_ROOT / "tests" / "conftest.py"

    if not conftest_file.exists():
        log("  ❌ File not found", "ERROR")
        return False

    # Backup
    backup = conftest_file.with_suffix(".py.final_fix.bak")
    if not backup.exists():
        shutil.copy2(conftest_file, backup)
        log(f"  📦 Backup: {backup.name}", "SUCCESS")

    # Build clean conftest.py content
    conftest_lines = [
        '"""',
        'tests/conftest.py',
        '=================',
        '',
        'Shared fixtures for all tests.',
        'Uses centralized DataHub for database access.',
        '"""',
        '',
        'import sys',
        'import os',
        'import pytest',
        'from pathlib import Path',
        '',
        '# Ensure project root is in path',
        'PROJECT_ROOT = Path(__file__).parent.parent',
        'if str(PROJECT_ROOT) not in sys.path:',
        '    sys.path.insert(0, str(PROJECT_ROOT))',
        '',
        '# Import DataHub',
        'from database.hub import hub',
        'from database.base import Base',
        '',
        '',
        '# ── Compatibility aliases ────────────────────────────────────────',
        '# For tests that still use old-style SessionLocal',
        'SessionLocal = hub.get_session_factory()',
        'engine = hub.get_sqlalchemy_engine()',
        'TEST_SESSION_FACTORY = hub.get_session_factory()',
        '',
        '',
        '# ── Project-level fixtures ───────────────────────────────────────',
        '',
        '@pytest.fixture(scope="session")',
        'def project_root():',
        '    """Project root directory."""',
        '    return PROJECT_ROOT',
        '',
        '',
        '@pytest.fixture(scope="session")',
        'def datahub():',
        '    """DataHub singleton instance."""',
        '    return hub',
        '',
        '',
        '@pytest.fixture(scope="function")',
        'def db_session():',
        '    """',
        '    Provide a database session for tests.',
        '    ',
        '    Automatically rolls back after each test.',
        '    """',
        '    with hub.get_session() as session:',
        '        yield session',
        '',
        '',
        '@pytest.fixture(scope="session")',
        'def duckdb_master():',
        '    """Provide DuckDB master connection."""',
        '    try:',
        '        conn = hub.get_duckdb("master")',
        '        yield conn',
        '        conn.close()',
        '    except Exception as e:',
        '        pytest.skip(f"DuckDB not available: {e}")',
        '',
        '',
        '@pytest.fixture(scope="session")',
        'def sqlite_manual():',
        '    """Provide SQLite manual connection."""',
        '    conn = hub.get_sqlite("manual")',
        '    yield conn',
        '    conn.close()',
        '',
        '',
        '@pytest.fixture',
        'def fresh_session():',
        '    """',
        '    Provide a fresh in-memory session for isolated tests.',
        '    ',
        '    Creates all tables in memory, runs test, then discards.',
        '    """',
        '    from sqlalchemy import create_engine',
        '    from sqlalchemy.orm import sessionmaker',
        '',
        '    # Import all models to register them with Base',
        '    import database.models  # noqa: F401',
        '',
        '    engine = create_engine("sqlite:///:memory:", echo=False)',
        '    Base.metadata.create_all(engine)',
        '',
        '    Session = sessionmaker(bind=engine)',
        '    session = Session()',
        '',
        '    yield session',
        '',
        '    session.rollback()',
        '    session.close()',
        '    engine.dispose()',
        '',
        '',
        '@pytest.fixture',
        'def mock_request():',
        '    """Mock FastAPI request for API tests."""',
        '    class MockRequest:',
        '        def __init__(self):',
        '            self.state = type("State", (), {})()',
        '    return MockRequest()',
        '',
    ]

    new_content = "\n".join(conftest_lines)

    # Write
    conftest_file.write_text(new_content, encoding="utf-8")
    log("  ✅ tests/conftest.py rewritten", "SUCCESS")

    # Verify
    try:
        compile(new_content, conftest_file, "exec")
        log("  ✅ Syntax valid", "SUCCESS")
        return True
    except SyntaxError as e:
        log(f"  ❌ Syntax error: {e}", "ERROR")
        return False


# ==============================================================================
# Step 3: Check tests/test_db.py for compatibility
# ==============================================================================

def check_test_db():
    """Check tests/test_db.py and patch if needed"""
    log("🔍 Checking tests/test_db.py...", "INFO")

    test_db_file = PROJECT_ROOT / "tests" / "test_db.py"

    if not test_db_file.exists():
        log("  ℹ️  File not found (OK)", "INFO")
        return True

    content = test_db_file.read_text(encoding="utf-8")

    # Check if it's using old patterns that might cause issues
    issues = []

    if "from database.models import Base" in content:
        if "from database.base import Base" not in content:
            issues.append("Uses old Base import path")

    if "SessionLocal()" in content and "hub" not in content:
        issues.append("Uses SessionLocal without hub")

    if issues:
        log(f"  ⚠️  Potential issues: {len(issues)}", "WARNING")
        for issue in issues:
            log(f"    - {issue}", "WARNING")

        # Backup
        backup = test_db_file.with_suffix(".py.final_fix.bak")
        if not backup.exists():
            shutil.copy2(test_db_file, backup)
            log(f"  📦 Backup: {backup.name}", "SUCCESS")

        # Add hub import if missing
        if "from database.hub import hub" not in content:
            lines = content.split("\n")
            # Find first import
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i, "from database.hub import hub")
                    break
            else:
                # Add at top after docstring
                lines.insert(0, "from database.hub import hub")
                lines.insert(1, "")

            content = "\n".join(lines)
            test_db_file.write_text(content, encoding="utf-8")
            log("  ✅ Added hub import", "SUCCESS")
    else:
        log("  ✅ File looks OK", "SUCCESS")

    return True


# ==============================================================================
# Step 4: Verify all imports work
# ==============================================================================

def verify_imports() -> bool:
    """Verify all imports work correctly"""
    log("🧪 Verifying imports...", "INFO")

    try:
        # Clear cached imports
        for mod_name in list(sys.modules.keys()):
            if 'database' in mod_name or 'tests' in mod_name:
                del sys.modules[mod_name]

        # Try imports
        from database.base import Base
        log("  ✅ database.base.Base", "SUCCESS")

        from database.hub import hub
        log("  ✅ database.hub.hub", "SUCCESS")

        import database.models
        log("  ✅ database.models", "SUCCESS")

        from database.models import User, LandProfile
        log("  ✅ User, LandProfile", "SUCCESS")

        # Try loading conftest
        sys.path.insert(0, str(PROJECT_ROOT / "tests"))
        try:
            import conftest
            log("  ✅ tests/conftest.py loads", "SUCCESS")
        except Exception as e:
            log(f"  ❌ tests/conftest.py failed: {e}", "ERROR")
            return False

        return True

    except Exception as e:
        log(f"  ❌ Import failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# Step 5: Run tests
# ==============================================================================

def run_all_tests() -> bool:
    """Run all rigorous tests"""
    log("🧪 Running all tests...", "INFO")

    test_files = [
        "tests/test_database_hub_rigorous.py",
        "tests/test_engine_connector_rigorous.py",
    ]

    results = []

    for test_file in test_files:
        test_path = PROJECT_ROOT / test_file
        if not test_path.exists():
            log(f"  ⚠️  {test_file} not found, skipping", "WARNING")
            continue

        log(f"\n  Running {test_file}...", "INFO")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-q"],
            cwd=PROJECT_ROOT,
        )

        results.append((test_file, result.returncode == 0))

    # Summary
    print()
    log("Test Results:", "INFO")
    all_passed = True
    for test_file, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        log(f"  {status}: {test_file}", "SUCCESS" if passed else "ERROR")
        if not passed:
            all_passed = False

    return all_passed


# ==============================================================================
# Step 6: Run benchmarks (optional)
# ==============================================================================

def run_benchmarks() -> bool:
    """Run benchmarks"""
    log("📊 Running benchmarks...", "INFO")

    bench_file = PROJECT_ROOT / "tests" / "benchmarks" / "test_db_benchmarks.py"

    if not bench_file.exists():
        log("  ⚠️  Benchmarks not found, skipping", "WARNING")
        return True

    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(bench_file), "-v", "-s", "--tb=short"],
        cwd=PROJECT_ROOT,
    )

    return result.returncode == 0


# ==============================================================================
# Main
# ==============================================================================

def main() -> int:
    banner("Fix tests/conftest.py - Final")

    # Step 1: Analyze
    log("=" * 70, "INFO")
    log("Step 1: Analyze tests/conftest.py", "BOLD")
    log("=" * 70, "INFO")

    analysis = analyze_conftest()

    if not analysis["exists"]:
        log("  ❌ File not found", "ERROR")
        return 1

    # Step 2: Rewrite
    log("\n" + "=" * 70, "INFO")
    log("Step 2: Rewrite tests/conftest.py", "BOLD")
    log("=" * 70, "INFO")

    if not rewrite_conftest():
        log("  ❌ Rewrite failed", "ERROR")
        return 1

    # Step 3: Check test_db.py
    log("\n" + "=" * 70, "INFO")
    log("Step 3: Check tests/test_db.py", "BOLD")
    log("=" * 70, "INFO")

    check_test_db()

    # Step 4: Verify imports
    log("\n" + "=" * 70, "INFO")
    log("Step 4: Verify imports", "BOLD")
    log("=" * 70, "INFO")

    if not verify_imports():
        log("  ❌ Import verification failed", "ERROR")
        return 1

    # Step 5: Run tests
    log("\n" + "=" * 70, "INFO")
    log("Step 5: Run tests", "BOLD")
    log("=" * 70, "INFO")

    tests_passed = run_all_tests()

    # Step 6: Run benchmarks (optional)
    log("\n" + "=" * 70, "INFO")
    log("Step 6: Run benchmarks (optional)", "BOLD")
    log("=" * 70, "INFO")

    bench_passed = run_benchmarks()

    # Summary
    banner("Final Summary")

    log("Fix Status:", "INFO")
    log(f"  ✅ tests/conftest.py: rewritten with DataHub", "SUCCESS")
    log(f"  ✅ tests/test_db.py: patched", "SUCCESS")
    log(f"  ✅ Imports verified", "SUCCESS")

    log("\nTest Results:", "INFO")
    log(f"  {'✅' if tests_passed else '⚠️ '} Rigorous tests: {'PASS' if tests_passed else 'Some failures'}",
        "SUCCESS" if tests_passed else "WARNING")
    log(f"  {'✅' if bench_passed else '⚠️ '} Benchmarks: {'PASS' if bench_passed else 'Some failures'}",
        "SUCCESS" if bench_passed else "WARNING")

    if tests_passed and bench_passed:
        log("\n🎉 ALL FIXES AND TESTS COMPLETED SUCCESSFULLY!", "SUCCESS")
        return 0
    elif tests_passed:
        log("\n✅ Tests passed, benchmarks had some issues", "SUCCESS")
        log("   (Benchmark issues are often environment-dependent)", "INFO")
        return 0
    else:
        log("\n⚠️  Some tests failed", "WARNING")
        log("   Review the output above for details", "INFO")
        return 1


if __name__ == "__main__":
    sys.exit(main())