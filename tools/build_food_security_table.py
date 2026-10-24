#!/usr/bin/env python3
"""Build ``data/food_security.duckdb`` from free World Bank / FAO data.

Why this script exists
----------------------
``services/data_manual/loader.py`` has always exposed a
``food_security()`` accessor, and the SQLite reference dataset it reads was
never built — so the accessor was code without data. This builder creates
the missing store from two *free, key-less* sources that were verified live
on 2026-10-10:

    World Bank API v2 (no token)
        https://api.worldbank.org/v2/country/{ISO3s}/indicator/{code}?format=json
        Indicators: AG.YLD.CREL.KG (cereal yield, kg/ha), AG.PRD.CREL.MT
        (cereal production, tonnes), SP.POP.TOTL (population),
        NV.AGR.TOTL.ZS (agriculture value added, % of GDP),
        AG.LND.ARBL.HA (arable land, ha), SN.ITK.DEFC.ZS (undernourishment,
        %) and TM.VAL.FOOD.ZS.UN (food imports, % of merchandise imports).
        Licence: CC BY 4.0 (verified live at
        https://data.worldbank.org/summary-terms-of-use).

    FAO FAOSTAT bulk download — Food Security domain (no key, no login)
        https://fenixservices.fao.org/faostat/static/bulkdownloads/Food_Security_Data_E_All_Data.zip
        18 843 rows of SDG 2 food-security indicators (prevalence of
        undernourishment, FIES prevalence of moderate/severe food
        insecurity, dietary energy supply adequacy, cereal import
        dependency ratio, arable land equipped for irrigation, ...).
        Licence: CC BY 4.0 per the FAO statistical databases terms of use
        (https://www.fao.org/contact-us/terms/db-terms-of-use/en/).

    Deliberately *not* used
        - FAOSTAT REST API (https://faostatservices.fao.org/api/v1/en/...):
          returns HTTP 401 "Missing Authorization Header", i.e. the public
          API now needs a token (verified live 2026-10-10).
        - The bulks-faostat.fao.org origin of the same ZIP: returns HTTP 403
          for anonymous clients (verified live); the fenixservices.fao.org
          origin serves the identical file anonymously.
        - The FAO Food Price Index CSV endpoints probed
          (https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/
          food_price_index_data_monthly.csv and
          https://www.fao.org/worldfoodsituation/foodpricesindex/api/en/):
          both returned HTTP 404 (verified live 2026-10-10). The index is
          also a global monthly series, not a country indicator, so it does
          not belong in a per-country indicator table anyway.

Storage location — why a separate DuckDB file
---------------------------------------------
Output defaults to ``data/food_security.duckdb``. It is **not** written into
``data/master/eco_nojin_master.duckdb`` on purpose:
``tools/build_master_duckdb.py`` unconditionally deletes and rebuilds that
file on every run, so any table added there would be silently destroyed by
the next master build (and this builder would in turn have to unlink a file
that belongs to another build). A separate file that only this script
writes cannot destroy the master's five tables, and the master build cannot
destroy this one. Both readers default to their own path; the
``FOOD_SECURITY_DB`` environment variable overrides it.

What goes in
------------
Two tables, both fully provenance-stamped (no unlabelled numbers):

    ``food_security_indicators``
        country_code, country_fa, indicator_code, indicator_fa, year, value,
        unit, source, source_url, retrieved_at
        ``source`` is ``world_bank``, ``faostat_food_security`` or
        ``derived``; every row carries the URL it came from and the UTC
        timestamp at which it was retrieved.

    ``food_security_sources``
        One row per source: publisher, URLs, licence, licence URL, retrieval
        timestamp, row count and — for the derived source — the formulas.

Derived indicators (formulas; see ``DERIVED_FORMULAS``)
-------------------------------------------------------
Raw indicators are copied verbatim. Three derived indicators are computed
from them and marked ``source='derived'``.  ``AG.PRD.CREL.MT`` is the World
Bank *metric tonnes* series, so every formula converts with
``1 tonne = 1 000 kg``:

1. ``derived:cereal_self_sufficiency_proxy``
       production_tonnes * 1000 / (yield_kg_per_ha * arable_ha)
   Assumption: the whole arable area produced cereals at the reported
   national mean yield. This measures internal consistency between the
   reported production, area and yield series; it is **not** the FAO
   self-sufficiency ratio production/(production+imports-exports), which
   needs trade data this builder does not fetch. FAO's official *cereal
   import dependency ratio* is stored as raw indicator ``FAO_FSC:21035``.

2. ``derived:per_capita_cereal_production_kg``
       production_tonnes * 1000 / population
   Domestic cereal production per inhabitant per year. It is not supply or
   consumption: feed, seed, food-processing, waste and all trade are
   excluded.

3. ``derived:cereal_import_dependency_proxy``
       100 * max(0, 1 - cereal_self_sufficiency_proxy)
   The share of domestic output that would have to be imported when the
   proxy is below one, clamped at zero for surplus years. It is a proxy for
   the import dependency, not FAO's ratio (``FAO_FSC:21035``).

Country set: IRN (primary), TUR, EGY, PAK, CHN, USA as comparators.

Sanity check on the 2026-10-10 live run (2024, Iran)
---------------------------------------------------
    AG.PRD.CREL.MT   24 511 344.7 t     (cereal production)
    AG.YLD.CREL.KG        2 724.8 kg/ha (cereal yield)
    AG.LND.ARBL.HA   15 699 000 ha     (arable land)
    SP.POP.TOTL          91 567 738     (population)
    -> self-sufficiency proxy          0.573
    -> per-capita cereal production   267.7 kg/person/year
    -> import-dependency proxy          42.7 %
    FAO_FSC:21035 (FAO cereal import dependency ratio, 2023) = 40.6 %
The proxy sits close to FAO's ratio for a deficit country like Iran and
stays far from it for net exporters (USA 2024: proxy 64 % vs FAO −20 %),
which is exactly why it is labelled a proxy and why FAO's own ratio is
stored alongside it as ``FAO_FSC:21035``.

Usage
-----
    python tools/build_food_security_table.py                     # fetch live
    python tools/build_food_security_table.py --fixtures <path>    # replay
    python tools/build_food_security_table.py --record-fixtures out.json
    python tools/build_food_security_table.py --json

The tests replay ``tools/tests/fixtures/live_exchange_2026-10-10.json``, a
recording of a live exchange (World Bank rows from 2015 on; FAOSTAT rows for
the 6 configured countries and curated item codes). Re-record it on a
machine with network access using ``--record-fixtures``.

Exit status is non-zero when a source is unreachable or malformed. No
number is written without a source URL and a retrieval timestamp, and a
fixture that does not cover a request is an error rather than a silent
fallback to invented values.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import logging
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger("build_food_security_table")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Default output. ``tools/build_master_duckdb.py`` keeps its own default at
#: ``data/master/eco_nojin_master.duckdb``; the two files never cross.
DEFAULT_OUTPUT: Path = PROJECT_ROOT / "data" / "food_security.duckdb"

#: World Bank API root (key-less).
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

#: FAOSTAT bulk download that serves the Food Security domain anonymously.
FAOSTAT_BULK_URL = (
    "https://fenixservices.fao.org/faostat/static/bulkdownloads/Food_Security_Data_E_All_Data.zip"
)

#: Environment variable that overrides the store location. Both
#: ``tools/build_food_security_table.py`` and ``engine/data_connector.py``
#: read the same name so a deployment can point both at one file.
FOOD_SECURITY_DB_ENV = "FOOD_SECURITY_DB"

WORLD_BANK_LICENCE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
WORLD_BANK_LICENCE_URL = "https://data.worldbank.org/summary-terms-of-use"
FAOSTAT_LICENCE = (
    "Creative Commons Attribution 4.0 International (CC BY 4.0), per the FAO "
    "statistical databases terms of use"
)
FAOSTAT_LICENCE_URL = "https://www.fao.org/contact-us/terms/db-terms-of-use/en/"

#: Country set: ISO3 code -> Persian country name. Persian names are stored
#: because that is the key ``services.data_manual.food_security(country_fa=)``
#: filters on.
COUNTRIES: dict[str, str] = {
    "IRN": "ایران",
    "TUR": "ترکیه",
    "EGY": "مصر",
    "PAK": "پاکستان",
    "CHN": "چین",
    "USA": "ایالات متحده آمریکا",
}

#: World Bank indicator code -> (Persian name, unit).
WORLD_BANK_INDICATORS: dict[str, tuple[str, str]] = {
    "AG.YLD.CREL.KG": ("بازده غلات", "کیلوگرم بر هکتار"),
    "AG.PRD.CREL.MT": ("تولید غلات", "تن"),
    "SP.POP.TOTL": ("جمعیت کل", "نفر"),
    "NV.AGR.TOTL.ZS": ("سهم کشاورزی از تولید ناخالص داخلی", "درصد"),
    "AG.LND.ARBL.HA": ("زمین‌های زراعتی", "هکتار"),
    "SN.ITK.DEFC.ZS": ("شیوع سوءتغذی (بانک جهانی)", "درصد"),
    "TM.VAL.FOOD.ZS.UN": ("سهم واردات مواد غذایی از واردات کالایی", "درصد"),
}

#: FAOSTAT Food Security domain item codes -> (Persian name, unit).
#: Units are normalised labels; the raw FAOSTAT unit strings are documented
#: in ``food_security_sources.notes`` for the faostat source.
FAOSTAT_ITEMS: dict[str, tuple[str, str]] = {
    "210041": ("شیوع سوءتغذی (FAO)", "درصد"),
    "210040": ("شیوع سوءتغذی (مقدار سالانه)", "درصد"),
    "210091": ("شیوع ناامنی غذایی متوسط تا شدید در کل جمعیت", "درصد"),
    "210090": ("شیوع ناامنی غذایی متوسط تا شدید در کل جمعیت (سالانه)", "درصد"),
    "210401": ("شیوع ناامنی غذایی شدید در کل جمعیت", "درصد"),
    "210400": ("شیوع ناامنی غذایی شدید در کل جمعیت (سالانه)", "درصد"),
    "210081": ("تعداد افراد ناامن غذایی متوسط تا شدید", "میلیون نفر"),
    "210011": ("تعداد افراد سوءتغذیه", "میلیون نفر"),
    "21010": ("کفایت انرژی غذایی", "درصد"),
    "21012": ("سهم غلات و ریشه‌های نشایی از انرژی غذایی", "درصد"),
    "21013": ("تأمین پروتئین به ازای هر نفر", "گرم بر نفر در روز"),
    "21061": ("تأمین چربی به ازای هر نفر", "گرم بر نفر در روز"),
    "21031": ("تغییرپذیری تأمین غذایی به ازای هر نفر", "کیلوکالری بر نفر در روز"),
    "21035": ("نسبت وابستگی وارداتی غلات (گزارش رسمی FAO)", "درصد"),
    "21034": ("درصد زمین‌های زراعتی مجهز به آبیاری", "درصد"),
    "21059": ("میزان اتلاف کالری در خرده‌فروشی", "درصد"),
}

#: FAOSTAT area names mapped to ISO3 codes. ``China, mainland`` is used (not
#: the FAOSTAT ``China`` aggregate that also contains Hong Kong SAR, Macao
#: SAR and Taiwan Province of) so the FAOSTAT rows and the World Bank ``CHN``
#: rows describe the same territory.
FAOSTAT_AREAS: dict[str, str] = {
    "Iran (Islamic Republic of)": "IRN",
    "Türkiye": "TUR",
    "Turkey": "TUR",
    "Egypt": "EGY",
    "Pakistan": "PAK",
    "China, mainland": "CHN",
    "United States of America": "USA",
}

#: Raw FAOSTAT unit string -> normalised unit label used in the indicator
#: table, so a unit is never silently re-labelled.
FAOSTAT_UNIT_NORMALISATION: dict[str, str] = {
    "%": "درصد",
    "g/cap/d": "گرم بر نفر در روز",
    "kcal/cap/d": "کیلوکالری بر نفر در روز",
    "million No": "میلیون نفر",
}

#: ``AG.PRD.CREL.MT`` is **metric tonnes**, so one unit is 1 000 kg. This
#: matters: applying a x1e6 conversion here (the "production x 1e6" shorthand
#: that reads as if the series were kilotonnes) inflates every derived cereal
#: number by a factor of 1000. A self-sufficiency proxy of 557 — the wrong
#: result x1e6 produces — is the tell that the conversion is off.
TONNES_TO_KG = 1000.0

SOURCE_WORLD_BANK = "world_bank"
SOURCE_FAOSTAT = "faostat_food_security"
SOURCE_DERIVED = "derived"

#: Source id used for the three derived indicators below.
DERIVED_FORMULAS: dict[str, str] = {
    "derived:cereal_self_sufficiency_proxy": (
        "AG.PRD.CREL.MT * 1000 / (AG.YLD.CREL.KG * AG.LND.ARBL.HA); "
        "production_tonnes * 1000 kg / (cereal_yield_kg_per_ha * arable_land_ha). "
        "AG.PRD.CREL.MT is metric tonnes, so 1 tonne = 1000 kg (a x1e6 "
        "conversion overstates this by 1000x). A proxy: it measures the "
        "consistency of the reported production, area and yield series, not "
        "the FAO self-sufficiency ratio, which needs trade data"
    ),
    "derived:per_capita_cereal_production_kg": (
        "AG.PRD.CREL.MT * 1000 / SP.POP.TOTL; domestic cereal production in kg "
        "per inhabitant per year, not consumption: feed, seed, processing "
        "losses and trade are excluded"
    ),
    "derived:cereal_import_dependency_proxy": (
        "100 * max(0, 1 - derived:cereal_self_sufficiency_proxy); the share of "
        "domestic cereal output (AG.PRD.CREL.MT) that would have to be imported "
        "below parity, clamped at zero for surplus years; a proxy, not FAO's "
        "cereal import dependency ratio (FAO_FSC:21035)"
    ),
}

WB_CEREAL_PRODUCTION = "AG.PRD.CREL.MT"
WB_CEREAL_YIELD = "AG.YLD.CREL.KG"
WB_ARABLE_LAND = "AG.LND.ARBL.HA"
WB_POPULATION = "SP.POP.TOTL"

SCHEMA_VERSION = "1"


class BuildError(RuntimeError):
    """A source is missing, unreachable or malformed; nothing is fabricated."""


class SourceUnavailable(BuildError):
    """A source returned a non-2xx status or could not be reached at all."""


class MalformedResponse(BuildError):
    """A response arrived but did not carry the documented shape."""


# ── rows ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IndicatorRow:
    """One indicator observation, exactly the table's ten columns."""

    country_code: str
    country_fa: str
    indicator_code: str
    indicator_fa: str
    year: int
    value: float
    unit: str
    source: str
    source_url: str
    retrieved_at: str

    def as_tuple(self) -> tuple:
        return (
            self.country_code,
            self.country_fa,
            self.indicator_code,
            self.indicator_fa,
            self.year,
            self.value,
            self.unit,
            self.source,
            self.source_url,
            self.retrieved_at,
        )


