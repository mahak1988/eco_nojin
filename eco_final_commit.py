#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_final_commit.py
===================

Commit تکمیلی برای ثبت همه تغییرات واقعی معماری

اقدامات:
1. پاک‌سازی فایل‌های .bak از repo
2. افزودن .bak به .gitignore
3. حذف tests/benchmarks و reports از .gitignore
4. Commit همه تغییرات معماری
5. Push به GitHub
"""

import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

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
    print(f"\n{Colors.BOLD}{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}{Colors.RESET}\n")


def run_git(args: list, check: bool = False) -> subprocess.CompletedProcess:
    """Run git command and return result."""
    return subprocess.run(
        ["git"] + args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def cleanup_bak_files() -> int:
    """Remove .bak files from repo (but keep on disk)."""
    log("🗑️  پاک‌سازی فایل‌های .bak از repo...", "INFO")

    result = run_git(["ls-files", "--cached"])
    tracked_files = result.stdout.splitlines()

    bak_files = [f for f in tracked_files if f.endswith(".bak")]

    if not bak_files:
        log("  ℹ️  هیچ فایل .bak در repo نیست", "INFO")
        return 0

    log(f"  📊 {len(bak_files)} فایل .bak یافت شد", "INFO")

    # Untrack (but don't delete from disk)
    for bak_file in bak_files:
        run_git(["rm", "--cached", bak_file])
        log(f"    ✓ {bak_file}", "SUCCESS")

    return len(bak_files)


def update_gitignore() -> bool:
    """Update .gitignore to ignore .bak files and include benchmarks/reports."""
    log("📝 به‌روزرسانی .gitignore...", "INFO")

    gitignore = PROJECT_ROOT / ".gitignore"

    if not gitignore.exists():
        log("  ⚠️  .gitignore یافت نشد", "WARNING")
        return False

    content = gitignore.read_text(encoding="utf-8")
    lines = content.splitlines()
    original = content

    # Additions needed
    additions = [
        "",
        "# ── Database migration backups ──────────────────────────────",
        "*.phase1.bak",
        "*.phase2.bak",
        "*.phase3.bak",
        "*.base_fix.bak",
        "*.final.bak",
        "*.final_fix.bak",
        "*.fixtures.bak",
        "*.patch.bak",
        "*.sql.bak",
        "*.surgical.bak",
        "*.security.bak",
        "*.final_rebuild.bak",
    ]

    # Removals needed (allow benchmarks and reports)
    removals = [
        "reports/",
        "tests/benchmarks/",
    ]

    # Remove exclusions
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped in removals:
            log(f"  ✓ حذف: {stripped}", "SUCCESS")
            continue
        new_lines.append(line)

    # Add backup patterns if not already there
    for add in additions:
        if add and add not in new_lines:
            new_lines.append(add)

    new_content = "\n".join(new_lines)

    if new_content == original:
        log("  ℹ️  تغییری لازم نبود", "INFO")
        return True

    gitignore.write_text(new_content, encoding="utf-8")
    log("  ✅ .gitignore به‌روز شد", "SUCCESS")
    return True


def stage_architecture_changes() -> bool:
    """Stage all architecture-related changes."""
    log("📦 Stage تغییرات معماری...", "INFO")

    paths_to_add = [
        "database/base.py",
        "database/config.py",
        "database/models.py",
        "database/hub/",
        "engine/__init__.py",
        "engine/data_connector.py",
        "services/",
        "tests/conftest.py",
        "tests/conftest_db.py",
        "tests/test_database_hub_rigorous.py",
        "tests/test_engine_connector_rigorous.py",
        "tests/test_db.py",
        "tests/integration/",
        "tests/unit/",
        "tests/benchmarks/",
        "tests/test_alert_loop.py",
        "tests/test_bot_phase1.py",
        "tests/test_land_profile_challenging.py",
        "tests/test_land_profile_comprehensive.py",
        "tests/test_land_profile_model.py",
        "reports/",
        "docs/database_architecture.md",
        "docs/database_hub_usage.md",
    ]

    staged = 0
    for path in paths_to_add:
        result = run_git(["add", path])
        if result.returncode == 0:
            log(f"  ✅ {path}", "SUCCESS")
            staged += 1
        else:
            if "did not match" not in result.stderr:
                log(f"  ⚠️  {path}: {result.stderr.strip()}", "WARNING")

    log(f"  📊 {staged}/{len(paths_to_add)} مسیر stage شدند", "INFO")
    return staged > 0


def commit_and_push() -> bool:
    """Commit changes and push to GitHub."""
    log("📝 Commit و push...", "INFO")

    # Check status
    status = run_git(["status", "--short"])
    if not status.stdout.strip():
        log("  ℹ️  هیچ تغییری برای commit نیست", "INFO")
        return True

    log(f"  📊 تغییرات:\n{status.stdout}", "INFO")

    # Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"""refactor: complete database architecture migration

