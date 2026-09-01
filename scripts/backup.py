"""Eco Nojin automated backup (Phase 0).

Pure-stdlib, no container needed. Backs up:
  1. SQLite databases (consistent copy via sqlite3 backup API)
  2. .env (secrets) — only if present
  3. Git bundle (full history, single file)
  4. Alembic migrations + requirements lockfiles

Usage:
    python scripts/backup.py                 # backup into backups/<timestamp>/
    python scripts/backup.py --retain 10     # keep last N backups
"""
import structlog

logger = structlog.get_logger()
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import shutil
import sqlite3
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKUP_ROOT = ROOT / "backups"
DB_GLOBS = ("*.db", "*.db-wal", "*.db-shm")
EXTRA_FILES = (".env", "requirements.txt", "requirements.lock.txt", "alembic.ini")


def _copy_sqlite(src: pathlib.Path, dst: pathlib.Path) -> bool:
    """Consistent SQLite copy using the online backup API."""
    try:
        con = sqlite3.connect(str(src))
        out = sqlite3.connect(str(dst))
        con.backup(out)
        out.close()
        con.close()
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.info(f"  ! sqlite backup failed for {src.name}: {exc}")
        return False


def run(retain: int) -> int:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_ROOT / stamp
    target.mkdir(parents=True, exist_ok=True)
    logger.info(f"Backup -> {target}")

    # 1) SQLite databases
    for db in ROOT.glob("*.db"):
        if db.name.startswith(("test_", "_")):
            continue
        logger.info(f"  db: {db.name}")
        _copy_sqlite(db, target / db.name)

    # 2) env + lockfiles
    for name in EXTRA_FILES:
        f = ROOT / name
        if f.exists():
            shutil.copy2(f, target / name)
            logger.info(f"  file: {name}")

    # 3) alembic migrations
    alem = ROOT / "alembic"
    if alem.exists():
        shutil.copytree(alem, target / "alembic", dirs_exist_ok=True)
        logger.info("  dir: alembic/")

    # 4) git bundle (full history, single file)
    try:
        bundle = target / "eco_nojin.bundle"
        subprocess.run(
            ["git", "bundle", "create", str(bundle), "--all"],
            cwd=ROOT, check=True, capture_output=True, timeout=300,
        )
        logger.info(f"  git bundle: {bundle.name}")
    except Exception as exc:  # pragma: no cover - defensive
        logger.info(f"  ! git bundle failed: {exc}")

    # 5) retention
    backups = sorted(BACKUP_ROOT.glob("20*"), reverse=True)
    for old in backups[retain:]:
        shutil.rmtree(old, ignore_errors=True)
        logger.info(f"  removed old backup: {old.name}")

    logger.info(f"Done. Total: {(sum(f.stat().st_size for f in target.rglob('*') if f.is_file()) / 1024 / 1024):.1f} MB")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eco Nojin backup")
    parser.add_argument("--retain", type=int, default=10, help="keep last N backups")
    args = parser.parse_args()
    sys.exit(run(args.retain))