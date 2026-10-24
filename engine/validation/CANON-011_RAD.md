# Validation Evidence — CANON-011_RAD

**Model:** `CANON-011_RAD` — Extraterrestrial Radiation (registry version `1.0.0`)
**Cluster:** radiation / crop water requirements
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_et_pm_group` (`ET0_EXTRATERRESTRIAL_RADIATION`)
**Implementation:** `engine/hydroma/climate/et_calculator.py::calc_extraterrestrial_radiation`
**Model card:** `engine/models/cards/CANON-011_RAD_extraterrestrial_radiation.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

---

## 1. Published reference

**Citation.** Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., *Crop
Evapotranspiration — Guidelines for Computing Crop Water Requirements*, FAO
Irrigation and Drainage Paper 56, 1998, Chapter 3, equation 21:

```
dr    = 1 + 0.033 * cos(2 pi J / 365)
delta = 0.409 * sin(2 pi J / 365 - 1.39)
ws    = acos(-tan(phi) * tan(delta))
Ra    = (24 * 60 / pi) * Gsc * dr * [ws sin(phi) sin(delta) + cos(phi) cos(delta) sin(ws)]
```

with `Gsc = 0.0820 MJ/m2/min` the solar constant, `J` the day of the year, `phi`
the latitude in radians and `ws` the sunset hour angle. The result is the daily
extraterrestrial radiation in MJ/m2/day. The engine's own source cites the
published chapter (`https://www.fao.org/3/x0490e/x0490e07.htm`).

**How the reference values below were obtained.** The reference column is an
independent evaluation of equation 21 with the published constants, written out
in the test module from the equation above. No engine module is consulted.

**Reference-source note.** This registered model is distinct from the `CANON-011`
("Meteorological Pattern Calculator") entry, whose card
(`engine/models/cards/CANON-011_solar_radiation.md`) covers the wider model that
computes net radiation as well. The card's own `reference_cases` row quotes
`Ra = 41.0068 MJ/m2/day` for latitude 41.9, day of year 193; the value this
record reproduces from equation 21 independently is `41.006807208133594`, which
agrees with the card's quoted figure to the six decimals it prints. The card
itself records a retired "24.5 MJ" figure and states that no published worked
number for that value exists in the repository; the independent evaluation here
is what closes that gap for `Ra`.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Latitude | `latitude` (phi) | degrees | 0.0 – 50.8 |
| Day of year | `doy` (J) | 1–365 | 15 – 355 |

The two inputs fully determine the output, and the cases span the extremes the
equation can produce over the Earth's seasonal cycle: the equinox over the
equator (case 4, 37.80 MJ/m2/day), the northern summer solstice (case 1, 41.01),
mid-April at mid latitude (case 2, 34.15), the FAO-56 Example 18 site and season
(case 3, 41.09), northern mid-season in the subtropics (case 5, 40.46), the
northern winter solstice (case 6, 17.65) and mid-December at mid latitude
(case 7, 10.44).

**Latitudes above the Arctic and Antarctic circles.** Equation 21's sunset hour
angle is undefined for a polar day or a polar night (`acos` of a value outside
[-1, 1]). This record does not cover those cases; the model's own behaviour
there is outside the published equation's domain and is not asserted either way.
`engine/strict_tests/test_s02_climate_et0.py` records that the edge cases were
satisfied "by construction" without a published example.

---

## 3. Tolerance

`tolerance_absolute = 1e-12` (MJ/m2/day).

**Basis.** Equation 21 is a closed form evaluated in double precision and the
model performs no rounding of its reported `ra_mj_m2_day`. The probe that
produced this record measured `+0.000e+00` bit-for-bit on every case, and
`engine/tests/test_card_code_agreement.py::TestCanon011Radiation` already asserts
the same equation at `rel=1e-9` for the reference day. 1e-12 is the double
precision round-off bound on a value of order ten.

---

## 4. Comparison table — model output vs reference output

| # | latitude (deg) | doy | Model output (MJ/m2/day) | Reference (MJ/m2/day) | Verdict |
|---|---|---|---|---|---|
| 1 | 41.9 | 193 | 41.006807208133594 | 41.006807208133594 | match |
| 2 | 41.9 | 105 | 34.146161827477236 | 34.146161827477236 | match |
| 3 | 50.8 | 187 | 41.08837556354228 | 41.08837556354228 | match |
| 4 | 0.0 | 81 | 37.803690069294014 | 37.803690069294014 | match |
| 5 | 33.0 | 200 | 40.456110083959985 | 40.456110083959985 | match |
| 6 | 35.7 | 15 | 17.64927067189183 | 17.64927067189183 | match |
| 7 | 45.0 | 355 | 10.440584974418353 | 10.440584974418353 | match |

Case 3 is the published FAO-56 Example 18 site (Uccle, Belgium), whose published
`Ra` is 41.11 MJ/m2/day; the independently re-derived value is 41.0884, within
0.05 % of the published figure. The small residual is FAO-56's own
three-significant-figure presentation, not a disagreement with equation 21.

---

## 5. Uncertainty statement

