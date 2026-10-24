"""API v1 router — initial stable API.

Every endpoint here either answers with data it actually read, or says it could
not read it. None of them may report a failure as an empty result: ``[]`` and
``{}`` are claims about what exists, and a client cannot distinguish "there are
none" from "this server could not find out". A missing reference store and a
missing row are different facts and get different answers.

The convention matches the rest of the gateway — ``HTTPException(503, detail=)``
naming the cause, as in ``routers/mrv.py:450`` and ``routers/automation.py:74``.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..versioning import ApiVersion

logger = structlog.get_logger("api.v1")

router = APIRouter(prefix="/api/v1")


class HealthResponse(BaseModel):
    status: str
    version: str


class QuantityResponse(BaseModel):
    value: float
    unit: str
    uc: float | None = None
    k: int | None = None
    p: float | None = None
    source: str | None = None


class MotorInfo(BaseModel):
    motor_type: str
    display_name: str
    description: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=ApiVersion.V1.value)


@router.get("/motors", response_model=list[MotorInfo])
async def list_motors() -> list[MotorInfo]:
    """List all available scientific motors.

    Answers 503 when the registry cannot be read. It did not used to: the body
    caught every exception and returned ``[]``, which a client cannot tell apart
    from "this product has no motors". An empty list here is a claim, so a
    failure must not produce one.
    """
    try:
        from services.scientific_motors.registry import MOTOR_REGISTRY

        return [
            MotorInfo(
                motor_type=mtr.motor_type.value,
                display_name=mtr.display_name,
                description=mtr.__doc__ or "",
            )
            for mtr in MOTOR_REGISTRY
        ]
    except Exception as e:
        logger.error(
            "motor_registry_unavailable",
            extra={"error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail="Motor registry is unavailable; the motor list cannot be determined",
        ) from e


@router.get("/motors/{motor_type}", response_model=dict)
async def get_motor_info(motor_type: str) -> dict:
    """Get detailed info about a specific motor."""
    try:
        from services.scientific_motors.registry import get_motor

        motor = get_motor(motor_type)
        if motor is None:
            raise HTTPException(status_code=404, detail=f"Motor {motor_type} not found")
        inputs = motor.get_input_requirements()
        outputs = motor.get_outputs()
        return {
            "motor_type": motor.motor_type.value,
            "display_name": motor.display_name,
            "inputs": [
                {"name": inp.name, "data_type": inp.data_type, "required": inp.required}
                for inp in inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "data_type": out.data_type,
                    "unit": out.quantity.unit if out.quantity else None,
                }
                for out in outputs
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "decision_engine_unavailable",
            extra={"error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=500,
            detail="Decision engine is unavailable",
        ) from e


def _query_reference_table(table: str, columns: tuple[str, ...]) -> list[tuple]:
    """Read a reference table from the DuckDB mirror.

    Raises ``HTTPException`` 503 for every way this can fail, including a missing
    database file. A missing file means the reference data cannot be read, which
    is not the same as the table being empty, and the two used to be reported
    identically.

    The store is reached through ``database.hub.hub``, like every other consumer
    of the reference data. It used to build the path itself --
    ``parents[4] / "data" / "eco_nojin_master.duckdb"`` -- which meant this one
    endpoint kept reading the retired file after the consolidation, and would
    have kept working only for as long as that file was left on disk. The alias
    ``"master"`` is passed unchanged because that is what ``dashboard.py`` and
    ``data_connector.py`` pass, and the hub resolves all three of its aliases to
    ``data/internal.duckdb``.

    ``read_only=True`` is not incidental. This function only issues ``SELECT``,
    and DuckDB refuses a read-only and a read/write handle on one file in a
    single process (measured 2026-10-03). Asking for the read/write handle here
    would lock out ``ScientificDataRepository``, which holds a read-only handle
    for the life of the process. The existence check stays ahead of the connect
    for the same reason it always did: a read-only connect to a missing file
    raises an ``IOException`` that says less than the 503 below.
    """
    from database.hub import hub

    conn = None
    try:
        db_path = hub.internal_duckdb
        if not db_path.exists():
            logger.error(
                "reference_store_missing",
                extra={"path": str(db_path), "table": table},
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Reference store is unavailable: {db_path.name} does not exist, so "
                    f"{table} cannot be read. This is a missing data source, not an "
                    "empty table."
                ),
            )
        conn = hub.get_duckdb("master", read_only=True)
        selected = ", ".join(columns)
        return conn.execute(f"SELECT {selected} FROM {table}").fetchall()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "reference_store_unavailable",
            extra={"table": table, "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail=f"Reference store is unavailable; {table} cannot be read",
        ) from e
    finally:
        if conn is not None:
            hub.release_duckdb(conn)


@router.get("/rules", response_model=list[dict])
async def list_rules() -> list[dict]:
    """List all rules from the decision engine.

    Answers 503 when the store cannot be read rather than an empty list.

    The columns are the ones ``ref_rules`` actually has. It used to select
    ``tag`` and ``category``, which it does not: the query raised a
    BinderException, the ``except`` returned ``[]``, and **118 rows were
    invisible** -- a product with no rules rather than a product with 118.
    Measured 2026-10-03 against ``data/eco_nojin_master.duckdb``.
    """
    rows = _query_reference_table(
        "ref_rules",
        ("rule_id", "priority", "condition", "recommendation", "confidence"),
    )
    return [
        {
            "rule_id": r[0],
            "priority": r[1],
            "condition": r[2],
            "recommendation": r[3],
            "confidence": r[4],
        }
        for r in rows
    ]


@router.get("/units", response_model=list[dict])
async def list_units() -> list[dict]:
    """List all reference units.

    Answers 503 when the store cannot be read rather than an empty list.
    """
    rows = _query_reference_table(
        "ref_units_reference",
        # ``conversion_to_SI`` was renamed to ``conversion_to_si`` at the source
        # by the portability pass -- an unquoted identifier with capitals is
        # folded to lower case by Postgres, so the name cannot survive a move.
        # See ``convert_workbooks.PORTABLE_COLUMN_NAMES``. The retired master
        # file still carries the old spelling, which is why this name is the one
        # thing in this module that changed with the repointing. The response
        # key was already ``conversion_to_si``.
        ("unit_id", "quantity", "unit_code", "unit_fa", "conversion_to_si"),
    )
    return [
        {
            "unit_id": r[0],
            "quantity": r[1],
            "unit_code": r[2],
            "unit_fa": r[3],
            "conversion_to_si": r[4],
        }
        for r in rows
    ]
