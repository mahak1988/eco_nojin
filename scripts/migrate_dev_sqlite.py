"""Idempotent dev-SQLite migration: adds columns introduced by fixes D2/D6.

Safe to run multiple times. Only touches the local SQLite database
(data/econojin.db by default). Production Postgres should use Alembic.

Usage:
    python scripts/migrate_dev_sqlite.py [path-to-db]
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

def _safe_ident(name: str) -> str:
    """Validate a SQL identifier."""
    if not _IDENT_RE.fullmatch(str(name)):
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return str(name)

TARGET_COLUMNS = {
    "farms": [
        ("owner_id", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("elevation_m", "REAL"),
        ("area_hectares", "REAL"),
        ("soil_type", "TEXT"),
        ("climate_zone", "TEXT"),
        ("created_at", "TIMESTAMP"),
    ],
    "marketplace_sellers": [
        ("location", "TEXT"),
    ],
    "land_profiles": [
        ("description", "TEXT"),
        ("dem_source", "TEXT"),
        ("dem_resolution_m", "REAL"),
    ],
}


def main() -> int:
    default_db = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "econojin.db")
    )
    db_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else default_db
    if not os.path.exists(db_path):
        print(f"database not found: {db_path}")
        return 1

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for table, columns in TARGET_COLUMNS.items():
        safe_table = _safe_ident(table)
        existing = {row[1] for row in cur.execute("PRAGMA table_info({})".format(safe_table))}
        if not existing:
            print(f"skip {table}: table not found (create_all will build it)")
            continue
        for name, ddl_type in columns:
            safe_name = _safe_ident(name)
            if name in existing:
                print(f"ok    {table}.{name} already exists")
            else:
                cur.execute("ALTER TABLE {} ADD COLUMN {} {}".format(safe_table, safe_name, ddl_type))
                print(f"added {table}.{name} {ddl_type}")
    con.commit()
    con.close()
    print("migration done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())