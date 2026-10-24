"""Guards for ``tools/build_food_security_table.py``.

These tests never touch the network.  The builder's transport is injected as
a :class:`~tools.build_food_security_table.FixtureTransport` replaying
``tools/tests/fixtures/live_exchange_2026-10-10.json`` — real, unmodified
responses recorded live from the World Bank API v2 and the FAO FAOSTAT bulk
download (filtered only to keep the file small; see the fixture's ``note``).

What they pin down
------------------
* the store contains exactly the two documented tables with the documented
  columns, and every row carries ``source``, ``source_url`` and
  ``retrieved_at``;
* the three derived indicators equal the documented formulas applied to the
  raw rows that sit next to them in the same table;
* a missing network — or a fixture that does not cover the request — is a
  typed error that writes nothing, never a fabricated row.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import duckdb
import pytest

# The builder lives in tools/, which is not a package; load it by path.
TOOLS_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = TOOLS_DIR / "build_food_security_table.py"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "live_exchange_2026-10-10.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_food_security_table", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_food_security_table"] = module
    spec.loader.exec_module(module)
    return module


builder = _load_builder()

if not FIXTURE_PATH.is_file():  # pragma: no cover - regeneration instructions
    raise RuntimeError(
        f"fixture is missing: {FIXTURE_PATH}; re-record it from a machine with "
        "network access using 'python tools/build_food_security_table.py "
        "--record-fixtures <path>'"
    )


@pytest.fixture(scope="module")
def fixture_document() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built(tmp_path_factory, fixture_document):
    """The store, built once into a temporary directory from the fixtures."""
    db_path = tmp_path_factory.mktemp("food_security") / "food_security.duckdb"
    # A fixed build timestamp makes the derived rows' stamp deterministic
    # while the raw rows keep the fixture's live retrieval timestamps.
    report = builder.build_food_security(
        db_path,
        transport=builder.FixtureTransport.from_file(FIXTURE_PATH),
        retrieved_at="2026-10-10T03:00:00+00:00",
    )
    return db_path, report


def _rows(db_path: Path, sql: str, params: list | None = None) -> list[tuple]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return conn.execute(sql, params or []).fetchall()
    finally:
        conn.close()


def _one(db_path: Path, sql: str, params: list | None = None):
    """First column of the first row."""
    rows = _rows(db_path, sql, params)
    return rows[0][0]
def _tables(db_path: Path) -> set[str]:
    return {
        row[0]
        for row in _rows(
            db_path,
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'",
        )
    }


# ── schema ───────────────────────────────────────────────────────────


def test_store_contains_exactly_the_documented_tables(built):
    db_path, _ = built
    assert _tables(db_path) == {"food_security_indicators", "food_security_sources"}


def test_indicator_table_has_the_documented_columns_in_order(built):
    db_path, _ = built
    columns = [
        row[0]
        for row in _rows(
            db_path,
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_name = 'food_security_indicators' ORDER BY ordinal_position",
        )
    ]
    assert columns == [
        "country_code",
        "country_fa",
        "indicator_code",
        "indicator_fa",
        "year",
        "value",
        "unit",
        "source",
        "source_url",
        "retrieved_at",
    ]


def test_sources_table_has_the_documented_columns(built):
    db_path, _ = built
    columns = {
        row[0]
        for row in _rows(
            db_path,
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_name = 'food_security_sources'",
        )
    }
    assert {"source_id", "request_url", "retrieved_at", "licence", "row_count"} <= columns


def test_report_counts_match_what_is_on_disk(built):
    db_path, report = built
    assert report["mode"] == "fixture"
    assert report["tables"]["food_security_indicators"] == sum(report["rows_by_source"].values())
    assert report["tables"]["food_security_sources"] == 3
    assert set(report["rows_by_source"]) == {"derived", "faostat_food_security", "world_bank"}
    for source, count in report["rows_by_source"].items():
        stored = _one(
            db_path, "SELECT COUNT(*) FROM food_security_indicators WHERE source = ?", [source]
        )
        assert stored == count
    assert report["schema_version"] == "1"


# ── provenance ───────────────────────────────────────────────────────


def test_world_bank_rows_point_at_the_api_url_they_came_from(built, fixture_exchanges):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT source_url, retrieved_at, COUNT(*) FROM food_security_indicators"
        " WHERE source = 'world_bank' GROUP BY 1, 2",
    )
    assert rows
    for url, retrieved_at, _count in rows:
        assert url.startswith("https://api.worldbank.org/v2/country/IRN;TUR;EGY;PAK;CHN;USA")
        # The live exchange timestamp is preserved on every row it produced.
        assert retrieved_at == fixture_exchanges[url]["retrieved_at"]
        assert retrieved_at.endswith("+00:00")


@pytest.fixture(scope="module")
def fixture_exchanges(fixture_document) -> dict:
    """The fixture's recorded exchanges, keyed by URL."""
    return {record["url"]: record for record in fixture_document["responses"]}