@dataclass(frozen=True)
class Fetched:
    """A single HTTP exchange, recorded so provenance can be replayed.

    ``retrieved_at`` is the UTC timestamp of the exchange itself.  For a
    network fetch that is the moment the response was read; for a replayed
    fixture it is the timestamp recorded when the response was captured, so a
    fixture build never claims a retrieval that did not happen.
    """

    url: str
    status_code: int
    retrieved_at: str
    payload: Any = None
    content: bytes | None = None


class Transport(Protocol):
    """Anything that can perform a recorded HTTP exchange.

    Implemented by :class:`NetworkTransport` (the live socket),
    :class:`FixtureTransport` (replay, used by the tests) and
    :class:`RecordingTransport` (network + journal).
    """

    def get_json(self, url: str) -> Fetched:
        """Fetch *url* and parse it as JSON."""
        ...

    def get_bytes(self, url: str) -> Fetched:
        """Fetch *url* and return its raw bytes."""
        ...


class NetworkTransport:
    """Network transport: the only path that really opens a socket."""

    def __init__(self, timeout: float = 60.0, max_retries: int = 3) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    def _get(self, url: str) -> Any:
        import requests

        last: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return requests.get(
                    url,
                    timeout=(10.0, self.timeout),
                    headers={"User-Agent": "hydroma-food-security-builder/1.0"},
                )
            except requests.RequestException as exc:  # retried below
                last = exc
                logger.warning(
                    "%s unreachable (attempt %d/%d): %s", url, attempt + 1, self.max_retries, exc
                )
        assert last is not None  # max_retries >= 1 always leaves a last error
        raise SourceUnavailable(f"{url} could not be reached: {type(last).__name__}: {last}")

    def get_json(self, url: str) -> Fetched:
        response = self._get(url)
        stamp = datetime.now(UTC).isoformat(timespec="seconds")
        if response.status_code != 200:
            raise SourceUnavailable(f"{url} returned HTTP {response.status_code}")
        try:
            return Fetched(url=url, status_code=200, retrieved_at=stamp, payload=response.json())
        except ValueError as exc:
            raise MalformedResponse(f"{url} did not return JSON: {exc}") from exc

    def get_bytes(self, url: str) -> Fetched:
        response = self._get(url)
        stamp = datetime.now(UTC).isoformat(timespec="seconds")
        if response.status_code != 200:
            raise SourceUnavailable(f"{url} returned HTTP {response.status_code}")
        return Fetched(url=url, status_code=200, retrieved_at=stamp, content=response.content)


