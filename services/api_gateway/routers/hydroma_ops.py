"""HyDroMa ops API: formula verification + internal database health.

GET /api/v1/hydroma/validation  -> run the formula verification suite
GET /api/v1/hydroma/db-stats    -> internal database health (rows, indexes, journal mode)

Pure, read-only operations (no writes to business tables).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from database.hub import hub

router = APIRouter(prefix="/api/v1/hydroma", tags=["hydroma-ops"])


@router.get("/validation")
def validation_report() -> dict[str, Any]:
    """Run the independent formula verification suite and return the report."""
    try:
        from services.validation.formula_checks import run_all
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"validation suite unavailable: {exc}") from exc
    return run_all()


@router.get("/db-stats")
def db_stats() -> dict[str, Any]:
    """Internal database health: engine, journal mode, table rows, indexes."""
    engine = hub.get_sqlalchemy_engine()
    out: dict[str, Any] = {"dialect": engine.dialect.name}
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "sqlite":
                out["journal_mode"] = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
                out["foreign_keys"] = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
                out["page_count"] = conn.exec_driver_sql("PRAGMA page_count").scalar()
                out["page_size"] = conn.exec_driver_sql("PRAGMA page_size").scalar()
                out["db_size_mb"] = round(
                    (out["page_count"] or 0) * (out["page_size"] or 0) / 1e6, 3
                )
                tables = [
                    r[0]
                    for r in conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                    )
                ]
                out["tables"] = tables
                counts: dict[str, int] = {}
                for t in tables[:40]:
                    try:
                        counts[t] = int(
                            conn.exec_driver_sql(f'SELECT COUNT(*) FROM "{t}"').scalar() or 0
                        )
                    except Exception:
                        counts[t] = -1
                out["row_counts"] = counts
                out["total_rows"] = sum(v for v in counts.values() if v > 0)
                out["indexes"] = [
                    r[0]
                    for r in conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                    )
                ]
            else:
                out["tables"] = []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"db stats failed: {exc}") from exc
    return out