def test_faostat_rows_point_at_the_bulk_download(built, fixture_exchanges):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT DISTINCT source_url, retrieved_at FROM food_security_indicators"
        " WHERE source = 'faostat_food_security'",
    )
    assert [url for url, _stamp in rows] == [builder.FAOSTAT_BULK_URL]
    # The live exchange timestamp is preserved, not replaced by the build's.
    assert rows[0][1] == fixture_exchanges[builder.FAOSTAT_BULK_URL]["retrieved_at"]
    assert rows[0][1] != "2026-10-10T03:00:00+00:00"


def test_derived_rows_are_marked_and_link_their_inputs(built):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT indicator_code, source_url, retrieved_at, unit"
        " FROM food_security_indicators WHERE source = 'derived' LIMIT 3",
    )
    assert rows
    for indicator_code, source_url, retrieved_at, _unit in rows:
        assert indicator_code.startswith("derived:")
        assert retrieved_at == "2026-10-10T03:00:00+00:00"
        for input_code in (
            "AG.PRD.CREL.MT",
            "AG.YLD.CREL.KG",
            "AG.LND.ARBL.HA",
            "SP.POP.TOTL",
        ):
            assert f"indicator/{input_code}?" in source_url
        assert "api.worldbank.org" in source_url


def test_provenance_columns_are_never_empty(built):
    db_path, _ = built
    missing = _one(
        db_path,
        "SELECT COUNT(*) FROM food_security_indicators"
        " WHERE source IS NULL OR source = '' OR source_url IS NULL OR source_url = ''"
        " OR retrieved_at IS NULL OR retrieved_at = '' OR value IS NULL"
        " OR country_fa IS NULL OR country_fa = '' OR indicator_fa IS NULL"
        " OR indicator_fa = '' OR unit IS NULL OR unit = ''",
    )
    assert missing == 0
    non_https = _one(
        db_path,
        "SELECT COUNT(*) FROM food_security_indicators"
        " WHERE source <> 'derived' AND source_url NOT LIKE 'https://%'",
    )
    assert non_https == 0


def test_sources_table_records_licence_and_retrieval_per_source(built, fixture_exchanges):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT source_id, publisher, request_url, licence, licence_url, retrieved_at,"
        " row_count FROM food_security_sources ORDER BY source_id",
    )
    by_id = {row[0]: row for row in rows}
    assert set(by_id) == {"derived", "faostat_food_security", "world_bank"}

    world_bank = by_id["world_bank"]
    assert world_bank[1] == "The World Bank"
    assert world_bank[2].startswith("https://api.worldbank.org/v2/country/")
    assert "{indicator}" in world_bank[2]
    assert "CC BY 4.0" in world_bank[3]
    assert world_bank[4].startswith("https://")
    assert world_bank[5] == min(
        record["retrieved_at"] for url, record in fixture_exchanges.items() if "worldbank" in url
    )
    assert world_bank[6] > 0

    faostat = by_id["faostat_food_security"]
    assert faostat[2] == builder.FAOSTAT_BULK_URL
    assert "CC BY 4.0" in faostat[3]
    assert faostat[5].endswith("+00:00")


