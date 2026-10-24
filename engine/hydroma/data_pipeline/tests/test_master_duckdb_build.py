"""Guards for ``tools/build_master_duckdb.py``.

The point of this build is honesty: the DuckDB master that
``engine/data_connector.py`` reads must contain exactly the tables that can
be sourced from files in this repository — no more, no fewer. These tests
run the builder into a ``tmp_path`` and check the real schema, the real row
counts, and that cell values come from the source files unchanged
(including the CSV's disputed-status labels and its deliberately empty
``ks_admissible_max`` cell).
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import duckdb
import pytest

# The builder lives in tools/, which is not a package; load it by path.
BUILDER_PATH = Path(__file__).resolve().parents[4] / "tools" / "build_master_duckdb.py"
_spec = importlib.util.spec_from_file_location("build_master_duckdb", BUILDER_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load builder from {BUILDER_PATH}")
build_master_duckdb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_master_duckdb)

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The exact schema this build is documented to produce. Asserting the set
#: (not just the counts) is what keeps "invent a table to reach a number"
#: from creeping back in.
EXPECTED_TABLES = {
    "soil_parameters": 12,
    "crop_parameters": 3,
    "model_registry": 9,
    "soil_texture_classes": 12,
    "master_build_provenance": 4,
}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """The master DuckDB, built once into a temporary directory."""
    db_path = tmp_path_factory.mktemp("master") / "eco_nojin_master.duckdb"
    report = build_master_duckdb.build_master(db_path, built_at="2026-10-10T00:00:00+00:00")
    return db_path, report


def _rows(db_path: Path, sql: str) -> list[tuple]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


# ── schema and counts ──────────────────────────────────────────────


def test_build_report_lists_the_real_tables_and_counts(built):
    _, report = built
    assert report["tables"] == EXPECTED_TABLES


def test_database_contains_exactly_the_documented_tables(built):
    db_path, _ = built
    tables = {
        row[0]
        for row in _rows(
            db_path,
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'",
        )
    }
    assert tables == set(EXPECTED_TABLES)


def test_weather_daily_is_absent_on_purpose(built):
    """No climate time series exists in the repo, so none may be invented."""
    db_path, _ = built
    assert "weather_daily" not in {row[0] for row in _rows(db_path, "SHOW TABLES")}
    _, report = built
    assert "weather_daily" in report["not_built"]


# ── values come from the sources ───────────────────────────────────


def _csv_index(path: Path, key: str) -> dict:
    return {
        row[key]: row
        for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    }


def test_soil_parameters_values_match_the_csv(built):
    db_path, _ = built
    source = _csv_index(REPO_ROOT / "engine" / "data" / "soil_vg_table.csv", "texture")

    rows = _rows(
        db_path,
        "SELECT soil_type, theta_r, theta_s, alpha, n, ks_cm_per_day, ks_admissible_max,"
        " provenance, status FROM soil_parameters WHERE soil_type = 'loam'",
    )
    assert len(rows) == 1
    soil_type, theta_r, theta_s, alpha, n, ks, ks_max, provenance, status = rows[0]
    loam = source["loam"]
    assert soil_type == "loam"
    assert theta_r == float(loam["theta_r"])
    assert theta_s == float(loam["theta_s"])
    assert alpha == float(loam["alpha"])
    assert n == float(loam["n"])
    assert ks == float(loam["ks_cm_per_day"])
    assert provenance == loam["provenance"]
    assert status == loam["status"]


def test_soil_parameters_carries_the_empty_ks_cell_as_null(built):
    """The CSV leaves sand's ks_admissible_max empty on purpose; so must the DB."""
    db_path, _ = built
    (value,) = _rows(
        db_path, "SELECT ks_admissible_max FROM soil_parameters WHERE soil_type = 'sand'"
    )[0]
    assert value is None


def test_soil_parameters_keep_the_disputed_row_labels(built):
    db_path, _ = built
    disputed = _rows(
        db_path,
        "SELECT COUNT(*) FROM soil_parameters WHERE status = 'design_assumption_disputed'",
    )[0][0]
    assert disputed == 2


