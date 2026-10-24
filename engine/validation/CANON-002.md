# Validation Evidence — CANON-002

**Model:** `CANON-002` — Hargreaves Reference Evapotranspiration (ET0) (registry version `1.0.0`)
**Cluster:** evapotranspiration / crop water requirements
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_et_pm_group` (`ET0_HARGREAVES`)
**Implementation:** `engine/hydroma/climate/et_calculator.py::HargreavesET0Calculator.calculate_et`
**Model card:** `engine/models/cards/CANON-002_hargreaves_et0.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

---

## 1. Published reference

**Citation.** Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., *Crop
Evapotranspiration — Guidelines for Computing Crop Water Requirements*, FAO
Irrigation and Drainage Paper 56, 1998, Chapter 4, equation 52:

```
ET0 = 0.0023 * (Tmean + 17.8) * (Tmax - Tmin)^0.5 * Ra
```

with `Tmean = (Tmax + Tmin) / 2` and `Ra` the extraterrestrial radiation in
**mm/day**, obtained from the same chapter's equation 21 in MJ/m²/day and
converted with equation 40 (`Ra[mm/day] = 0.408 * Ra[MJ/m²/day]`). The equation
is the Hargreaves-Samani (1985) estimator in the form FAO-56 recommends it; the
engine's own source cites the published chapter
(`https://www.fao.org/3/x0490e/x0490e07.htm`).

**How the reference values below were obtained.** Two independent steps, both
written from the published equations in the test module:

1. `Ra` is re-derived from FAO-56 equation 21 with the published constants
   (`Gsc = 0.0820`, `dr = 1 + 0.033 cos(2 pi J / 365)`,
   `delta = 0.409 sin(2 pi J / 365 - 1.39)`,
   `ws = acos(-tan phi tan delta)`, and the day-length integral), and converted
   with 0.408.
2. Equation 52 is then applied to that `Ra`.

No engine module is consulted when the reference number is produced, so a change
in the engine's `Ra` cannot move the reference.

**Card correction recorded with this evidence.** The card's
`governing_equations` row used to state `ET0 = 0.0023 * (Tmean + 17.8) *
(Tmax - Tmin)^0.6 * Ra^0.5` — the original Hargreaves-Samani (1985) parameterisation
with `Ra` expressed in equivalent millimetres of evaporation. FAO-56 equation 52
substitutes `(Tmax - Tmin)^0.5` and an unconverted `Ra`, which is what the
implementation computes (it multiplies `Ra` in MJ/m²/day by 0.408 before the
equation, as equation 40 requires). The card row has been corrected to equation
52 so that the card states the equation the model actually evaluates and this
record validates against.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Minimum temperature | `temp_min` (Tmin) | °C | 10 (fixed) |
| Maximum temperature | `temp_max` (Tmax) | °C | 25 (fixed) |
| Latitude | `latitude` (phi) | degrees | 0.0 – 50.8 |
| Day of year | `doy` (J) | 1–365 | 15 – 355 |

The temperature pair is held fixed at Tmin = 10, Tmax = 25 (a 15 °C diurnal
range) so that the comparison isolates the radiation term, which is the part the
model computes rather than reads. The latitude/DOY pairs are then chosen to span
the full range of extraterrestrial radiation the equation can encounter: the
equinox over the equator (case 4, 37.80 MJ/m²/day), the northern summer solstice
(cases 1 and 2), a low-latitude mid-season point (case 5), the northern winter
solstice (case 6, 10.44 MJ/m²/day) and mid-January (case 7, 17.65 MJ/m²/day).
`Ra` therefore spans 10.4 to 41.1 MJ/m²/day, and the ET0 output 1.34 to
5.27 mm/day.

---

## 3. Tolerance

`tolerance_absolute = 1e-12` (mm/day).

**Basis.** FAO-56 equation 52 is a closed form evaluated in double precision;
the engine performs no rounding of its reported ET0. The probe that produced
this record measured `+0.00e+00` bit-for-bit on every case. 1e-12 is the
round-off bound of double precision on a value of order unity, not a loosened
scientific claim.

---

## 4. Comparison table — model output vs reference output

| # | lat (deg) | doy | Ra (MJ/m²/day) model | Ra (MJ/m²/day) ref | Model ET0 (mm/day) | Reference ET0 (mm/day) | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 41.9 | 193 | 41.006807208133594 | 41.006807208133594 | 5.2609514070310155 | 5.2609514070310155 | match |
| 2 | 41.9 | 105 | 34.146161827477236 | 34.146161827477236 | 4.38076773934606 | 4.38076773934606 | match |
| 3 | 50.8 | 187 | 41.08837556354228 | 41.08837556354228 | 5.271416185524461 | 5.271416185524461 | match |
| 4 | 0.0 | 81 | 37.803690069294014 | 37.803690069294014 | 4.850008815647778 | 4.850008815647778 | match |
| 5 | 33.0 | 200 | 40.456110083959985 | 40.456110083959985 | 5.190299946760915 | 5.190299946760915 | match |
| 6 | 35.7 | 15 | 17.64927067189183 | 17.64927067189183 | 2.2643058968985916 | 2.2643058968985916 | match |
| 7 | 45.0 | 355 | 10.440584974418353 | 10.440584974418353 | 1.33947054040575 | 1.33947054040575 | match |

Case 3 is the FAO-56 Example 18 site (Uccle, Belgium, latitude 50.8 deg N, day of
year 187) whose published `Ra` is 41.11 MJ/m squared per day; the independently
re-derived value is 41.0884, within 0.05 % of the published figure. Case 1 is the
latitude and day of year the CANON-011 card quotes as its own reference day.

