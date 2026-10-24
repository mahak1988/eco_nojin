#!/usr/bin/env python3
"""Build the real eco_nojin_master.duckdb from data that exists in this repo.

Why this script exists
----------------------
``engine/data_connector.py`` used to document a 132-table DuckDB master, a
62-table transactional SQLite and an 18-table manual SQLite. None of those
files existed: the repository carries zero ``*.duckdb`` / ``*.db`` /
``*.sqlite`` files. This builder replaces the fiction with the truth — a
small DuckDB master assembled from data that is *actually on disk*, with
per-table provenance (source file, SHA-256, extraction timestamp).

What goes in, and what deliberately does not
--------------------------------------------
Four tables are built, each from one in-repo source:

====================================  ==========================================
Table                                 Source
====================================  ==========================================
``soil_parameters``                   ``engine/data/soil_vg_table.csv`` (12 rows)
``crop_parameters``                   ``engine/hydroma/data/kc_data.csv`` (3 rows)
``model_registry``                    ``data/model_registry.json`` (9 rows)
``soil_texture_classes``              ``engine/hydroma/soil/taxonomy.py``
                                      ``TEXTURE_CLASSES`` (12 rows, read by AST
                                      so importing the engine package is not
                                      required)
``master_build_provenance``           this build: source file, SHA-256, row
                                      count and build timestamp per table
====================================  ==========================================

Tables are *not* invented to reach a number. In particular
``weather_daily`` — which ``engine.data_connector.get_climate_data``
queries — is intentionally absent: no climate station time series exists in
this repository, so the connector fails with an honest catalog error rather
than being handed fabricated weather. The same applies to every transactional
or manual-reference table the old docstring claimed: no SQLite source for
them exists here, so none is built. Populating them means adding a real
source, not a table.

The soil rows carry their repository status verbatim (``provenance`` and
``status`` columns of the CSV, including the two ``design_assumption_disputed``
rows), so a consumer of this database sees the same disagreement labels the
engine shows.

Usage
-----
    python tools/build_master_duckdb.py
    python tools/build_master_duckdb.py --output data/master/eco_nojin_master.duckdb
    python tools/build_master_duckdb.py --json

Exit status is non-zero if any source is missing or malformed.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("build_master_duckdb")

#: Default output location. ``engine.data_connector`` defaults to the same
#: path (overridable with the ``ECO_MASTER_DUCKDB`` environment variable).
DEFAULT_OUTPUT = Path("data/master/eco_nojin_master.duckdb")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Sources, resolved relative to the project root so the script works from
#: any working directory.
SOURCE_FILES: dict[str, Path] = {
    "soil_vg_csv": PROJECT_ROOT / "engine" / "data" / "soil_vg_table.csv",
    "kc_csv": PROJECT_ROOT / "engine" / "hydroma" / "data" / "kc_data.csv",
    "model_registry_json": PROJECT_ROOT / "data" / "model_registry.json",
    "taxonomy_py": PROJECT_ROOT / "engine" / "hydroma" / "soil" / "taxonomy.py",
}

SCHEMA_VERSION = "1"


class BuildError(RuntimeError):
    """A source file is missing or malformed; nothing is fabricated to work around it."""


def _sources(repo_root: Path | None) -> dict[str, Path]:
    """Resolve the four source files, optionally against another root."""
    if repo_root is None:
        return dict(SOURCE_FILES)
    root = Path(repo_root).resolve()
    return {
        "soil_vg_csv": root / "engine" / "data" / "soil_vg_table.csv",
        "kc_csv": root / "engine" / "hydroma" / "data" / "kc_data.csv",
        "model_registry_json": root / "data" / "model_registry.json",
        "taxonomy_py": root / "engine" / "hydroma" / "soil" / "taxonomy.py",
    }


def _relative(path: Path) -> str:
    """Source path as recorded in provenance; absolute when outside the repo."""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


# ── helpers ────────────────────────────────────────────────────────


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise BuildError(f"required source file is missing: {path}")
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    text = _read_text(path)
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise BuildError(f"{path} contains no data rows")
    return rows


def _read_texture_classes(path: Path) -> list[dict[str, Any]]:
    """Read ``TEXTURE_CLASSES`` from taxonomy.py via AST (no engine import).

    The module is parsed rather than imported so the builder never executes
    the engine package (or its optional dependencies) just to read twelve
    documented ranges. A parse failure raises rather than guessing.
    """
    tree = ast.parse(_read_text(path), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TEXTURE_CLASSES" for t in node.targets
        ):
            classes = ast.literal_eval(node.value)
            break
    else:
        raise BuildError(f"TEXTURE_CLASSES not found in {path}")

    rows: list[dict[str, Any]] = []
    for texture, ranges in classes.items():
        row: dict[str, Any] = {"texture_class": texture}
        for fraction in ("clay", "silt", "sand"):
            bounds = ranges[fraction]
            row[f"{fraction}_min"] = float(bounds[0])
            row[f"{fraction}_max"] = float(bounds[1])
        rows.append(row)
    if not rows:
        raise BuildError(f"TEXTURE_CLASSES in {path} is empty")
    return rows


def _optional_float(raw: str | None) -> float | None:
    """Parse a float, mapping empty strings to NULL (present-but-unknown)."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    return float(raw)