def test_crop_parameters_values_match_the_csv(built):
    db_path, _ = built
    source = _csv_index(REPO_ROOT / "engine" / "hydroma" / "data" / "kc_data.csv", "crop_type")

    rows = _rows(db_path, "SELECT crop_name, kc_gs_avg FROM crop_parameters")
    assert dict(rows) == {name: float(row["kc_gs_avg"]) for name, row in source.items()}
    assert dict(rows)["wheat"] == 1.15


def test_model_registry_values_match_the_json(built):
    db_path, _ = built
    registry = json.loads((REPO_ROOT / "data" / "model_registry.json").read_text(encoding="utf-8"))
    expected = {model["model_id"]: model for model in registry["models"]}

    rows = _rows(
        db_path,
        "SELECT model_id, name, version, domain, fidelity, status, doi, tags_json"
        " FROM model_registry",
    )
    got = {row[0]: row for row in rows}
    assert got.keys() == expected.keys()
    first = next(iter(expected))
    model = expected[first]
    assert got[first][1] == model["name"]
    assert got[first][2] == model["version"]
    assert got[first][3] == model["domain"]
    assert got[first][4] == model["fidelity"]
    assert got[first][6] == model["doi"]
    assert json.loads(got[first][7]) == model["tags"]


def test_soil_texture_classes_values_match_taxonomy(built):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT texture_class, clay_min, clay_max, silt_min, silt_max, sand_min, sand_max"
        " FROM soil_texture_classes",
    )
    got = {row[0]: row[1:] for row in rows}
    # engine/hydroma/soil/taxonomy.py: TEXTURE_CLASSES entries as written.
    assert got["sand"] == (0, 10, 0, 15, 85, 100)
    assert got["clay"] == (40, 100, 0, 45, 0, 45)
    assert got["loam"] == (7, 27, 28, 50, 23, 52)


# ── provenance ─────────────────────────────────────────────────────


def test_provenance_records_source_hashes_and_row_counts(built):
    db_path, report = built
    rows = _rows(
        db_path,
        "SELECT table_name, source_file, source_sha256, row_count, schema_version"
        " FROM master_build_provenance ORDER BY table_name",
    )
    by_table = {row[0]: row for row in rows}
    for entry in report["provenance"]:
        row = by_table[entry["table"]]
        assert row[1] == Path(entry["source_path"]).name
        assert row[2] == hashlib.sha256(Path(entry["source_path"]).read_bytes()).hexdigest()
        assert row[3] == entry["rows"]
        assert row[4] == "1"
    assert set(by_table) == {
        "soil_parameters",
        "crop_parameters",
        "model_registry",
        "soil_texture_classes",
    }


def test_extraction_timestamp_is_recorded_on_every_row(built):
    db_path, _ = built
    for table in (
        "soil_parameters",
        "crop_parameters",
        "model_registry",
        "soil_texture_classes",
    ):
        stamps = _rows(db_path, f"SELECT DISTINCT extracted_at FROM {table}")
        assert stamps == [("2026-10-10T00:00:00+00:00",)]


# ── failure behaviour ──────────────────────────────────────────────


def test_missing_source_is_a_build_error(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(build_master_duckdb.BuildError):
        build_master_duckdb.build_master(tmp_path / "m.duckdb", repo_root=repo)


def test_malformed_source_is_a_build_error(tmp_path):
    repo = tmp_path / "repo"
    (repo / "engine" / "data").mkdir(parents=True)
    (repo / "engine" / "hydroma" / "data").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "engine" / "hydroma" / "soil").mkdir(parents=True)
    # Copy everything except the soil CSV, which is replaced by a malformed one.
    for relative in (
        "engine/hydroma/data/kc_data.csv",
        "data/model_registry.json",
        "engine/hydroma/soil/taxonomy.py",
    ):
        target = repo / relative
        target.write_text(
            (REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (repo / "engine" / "data" / "soil_vg_table.csv").write_text(
        "texture,theta_r\nloam,not-a-number\n", encoding="utf-8"
    )

    with pytest.raises((ValueError, build_master_duckdb.BuildError)):
        build_master_duckdb.build_master(tmp_path / "m.duckdb", repo_root=repo)