def test_derived_formulas_are_stored_in_the_sources_table(built):
    db_path, _ = built
    formula_json = _one(
        db_path, "SELECT formula FROM food_security_sources WHERE source_id = 'derived'"
    )
    formulas = json.loads(formula_json)
    assert set(formulas) == set(builder.DERIVED_FORMULAS)
    for code, formula in formulas.items():
        assert len(formula) > 60
        assert code in builder.DERIVED_FORMULAS
    # The formula has to name the raw series it consumes, including the tonne
    # conversion that the x1e6 shorthand gets wrong.
    joined = " ".join(formulas.values())
    for source_code in ("AG.PRD.CREL.MT", "AG.YLD.CREL.KG", "AG.LND.ARBL.HA", "SP.POP.TOTL"):
        assert source_code in joined
    assert "1000 kg" in joined


# ── derived indicator arithmetic ─────────────────────────────────────


def test_derived_indicators_equal_the_documented_formulas(built):
    """Every derived row must reproduce its formula from the raw rows beside it."""
    db_path, _ = built
    raw = {
        (country_code, indicator_code, year): value
        for country_code, indicator_code, year, value in _rows(
            db_path,
            "SELECT country_code, indicator_code, year, value FROM food_security_indicators"
            " WHERE source = 'world_bank'",
        )
    }
    derived = _rows(
        db_path,
        "SELECT country_code, indicator_code, year, value FROM food_security_indicators"
        " WHERE source = 'derived' ORDER BY country_code, indicator_code, year",
    )
    assert derived
    for country_code, indicator_code, year, value in derived:
        production = raw[(country_code, "AG.PRD.CREL.MT", year)]
        yield_kg = raw[(country_code, "AG.YLD.CREL.KG", year)]
        arable = raw[(country_code, "AG.LND.ARBL.HA", year)]
        population = raw[(country_code, "SP.POP.TOTL", year)]
        self_sufficiency = production * 1000.0 / (yield_kg * arable)
        if indicator_code == "derived:cereal_self_sufficiency_proxy":
            expected = self_sufficiency
        elif indicator_code == "derived:per_capita_cereal_production_kg":
            expected = production * 1000.0 / population
        elif indicator_code == "derived:cereal_import_dependency_proxy":
            expected = 100.0 * max(0.0, 1.0 - self_sufficiency)
        else:  # pragma: no cover - the builder only writes these three
            raise AssertionError(f"unexpected derived indicator {indicator_code}")
        assert value == pytest.approx(expected, rel=1e-12), (country_code, indicator_code, year)


def test_derived_values_stay_in_a_plausible_range(built):
    """Guards the unit conversion: x1e6 instead of x1000 shows up here as 1000x."""
    db_path, _ = built
    ratios = [
        value
        for (value,) in _rows(
            db_path,
            "SELECT value FROM food_security_indicators"
            " WHERE indicator_code = 'derived:cereal_self_sufficiency_proxy'",
        )
    ]
    assert ratios
    assert 0.01 < min(ratios)
    assert max(ratios) < 20.0
    per_capita = [
        value
        for (value,) in _rows(
            db_path,
            "SELECT value FROM food_security_indicators"
            " WHERE indicator_code = 'derived:per_capita_cereal_production_kg'",
        )
    ]
    # Domestic cereal production per inhabitant: single-digit to low hundreds
    # of kg per person per year for these six countries.
    assert 1.0 < min(per_capita) < 2000.0
    assert max(per_capita) < 2000.0


def test_derived_indicators_exist_for_every_country(built):
    db_path, _ = built
    rows = _rows(
        db_path,
        "SELECT DISTINCT country_code, country_fa FROM food_security_indicators"
        " WHERE source = 'derived' ORDER BY country_code",
    )
    assert {code for code, _fa in rows} == {"CHN", "EGY", "IRN", "PAK", "TUR", "USA"}
    for code, fa in rows:
        assert code in builder.COUNTRIES
        assert fa == builder.COUNTRIES[code]
        assert fa in ("ایران", "ترکیه", "مصر", "پاکستان", "چین", "ایالات متحده آمریکا")