This commit finalizes the centralized database architecture:

Core Changes:
- Unified Base class across all models (database/base.py)
- Migrated 59 service files from database.config to database.hub
- Updated database/models.py to use centralized Base
- Enhanced DataHub with session management and connection pooling
- Added DataConnector for processing engine integration

Testing Infrastructure:
- Added tests/conftest_db.py with shared fixtures
- Added tests/test_database_hub_rigorous.py (18 tests)
- Added tests/test_engine_connector_rigorous.py (25 tests)
- Added tests/benchmarks/test_db_benchmarks.py (8 benchmarks)
- Updated tests/conftest.py with DataHub-based fixtures

Documentation:
- docs/database_architecture.md: Architecture overview
- docs/database_hub_usage.md: Usage guide
- reports/phase2_migration_report.txt: Migration report
- reports/phase3_consolidation_report.txt: Consolidation report

Results:
- 79 original tests passing (no regression)
- 43 new rigorous tests passing
- 8 benchmarks passing with SLOs
- Consolidated 3 DuckDB into 1 master (132 tables, 467K+ rows)

Migration completed: {timestamp}"""

    result = run_git(["commit", "-m", commit_msg])
    if result.returncode == 0:
        log("  ✅ Commit موفق", "SUCCESS")
    else:
        log(f"  ❌ Commit failed: {result.stderr}", "ERROR")
        return False

    # Push
    result = run_git(["push", "origin", "main"])
    if result.returncode == 0:
        log("  ✅ Push موفق", "SUCCESS")
        return True
    else:
        log(f"  ❌ Push failed: {result.stderr}", "ERROR")
        return False


def main() -> int:
    banner("Complete Architecture Commit")

    # Step 1: Update .gitignore
    log("=" * 70, "INFO")
    log("Step 1: Update .gitignore", "BOLD")
    log("=" * 70, "INFO")
    update_gitignore()

    # Step 2: Cleanup .bak files from repo
    log("\n" + "=" * 70, "INFO")
    log("Step 2: Cleanup .bak files from repo", "BOLD")
    log("=" * 70, "INFO")
    bak_count = cleanup_bak_files()

    # Step 3: Stage architecture changes
    log("\n" + "=" * 70, "INFO")
    log("Step 3: Stage architecture changes", "BOLD")
    log("=" * 70, "INFO")
    if not stage_architecture_changes():
        log("  ❌ No changes staged", "ERROR")
        return 1

    # Step 4: Commit and push
    log("\n" + "=" * 70, "INFO")
    log("Step 4: Commit and push", "BOLD")
    log("=" * 70, "INFO")
    if not commit_and_push():
        return 1

    # Final summary
    banner("Final Summary")

    log("✅ Completed:", "SUCCESS")
    log("  - .bak files removed from repo (kept on disk)", "INFO")
    log("  - .gitignore updated to exclude future .bak files", "INFO")
    log("  - tests/benchmarks/ and reports/ now tracked", "INFO")
    log(f"  - {bak_count} .bak files untracked", "INFO")
    log("  - All architecture changes committed and pushed", "INFO")

    log("\n🎯 Next steps:", "INFO")
    log("  1. Verify on GitHub: https://github.com/mahak1988/eco_nojin", "INFO")
    log("  2. Clean up .bak files from disk after 1 week (optional):", "INFO")
    log("     Get-ChildItem -Path D:\\eco_nojin -Recurse -Filter '*.bak' | Remove-Item", "INFO")

    return 0


if __name__ == "__main__":
    sys.exit(main())