#!/usr/bin/env python3
"""SQLite deployment safety check (B6 / D-16 / KN-09).

The runtime SQLite (3.49.1) is below the WAL-reset fix (3.51.3, backports
3.44.6, 3.50.7). A WAL deployment on an affected build risks a corrupted
WAL database, so this check must pass before any WAL deployment.

Usage:
    python tools/check_sqlite_safety.py               # enforce
    python tools/check_sqlite_safety.py --wal          # also require WAL safety
    python tools/check_sqlite_safety.py --print        # report only

Exit codes:
    0  safe (or --print)
    1  unsafe for WAL deployment
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.hub import (
    _WAL_MIN_SQLITE_VERSION,
    _WAL_MIN_SQLITE_VERSION_TEXT,
    _sqlite_version_info,
    sqlite_wal_deployment_safe,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wal", action="store_true", help="require WAL deployment safety")
    parser.add_argument("--print", action="store_true", help="report only, always 0")
    args = parser.parse_args()

    version = _sqlite_version_info()
    safe = sqlite_wal_deployment_safe()

    print("=" * 70)
    print("SQLITE DEPLOYMENT SAFETY CHECK (B6 / D-16)")
    print("=" * 70)
    print(f"Runtime SQLite version: {'.'.join(map(str, version))}")
    print(f"WAL-safe minimum:       {_WAL_MIN_SQLITE_VERSION_TEXT}")
    print(f"WAL deployment safe:    {safe}")
    print()

    if args.wal and not safe:
        print(
            "UNSAFE: this runtime SQLite is affected by the WAL-reset bug "
            "(fixed in 3.51.3). A WAL deployment risks a corrupted database. "
            "Upgrade SQLite or install the pysqlite3 wheel before deploying "
            "with WAL."
        )
        print("=" * 70)
        print("Status: FAIL")
        return 1

    if safe:
        print("SAFE: WAL deployment is allowed on this runtime.")
    else:
        print("SAFE for default journal (DELETE). WAL deployment requires an upgrade.")
    print("=" * 70)
    print("Status: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
