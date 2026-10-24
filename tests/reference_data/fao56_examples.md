# FAO-56 Example 18 — independent reference data (AUTHORITATIVE row)

Source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998), *Crop
evapotranspiration — Guidelines for computing crop water requirements*, FAO
Irrigation and Drainage Paper 56, Chapter 4 "Determination of ET0", **Example 18
"Determination of ET0 with daily data"**, as published in the primary source at
<https://www.fao.org/4/X0490E/x0490e08.htm>.

Published inputs, read verbatim from `fao56_examples.csv`: **Uccle (Brussels,
Belgium), 6 July**; latitude 50°48'N = 50.80°N; elevation 100 m; Tmax 21.5 °C;
Tmin 12.3 °C (Tmean 16.9 °C); RHmax 84 %; RHmin 63 %; wind 10 km/h measured at
10 m converted per FAO eq. 47 to **u2 = 2.078 m/s**; bright sunshine hours
n = 9.25 with N = 16.1, from which FAO estimates **Rs = 22.07 MJ/m²/day** via
the Angström formula (eq. 35) and Rso = 30.90 MJ/m²/day (eq. 37). The day of
year for 6 July is **J = 187** (non-leap convention used by FAO in the example
itself). The published result is **ET0 = 3.88 → 3.9 mm/day** (eq. 6), with the
test tolerance **±0.05 mm/day**.

These numbers are published reference values, not engine output, and are
loaded by `engine/tests/test_fao56_example18.py` with the standard-library
`csv` module only.

## Resolution of the earlier discrepancy (2026-10-10, gap G-S6b closed)

The project specification (`docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md` §8.3)
described Example 18 as "Rome, Italy, 6 July, latitude 41.8°, Tmax 34.8 °C,
Tmin 24.6 °C, RHmax 52 %, RHmin 28 %, u2 = 2.0 m/s, Rs = 22.3 MJ/m²/day,
elevation 142 m, ET0 = 5.08 mm/day". Primary-source verification shows that
row is not FAO-56 Example 18: no such numbers appear anywhere in FAO Paper 56,
and evaluating the FAO-56 equations (eq. 21, 36–40, 6) on those inputs yields
6.70 mm/day — the value the engine also produces (6.7035) and that
independent reproductions confirm (NCAR `refevt_penman_fao56`,
R `MeTo`/`pyet`, Python `hydpy` all reproduce the authoritative Uccle example
to 3.87–3.9 mm/day). The engine was therefore FAO-56-correct and the
specification's reference row was invalid; the row here is now the
authoritative Uccle example, and the engine is validated against it
(measured 3.8801 mm/day, delta −0.0199 from the published 3.9).

The engine implementation under test is
`engine/hydroma/climate/et_calculator.py:256`, `calc_et0_penman_monteith`,
reached through a `ClimateData` dataclass instance built from this row.

## Example 20 — determination of ETo with missing data (second anchor, same page)

Same primary source (`fao.org/4/X0490E/x0490e08.htm`), **Example 20 "Determination
of ETo with missing data"**: a station **near Lyon, France**, monthly-average data
for July (day 15, J = 196), latitude 45°43'N = **45.72 °N**, elevation **200 m**,
Tmax **26.6 °C**, Tmin **14.8 °C**, with **no other recorded data**: u2 estimated
at 2 m/s (FAO's own instruction), humidity via Tdew ≈ Tmin → ea = 1.68 kPa
(equivalently RHmax = 100 %, RHmin = 48 %, which Example 20 itself derives), and
Rs estimated by eq. 50 as 0.16·√(26.6−14.8)·Ra = 0.55·Ra = **22.29 MJ/m²/day**
(Ra = 40.55). The published results are **ETo(PM) = 4.56 → 4.6 mm/day** and
**ETo(Hargreaves, eq. 52) = 5.0 mm/day**, plus the wind sensitivity (1 or 3 m/s →
4.2 / 4.8 mm/day).

This row is the second external anchor for `ENO_ET0_FAO56_001` and the FIRST
external anchor for the Hargreaves path (`engine/hydroma/climate/et_calculator.py:112-125`,
`ENO_HARGREAVES_ET0`); it is exercised by
`engine/tests/test_fao56_example20_missing_data.py` while Example 18 above is
exercised by `engine/tests/test_fao56_example18.py`.
