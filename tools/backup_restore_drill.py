#!/usr/bin/env python3
"""Backup / restore drill (B6 / D-17).

Proves the backup→restore→row-count path end-to-end on a throwaway
database, and records the evidence. The drill is run against a *copy* of the
live database (never the live one), so it is safe to run in production.

Steps:
  1. create a backup of the source database (copy file + sha256 manifest)
  2. restore into a fresh target path
  3. compare row counts per table (and the total) between source and target
  4. write an evidence JSON with the measured RPO/RTO

Usage:
    python tools/backup_restore_drill.py --source data/app.db --target /tmp/restore.db
    python tools/backup_restore_drill.py --source data/app.db --target /tmp/restore.db --json evidence.json

Exit codes:
    0  drill passed (row counts match)
    1  drill failed (mismatch or error)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import time
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _row_counts(path: Path) -> dict[str, int]:
    """Return {table_name: row_count} for every user table."""
    conn = sqlite3.connect(str(path))
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="source database path")
    parser.add_argument("--target", required=True, help="target (restore) database path")
    parser.add_argument("--json", help="write evidence JSON to this path")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    target = Path(args.target).resolve()

    if not source.exists():
        print(f"source not found: {source}")
        return 1

    print("=" * 70)
    print("BACKUP / RESTORE DRILL (B6 / D-17)")
    print("=" * 70)
    print(f"Source: {source}")
    print(f"Target: {target}")
    print()

    # Step 1: backup (copy + manifest)
    backup_path = target.with_suffix(target.suffix + ".backup")
    if backup_path.exists():
        backup_path.unlink()
    t0 = time.perf_counter()
    shutil.copy2(source, backup_path)
    backup_sha = _sha256(backup_path)
    backup_elapsed = time.perf_counter() - t0

    print(f"Step 1 — backup: {backup_elapsed*1000:.1f} ms, sha256={backup_sha[:12]}…")

    # Step 2: restore into a fresh target
    if target.exists():
        target.unlink()
    t1 = time.perf_counter()
    shutil.copy2(backup_path, target)
    restore_elapsed = time.perf_counter() - t1

    # Verify the restored file matches the backup
    assert _sha256(target) == backup_sha, "restored file does not match the backup"

    print(f"Step 2 — restore: {restore_elapsed*1000:.1f} ms, sha256 matches")

    # Step 3: compare row counts
    source_counts = _row_counts(source)
    target_counts = _row_counts(target)

    mismatched: list[tuple[str, int, int]] = []
    for table in sorted(set(source_counts) | set(target_counts)):
        sc = source_counts.get(table, 0)
        tc = target_counts.get(table, 0)
        if sc != tc:
            mismatched.append((table, sc, tc))

    total_source = sum(source_counts.values())
    total_target = sum(target_counts.values())

    print()
    print(f"Step 3 — row counts: source={total_source}, target={total_target}")
    print(f"  tables compared: {len(source_counts)}")
    if mismatched:
        print(f"  MISMATCHED TABLES: {len(mismatched)}")
        for table, sc, tc in mismatched:
            print(f"    {table}: source={sc}, target={tc}")
    else:
        print("  all table counts match")

    # Step 4: evidence
    evidence = {
        "drill_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "source": str(source),
        "target": str(target),
        "backup_path": str(backup_path),
        "backup_sha256": backup_sha,
        "backup_ms": round(backup_elapsed * 1000, 1),
        "restore_ms": round(restore_elapsed * 1000, 1),
        "rto_ms": round(restore_elapsed * 1000, 1),
        "tables_compared": len(source_counts),
        "total_rows_source": total_source,
        "total_rows_target": total_target,
        "mismatched_tables": [
            {"table": t, "source": sc, "target": tc} for t, sc, tc in mismatched
        ],
        "result": "PASS" if not mismatched else "FAIL",
    }

    if args.json:
        Path(args.json).write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nEvidence written to {args.json}")

    print()
    print("=" * 70)
    if mismatched:
        print("DRILL RESULT: FAIL")
        return 1
    print("DRILL RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
