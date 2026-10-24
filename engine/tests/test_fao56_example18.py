"""Independent reference test for FAO-56 ET0 (spec §6.10 ECO-10, §8.3 ENO_ET0_FAO56_001).

Reference source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998),
FAO Irrigation and Drainage Paper 56, Chapter 4 "Determination of ET0", Example
18 "Determination of ET0 with daily data" — **Uccle (Brussels, Belgium), 6
July**, published at https://www.fao.org/4/X0490E/x0490e08.htm. Verified
2026-10-10 against the primary source (gap G-S6b closed): the "Rome / ET0 5.08"
row the project specification carried is not FAO-56 Example 18 and yields
6.70 mm/day under FAO's own equations — that row was invalid, the engine is
FAO-56-correct, and this file now tests the authoritative example.

Two independent checks are applied, neither of which can agree with the engine
by construction:

1. the published Uccle row, read with the stdlib ``csv`` module from
   ``tests/reference_data/fao56_examples.csv``, asserted against FAO's
   published ET0 = 3.9 mm/day within ±0.05 mm/day;
2. an independent first-principles re-implementation of FAO-56 eq. 6 written
   out in this test with the standard library, which the engine must match
   for BOTH the authoritative row and the specification's (invalid) historical
   row.

Engine under test: ``engine/hydroma/climate/et_calculator.py:256``,
``calc_et0_penman_monteith``, reached through the ``ClimateData`` dataclass of
the same module.
"""

from __future__ import annotations

import calendar
import csv
import math
from pathlib import Path
from typing import Any

from engine.hydroma.climate.et_calculator import ClimateData, calc_et0_penman_monteith

CSV_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "reference_data" / "fao56_examples.csv"
)

#: FAO-56 Example 18 (Uccle, 6 July) published result, eq. 6.
PUBLISHED_ET0_MM_DAY = 3.9
TOLERANCE_MM_DAY = 0.05
EXPECTED_DAY_OF_YEAR = 187  # 6 July, non-leap convention used by FAO Example 18

#: The project specification's *invalid* Example 18 row (retained as a
#: documented finding: no FAO-56 equation set produces 5.08 from it).
SPEC_DISPUTED_ROW = {
    "t_min_c": 24.6,
    "t_max_c": 34.8,
    "rh_min_pct": 28.0,
    "rh_max_pct": 52.0,
    "u2_m_s": 2.0,
    "rs_mj_m2_day": 22.3,
    "elevation_m": 142.0,
    "latitude_deg": 41.8,
}

_MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
_MONTH_LENGTHS_NON_LEAP = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _day_of_year(date_text: str) -> int:
    """Day of year for a 'D Month' date under FAO's non-leap convention."""
    day_text, month_text = date_text.split()
    month = _MONTHS[month_text.lower()]
    return int(day_text) + sum(_MONTH_LENGTHS_NON_LEAP[: month - 1])


def _load_reference_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _example18_row() -> dict[str, str]:
    rows = [
        r for r in _load_reference_rows() if "Example 18" in r.get("example", "")
    ]
    assert len(rows) == 1, f"expected one Example 18 row, found {len(rows)}"
    return rows[0]


def _build_climate_data(row: dict[str, Any]) -> ClimateData:
    return ClimateData(
        tmin=float(row["t_min_c"]),
        tmax=float(row["t_max_c"]),
        rh_min=float(row["rh_min_pct"]),
        rh_max=float(row["rh_max_pct"]),
        wind_speed=float(row["u2_m_s"]),
        solar_radiation=float(row["rs_mj_m2_day"]),
        elevation=float(row["elevation_m"]),
        latitude=float(row["latitude_deg"]),
        doy=EXPECTED_DAY_OF_YEAR,
    )


