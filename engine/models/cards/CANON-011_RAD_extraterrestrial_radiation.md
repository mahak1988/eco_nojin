# Model Card: CANON-011_RAD — Extraterrestrial Radiation

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `CANON-011_RAD` |
| **name** | Extraterrestrial Radiation |
| **version** | `1.0.0` |
| **scientific_domain** | Solar radiation |
| **intended_use** | Report the daily extraterrestrial radiation for a latitude and day of year, the upper bound on solar radiation that the FAO-56 evapotranspiration equations are driven by. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | FAO Irrigation and Drainage Paper 56 (Allen et al. 1998), ch. 3, eq. 21: `dr = 1 + 0.033 cos(2 pi J / 365)`; `delta = 0.409 sin(2 pi J / 365 - 1.39)`; `ws = acos(-tan phi tan delta)`; `Ra = (24 * 60 / pi) Gsc dr [ws sin phi sin delta + cos phi cos delta sin ws]` with `Gsc = 0.0820 MJ/m2/min`. |
| **equation_conventions** | Latitude in degrees, `J` the day of the year (1–365), `Ra` in MJ/m2/day. The result is the top-of-atmosphere daily integral, not a surface measurement. |
| **assumptions** | (1) A two-term solar declination and a single eccentricity coefficient, FAO-56's precision rather than the most precise astronomical computation. (2) No atmospheric absorption, cloud cover or aerosol term. |
| **applicability_domain** | Latitudes and days where the sunset hour angle is defined. Polar day and polar night put `acos` outside [-1, 1]; the equation has no value there and the model is outside this record's comparison. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `latitude` (float, degrees, −90..90), `doy` (int, 1..365) |
| **output_schema** | `ra_mj_m2_day` (float, MJ/m2/day), `method`, `units` |
| **units** | Radiation in MJ/m2/day (the `units` field records the mm/day equivalent the ET equations consume). |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/climate/et_calculator.py::calc_extraterrestrial_radiation`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_et_pm_group`. |
| **verification_status** | Verified — the implementation reproduces FAO-56 equation 21 bit-for-bit against an independent evaluation over seven latitude/day pairs spanning 10.44 to 41.09 MJ/m2/day; see `engine/validation/CANON-011_RAD.md`. |
| **validation_status** | **VALIDATED_METHOD** — validated against the published FAO-56 equation 21 with the evidence record `engine/validation/CANON-011_RAD.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. Only `Ra` is credited; the net-radiation and clear-sky estimates of the wider `CANON-011` model are separate claims. |
| **provenance** | `data_source: "computed"`; `model: "FAO-56 eq. 21"`; `computed: True` |
| **validation_record** | `engine/validation/CANON-011_RAD.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/tests/test_card_code_agreement.py::TestCanon011Radiation` |
