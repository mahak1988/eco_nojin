"""Idempotent dev-SQLite migration: adds columns introduced by fixes D2/D6.

Safe to run multiple times. Only touches the local SQLite database
(data/econojin.db by default). Production Postgres should use Alembic.

Usage:
    python scripts/migrate_dev_sqlite.py [path-to-db]
"""

from __future__ import annotations

import os
import sqlite3
import sys

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
        existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
        if not existing:
            print(f"skip {table}: table not found (create_all will build it)")
            continue
        for name, ddl_type in columns:
            if name in existing:
                print(f"ok    {table}.{name} already exists")
            else:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")
                print(f"added {table}.{name} {ddl_type}")
    con.commit()
    con.close()
    print("migration done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