@dataclass
class FetchResult:
    """Rows fetched from one source, plus the raw exchanges and provenance."""

    source_id: str
    rows: list[IndicatorRow]
    exchanges: list[Fetched]
    notes: str


class RecordingTransport:
    """Wraps another transport and keeps every exchange it made.

    Used by ``--record-fixtures`` so the recorded file contains exactly what
    the network returned — same URLs, same bytes, same timestamps.
    """

    def __init__(self, inner: Transport) -> None:
        self.inner = inner
        self.exchanges: list[Fetched] = []

    def get_json(self, url: str) -> Fetched:
        fetched = self.inner.get_json(url)
        self.exchanges.append(fetched)
        return fetched

    def get_bytes(self, url: str) -> Fetched:
        fetched = self.inner.get_bytes(url)
        self.exchanges.append(fetched)
        return fetched


class FixtureTransport:
    """Replays recorded responses; never opens a socket.

    A URL that the fixture does not cover raises :class:`SourceUnavailable`
    rather than falling back to invented values — an incomplete fixture is a
    build failure, exactly like an unreachable source.
    """

    def __init__(self, responses: dict[str, Fetched]) -> None:
        self.responses = responses

    @classmethod
    def from_file(cls, path: Path) -> FixtureTransport:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        version = document.get("fixture_version")
        if version != 1:
            raise BuildError(f"{path}: unsupported fixture_version {version!r}")
        responses: dict[str, Fetched] = {}
        for record in document.get("responses", []):
            url = record.get("url")
            if not url:
                raise BuildError(f"{path}: a recorded response has no url")
            payload = record.get("payload")
            content = base64.b64decode(record["content_b64"]) if record.get("content_b64") else None
            responses[url] = Fetched(
                url=url,
                status_code=int(record.get("status", 200)),
                retrieved_at=str(record.get("retrieved_at")),
                payload=payload,
                content=content,
            )
        if not responses:
            raise BuildError(f"{path}: no recorded responses")
        return cls(responses)

    def _lookup(self, url: str) -> Fetched:
        fetched = self.responses.get(url)
        if fetched is None:
            raise SourceUnavailable(
                f"{url} is not covered by the fixture; refusing to invent a value for it"
            )
        return fetched

    def get_json(self, url: str) -> Fetched:
        return self._lookup(url)

    def get_bytes(self, url: str) -> Fetched:
        return self._lookup(url)