# ── failure behaviour ────────────────────────────────────────────────


class _Unreachable:
    """A transport that cannot reach the source, like a machine offline."""

    def get_json(self, url: str):
        raise builder.SourceUnavailable(f"{url} could not be reached: ConnectionError")

    def get_bytes(self, url: str):
        raise builder.SourceUnavailable(f"{url} could not be reached: ConnectionError")


def test_missing_network_is_a_typed_error(tmp_path):
    db_path = tmp_path / "food_security.duckdb"
    with pytest.raises(builder.SourceUnavailable):
        builder.build_food_security(db_path, transport=_Unreachable())
    assert not db_path.exists()
    assert not db_path.with_name(db_path.name + ".partial").exists()


def test_an_unreachable_response_status_is_a_typed_error(tmp_path):
    class _UnavailableStatus:
        def get_json(self, url: str):
            raise builder.SourceUnavailable(f"{url} returned HTTP 503")

        def get_bytes(self, url: str):
            raise builder.SourceUnavailable(f"{url} returned HTTP 503")

    db_path = tmp_path / "food_security.duckdb"
    with pytest.raises(builder.SourceUnavailable) as excinfo:
        builder.build_food_security(db_path, transport=_UnavailableStatus())
    assert "503" in str(excinfo.value)
    assert not db_path.exists()


def test_a_fixture_that_does_not_cover_the_request_is_an_error(tmp_path, fixture_document):
    """A recorded exchange set with the FAOSTAT URL removed must not be faked."""
    partial = [record for record in fixture_document["responses"] if "worldbank" in record["url"]]
    doc = dict(fixture_document, responses=partial)
    fixture = tmp_path / "partial.json"
    fixture.write_text(json.dumps(doc), encoding="utf-8")

    transport = builder.FixtureTransport.from_file(fixture)
    db_path = tmp_path / "food_security.duckdb"
    with pytest.raises(builder.SourceUnavailable) as excinfo:
        builder.build_food_security(db_path, transport=transport)
    assert builder.FAOSTAT_BULK_URL in str(excinfo.value)
    assert not db_path.exists()


def test_a_malformed_payload_is_a_typed_error(tmp_path, fixture_document):
    import copy

    doc = copy.deepcopy(fixture_document)
    for record in doc["responses"]:
        if "worldbank" in record["url"]:
            record["payload"] = {"unexpected": True}
            break
    fixture = tmp_path / "malformed.json"
    fixture.write_text(json.dumps(doc), encoding="utf-8")

    with pytest.raises(builder.MalformedResponse):
        builder.build_food_security(
            tmp_path / "food_security.duckdb",
            transport=builder.FixtureTransport.from_file(fixture),
        )


def test_refuses_to_write_into_the_repo_master_duckdb(tmp_path, monkeypatch):
    """The master file belongs to tools/build_master_duckdb.py; leave it alone.

    ``PROJECT_ROOT`` is redirected so the repo's own master file is only ever
    *read* (to compare bytes), never written.
    """
    master = builder.PROJECT_ROOT / "data" / "master" / "eco_nojin_master.duckdb"
    if not master.is_file():  # pragma: no cover - master built by its own builder
        pytest.skip("data/master/eco_nojin_master.duckdb is not built on this machine")
    before = master.read_bytes()
    with pytest.raises(builder.BuildError) as excinfo:
        builder.build_food_security(
            master, transport=builder.FixtureTransport.from_file(FIXTURE_PATH)
        )
    message = str(excinfo.value)
    assert "eco_nojin_master.duckdb" in message
    assert "build_master_duckdb" in message
    assert master.read_bytes() == before