# ── table builders ─────────────────────────────────────────────────


def _soil_parameters_rows(sources: dict[str, Path], extracted_at: str) -> list[tuple]:
    """``soil_parameters`` from engine/data/soil_vg_table.csv.

    Column names follow the CSV. ``ks_admissible_max`` is NULL for the
    ``sand`` row because the CSV leaves it empty (the two neighbours
    contradict each other there) — the gap is carried through, not filled.
    """
    source = sources["soil_vg_csv"]
    rows = []
    for row in _read_csv_rows(source):
        texture = (row.get("texture") or "").strip()
        if not texture:
            raise BuildError(f"{source} has a row with no texture")
        rows.append(
            (
                texture,
                float(row["theta_r"]),
                float(row["theta_s"]),
                float(row["alpha"]),
                float(row["n"]),
                float(row["ks_cm_per_day"]),
                _optional_float(row.get("ks_admissible_min")),
                _optional_float(row.get("ks_admissible_max")),
                (row.get("provenance") or "").strip(),
                (row.get("status") or "").strip(),
                _relative(source),
                extracted_at,
            )
        )
    return rows


def _crop_parameters_rows(sources: dict[str, Path], extracted_at: str) -> list[tuple]:
    """``crop_parameters`` from engine/hydroma/data/kc_data.csv."""
    source = sources["kc_csv"]
    rows = []
    for row in _read_csv_rows(source):
        crop = (row.get("crop_type") or "").strip()
        if not crop:
            raise BuildError(f"{source} has a row with no crop_type")
        rows.append(
            (
                crop,
                float(row["kc_gs_avg"]),
                _relative(source),
                extracted_at,
            )
        )
    return rows


def _model_registry_rows(sources: dict[str, Path], extracted_at: str) -> list[tuple]:
    """``model_registry`` from data/model_registry.json."""
    source = sources["model_registry_json"]
    payload = json.loads(_read_text(source))
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        raise BuildError(f"{source} has no 'models' list")
    registry_updated_at = payload.get("updated_at")
    rows = []
    for model in models:
        rows.append(
            (
                str(model.get("model_id", "")),
                str(model.get("name", "")),
                str(model.get("version", "")),
                str(model.get("domain", "")),
                str(model.get("fidelity", "")),
                str(model.get("status", "")),
                str(model.get("description", "")),
                str(model.get("doi", "")),
                json.dumps(model.get("authors", []), ensure_ascii=False),
                json.dumps(model.get("references", []), ensure_ascii=False),
                json.dumps(model.get("tags", []), ensure_ascii=False),
                model.get("created_at"),
                model.get("updated_at"),
                registry_updated_at,
                _relative(source),
                extracted_at,
            )
        )
    return rows


def _soil_texture_classes_rows(sources: dict[str, Path], extracted_at: str) -> list[tuple]:
    """``soil_texture_classes`` from engine/hydroma/soil/taxonomy.py."""
    source = sources["taxonomy_py"]
    return [
        (
            row["texture_class"],
            row["clay_min"],
            row["clay_max"],
            row["silt_min"],
            row["silt_max"],
            row["sand_min"],
            row["sand_max"],
            _relative(source),
            extracted_at,
        )
        for row in _read_texture_classes(source)
    ]


