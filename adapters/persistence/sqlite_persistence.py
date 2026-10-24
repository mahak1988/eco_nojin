"""SQLite adapter for the ECO-04 §4.5 ``PersistencePort`` contract.

This module is an *additional*, spec-conformant implementation of the
abstract persistence contract defined in section ۴.۵ of
``docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md``. It is deliberately kept
separate from the existing engine ports and their in-memory / file-backed
implementations (``engine/ports/*``), which are untouched.

Scope
-----
* Storage: SQLite via the standard library ``sqlite3`` module only
  (ZED rule — no SQLAlchemy, no DuckDB).
* Schema: the section ۴.۴ tables (``datasets``, ``model_runs``, ``models``,
  ``evidence``, ``claims``, ``claim_evidence``, ``scenarios``,
  ``decisions``) created verbatim on init.
* Contract: the section ۴.۵ abstract methods, exactly as declared.

Design notes
------------
* Every connection is opened per operation with ``PRAGMA foreign_keys = ON``
  so the section ۴.۴ foreign keys are enforced (``model_runs.model_id``,
  ``evidence.source_*``, ``claim_evidence.*``).
* Every statement is parameterized; identifiers come only from the
  :data:`_SCHEMA_DDL` / :data:`_TABLE_COLUMNS` constants, never from caller
  input.
* Structured payloads (lists / dicts) are stored through ``json.dumps``
  and read back through ``json.loads``; scalars keep their column type.
* Duplicate ``datasets.content_hash`` (``UNIQUE``) is reported as a
  ``ValueError`` instead of a raw ``sqlite3.IntegrityError``.

Spec wiring: the spec imports ``PersistencePort`` from
``engine.ports.persistence_port``. That module now exists at the
spec-mandated path, so the abstract contract is imported from there
instead of being re-declared in this module; ``PersistencePort`` is still
re-exported here for backwards compatibility.

Beyond the contract, this adapter also provides symmetric read/write
helpers for the tables the contract only writes: ``save_model`` /
``get_model`` (``model_runs`` has a foreign key into ``models``, so the
target row must be writable), ``get_claim``, ``get_scenario`` and
``get_decision``.

Writes are idempotent upserts keyed on the table primary key; keys that
are not columns of the target table (for example the recommended
data-contract aliases of section ۴.۶) are ignored.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from engine.ports.persistence_port import PersistencePort

__all__ = ["PersistencePort", "SQLitePersistence"]


def _new_id() -> str:
    """Return a fresh UUID4 hex string for records without an explicit id."""
    return uuid.uuid4().hex


def _quote(identifier: str) -> str:
    """Quote a table/column identifier (never caller-supplied data)."""
    return '"' + identifier + '"'


def _encode(value: Any) -> Any:
    """Convert a Python payload into a storable SQLite value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _decode(value: Any) -> Any:
    """Convert a stored SQLite value back into a Python payload.

    Text that was written by :func:`_encode` starts with ``{`` or ``[``
    and is parsed back into a container; anything else is returned
    unchanged so plain strings, numbers and ``None`` round-trip exactly.
    """
    if isinstance(value, str) and value[:1] in ("{", "["):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


# ── Section ۴.۴ schema (copied verbatim; parents created before children) ───