def test_refuses_an_existing_file_named_like_the_master(tmp_path, monkeypatch):
    """The guard follows the resolved path, and never touches the real file.

    ``PROJECT_ROOT`` is pointed at a temporary tree so the test cannot reach
    ``data/master/eco_nojin_master.duckdb`` in the repository.
    """
    repo_master = (
        Path(__file__).resolve().parents[2] / "data" / "master" / "eco_nojin_master.duckdb"
    )
    repo_bytes = repo_master.read_bytes() if repo_master.is_file() else None

    fake_root = tmp_path / "project"
    (fake_root / "data" / "master").mkdir(parents=True)
    target = fake_root / "data" / "master" / "eco_nojin_master.duckdb"
    target.write_bytes(b"")
    monkeypatch.setattr(builder, "PROJECT_ROOT", fake_root)

    with pytest.raises(builder.BuildError) as excinfo:
        builder.build_food_security(
            target, transport=builder.FixtureTransport.from_file(FIXTURE_PATH)
        )
    assert "eco_nojin_master.duckdb" in str(excinfo.value)
    assert target.read_bytes() == b""
    if repo_bytes is None:
        assert not repo_master.exists()
    else:
        assert repo_master.read_bytes() == repo_bytes


def test_a_failed_fetch_leaves_an_existing_store_intact(tmp_path):
    db_path = tmp_path / "food_security.duckdb"
    report = builder.build_food_security(
        db_path, transport=builder.FixtureTransport.from_file(FIXTURE_PATH)
    )
    assert db_path.is_file()
    before = db_path.read_bytes()

    with pytest.raises(builder.SourceUnavailable):
        builder.build_food_security(db_path, transport=_Unreachable())
    # The previous good store is untouched: the build wrote nothing.
    assert db_path.read_bytes() == before
    assert report["tables"]["food_security_indicators"] > 0


# ── unit-level behaviours ────────────────────────────────────────────


def test_faostat_reference_year_columns():
    assert builder._faostat_reference_year("Y2024", "u") == 2024
    assert builder._faostat_reference_year("Y20232025", "u") == 2025
    assert builder._faostat_reference_year("Y20002002", "u") == 2002
    assert builder._faostat_reference_year("Y2000F", "u") is None
    assert builder._faostat_reference_year("Y2000N", "u") is None
    assert builder._faostat_reference_year("Area", "u") is None
    with pytest.raises(builder.MalformedResponse):
        builder._faostat_reference_year("Y", "https://example.invalid")
    with pytest.raises(builder.MalformedResponse):
        builder._faostat_reference_year("Y20X0", "https://example.invalid")


def test_world_bank_year_parser_rejects_non_annual_values():
    assert builder._parse_year("2024", "u") == 2024
    for bad in ("2024Q1", "24", "YR2024", ""):
        with pytest.raises(builder.MalformedResponse):
            builder._parse_year(bad, "u")


def test_world_bank_request_url_matches_the_live_endpoint():
    url = builder._world_bank_request_url("AG.YLD.CREL.KG", list(builder.COUNTRIES))
    assert url == (
        "https://api.worldbank.org/v2/country/IRN;TUR;EGY;PAK;CHN;USA"
        "/indicator/AG.YLD.CREL.KG?format=json&per_page=5000"
    )


def test_indicator_and_country_mappings_are_documented():
    assert len(builder.WORLD_BANK_INDICATORS) == 7
    assert len(builder.FAOSTAT_ITEMS) == 16
    assert len(builder.COUNTRIES) == 6
    for code, (name, unit) in builder.WORLD_BANK_INDICATORS.items():
        assert code == code.strip().upper() or "." in code
        assert name and unit
    for code, (name, unit) in builder.FAOSTAT_ITEMS.items():
        assert code.isdigit()
        assert name and unit
    for iso3, name in builder.COUNTRIES.items():
        assert len(iso3) == 3
        # Persian names: at least one character outside ASCII.
        assert any(ord(char) > 127 for char in name)


def test_faostat_areas_map_onto_the_configured_countries():
    assert set(builder.FAOSTAT_AREAS.values()) == set(builder.COUNTRIES)


def test_recorded_fixture_is_labelled_as_a_recorded_copy(fixture_document):
    assert fixture_document["fixture_version"] == 1
    assert fixture_document["responses"]
    for record in fixture_document["responses"]:
        assert record["retrieved_at"]
        assert record["url"].startswith("https://")
        assert ("payload" in record) ^ ("content_b64" in record)
