"""Internal database maintenance: integrity check, optimize, safe backup.

Usage:
    python scripts/db_maintenance.py            # check + ANALYZE + stats
    python scripts/db_maintenance.py --backup   # also write backups/econojin-<ts>.db
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--backup', action='store_true')
    args = ap.parse_args()

    db_path = Path('data/econojin.db')
    if not db_path.exists():
        print(f'[db] not found: {db_path}', file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    integrity = cur.execute('PRAGMA integrity_check').fetchone()[0]
    journal = cur.execute('PRAGMA journal_mode').fetchone()[0]
    fk = cur.execute('PRAGMA foreign_keys').fetchone()[0]
    size_mb = db_path.stat().st_size / 1e6
    tables = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    rows = 0
    for (name,) in tables:
        try:
            rows += cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        except sqlite3.Error:
            pass
    cur.execute('ANALYZE')
    conn.commit()

    print(f'[db] integrity={integrity} journal={journal} foreign_keys={fk}')
    print(f'[db] size={size_mb:.2f}MB tables={len(tables)} rows={rows}')

    if args.backup:
        backups = Path('backups')
        backups.mkdir(exist_ok=True)
        target = backups / f'econojin-{datetime.now().strftime("%Y%m%d-%H%M%S")}.db'
        conn.execute(f"VACUUM INTO '{target.as_posix()}'")
        print(f'[db] backup written: {target}')

    conn.close()
    return 0 if integrity == 'ok' else 2


if __name__ == '__main__':
    raise SystemExit(main())
