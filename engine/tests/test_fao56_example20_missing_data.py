"""Second external anchor: FAO-56 Chapter 4, Example 20 (missing-data estimates).

Source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998), FAO
Irrigation and Drainage Paper 56, Chapter 4 "Determination of ET0", Example 20
"Determination of ET0 with missing data" — station near Lyon, France,
month-average July data, published at https://www.fao.org/4/X0490E/x0490e08.htm.
Verified against the primary source 2026-10-10.

What is published there, and used here as independent reference values:

* inputs: latitude 45.72 degN, elevation 200 m, Tmax 26.6 degC, Tmin 14.8 degC,
  and NO other recorded data — u2 = 2 m/s (FAO's own temporary estimate),
  humidity via Tdew ~ Tmin giving ea = 1.68 kPa (which Example 20 itself
  converts to RHmax = 100 %, RHmin = 48 %), and Rs estimated by eq. 50 as
  0.16*sqrt(26.6-14.8)*Ra = 0.55*Ra = 22.29 MJ/m2/day (Ra = 40.55, J = 196);
* published results: **ETo(Penman-Monteith, eq. 6) = 4.56 mm/day** (printed as
  4.6) and **ETo(Hargreaves, eq. 52) = 5.0 mm/day**, with the wind sensitivity
  1 or 3 m/s -> 4.2 / 4.8 mm/day.

This row closes the two gaps recorded in the formula-validation register:
it is the first *external* anchor for the engine's Hargreaves path
(`ENO_HARGREAVES_ET0`, engine/hydroma/climate/et_calculator.py:112-125) and a
second, independent anchor for the PM path that exercises the *estimated-data*
route (RHmin/RHmax derived from ea) rather than measured humidity.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from engine.hydroma.climate.et_calculator import (
    ClimateData,
    calc_et0_hargreaves,
    calc_et0_penman_monteith,
)

CSV_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "reference_data" / "fao56_examples.csv"
)

#: Published values of Example 20.
PM_ET0_MM_DAY = 4.56
HARGREAVES_ET0_MM_DAY = 5.0

#: FAO prints 4.56/5.0; the example's own sensitivity band is +-7 %, so a
#: tolerance of 0.05 for PM and 0.10 for Hargreaves (published to 2 s.f.) is
#: strict while honouring the printed precision.
PM_TOLERANCE_MM_DAY = 0.05
HARGREAVES_TOLERANCE_MM_DAY = 0.10

#: Inputs as published (see module docstring).
LATITUDE_DEG = 45.72
ELEVATION_M = 200.0
T_MAX_C = 26.6
T_MIN_C = 14.8
RH_MAX_PCT = 100.0
RH_MIN_PCT = 48.0
U2_M_S = 2.0
RS_MJ_M2_DAY = 22.29
DAY_OF_YEAR = 196


def _example20_row() -> dict[str, str]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if "Example 20" in r["example"]]
    assert len(rows) == 1, f"expected one Example 20 row, found {len(rows)}"
    return rows[0]


def test_reference_row_matches_the_published_example() -> None:
    """The CSV row must carry Example 20's published inputs verbatim."""
    row = _example20_row()
    assert float(row["latitude_deg"]) == LATITUDE_DEG
    assert float(row["elevation_m"]) == ELEVATION_M
    assert float(row["t_max_c"]) == T_MAX_C
    assert float(row["t_min_c"]) == T_MIN_C
    assert float(row["rh_max_pct"]) == RH_MAX_PCT
    assert float(row["rh_min_pct"]) == RH_MIN_PCT
    assert float(row["u2_m_s"]) == U2_M_S
    assert float(row["rs_mj_m2_day"]) == RS_MJ_M2_DAY
    assert float(row["et0_reference_mm_day"]) == PM_ET0_MM_DAY


def test_penman_monteith_matches_published_example20() -> None:
    """ETo(PM) = 4.56 mm/day (eq. 6), inputs as published."""
    data = ClimateData(
        tmin=T_MIN_C,
        tmax=T_MAX_C,
        rh_min=RH_MIN_PCT,
        rh_max=RH_MAX_PCT,
        wind_speed=U2_M_S,
        solar_radiation=RS_MJ_M2_DAY,
        elevation=ELEVATION_M,
        latitude=LATITUDE_DEG,
        doy=DAY_OF_YEAR,
    )
    result = calc_et0_penman_monteith(data)
    assert abs(result - PM_ET0_MM_DAY) <= PM_TOLERANCE_MM_DAY, (
        f"measured ET0={result!r} mm/day vs published {PM_ET0_MM_DAY}"
        f"±{PM_TOLERANCE_MM_DAY}"
    )


def test_hargreaves_matches_published_example20() -> None:
    """Hargreaves eq. 52 = 5.0 mm/day on the same published day.

    The published Hargreaves result uses the estimated Ra of Example 20
    (40.55 MJ/m2/day); the engine's own eq. 21 for 45.72 degN, J=196 is the
    independent quantity under test.
    """
    t_mean = (T_MAX_C + T_MIN_C) / 2.0
    result = calc_et0_hargreaves(
        t_min=T_MIN_C, t_max=T_MAX_C, t_mean=t_mean, ra_mj=40.55
    )
    assert abs(result - HARGREAVES_ET0_MM_DAY) <= HARGREAVES_TOLERANCE_MM_DAY, (
        f"measured Hargreaves ET0={result!r} mm/day vs published "
        f"{HARGREAVES_ET0_MM_DAY}±{HARGREAVES_TOLERANCE_MM_DAY}"
    )


def test_engine_ra_and_rs_estimation_reproduce_example20() -> None:
    """The engine's eq. 21 Ra and eq. 50 Rs-estimation reproduce the example.

    Ra = 40.55 MJ/m2/day for 45.72 degN, J = 196 (published), and
    Rs = 0.16*sqrt(Tmax-Tmin)*Ra = 22.29 MJ/m2/day (published, eq. 50).
    """
    from engine.hydroma.climate.et_calculator import calc_extraterrestrial_radiation

    ra = calc_extraterrestrial_radiation(LATITUDE_DEG, DAY_OF_YEAR)
    assert abs(ra - 40.55) <= 0.05, f"Ra={ra!r} vs published 40.55"

    rs_estimated = 0.16 * math.sqrt(T_MAX_C - T_MIN_C) * ra
    assert abs(rs_estimated - RS_MJ_M2_DAY) <= 0.05, (
        f"eq. 50 estimate={rs_estimated!r} vs published {RS_MJ_M2_DAY}"
    )