_SCHEMA_DDL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS datasets (
        dataset_id TEXT PRIMARY KEY,
        dataset_version TEXT NOT NULL,
        source_id TEXT NOT NULL,
        source_uri TEXT,
        provider TEXT,
        license TEXT,
        retrieved_at TEXT,
        valid_from TEXT,
        valid_to TEXT,
        variable TEXT NOT NULL,
        unit TEXT NOT NULL,
        spatial_ref TEXT,
        temporal_resolution TEXT,
        spatial_resolution TEXT,
        quality_flag TEXT,
        uncertainty REAL,
        processing_history TEXT,
        content_hash TEXT UNIQUE,
        local_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS models (
        model_id TEXT PRIMARY KEY,
        model_version TEXT NOT NULL,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        purpose TEXT,
        inputs_schema TEXT,
        outputs_schema TEXT,
        assumptions TEXT,
        equations TEXT,
        applicability_domain TEXT,
        limitations TEXT,
        scientific_references TEXT,
        calibration_status TEXT,
        validation_status TEXT,
        uncertainty_method TEXT,
        maturity_level TEXT CHECK(maturity_level IN ("S0","S1","S2","S3","S4","S5","S6")),
        UNIQUE(model_id, model_version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_runs (
        run_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        model_version TEXT NOT NULL,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        parameters_json TEXT,
        inputs_hash TEXT,
        outputs_hash TEXT,
        status TEXT CHECK(status IN ("PENDING", "RUNNING", "SUCCESS", "FAILED", "BLOCKED")),
        error_message TEXT,
        execution_time_ms INTEGER,
        environment_json TEXT,
        FOREIGN KEY (model_id) REFERENCES models(model_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id TEXT PRIMARY KEY,
        evidence_type TEXT CHECK(evidence_type IN ("MEASUREMENT", "OBSERVATION",
            "SIMULATION", "EXPERT_OPINION", "SCIENTIFIC_EVIDENCE", "MODEL_OUTPUT")),
        source_dataset_id TEXT,
        source_model_run_id TEXT,
        location TEXT,
        valid_time TEXT,
        value REAL,
        unit TEXT,
        quality_score REAL,
        uncertainty REAL,
        provenance_chain TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_dataset_id) REFERENCES datasets(dataset_id),
        FOREIGN KEY (source_model_run_id) REFERENCES model_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        claim_text TEXT NOT NULL,
        claim_type TEXT,
        epistemic_status TEXT CHECK(epistemic_status IN ("OBSERVATION",
            "MEASUREMENT", "LOCAL_KNOWLEDGE", "TRADITIONAL_KNOWLEDGE",
            "EXPERT_OPINION", "SCIENTIFIC_EVIDENCE", "MODEL_OUTPUT",
            "INFERENCE", "HYPOTHESIS", "EXPERIMENTAL_RESULT")),
        confidence_basis TEXT,
        known_limitations TEXT,
        review_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS claim_evidence (
        claim_id TEXT REFERENCES claims(claim_id),
        evidence_id TEXT REFERENCES evidence(evidence_id),
        relationship TEXT CHECK(relationship IN ("SUPPORTS", "CONTRADICTS", "NEUTRAL")),
        weight REAL DEFAULT 1.0,
        PRIMARY KEY (claim_id, evidence_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scenarios (
        scenario_id TEXT PRIMARY KEY,
        scenario_version TEXT NOT NULL,
        baseline_id TEXT,
        spatial_scope TEXT,
        time_horizon TEXT,
        climate_assumptions TEXT,
        land_management TEXT,
        crop_plan TEXT,
        water_allocation TEXT,
        soil_interventions TEXT,
        economic_assumptions TEXT,
        social_constraints TEXT,
        model_versions TEXT,
        dataset_versions TEXT,
        parameter_set_versions TEXT,
        uncertainty_settings TEXT,
        execution_status TEXT,
        validation_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
        decision_id TEXT PRIMARY KEY,
        problem_definition TEXT,
        objectives TEXT,
        constraints TEXT,
        options_evaluated TEXT,
        scenarios_used TEXT,
        evidence_considered TEXT,
        model_outputs_used TEXT,
        risks TEXT,
        uncertainty_handling TEXT,
        trade_offs TEXT,
        recommendation TEXT,
        recommendation_basis TEXT,
        monitoring_plan TEXT,
        limitations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
)

# Column order per table, mirroring _SCHEMA_DDL exactly. Used to build the
# parameterized INSERT/SELECT statements and to decode rows on read.
_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "datasets": (
        "dataset_id",
        "dataset_version",
        "source_id",
        "source_uri",
        "provider",
        "license",
        "retrieved_at",
        "valid_from",
        "valid_to",
        "variable",
        "unit",
        "spatial_ref",
        "temporal_resolution",
        "spatial_resolution",
        "quality_flag",
        "uncertainty",
        "processing_history",
        "content_hash",
        "local_path",
        "created_at",
    ),
    "models": (
        "model_id",
        "model_version",
        "name",
        "domain",
        "purpose",
        "inputs_schema",
        "outputs_schema",
        "assumptions",
        "equations",
        "applicability_domain",
        "limitations",
        "scientific_references",
        "calibration_status",
        "validation_status",
        "uncertainty_method",
        "maturity_level",
    ),
    "model_runs": (
        "run_id",
        "model_id",
        "model_version",
        "executed_at",
        "parameters_json",
        "inputs_hash",
        "outputs_hash",
        "status",
        "error_message",
        "execution_time_ms",
        "environment_json",
    ),
    "evidence": (
        "evidence_id",
        "evidence_type",
        "source_dataset_id",
        "source_model_run_id",
        "location",
        "valid_time",
        "value",
        "unit",
        "quality_score",
        "uncertainty",
        "provenance_chain",
        "created_at",
    ),
    "claims": (
        "claim_id",
        "claim_text",
        "claim_type",
        "epistemic_status",
        "confidence_basis",
        "known_limitations",
        "review_status",
        "created_at",
        "updated_at",
    ),
    "claim_evidence": ("claim_id", "evidence_id", "relationship", "weight"),
    "scenarios": (
        "scenario_id",
        "scenario_version",
        "baseline_id",
        "spatial_scope",
        "time_horizon",
        "climate_assumptions",
        "land_management",
        "crop_plan",
        "water_allocation",
        "soil_interventions",
        "economic_assumptions",
        "social_constraints",
        "model_versions",
        "dataset_versions",
        "parameter_set_versions",
        "uncertainty_settings",
        "execution_status",
        "validation_status",
        "created_at",
    ),
    "decisions": (
        "decision_id",
        "problem_definition",
        "objectives",
        "constraints",
        "options_evaluated",
        "scenarios_used",
        "evidence_considered",
        "model_outputs_used",
        "risks",
        "uncertainty_handling",
        "trade_offs",
        "recommendation",
        "recommendation_basis",
        "monitoring_plan",
        "limitations",
        "created_at",
    ),
}

# Primary key of each table, used as the ON CONFLICT target of the upserts.
_TABLE_PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "datasets": ("dataset_id",),
    "models": ("model_id",),
    "model_runs": ("run_id",),
    "evidence": ("evidence_id",),
    "claims": ("claim_id",),
    "claim_evidence": ("claim_id", "evidence_id"),
    "scenarios": ("scenario_id",),
    "decisions": ("decision_id",),
}

# Tables carrying a UNIQUE constraint besides the primary key.
_TABLE_UNIQUE_COLUMNS: dict[str, str] = {"datasets": "content_hash"}


# ── Section ۴.۵ PersistencePort (abstract contract) ─────────────────────────
# Imported from its spec-mandated path, ``engine/ports/persistence_port``
# (see the module docstring); no longer re-declared in this module.


# ── SQLite adapter ──────────────────────────────────────────────────────────


class SQLitePersistence(PersistencePort):
    """SQLite-backed :class:`PersistencePort` (stdlib ``sqlite3`` only).

    Parameters
    ----------
    db_path:
        Location of the SQLite database file. The parent directory is
        created when missing. Passing ``":memory:"`` yields a transient
        in-process database (useful for tests).
    """

    def __init__(self, db_path: str = "data/eco-nojin.db") -> None:
        self.db_path = str(db_path)
        parent = Path(self.db_path).expanduser().parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        # SEC-11: the database file carries the coordination state (and,
        # depending on the adapter configuration, secrets); create it with
        # owner-only permissions instead of the umask default, so a local
        # user with filesystem access cannot read it. In-memory databases
        # have no file and are skipped.
        if self.db_path != ":memory:":
            db_file = Path(self.db_path).expanduser()
            if not db_file.exists():
                db_file.touch()
            try:
                db_file.chmod(0o600)
            except OSError:
                # Some filesystems (or non-owner runs) refuse chmod; the
                # database still works, only the permissions stay permissive.
                pass
        self._init_tables()

    # ── connection / schema ────────────────────────────────────────

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with foreign keys enabled and row factory set."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self) -> None:
        """Create the section ۴.۴ tables if they do not exist yet."""
        with self._connect() as conn:
            for statement in _SCHEMA_DDL:
                conn.execute(statement)

    # ── generic row helpers ────────────────────────────────────────

    def _build_row(
        self,
        table: str,
        data: dict[str, Any],
        record_id: str,
    ) -> dict[str, Any]:
        """Return the parameterized row for *data*; unknown keys are ignored."""
        row: dict[str, Any] = {}
        for column in _TABLE_COLUMNS[table]:
            if column == _TABLE_PRIMARY_KEYS[table][0]:
                row[column] = record_id
            elif column in data:
                row[column] = _encode(data[column])
        return row

    def _insert(self, table: str, row: dict[str, Any]) -> None:
        """Upsert *row* into *table* using only parameterized statements."""
        primary_key = _TABLE_PRIMARY_KEYS[table]
        columns = list(row)
        column_sql = ", ".join(_quote(column) for column in columns)
        placeholder_sql = ", ".join(":" + column for column in columns)
        sql = f"INSERT INTO {_quote(table)} ({column_sql}) VALUES ({placeholder_sql})"
        updates = ", ".join(
            f"{_quote(column)} = excluded.{_quote(column)}"
            for column in columns
            if column not in primary_key
        )
        if updates:
            target_sql = ", ".join(_quote(column) for column in primary_key)
            sql += f" ON CONFLICT ({target_sql}) DO UPDATE SET {updates}"
        with self._connect() as conn:
            conn.execute(sql, row)

    def _save(self, table: str, data: dict[str, Any], id_field: str) -> str:
        """Insert/update a record and return its primary key."""
        payload = dict(data)
        record_id = payload.get(id_field) or _new_id()
        row = self._build_row(table, payload, str(record_id))
        try:
            self._insert(table, row)
        except sqlite3.IntegrityError as exc:
            unique_column = _TABLE_UNIQUE_COLUMNS.get(table)
            if unique_column and unique_column in str(exc):
                raise ValueError(
                    f"duplicate {table}.{unique_column}: "
                    f"{payload.get(unique_column)!r} already exists"
                ) from exc
            raise
        return str(record_id)

    def _get(self, table: str, id_field: str, record_id: str) -> dict[str, Any] | None:
        """Fetch one row of *table* by primary key, or ``None``."""
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {_quote(table)} WHERE {_quote(id_field)} = ?",
                (record_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {column: _decode(value) for column, value in dict(row).items()}

    # ── datasets ───────────────────────────────────────────────────

    def save_dataset(self, dataset: dict[str, Any]) -> str:
        """Persist a dataset record. Returns ``dataset_id``."""
        return self._save("datasets", dataset, "dataset_id")

    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        """Return the dataset record with *dataset_id*, or ``None``."""
        return self._get("datasets", "dataset_id", dataset_id)

    # ── model runs ─────────────────────────────────────────────────

    def save_model_run(self, model_run: dict[str, Any]) -> str:
        """Persist a model run. Returns ``run_id``.

        Raises
        ------
        sqlite3.IntegrityError
            Propagated as-is when ``model_id`` does not reference an
            existing row in ``models`` (foreign-key constraint) or when
            ``status`` is outside the CHECK domain.
        """
        return self._save("model_runs", model_run, "run_id")

    def get_model_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the model run with *run_id*, or ``None``."""
        return self._get("model_runs", "run_id", run_id)

    # ── models (helper: model_runs FK target) ──────────────────────

    def save_model(self, model: dict[str, Any]) -> str:
        """Persist a registry model. Returns ``model_id``.

        Not part of the section ۴.۵ contract, but required because
        ``model_runs.model_id`` is a foreign key into ``models``.
        """
        return self._save("models", model, "model_id")

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Return the registry model with *model_id*, or ``None``."""
        return self._get("models", "model_id", model_id)

    # ── evidence ───────────────────────────────────────────────────

    def save_evidence(self, evidence: dict[str, Any]) -> str:
        """Persist an evidence item. Returns ``evidence_id``."""
        return self._save("evidence", evidence, "evidence_id")

    def get_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        """Return the evidence item with *evidence_id*, or ``None``."""
        return self._get("evidence", "evidence_id", evidence_id)

    # ── claims and claim/evidence links ────────────────────────────

    def save_claim(self, claim: dict[str, Any]) -> str:
        """Persist a claim. Returns ``claim_id``."""
        return self._save("claims", claim, "claim_id")

    def get_claim(self, claim_id: str) -> dict[str, Any] | None:
        """Return the claim with *claim_id*, or ``None``."""
        return self._get("claims", "claim_id", claim_id)

    def link_evidence_to_claim(
        self,
        claim_id: str,
        evidence_id: str,
        relationship: str,
        weight: float = 1.0,
    ) -> None:
        """Link an evidence item to a claim with a relationship and weight.

        ``relationship`` must be one of ``SUPPORTS``, ``CONTRADICTS`` or
        ``NEUTRAL``; anything else is rejected by the section ۴.۴ CHECK
        constraint (``sqlite3.IntegrityError``). Linking to a missing claim
        or evidence item is likewise rejected by the foreign keys.
        """
        row = {
            "claim_id": claim_id,
            "evidence_id": evidence_id,
            "relationship": relationship,
            "weight": weight,
        }
        columns = ("claim_id", "evidence_id", "relationship", "weight")
        placeholders = ", ".join(":" + column for column in columns)
        updates = ", ".join(
            f"{_quote(column)} = excluded.{_quote(column)}"
            for column in ("relationship", "weight")
        )
        sql = (
            f"INSERT INTO {_quote('claim_evidence')} "
            f"({', '.join(_quote(column) for column in columns)}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({_quote('claim_id')}, {_quote('evidence_id')}) "
            f"DO UPDATE SET {updates}"
        )
        with self._connect() as conn:
            conn.execute(sql, row)

    def get_claim_evidence(self, claim_id: str) -> list[dict[str, Any]]:
        """Return every evidence link for *claim_id*."""
        columns = ("claim_id", "evidence_id", "relationship", "weight")
        sql = (
            f"SELECT {', '.join(_quote(column) for column in columns)} "
            f"FROM {_quote('claim_evidence')} WHERE {_quote('claim_id')} = ?"
        )
        with self._connect() as conn:
            rows = conn.execute(sql, (claim_id,)).fetchall()
        return [
            {
                "claim_id": row["claim_id"],
                "evidence_id": row["evidence_id"],
                "relationship": row["relationship"],
                "weight": _decode(row["weight"]),
            }
            for row in rows
        ]

    # ── scenarios ──────────────────────────────────────────────────

    def save_scenario(self, scenario: dict[str, Any]) -> str:
        """Persist a scenario. Returns ``scenario_id``."""
        return self._save("scenarios", scenario, "scenario_id")

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        """Return the scenario with *scenario_id*, or ``None``."""
        return self._get("scenarios", "scenario_id", scenario_id)

    # ── decisions ──────────────────────────────────────────────────

    def save_decision(self, decision: dict[str, Any]) -> str:
        """Persist a decision. Returns ``decision_id``."""
        return self._save("decisions", decision, "decision_id")

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        """Return the decision with *decision_id*, or ``None``."""
        return self._get("decisions", "decision_id", decision_id)