# ── World Bank ───────────────────────────────────────────────────────


def _world_bank_request_url(indicator_code: str, countries: list[str]) -> str:
    """The exact URL requested for one indicator across the whole country set.

    The API accepts a semicolon-separated country list, so one request covers
    all six countries (verified live: ``total`` 396 rows for 6 countries).
    """
    joined = ";".join(countries)
    return (
        f"{WORLD_BANK_BASE_URL}/country/{joined}/indicator/{indicator_code}"
        f"?format=json&per_page=5000"
    )


def fetch_world_bank(
    transport: Transport,
    countries: dict[str, str] | None = None,
    indicators: dict[str, tuple[str, str]] | None = None,
) -> FetchResult:
    """Fetch the World Bank indicator series for the configured countries.

    Rows whose ``value`` is null are dropped (present-but-unknown), as are
    rows for aggregates the API may return alongside the requested countries.
    """
    countries = countries or COUNTRIES
    indicators = indicators or WORLD_BANK_INDICATORS
    codes = list(countries)
    rows: list[IndicatorRow] = []
    exchanges: list[Fetched] = []

    for indicator_code, (indicator_fa, unit) in indicators.items():
        url = _world_bank_request_url(indicator_code, codes)
        fetched = transport.get_json(url)
        exchanges.append(fetched)
        payload = fetched.payload
        if not isinstance(payload, list) or len(payload) != 2:
            raise MalformedResponse(
                f"{url}: expected [metadata, rows], got {type(payload).__name__}"
            )
        metadata, observations = payload
        if not isinstance(metadata, dict) or not isinstance(observations, list):
            raise MalformedResponse(f"{url}: metadata is not an object or rows are not a list")
        total = metadata.get("total")
        pages = metadata.get("pages")
        if isinstance(total, int) and len(observations) < total:
            raise MalformedResponse(
                f"{url}: {pages} page(s) returned {len(observations)} of {total} rows; "
                "raise per_page instead of paging silently"
            )
        for observation in observations:
            if not isinstance(observation, dict):
                raise MalformedResponse(f"{url}: a row is not an object")
            iso3 = observation.get("countryiso3code")
            if not iso3 or iso3 not in countries:
                continue
            date = observation.get("date")
            value = observation.get("value")
            if value is None:
                continue
            year = _parse_year(date, url)
            rows.append(
                IndicatorRow(
                    country_code=iso3,
                    country_fa=countries[iso3],
                    indicator_code=indicator_code,
                    indicator_fa=indicator_fa,
                    year=year,
                    value=float(value),
                    unit=unit,
                    source=SOURCE_WORLD_BANK,
                    source_url=url,
                    retrieved_at=fetched.retrieved_at,
                )
            )

    rows.sort(key=lambda row: (row.country_code, row.indicator_code, row.year))
    return FetchResult(
        source_id=SOURCE_WORLD_BANK,
        rows=rows,
        exchanges=exchanges,
        notes=(
            "World Bank API v2, key-less. Values copied verbatim; rows with a "
            "null value are dropped and aggregates are ignored. The API returns "
            "an empty unit field, so units come from this builder's documented "
            "indicator mapping. 7 indicators x 6 countries in one request each."
        ),
    )