#: Every table this build knows how to produce: name, source key, DDL and
#: row builder. A source that does not exist is a build error; nothing is
#: conditionally skipped to keep a count up.
TABLES: list[dict[str, Any]] = [
    {
        "table": "soil_parameters",
        "source": "soil_vg_csv",
        "ddl": """
            CREATE TABLE soil_parameters (
                soil_type          VARCHAR PRIMARY KEY,
                theta_r            DOUBLE NOT NULL,
                theta_s            DOUBLE NOT NULL,
                alpha              DOUBLE NOT NULL,
                n                  DOUBLE NOT NULL,
                ks_cm_per_day      DOUBLE NOT NULL,
                ks_admissible_min  DOUBLE,
                ks_admissible_max  DOUBLE,
                provenance         VARCHAR NOT NULL,
                status             VARCHAR NOT NULL,
                source_file        VARCHAR NOT NULL,
                extracted_at       VARCHAR NOT NULL
            )
        """,
        "build": _soil_parameters_rows,
        "note": (
            "van Genuchten parameters per USDA texture; provenance/status "
            "carried verbatim from the CSV, including disputed rows"
        ),
    },
    {
        "table": "crop_parameters",
        "source": "kc_csv",
        "ddl": """
            CREATE TABLE crop_parameters (
                crop_name     VARCHAR PRIMARY KEY,
                kc_gs_avg     DOUBLE NOT NULL,
                source_file   VARCHAR NOT NULL,
                extracted_at  VARCHAR NOT NULL
            )
        """,
        "build": _crop_parameters_rows,
        "note": "growing-season average crop coefficients (Kc)",
    },
    {
        "table": "model_registry",
        "source": "model_registry_json",
        "ddl": """
            CREATE TABLE model_registry (
                model_id            VARCHAR PRIMARY KEY,
                name                VARCHAR NOT NULL,
                version             VARCHAR NOT NULL,
                domain              VARCHAR NOT NULL,
                fidelity            VARCHAR NOT NULL,
                status              VARCHAR NOT NULL,
                description         VARCHAR NOT NULL,
                doi                 VARCHAR NOT NULL,
                authors_json        VARCHAR NOT NULL,
                references_json     VARCHAR NOT NULL,
                tags_json           VARCHAR NOT NULL,
                created_at          VARCHAR,
                updated_at          VARCHAR,
                registry_updated_at VARCHAR,
                source_file         VARCHAR NOT NULL,
                extracted_at        VARCHAR NOT NULL
            )
        """,
        "build": _model_registry_rows,
        "note": "scientific model registry entries",
    },
    {
        "table": "soil_texture_classes",
        "source": "taxonomy_py",
        "ddl": """
            CREATE TABLE soil_texture_classes (
                texture_class VARCHAR PRIMARY KEY,
                clay_min      DOUBLE NOT NULL,
                clay_max      DOUBLE NOT NULL,
                silt_min      DOUBLE NOT NULL,
                silt_max      DOUBLE NOT NULL,
                sand_min      DOUBLE NOT NULL,
                sand_max      DOUBLE NOT NULL,
                source_file   VARCHAR NOT NULL,
                extracted_at  VARCHAR NOT NULL
            )
        """,
        "build": _soil_texture_classes_rows,
        "note": (
            "USDA texture-triangle class ranges; overlapping ranges are "
            "resolved by engine.data.soil_table.FINENESS_ORDER"
        ),
    },
]


# ── build ──────────────────────────────────────────────────────────