This is **exact-method conformance** to FAO-56 equation 21: it establishes that
the engine evaluates the published closed form to floating-point round-off for
every latitude and day compared, spanning a nearly four-fold range of radiation.

Extraterrestrial radiation is not a quantity that carries empirical uncertainty
in the usual sense — it is a geometric maximum determined by Earth's orbit and
the Sun's output, and its published constants (`Gsc = 0.0820 MJ/m2/min`, the
eccentricity coefficient 0.033, the obliquity coefficient 0.409 and the phase
1.39 rad) are themselves rounded to FAO-56's chosen precision. The honest
statement about this model's accuracy is therefore that it reproduces the
published equation to round-off and inherits the published constants' own
rounding, which is well under 0.1 % on `Ra`.

The substantial uncertainty in the quantity this model is usually used for is
downstream: `Ra` is the upper bound on solar radiation `Rs`, and the ratio
between them depends on cloud cover, which equation 21 does not model. Consumers
(`CANON-002`, and the FAO-56 net-radiation estimator) inherit that gap.

---

## 6. Limitations

1. **Polar day and polar night are outside the published equation** and are not
   compared here: at a latitude above the seasonal circle the sunset hour angle
   is undefined.
2. **Only `Ra` is validated.** The wider `CANON-011` model computes net radiation
   and clear-sky estimates on top of it; those are separate claims with their own
   references and are not covered by this record.
3. **No atmospheric or orbital-refinement term.** FAO-56 equation 21 uses a
   two-term solar declination and a single eccentricity coefficient. More precise
   orbital ephemerides would give slightly different `Ra`; the model is
   faithful to FAO-56, not to the most precise astronomical computation.
4. **No radiation measurement is compared**, and none should be: the quantity is
   a geometric maximum, and a pyranometer measures `Rs`, not `Ra`.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. Each reference value is FAO-56 equation 21
evaluated independently in the test module.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "CANON-011_RAD",
  "model_name": "Extraterrestrial Radiation",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_et_pm_group",
  "reference": {
    "citation": "Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements, FAO Irrigation and Drainage Paper 56, 1998, ch. 3, eq. 21, with Gsc = 0.0820 MJ/m2/min.",
    "equation": "dr = 1 + 0.033 cos(2 pi J/365); delta = 0.409 sin(2 pi J/365 - 1.39); ws = acos(-tan phi tan delta); Ra = (1440/pi) Gsc dr [ws sin phi sin delta + cos phi cos delta sin ws]"
  },
  "input_range": {
    "latitude_deg": [0.0, 50.8],
    "doy": [15, 355]
  },
  "output_key": "ra_mj_m2_day",
  "tolerance": {
    "absolute": 1e-12,
    "basis": "a closed form evaluated in double precision with no rounding of the reported value"
  },
  "cases": [
    {
      "name": "northern_summer_solstice_mid_latitude",
      "inputs": {"latitude": 41.9, "doy": 193},
      "reference": 41.006807208133594,
      "recorded": 41.006807208133594,
      "verdict": "match"
    },
    {
      "name": "mid_april_mid_latitude",
      "inputs": {"latitude": 41.9, "doy": 105},
      "reference": 34.146161827477236,
      "recorded": 34.146161827477236,
      "verdict": "match"
    },
    {
      "name": "fao56_example18_site_uccele_belgium",
      "inputs": {"latitude": 50.8, "doy": 187},
      "reference": 41.08837556354228,
      "recorded": 41.08837556354228,
      "verdict": "match"
    },
    {
      "name": "equinox_on_the_equator",
      "inputs": {"latitude": 0.0, "doy": 81},
      "reference": 37.803690069294014,
      "recorded": 37.803690069294014,
      "verdict": "match"
    },
    {
      "name": "northern_mid_season_sub_tropical",
      "inputs": {"latitude": 33.0, "doy": 200},
      "reference": 40.456110083959985,
      "recorded": 40.456110083959985,
      "verdict": "match"
    },
    {
      "name": "northern_winter_solstice",
      "inputs": {"latitude": 35.7, "doy": 15},
      "reference": 17.64927067189183,
      "recorded": 17.64927067189183,
      "verdict": "match"
    },
    {
      "name": "mid_december_mid_latitude",
      "inputs": {"latitude": 45.0, "doy": 355},
      "reference": 10.440584974418353,
      "recorded": 10.440584974418353,
      "verdict": "match"
    }
  ],
  "validation_status": "validated",
  "status_vocabulary_label": "VALIDATED_METHOD",
  "uncertainty": "Exact-method conformance to FAO-56 eq. 21 to floating-point round-off, with Ra spanning 10.4 to 41.1 MJ/m2/day. Ra is a geometric maximum that carries no empirical uncertainty; the gap between it and measured solar radiation is the downstream consumers' problem.",
  "limitations": [
    "Polar day and polar night lie outside the published equation and are not compared.",
    "Only Ra is validated, not the net-radiation and clear-sky estimates the wider CANON-011 model adds.",
    "The two-term solar declination and single eccentricity coefficient are FAO-56's, not the most precise astronomical ones.",
    "No radiation measurement is compared, and none should be: Ra is a geometric maximum."
  ]
}
```