def _independent_fao56_et0(
    tmin: float,
    tmax: float,
    rh_min: float,
    rh_max: float,
    u2: float,
    rs: float,
    elevation: float,
    latitude_deg: float,
    doy: int,
) -> float:
    """FAO-56 eq. 6 written out with the standard library (independent of the engine).

    Equations, per FAO Irrigation and Drainage Paper 56 Chapter 4: es (eq. 11),
    ea (eq. 17), Delta (eq. 13), gamma (eq. 8), Ra (eq. 21), Rso (eq. 37),
    Rns (eq. 38), Rnl (eq. 40), Rn (eq. 40), ET0 (eq. 6 with G = 0 daily).
    Correction of record (2026-10-10, formula audit): this oracle originally
    used exponent 5.54 for atmospheric pressure where FAO eq. 7 (and the
    engine, `et_calculator.py:52`) use 5.26; the effect is 0.03 % (inside the
    test tolerance) but the oracle must match the cited standard exactly, so
    the exponent is now 5.26.
    """
    def es(t: float) -> float:
        return 0.6108 * math.exp(17.27 * t / (t + 237.3))

    es_tmax, es_tmin = es(tmax), es(tmin)
    es_mean = (es_tmax + es_tmin) / 2.0
    ea = (es_tmin * rh_max / 100.0 + es_tmax * rh_min / 100.0) / 2.0
    tmean = (tmax + tmin) / 2.0
    delta = 4098.0 * es(tmean) / (tmean + 237.3) ** 2

    pressure: float = 101.3 * ((293.0 - 0.0065 * elevation) / 293.0) ** 5.26
    gamma = 0.665e-3 * pressure

    lat = math.radians(latitude_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    declination = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    sunset = math.acos(-math.tan(lat) * math.tan(declination))
    ra = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
        sunset * math.sin(lat) * math.sin(declination)
        + math.cos(lat) * math.cos(declination) * math.sin(sunset)
    )
    rso = (0.75 + 2e-5 * elevation) * ra
    rns = 0.77 * rs
    cloudiness = 1.35 * rs / rso - 0.35
    sigma = 4.903e-9
    rnl = (
        sigma
        * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4)
        / 2.0
        * (0.34 - 0.14 * math.sqrt(ea))
        * cloudiness
    )
    rn = rns - rnl

    numerator = 0.408 * delta * rn + gamma * (900.0 / (tmean + 273.0)) * u2 * (es_mean - ea)
    denominator = delta + gamma * (1.0 + 0.34 * u2)
    return numerator / denominator


def test_reference_row_is_the_authoritative_example() -> None:
    """Guard against regression to the specification's invalid 'Rome / 5.08' row."""
    row = _example18_row()
    assert "Uccle" in row["location"]
    assert row["date"] == "6 July"
    assert float(row["et0_reference_mm_day"]) == PUBLISHED_ET0_MM_DAY
    assert _day_of_year(row["date"]) == EXPECTED_DAY_OF_YEAR


def test_fao56_example18_et0_matches_published_reference() -> None:
    """Allen et al. 1998, FAO Paper 56, Example 18 (Uccle/Brussels, 6 July).

    The expected value and every input are published values; the engine value
    must land within ±0.05 mm/day of FAO's published ET0 = 3.9 mm/day.
    """
    rows = _load_reference_rows()
    row = rows[0]
    for field in (
        "latitude_deg",
        "t_max_c",
        "t_min_c",
        "rh_max_pct",
        "rh_min_pct",
        "u2_m_s",
        "rs_mj_m2_day",
        "elevation_m",
    ):
        assert float(row[field]) > 0.0, field

    data = _build_climate_data(row)
    result = calc_et0_penman_monteith(data)

    assert abs(result - PUBLISHED_ET0_MM_DAY) <= TOLERANCE_MM_DAY, (
        f"measured ET0={result!r} mm/day vs published {PUBLISHED_ET0_MM_DAY}"
        f"±{TOLERANCE_MM_DAY}; deviation {result - PUBLISHED_ET0_MM_DAY:.4f} mm/day"
    )


def test_engine_matches_independent_first_principles_implementation() -> None:
    """The engine must equal an independently written FAO-56 eq. 6 evaluation.

    Applied to two rows: the authoritative Uccle example and the specification's
    historical (invalid) Rome row. The second case documents why 5.08 was never
    reachable: every faithful evaluation of those inputs gives ≈6.7 mm/day.
    """
    authoritative = _example18_row()
    cases: list[tuple[ClimateData, dict[str, Any]]] = [
        (_build_climate_data(authoritative), authoritative),
        (_build_climate_data(SPEC_DISPUTED_ROW), SPEC_DISPUTED_ROW),
    ]
    for data, row in cases:
        engine = calc_et0_penman_monteith(data)
        independent = _independent_fao56_et0(
            tmin=float(row["t_min_c"]),
            tmax=float(row["t_max_c"]),
            rh_min=float(row["rh_min_pct"]),
            rh_max=float(row["rh_max_pct"]),
            u2=float(row["u2_m_s"]),
            rs=float(row["rs_mj_m2_day"]),
            elevation=float(row["elevation_m"]),
            latitude_deg=float(row["latitude_deg"]),
            doy=EXPECTED_DAY_OF_YEAR,
        )
        assert abs(engine - independent) <= 0.05, (
            f"engine={engine!r} vs independent FAO-56 evaluation={independent!r} "
            f"for row {row.get('location', 'spec-disputed')}"
        )
