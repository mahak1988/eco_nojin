"""Guards for ``engine.data_connector`` against the real master DuckDB.

The old module docstring claimed a 132-table DuckDB master, a 62-table
transactional SQLite and an 18-table reference SQLite. None of those files
existed. These tests pin the replacement contract:

* with the master file absent, methods fail with ``MasterDuckDBNotBuilt``
  naming the expected path — not an empty result that reads as "no data";
* with the master built by ``tools/build_master_duckdb.py``, the documented
  methods return the real rows;
* ``_safe_ident`` still rejects anything outside ``[A-Za-z_][A-Za-z0-9_]*``.

All files live under ``tmp_path``; the ``ECO_MASTER_DUCKDB`` variable is
set/removed with ``monkeypatch`` so no test depends on the developer's
environment.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

from engine.data_connector import (
    MASTER_DUCKDB_ENV,
    DataConnector,
    FileDuckDBHub,
    MasterDuckDBNotBuilt,
    _safe_ident,
    default_hub,
    master_duckdb_path,
)

BUILDER_PATH = Path(__file__).resolve().parents[4] / "tools" / "build_master_duckdb.py"
_spec = importlib.util.spec_from_file_location("build_master_duckdb_for_tests", BUILDER_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load builder from {BUILDER_PATH}")
build_master_duckdb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_master_duckdb)

EXPECTED_TABLES = {
    "crop_parameters",
    "master_build_provenance",
    "model_registry",
    "soil_parameters",
    "soil_texture_classes",
}


@pytest.fixture
def missing_master(tmp_path, monkeypatch):
    """An environment whose master DuckDB does not exist."""
    monkeypatch.setenv(MASTER_DUCKDB_ENV, str(tmp_path / "absent.duckdb"))
    return tmp_path / "absent.duckdb"


@pytest.fixture
def built_master(tmp_path, monkeypatch):
    """An environment whose master DuckDB has just been built."""
    db_path = tmp_path / "master" / "eco_nojin_master.duckdb"
    build_master_duckdb.build_master(db_path, built_at="2026-10-10T00:00:00+00:00")
    monkeypatch.setenv(MASTER_DUCKDB_ENV, str(db_path))
    return db_path


# ── missing master: honest failure ─────────────────────────────────


def test_master_path_follows_the_environment_variable(monkeypatch, tmp_path):
    monkeypatch.delenv(MASTER_DUCKDB_ENV, raising=False)
    assert master_duckdb_path().name == "eco_nojin_master.duckdb"
    assert master_duckdb_path().parent.name == "master"

    override = tmp_path / "elsewhere.duckdb"
    monkeypatch.setenv(MASTER_DUCKDB_ENV, str(override))
    assert master_duckdb_path() == override


def test_missing_master_raises_naming_the_path(missing_master):
    connector = DataConnector()
    with pytest.raises(MasterDuckDBNotBuilt) as excinfo:
        connector.get_climate_data(year=2020)

    message = str(excinfo.value)
    assert str(missing_master) in message
    assert "build_master_duckdb.py" in message


def test_soil_and_crop_lookups_fail_loudly_when_the_master_is_absent(missing_master):
    connector = DataConnector()
    for call in (
        lambda: connector.get_soil_parameters("loam"),
        lambda: connector.get_crop_parameters("wheat"),
        lambda: connector.get_table_list(),
        lambda: connector.query_master("SELECT 1"),
    ):
        with pytest.raises(MasterDuckDBNotBuilt):
            call()


def test_default_hub_serves_the_file_on_disk():
    assert isinstance(default_hub(), FileDuckDBHub)


def test_hub_rejects_unknown_database_names(tmp_path):
    hub = FileDuckDBHub()
    with pytest.raises(KeyError):
        hub.get_duckdb("no-such-database")


def test_sqlite_methods_do_not_pretend_a_database_exists():
    with pytest.raises(RuntimeError, match="No SQLite database"):
        FileDuckDBHub().get_sqlite()


# ── built master: real data ────────────────────────────────────────


def test_get_soil_parameters_returns_the_csv_row(built_master):
    expected = None
    for row in csv.DictReader(
        (Path(__file__).resolve().parents[4] / "engine" / "data" / "soil_vg_table.csv")
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        if row["texture"] == "loam":
            expected = row
    assert expected is not None

    result = DataConnector().get_soil_parameters("loam")

    assert result["soil_type"] == "loam"
    assert result["theta_s"] == float(expected["theta_s"])
    assert result["alpha"] == float(expected["alpha"])
    assert result["ks_cm_per_day"] == float(expected["ks_cm_per_day"])
    assert result["provenance"] == expected["provenance"]
    assert result["status"] == expected["status"]


def test_get_crop_parameters_returns_the_csv_row(built_master):
    result = DataConnector().get_crop_parameters("wheat")
    assert result["crop_name"] == "wheat"
    assert result["kc_gs_avg"] == 1.15


def test_get_table_list_returns_the_built_schema(built_master):
    assert set(DataConnector().get_table_list()) == EXPECTED_TABLES


def test_get_table_info_counts_real_rows(built_master):
    info = DataConnector().get_table_info("soil_parameters")
    assert info["table"] == "soil_parameters"
    assert info["rows"] == 12
    assert {column["name"] for column in info["columns"]} >= {
        "soil_type",
        "theta_r",
        "theta_s",
        "alpha",
        "n",
        "ks_cm_per_day",
    }


def test_query_master_returns_parameterized_results(built_master):
    rows = DataConnector().query_master(
        "SELECT soil_type, ks_cm_per_day FROM soil_parameters WHERE soil_type = ?", ["clay"]
    )
    # engine/data/soil_vg_table.csv, clay row: ks_cm_per_day = 4.8 (disputed).
    assert rows == [{"soil_type": "clay", "ks_cm_per_day": 4.8}]


def test_climate_data_fails_with_a_catalog_error_not_empty_data(built_master):
    """``weather_daily`` has no source in this repo; the connector must say so."""
    with pytest.raises(Exception) as excinfo:
        DataConnector().get_climate_data(year=2020)

    assert "weather_daily" in str(excinfo.value)


# ── safety rail ────────────────────────────────────────────────────


def test_safe_ident_still_rejects_injection():
    assert _safe_ident("soil_parameters") == "soil_parameters"
    for bad in ('bad"; DROP TABLE soil_parameters; --', "a b", "1table", ""):
        with pytest.raises(ValueError):
            _safe_ident(bad)