def _parse_year(raw: Any, url: str) -> int:
    if raw is None:
        raise MalformedResponse(f"{url}: a row has no date")
    text = str(raw).strip()
    if len(text) != 4 or not text.isdigit():
        raise MalformedResponse(f"{url}: unsupported date {text!r}; annual years only")
    return int(text)


# ── FAOSTAT ──────────────────────────────────────────────────────────


def _select_member(names: list[str]) -> str:
    """Pick the flagged (non-NOFLAG) bulk CSV out of the ZIP members."""
    candidates = sorted(
        (name for name in names if name.endswith("_All_Data.csv") and "NOFLAG" not in name),
        key=len,
    )
    if not candidates:
        raise MalformedResponse(
            "FAOSTAT bulk ZIP has no '*_All_Data.csv' member; members: " + ", ".join(names)
        )
    return candidates[0]


def _faostat_reference_year(column: str, url: str) -> int | None:
    """Map a wide-format year column to its reference year.

    ``Y2024`` is the annual value for 2024; ``Y20232025`` is the 3-year
    average ending in 2025, whose reference year is recorded as 2025.
    """
    if not column.startswith("Y"):
        return None
    digits = column[1:]
    if not digits.isdigit():
        # FAOSTAT mirrors every year column with an 'F' (flag) and an 'N'
        # (note) column; those are not values and are skipped.
        if len(digits) in (5, 9) and digits[-1] in "FN" and digits[:-1].isdigit():
            return None
        raise MalformedResponse(f"{url}: unsupported FAOSTAT year column {column!r}")
    if len(digits) == 4:
        return int(digits)
    if len(digits) == 8:
        return int(digits[4:])
    raise MalformedResponse(f"{url}: unsupported FAOSTAT year column {column!r}")