def build_master(
    db_path: Path,
    repo_root: Path | None = None,
    built_at: str | None = None,
) -> dict[str, Any]:
    """Build the master DuckDB at *db_path* and return a build report.

    The report lists the real table names and row counts written, the
    provenance recorded per table, and the tables this build intentionally
    does not create. *repo_root* is accepted so tests can point the builder
    at a fixture tree; it defaults to the project root.

    Raises:
        BuildError: a source file is missing or malformed.
    """
    sources = _sources(repo_root)
    extracted_at = built_at or datetime.now(UTC).isoformat(timespec="seconds")
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    import duckdb

    report_tables: list[dict[str, Any]] = []
    conn = duckdb.connect(str(db_path))
    try:
        conn.execute("BEGIN TRANSACTION")
        for spec in TABLES:
            source: Path = sources[spec["source"]]
            rows = spec["build"](sources, extracted_at)
            conn.execute(spec["ddl"])
            placeholders = ", ".join("?" for _ in rows[0])
            conn.executemany(f"INSERT INTO {spec['table']} VALUES ({placeholders})", rows)
            report_tables.append(
                {
                    "table": spec["table"],
                    "rows": len(rows),
                    "source_file": source.name,
                    "source_path": str(source),
                    "source_sha256": _sha256(source),
                    "extracted_at": extracted_at,
                    "note": spec["note"],
                }
            )

        # Provenance table, written last, recording the four data sources.
        conn.execute(
            """
            CREATE TABLE master_build_provenance (
                table_name     VARCHAR PRIMARY KEY,
                source_file    VARCHAR NOT NULL,
                source_path    VARCHAR NOT NULL,
                source_sha256  VARCHAR NOT NULL,
                row_count      BIGINT NOT NULL,
                built_at       VARCHAR NOT NULL,
                schema_version VARCHAR NOT NULL,
                note           VARCHAR NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO master_build_provenance VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    entry["table"],
                    entry["source_file"],
                    entry["source_path"],
                    entry["source_sha256"],
                    entry["rows"],
                    entry["extracted_at"],
                    SCHEMA_VERSION,
                    entry["note"],
                )
                for entry in report_tables
            ],
        )
        conn.execute("COMMIT")

        # Verify by reading back, so the report counts what is on disk.
        verified: dict[str, int] = {}
        for table in [spec["table"] for spec in TABLES] + ["master_build_provenance"]:
            count_row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            assert count_row is not None  # COUNT(*) always returns exactly one row
            verified[table] = int(count_row[0])
    finally:
        conn.close()
    return {
        "duckdb_path": str(db_path),
        "schema_version": SCHEMA_VERSION,
        "built_at": extracted_at,
        "tables": verified,
        "provenance": report_tables,
        "not_built": {
            "weather_daily": (
                "no climate station time series exists in this repository; "
                "engine.data_connector.get_climate_data therefore raises a "
                "catalog error instead of being served fabricated weather"
            ),
            "transactional_sqlite_tables": (
                "the 62-table econojin.db claimed by the old docstring has no "
                "source file in this repository"
            ),
            "manual_reference_sqlite_tables": (
                "the 18-table eco_manual_v1.sqlite claimed by the old "
                "docstring has no source file in this repository"
            ),
        },
    }


def print_report(report: dict[str, Any]) -> None:
    """Print the human-readable build report (real names, real counts)."""
    print("eco_nojin_master.duckdb build report")
    print("=" * 60)
    print(f"database:       {report['duckdb_path']}")
    print(f"schema version: {report['schema_version']}")
    print(f"built at:       {report['built_at']}")
    print()
    print(f"{'table':<26}{'rows':>6}  source")
    print("-" * 60)
    total_rows = 0
    sources_by_table = {entry["table"]: entry["source_file"] for entry in report["provenance"]}
    for table, rows in report["tables"].items():
        source = sources_by_table.get(table, "(this build)")
        print(f"{table:<26}{rows:>6}  {source}")
        total_rows += rows
    print("-" * 60)
    print(f"{'TOTAL':<26}{total_rows:>6}  ({len(report['tables'])} tables)")
    print()
    print("provenance")
    print("-" * 60)
    for entry in report["provenance"]:
        print(f"{entry['table']}  <-  {entry['source_path']}")
        print(f"    sha256 {entry['source_sha256'][:16]}…  rows {entry['rows']}")
    print()
    print("deliberately not built")
    print("-" * 60)
    for name, reason in report["not_built"].items():
        print(f"{name}: {reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build data/master/eco_nojin_master.duckdb from in-repository "
            "data, with per-table provenance."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output DuckDB path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="project root holding the source files (default: this repo)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the build report as JSON instead of text",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        report = build_master(args.output, repo_root=args.repo_root)
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - report any failure honestly
        print(f"BUILD FAILED ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