---

## 5. Uncertainty statement

This is **exact-method conformance** to the published FAO-56 equations 40, 52 and
21. It establishes that the engine computes the Hargreaves estimator FAO-56
publishes, over a radiation range spanning nearly four-fold. It does **not**
establish that the resulting ET0 agrees with measured ET0 at any site.

That gap is large and is well documented. FAO-56 chapter 4 reports the
Hargreaves estimator's performance against the Penman-Monteith reference as
degrading in tropical and humid climates and improving in arid and windy ones,
and the model's own card says as much ("Requires local validation for Iran and
other non-temperate regions"). The estimator also substitutes the diurnal
temperature range for solar radiation, so a cloudy day with a large range is
read as a clear one. A caller should treat the output as an index, not a
measurement, and calibrate it against local lysimeter or pan data before using
it to size or schedule anything.

The engine holds the same limitation for the wider model:
`engine/strict_tests/test_s06_watershed_design.py` and
`engine/strict_tests/test_s18_scientific_validation.py` both record that the
Hargreaves ET0 path is an *unvalidated estimator* relative to Penman-Monteith.
What this record does is establish that whatever its shortcomings, the engine
evaluates the published equation exactly.

---

## 6. Limitations

1. **No measured ET0 is compared.** This is conformance to the published
   estimator, not a field validation of it.
2. **The radiation term is a geometric maximum, not an observation.** FAO-56
   equation 52 assumes `Ra` is a proxy for `Rs`; no cloud or aerosol term is
   applied. Overcast days produce a biased ET0.
3. **The temperature pair is fixed in this record.** Sensitivity to the diurnal
   range is not established here.
4. **The card's `verification_status` is untouched** by this record: the card
   states, and `engine/tests/test_registry_status.py` pins, that the C++ unit
   test for this model is not executed in this repository and that the Python
   path is design-correspondence only. The validation below covers the Python
   path the gateway actually dispatches.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. Each reference ET0 is FAO-56 equations
21 + 40 + 52 evaluated independently in the test module.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "CANON-002",
  "model_name": "Hargreaves Reference Evapotranspiration",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_et_pm_group",
  "reference": {
    "citation": "Allen, R.G., Pereira, L.S., Raes, D. & Smith, M., Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements, FAO Irrigation and Drainage Paper 56, 1998, ch. 4, eqs. 52 (Hargreaves ET0), 40 (MJ/m2/day to mm/day) and 21 (extraterrestrial radiation); estimator due to Hargreaves & Samani (1985).",
    "equation": "et0 = 0.0023 * ((tmin + tmax) / 2 + 17.8) * (tmax - tmin)^0.5 * 0.408 * ra_eq21(latitude, doy)"
  },
  "input_range": {
    "temp_min_c": 10.0,
    "temp_max_c": 25.0,
    "latitude_deg": [0.0, 50.8],
    "doy": [15, 355]
  },
  "output_key": "et0_mm_day",
  "tolerance": {
    "absolute": 1e-12,
    "basis": "FAO-56 eq. 52 is a closed form evaluated in double precision and the model does not round its output"
  },
  "cases": [
    {
      "name": "northern_summer_solstice_mid_latitude",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 41.9, "doy": 193},
      "reference": 5.2609514070310155,
      "recorded": 5.2609514070310155,
      "verdict": "match"
    },
    {
      "name": "mid_april_mid_latitude",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 41.9, "doy": 105},
      "reference": 4.38076773934606,
      "recorded": 4.38076773934606,
      "verdict": "match"
    },
    {
      "name": "fao56_example18_site_uccele_belgium",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 50.8, "doy": 187},
      "reference": 5.271416185524461,
      "recorded": 5.271416185524461,
      "verdict": "match"
    },
    {
      "name": "equinox_on_the_equator",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 0.0, "doy": 81},
      "reference": 4.850008815647778,
      "recorded": 4.850008815647778,
      "verdict": "match"
    },
    {
      "name": "northern_mid_season_sub_tropical",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 33.0, "doy": 200},
      "reference": 5.190299946760915,
      "recorded": 5.190299946760915,
      "verdict": "match"
    },
    {
      "name": "northern_winter_solstice",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 35.7, "doy": 15},
      "reference": 2.2643058968985916,
      "recorded": 2.2643058968985916,
      "verdict": "match"
    },
    {
      "name": "mid_december_mid_latitude",
      "inputs": {"temp_min": 10.0, "temp_max": 25.0, "latitude": 45.0, "doy": 355},
      "reference": 1.33947054040575,
      "recorded": 1.33947054040575,
      "verdict": "match"
    }
  ],
  "validation_status": "validated",
  "status_vocabulary_label": "VALIDATED_METHOD",
  "uncertainty": "Exact-method conformance to FAO-56 eqs. 40, 52 and 21 to floating-point round-off, with Ra spanning 10.4 to 41.1 MJ/m2/day. No measured ET0 is compared, and the estimator's known climate-dependent bias against Penman-Monteith is not removed by this record.",
  "limitations": [
    "No measured ET0 is compared: this is conformance to the published estimator, not a field validation of it.",
    "Ra is a geometric maximum used as a proxy for solar radiation; no cloud or aerosol term is applied.",
    "The temperature pair is fixed at 10/25 C, so sensitivity to the diurnal range is not established here.",
    "The card's verification_status is untouched by this record and still reads design-correspondence only."
  ]
}
```
