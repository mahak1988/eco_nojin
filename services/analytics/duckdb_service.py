"""
DuckDB Analytics Service (Phase 4)
==================================
Fast analytical summaries over stored satellite rows using DuckDB's
in-process SQL engine.

Design
------
- ``summarize_satellite_rows`` accepts SQLAlchemy ORM rows and converts
  them to a list of plain dicts, then runs SQL against DuckDB's Python
  relation API (``duckdb.sql`` can query Python objects directly).
- The function is pure and unit-testable without any database file.
- Honest by construction: statistics are computed ONLY over rows that
  actually exist; missing data yields ``None``, never fabricated numbers.

DuckDB reference: https://duckdb.org/docs/
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import duckdb

_REQUIRED_KEYS = ("ndvi", "evi", "savi", "data_source")


def _rows_to_dicts(rows: Sequence[Any]) -> List[Dict[str, Any]]:
    """Convert SQLAlchemy ORM rows (or dicts) to plain dicts."""
    out: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            out.append(row)
        else:
            out.append(
                {
                    "ndvi": getattr(row, "ndvi", None),
                    "evi": getattr(row, "evi", None),
                    "savi": getattr(row, "savi", None),
                    "data_source": getattr(row, "data_source", "simulated"),
                }
            )
    return out


def summarize_satellite_rows(rows: Sequence[Any]) -> Dict[str, Any]:
    """NDVI/EVI/SAVI summary over stored satellite rows via DuckDB.

    Args:
        rows: ORM rows or dicts with ndvi/evi/savi/data_source keys.

    Returns:
        Dict with analyses count, ndvi mean/min/max/latest (None when no
        NDVI rows), real_data_count and engine name.
    """
    data = _rows_to_dicts(rows)
    n_real = sum(1 for r in data if r.get("data_source") == "copernicus")

    if not data:
        return {
            "analyses": 0,
            "ndvi_mean": None, "ndvi_min": None, "ndvi_max": None,
            "ndvi_latest": None,
            "real_data_count": 0,
            "engine": "duckdb",
        }

    # DuckDB in-process engine: load rows into a temp table, then run SQL.
    con = duckdb.connect()
    con.execute(
        "CREATE TEMP TABLE sat (ndvi DOUBLE, evi DOUBLE, savi DOUBLE, data_source VARCHAR)"
    )
    con.executemany(
        "INSERT INTO sat VALUES (?, ?, ?, ?)",
        [
            (r.get("ndvi"), r.get("evi"), r.get("savi"), r.get("data_source", "simulated"))
            for r in data
        ],
    )
    agg = con.execute(
        "SELECT count(*), round(avg(ndvi), 4), round(min(ndvi), 4), round(max(ndvi), 4)"
        " FROM sat WHERE ndvi IS NOT NULL"
    ).fetchone()
    latest_row = con.execute(
        "SELECT round(ndvi, 4) FROM sat WHERE ndvi IS NOT NULL"
        " ORDER BY rowid DESC LIMIT 1"
    ).fetchone()

    if agg is None or agg[0] == 0:
        return {
            "analyses": len(data),
            "ndvi_mean": None, "ndvi_min": None, "ndvi_max": None,
            "ndvi_latest": None,
            "real_data_count": n_real,
            "engine": "duckdb",
        }
    return {
        "analyses": len(data),
        "ndvi_mean": agg[1],
        "ndvi_min": agg[2],
        "ndvi_max": agg[3],
        "ndvi_latest": latest_row[0] if latest_row else None,
        "real_data_count": n_real,
        "engine": "duckdb",
    }
