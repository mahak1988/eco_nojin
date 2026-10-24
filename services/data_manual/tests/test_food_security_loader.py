"""Guards for the ``food_security()`` accessor in ``services.data_manual``.

The accessor used to query a ``food_security_indicators`` table inside the
SQLite reference dataset — a file that does not exist in this repository, so
the accessor was code without data.  It now reads ``data/food_security.duckdb``
built by ``tools/build_food_security_table.py`` from real World Bank / FAO
FAOSTAT data, and these tests pin that contract:

* when the store exists (built from recorded live exchanges, no network used
  here), the accessor returns the indicator rows with all provenance columns;
* when it does not, it raises a typed error naming
  ``python tools/build_food_security_table.py`` — never an empty frame that
  reads as "no data".
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import duckdb
import pytest

from services.data_manual import loader as manual

REPO_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = REPO_ROOT / "tools" / "build_food_security_table.py"
FIXTURE_PATH = REPO_ROOT / "tools" / "tests" / "fixtures" / "live_exchange_2026-10-10.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_food_security_table", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_food_security_table"] = module
    spec.loader.exec_module(module)
    return module


builder = _load_builder()

IRAN = "ایران"


@pytest.fixture(scope="module")
def built_store(tmp_path_factory):
    """The store, built from the recorded live exchanges into a temp directory."""
    db_path = tmp_path_factory.mktemp("food_security") / "food_security.duckdb"
    builder.build_food_security(
        db_path, transport=builder.FixtureTransport.from_file(FIXTURE_PATH)
    )
    return db_path


@pytest.fixture
def store_env(built_store, monkeypatch):
    """Point the loader at the built store, and restore the env afterwards."""
    monkeypatch.setenv(manual.FOOD_SECURITY_DB_ENV, str(built_store))
    return built_store


@pytest.fixture
def missing_store(tmp_path, monkeypatch):
    monkeypatch.setenv(manual.FOOD_SECURITY_DB_ENV, str(tmp_path / "absent.duckdb"))
    return tmp_path / "absent.duckdb"


# ── happy path ───────────────────────────────────────────────────────


def test_food_security_returns_the_indicator_rows(store_env):
    df = manual.food_security()

    assert not df.empty
    assert list(df.columns) == list(manual.FOOD_SECURITY_COLUMNS)
    assert set(df["source"]) == {"world_bank", "faostat_food_security", "derived"}
    assert set(df["country_fa"]) == set(builder.COUNTRIES.values())
    # Ordered by year, as the SQLite accessors are.
    years = df["year"].tolist()
    assert years == sorted(years)
    assert df["country_code"].isin(builder.COUNTRIES).all()
    assert df["year"].dtype.kind in "iu"


def test_food_security_filters_by_country_fa(store_env):
    df = manual.food_security(IRAN)

    assert not df.empty
    assert set(df["country_fa"]) == {IRAN}
    assert set(df["country_code"]) == {"IRN"}
    # The derived cereal indicators must be there too, marked as derived.
    derived = df[df["source"] == "derived"]
    assert set(derived["indicator_code"]) == set(builder.DERIVED_FORMULAS)
    assert (derived["indicator_fa"].str.len() > 0).all()


def test_every_returned_row_carries_provenance(store_env):
    df = manual.food_security()

    for column in ("source", "source_url", "retrieved_at"):
        assert df[column].notna().all()
        assert (df[column].astype(str).str.len() > 0).all()
    raw = df[df["source"] != "derived"]
    assert raw["source_url"].str.startswith("https://").all()
    assert df["value"].notna().all()
    assert df["indicator_code"].notna().all()
    assert df["indicator_fa"].notna().all()


def test_food_security_db_path_honours_the_environment(store_env, monkeypatch):
    assert manual.food_security_db_path() == store_env
    monkeypatch.delenv(manual.FOOD_SECURITY_DB_ENV, raising=False)
    assert manual.food_security_db_path().name == "food_security.duckdb"


def test_store_holds_a_data_dictionary_row_per_source(store_env):
    conn = duckdb.connect(str(store_env), read_only=True)
    try:
        rows = conn.execute(
            "SELECT source_id, request_url, licence, retrieved_at, row_count"
            " FROM food_security_sources ORDER BY source_id"
        ).fetchall()
    finally:
        conn.close()
    assert {row[0] for row in rows} == {"derived", "faostat_food_security", "world_bank"}
    for _source_id, request_url, licence, retrieved_at, row_count in rows:
        assert request_url
        assert licence
        assert retrieved_at
        assert row_count > 0
    by_id = {row[0]: row for row in rows}
    assert by_id["world_bank"][1].startswith("https://api.worldbank.org/v2/country/")
    assert by_id["faostat_food_security"][1].startswith("https://")
    # The derived row performs no HTTP request and says so instead of
    # pointing at a URL that was never fetched.
    assert "no HTTP request" in by_id["derived"][1]


# ── honest failure ───────────────────────────────────────────────────


def test_missing_store_raises_naming_the_build_command(missing_store):
    with pytest.raises(manual.FoodSecurityStoreMissing) as excinfo:
        manual.food_security()
    message = str(excinfo.value)
    assert str(missing_store) in message
    assert "python tools/build_food_security_table.py" in message
    assert manual.FOOD_SECURITY_DB_ENV in message


def test_missing_store_for_one_country_also_raises(missing_store):
    with pytest.raises(FileNotFoundError):
        manual.food_security(IRAN)


def test_store_without_the_table_is_a_typed_error(tmp_path, monkeypatch):
    empty = tmp_path / "food_security.duckdb"
    duckdb.connect(str(empty)).close()
    monkeypatch.setenv(manual.FOOD_SECURITY_DB_ENV, str(empty))

    with pytest.raises(manual.FoodSecurityStoreUnusable) as excinfo:
        manual.food_security()
    assert "build_food_security_table.py" in str(excinfo.value)


def test_unknown_country_returns_an_empty_frame_not_an_error(store_env):
    df = manual.food_security("کشور-ناموجود")
    assert df.empty
    assert list(df.columns) == list(manual.FOOD_SECURITY_COLUMNS)