def fetch_faostat(
    transport: Transport,
    countries: dict[str, str] | None = None,
    areas: dict[str, str] | None = None,
    items: dict[str, tuple[str, str]] | None = None,
) -> FetchResult:
    """Fetch the FAOSTAT Food Security domain from the bulk ZIP.

    The ZIP is parsed in memory: the ``_All_Data.csv`` member is read row by
    row, filtered to the configured areas and item codes, and only the
    ``Value`` element is imported (confidence intervals and non-value
    elements are left in the source file, not invented here).
    """
    areas = areas or FAOSTAT_AREAS
    items = items or FAOSTAT_ITEMS
    country_names = countries or COUNTRIES
    fetched = transport.get_bytes(FAOSTAT_BULK_URL)
    if not fetched.content:
        raise MalformedResponse(f"{FAOSTAT_BULK_URL}: empty response body")
    if fetched.content[:2] != b"PK":
        raise MalformedResponse(f"{FAOSTAT_BULK_URL}: response is not a ZIP archive")

    try:
        with zipfile.ZipFile(io.BytesIO(fetched.content)) as archive:
            member = _select_member(archive.namelist())
            text = archive.read(member).decode("utf-8-sig")
    except (zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise MalformedResponse(f"{FAOSTAT_BULK_URL}: unreadable bulk ZIP: {exc}") from exc

    rows: list[IndicatorRow] = []
    seen_elements: set[str] = set()
    censored_markers: set[str] = set()
    censored_cells = 0
    reader = csv.DictReader(io.StringIO(text))
    for record in reader:
        item_code = (record.get("Item Code") or "").strip()
        if item_code not in items:
            continue
        area = (record.get("Area") or "").strip()
        iso3 = areas.get(area)
        if iso3 is None:
            continue
        element = (record.get("Element") or "").strip()
        if element != "Value":
            seen_elements.add(element)
            continue
        indicator_fa, unit = items[item_code]
        raw_unit = (record.get("Unit") or "").strip()
        normalised_unit = FAOSTAT_UNIT_NORMALISATION.get(raw_unit)
        if normalised_unit is None or normalised_unit != unit:
            raise MalformedResponse(
                f"{FAOSTAT_BULK_URL}: item {item_code} uses FAOSTAT unit "
                f"{raw_unit!r}, which is not the documented {unit!r}"
            )
        for column, cell in record.items():
            if not column:
                continue
            year = _faostat_reference_year(column, FAOSTAT_BULK_URL)
            if year is None or cell is None or not cell.strip():
                continue
            try:
                value = float(cell.strip())
            except ValueError:
                # FAOSTAT reports very low prevalences as a censored bound
                # ('<2.5'). The table has no column for a bound, so the cell
                # is recorded as absent rather than parsed as if it were the
                # number itself.
                censored_cells += 1
                censored_markers.add(cell.strip())
                continue
            rows.append(
                IndicatorRow(
                    country_code=iso3,
                    country_fa=country_names[iso3],
                    indicator_code=f"FAO_FSC:{item_code}",
                    indicator_fa=indicator_fa,
                    year=year,
                    value=value,
                    unit=unit,
                    source=SOURCE_FAOSTAT,
                    source_url=FAOSTAT_BULK_URL,
                    retrieved_at=fetched.retrieved_at,
                )
            )

    rows.sort(key=lambda row: (row.country_code, row.indicator_code, row.year))
    if not rows:
        raise MalformedResponse(
            f"{FAOSTAT_BULK_URL}: no rows matched the configured items/areas"
        )
    if seen_elements:
        logger.info(
            "FAOSTAT elements not imported (only 'Value' is): %s",
            ", ".join(sorted(seen_elements)),
        )
    if censored_cells:
        logger.info(
            "dropped %d FAOSTAT cell(s) carrying inequality markers %s",
            censored_cells,
            ", ".join(sorted(censored_markers)),
        )
    censored_note = ""
    if censored_cells:
        censored_note = (
            f" {censored_cells} cell(s) carrying an FAO inequality marker "
            f"({', '.join(sorted(censored_markers))}) were dropped rather than "
            "parsed: the table has no column for a censored bound, so those "
            "observations are absent instead of being stored as if they were "
            "the bound itself."
        )
    return FetchResult(
        source_id=SOURCE_FAOSTAT,
        rows=rows,
        exchanges=[fetched],
        notes=(
            "FAO FAOSTAT Food Security domain, bulk ZIP (18 843 rows in the "
            "verified live file: SDG 2 indicators, 2000-2025). Rows filtered to "
            "the 6 configured countries and 16 curated item codes; only the "
            "'Value' element is imported (confidence intervals and modelled "
            "sub-groups stay in the source). 3-year-average columns are stored "
            "under their reference (final) year. Units are normalised labels "
            "from the raw FAOSTAT strings: % -> درصد, g/cap/d -> گرم بر نفر در "
            "روز, kcal/cap/d -> کیلوکالری بر نفر در روز, million No -> میلیون نفر."
            + censored_note
        ),
    )


# ── derived indicators ───────────────────────────────────────────────


def derive_indicators(
    rows: list[IndicatorRow],
    built_at: str,
    countries: dict[str, str] | None = None,
) -> list[IndicatorRow]:
    """Compute the derived indicators from the raw World Bank rows.

    A derived row is written only when every input it needs is present for
    the same country and year; a missing input yields no row rather than a
    filled-in value.
    """
    countries = countries or COUNTRIES
    values: dict[tuple[str, str, int], float] = {}
    urls: dict[tuple[str, str, int], str] = {}
    for row in rows:
        key = (row.country_code, row.indicator_code, row.year)
        values[key] = row.value
        urls.setdefault(key, row.source_url)

    derived: list[IndicatorRow] = []
    years = sorted({row.year for row in rows if row.source == SOURCE_WORLD_BANK})
    inputs = {
        country_code: {
            year: {
                WB_CEREAL_PRODUCTION: values.get((country_code, WB_CEREAL_PRODUCTION, year)),
                WB_CEREAL_YIELD: values.get((country_code, WB_CEREAL_YIELD, year)),
                WB_ARABLE_LAND: values.get((country_code, WB_ARABLE_LAND, year)),
                WB_POPULATION: values.get((country_code, WB_POPULATION, year)),
            }
            for year in years
        }
        for country_code in countries
    }

    for country_code, per_year in inputs.items():
        for year, series in per_year.items():
            production = series[WB_CEREAL_PRODUCTION]
            yield_kg = series[WB_CEREAL_YIELD]
            arable = series[WB_ARABLE_LAND]
            population = series[WB_POPULATION]
            if production is None or yield_kg is None or arable is None or population is None:
                continue
            if yield_kg * arable <= 0 or population <= 0:
                continue
            self_sufficiency = production * TONNES_TO_KG / (yield_kg * arable)
            per_capita = production * TONNES_TO_KG / population
            import_dependency = 100.0 * max(0.0, 1.0 - self_sufficiency)
            for code, name, value, unit in (
                (
                    "derived:cereal_self_sufficiency_proxy",
                    "نسبت خودکفایی غلات (تقریبی)",
                    self_sufficiency,
                    "نسبت",
                ),
                (
                    "derived:per_capita_cereal_production_kg",
                    "تولید غلات به ازای هر نفر",
                    per_capita,
                    "کیلوگرم به ازای هر نفر در سال",
                ),
                (
                    "derived:cereal_import_dependency_proxy",
                    "وابستگی وارداتی غلات (تقریبی)",
                    import_dependency,
                    "درصد",
                ),
            ):
                derived.append(
                    IndicatorRow(
                        country_code=country_code,
                        country_fa=countries[country_code],
                        indicator_code=code,
                        indicator_fa=name,
                        year=year,
                        value=value,
                        unit=unit,
                        source=SOURCE_DERIVED,
                        source_url=_derived_source_url(urls, country_code, year),
                        retrieved_at=built_at,
                    )
                )
    derived.sort(key=lambda row: (row.country_code, row.indicator_code, row.year))
    return derived


def _derived_source_url(
    urls: dict[tuple[str, str, int], str],
    country_code: str,
    year: int,
) -> str:
    """The URLs of the input series a derived row was computed from.

    A derived row therefore names a real, reachable URL for every input
    instead of pointing at the code that computed it.
    """
    ordered: list[str] = []
    for code in (WB_CEREAL_PRODUCTION, WB_CEREAL_YIELD, WB_ARABLE_LAND, WB_POPULATION):
        url = urls.get((country_code, code, year))
        if url and url not in ordered:
            ordered.append(url)
    return ";".join(ordered)


# ── DuckDB output ────────────────────────────────────────────────────


INDICATOR_DDL = """
    CREATE TABLE food_security_indicators (
        country_code   VARCHAR NOT NULL,
        country_fa     VARCHAR NOT NULL,
        indicator_code VARCHAR NOT NULL,
        indicator_fa   VARCHAR NOT NULL,
        year           INTEGER NOT NULL,
        value          DOUBLE NOT NULL,
        unit           VARCHAR NOT NULL,
        source         VARCHAR NOT NULL,
        source_url     VARCHAR NOT NULL,
        retrieved_at   VARCHAR NOT NULL,
        PRIMARY KEY (country_code, indicator_code, year)
    )
"""

SOURCES_DDL = """
    CREATE TABLE food_security_sources (
        source_id     VARCHAR PRIMARY KEY,
        source_name   VARCHAR NOT NULL,
        publisher     VARCHAR NOT NULL,
        base_url      VARCHAR NOT NULL,
        request_url   VARCHAR NOT NULL,
        licence       VARCHAR NOT NULL,
        licence_url   VARCHAR NOT NULL,
        retrieved_at  VARCHAR NOT NULL,
        row_count     BIGINT NOT NULL,
        formula       VARCHAR,
        notes         VARCHAR NOT NULL
    )
"""

INDICATOR_COLUMNS = (
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
)


def _source_rows(fetches: list[FetchResult], retrieved_at: str) -> list[tuple]:
    """One provenance row per source, including the derived formulas."""
    by_id = {fetch.source_id: fetch for fetch in fetches}
    world_bank = by_id[SOURCE_WORLD_BANK]
    faostat = by_id[SOURCE_FAOSTAT]
    derived = by_id[SOURCE_DERIVED]
    world_bank_request_template = (
        f"{WORLD_BANK_BASE_URL}/country/{';'.join(COUNTRIES)}"
        f"/indicator/{{indicator}}?format=json&per_page=5000"
    )
    return [
        (
            SOURCE_WORLD_BANK,
            "World Bank World Development Indicators",
            "The World Bank",
            WORLD_BANK_BASE_URL,
            world_bank_request_template,
            WORLD_BANK_LICENCE,
            WORLD_BANK_LICENCE_URL,
            min(exchange.retrieved_at for exchange in world_bank.exchanges),
            len(world_bank.rows),
            None,
            world_bank.notes,
        ),
        (
            SOURCE_FAOSTAT,
            "FAOSTAT Food Security domain",
            "Food and Agriculture Organization of the United Nations",
            FAOSTAT_BULK_URL,
            FAOSTAT_BULK_URL,
            FAOSTAT_LICENCE,
            FAOSTAT_LICENCE_URL,
            min(exchange.retrieved_at for exchange in faostat.exchanges),
            len(faostat.rows),
            None,
            faostat.notes,
        ),
        (
            SOURCE_DERIVED,
            "Derived food-security indicators",
            "computed by tools/build_food_security_table.py from the two sources above",
            "",
            # Not an HTTP request: the derived rows are computed in this build
            # from the raw rows above, and each one names its input URLs.
            "no HTTP request; computed by tools/build_food_security_table.py "
            "from the world_bank and faostat_food_security rows above",
            "derived from CC BY 4.0 sources; cite the input sources",
            "",
            retrieved_at,
            len(derived.rows),
            json.dumps(DERIVED_FORMULAS, ensure_ascii=False),
            (
                "Formulas and their assumptions: "
                + " | ".join(f"{code}: {formula}" for code, formula in DERIVED_FORMULAS.items())
                + ". Each derived row records the input source URLs and this "
                "build's timestamp, not a retrieval timestamp of its own."
            ),
        ),
    ]


def build_food_security(
    db_path: Path,
    *,
    transport: Transport | None = None,
    retrieved_at: str | None = None,
    countries: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the food-security DuckDB at *db_path* and return a report.

    The store is written atomically (temporary file + ``os.replace``), so a
    failed fetch never replaces a previously built good store with a partial
    one.  ``data/master/eco_nojin_master.duckdb`` is refused as an output
    path: it belongs to ``tools/build_master_duckdb.py``, which deletes it on
    every run.

    Raises:
        SourceUnavailable: a source could not be reached or returned non-2xx.
        MalformedResponse: a response did not carry the documented shape.
        BuildError: the output path is refused or the build cannot finish.
    """
    countries = countries or COUNTRIES
    db_path = Path(db_path).expanduser()
    master_path = PROJECT_ROOT / "data" / "master" / "eco_nojin_master.duckdb"
    if db_path.resolve() == master_path.resolve():
        raise BuildError(
            "refusing to write the food-security tables into "
            "data/master/eco_nojin_master.duckdb: that file is owned by "
            "tools/build_master_duckdb.py, which deletes and rebuilds it on "
            "every run. Use data/food_security.duckdb (the default)."
        )
    transport = transport or NetworkTransport()
    built_at = retrieved_at or datetime.now(UTC).isoformat(timespec="seconds")

    world_bank = fetch_world_bank(transport, countries)
    faostat = fetch_faostat(transport)
    derived = derive_indicators(world_bank.rows, built_at, countries)
    derived_fetch = FetchResult(SOURCE_DERIVED, derived, [], "")

    fetches = [world_bank, faostat, derived_fetch]
    all_rows: list[IndicatorRow] = [row for fetch in fetches for row in fetch.rows]
    if not all_rows:
        raise BuildError("no rows were fetched; refusing to write an empty store")
    _check_unique(all_rows)
    _check_provenance(all_rows)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_name(db_path.name + ".partial")
    if tmp_path.exists():
        tmp_path.unlink()

    import duckdb

    conn = duckdb.connect(str(tmp_path))
    try:
        conn.execute("BEGIN TRANSACTION")
        conn.execute(INDICATOR_DDL)
        conn.executemany(
            "INSERT INTO food_security_indicators VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [row.as_tuple() for row in all_rows],
        )
        conn.execute(SOURCES_DDL)
        conn.executemany(
            "INSERT INTO food_security_sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            _source_rows(fetches, built_at),
        )
        conn.execute("COMMIT")

        counts: dict[str, int] = {}
        for table in ("food_security_indicators", "food_security_sources"):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            assert row is not None  # COUNT(*) always returns exactly one row
            counts[table] = int(row[0])
        by_source = {
            str(source): count
            for source, count in conn.execute(
                "SELECT source, COUNT(*) FROM food_security_indicators"
                " GROUP BY source ORDER BY source"
            ).fetchall()
        }
        columns = [item[0] for item in conn.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_name = 'food_security_indicators' ORDER BY ordinal_position"
        ).fetchall()]
    finally:
        conn.close()

    os.replace(tmp_path, db_path)

    return {
        "duckdb_path": str(db_path),
        "schema_version": SCHEMA_VERSION,
        "built_at": built_at,
        "mode": "fixture" if isinstance(transport, FixtureTransport) else "network",
        "sources": {
            SOURCE_WORLD_BANK: world_bank.exchanges[0].url,
            SOURCE_FAOSTAT: FAOSTAT_BULK_URL,
        },
        "rows_by_source": by_source,
        "tables": counts,
        "indicator_columns": columns,
        "countries": countries,
        "sha256": hashlib.sha256(db_path.read_bytes()).hexdigest(),
    }


def _check_unique(rows: list[IndicatorRow]) -> None:
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        key = (row.country_code, row.indicator_code, row.year)
        if key in seen:
            raise BuildError(
                f"duplicate key {key} from source {row.source!r}; "
                "two sources would have to be merged, not stacked"
            )
        seen.add(key)


def _check_provenance(rows: list[IndicatorRow]) -> None:
    """Every row carries a source, a URL and a retrieval timestamp."""
    for row in rows:
        if not row.source or not row.source_url or not row.retrieved_at:
            raise BuildError(
                f"provenance missing for {row.country_code}/{row.indicator_code}"
                f"/{row.year}: source={row.source!r} url={row.source_url!r} "
                f"retrieved_at={row.retrieved_at!r}"
            )
        if row.source != SOURCE_DERIVED and not row.source_url.startswith("https://"):
            raise BuildError(f"source_url is not an https URL: {row.source_url!r}")


# ── reporting / CLI ──────────────────────────────────────────────────


def print_report(report: dict[str, Any]) -> None:
    print("food_security.duckdb build report")
    print("=" * 60)
    print(f"database:       {report['duckdb_path']}")
    print(f"schema version: {report['schema_version']}")
    print(f"built at:       {report['built_at']}")
    print(f"mode:           {report['mode']}")
    print()
    for table, rows in report["tables"].items():
        print(f"{table:<26}{rows:>7} rows")
    print()
    print("rows by source")
    print("-" * 60)
    for source, count in report["rows_by_source"].items():
        print(f"{source:<26}{count:>7}")
    print()
    print("fetched from")
    print("-" * 60)
    for source, url in report["sources"].items():
        print(f"{source:<26}{url}")


def record_fixture(path: Path, exchanges: list[Fetched]) -> None:
    """Write the raw exchanges of a network run to a replayable fixture."""
    document = {
        "fixture_version": 1,
        "kind": "food_security_fetch_fixture",
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "note": (
            "Recorded exchange-by-exchange from the live World Bank API v2 and "
            "the FAO FAOSTAT bulk download by tools/build_food_security_table.py "
            "--record-fixtures. Values are real, unmodified API responses; "
            "retrieved_at is the timestamp of the live exchange. Replay with "
            "--fixtures; a URL the fixture does not cover is a build error, not "
            "a fallback."
        ),
        "responses": [
            {
                "url": fetched.url,
                "status": fetched.status_code,
                "retrieved_at": fetched.retrieved_at,
                **(
                    {"content_b64": base64.b64encode(fetched.content).decode("ascii")}
                    if fetched.content is not None
                    else {"payload": fetched.payload}
                ),
            }
            for fetched in exchanges
        ],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build data/food_security.duckdb from the free World Bank API v2 "
            "and the FAO FAOSTAT bulk Food Security download, with full "
            "row-level provenance."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="replay recorded raw exchanges instead of fetching (offline builds and tests)",
    )
    parser.add_argument(
        "--record-fixtures",
        type=Path,
        default=None,
        help="record the raw exchanges of this network run to a fixture file",
    )
    parser.add_argument("--json", action="store_true", help="print the build report as JSON")
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="per-request timeout in seconds",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        recorder: RecordingTransport | None = None
        if args.fixtures is not None:
            if args.record_fixtures is not None:
                raise BuildError(
                    "--record-fixtures records a live exchange; it cannot be "
                    "combined with --fixtures (a replay performs no exchange)"
                )
            transport: Transport = FixtureTransport.from_file(args.fixtures)
        else:
            live = NetworkTransport(timeout=args.timeout)
            if args.record_fixtures is not None:
                recorder = RecordingTransport(live)
                transport = recorder
            else:
                transport = live
        report = build_food_security(args.output, transport=transport)
        if recorder is not None and args.record_fixtures is not None:
            record_fixture(args.record_fixtures, recorder.exchanges)
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
