# Model Card: SOIL_SAR — Sodium Adsorption Ratio

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `SOIL_SAR` |
| **name** | Sodium Adsorption Ratio |
| **version** | `1.0.0` |
| **scientific_domain** | Soil salinity |
| **intended_use** | Classify the sodium hazard of an irrigation water from its Na, Ca and Mg concentrations; an input to the salinity and sodicity advisory route. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | SAR = Na / sqrt((Ca + Mg) / 2)  — USDA Agriculture Handbook 60 (1954), ch. 6, restated as eq. (5) of Ayers & Westcot, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985. |
| **equation_conventions** | Ion concentrations are in milliequivalents per litre (meq/L) and stand in for ion activities. Sodium-hazard bands: low < 3, medium 3 – 6, high 6 – 9, very high >= 9. |
| **assumptions** | (1) Equilibrium ion activities approximated by concentrations. (2) Concentrations at soil temperature, not standardised. (3) The hazard bands describe the water, not the soil it will meet. |
| **applicability_domain** | Irrigation waters within the Handbook 60 ch. 6 table (0.5 – 40 meq/L per ion). Brines and very dilute rain sit outside the equation's described range. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `na` (float, meq/L, >= 0), `ca` (float, meq/L, >= 0), `mg` (float, meq/L, >= 0); `ca + mg > 0` |
| **output_schema** | `sar` (float, (meq/L)^0.5, rounded to 2 decimals), `classification` (sodium-hazard band), `suitable_for_irrigation` (bool) |
| **units** | Concentrations in meq/L; the ratio carries the square root of that unit. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/soil/chemistry.py::calculate_sar`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_soil_sar`. |
| **verification_status** | Verified — the implementation reproduces the published definition within its reported rounding granularity over four comparison cases spanning the whole sodium-hazard ladder; see `engine/validation/SOIL_SAR.md`. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation evaluates the published USDA Agriculture Handbook 60 sodium-hazard definition exactly over four comparison cases spanning the whole sodium-hazard ladder; the evidence record is `engine/validation/SOIL_SAR.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The registry is left at `unvalidated` for this model, because the machine-readable evidence register (`reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`, row `SAR_ESP_LEACHING`) records this family as method-conformance evidence and `engine/tests/test_machine_evidence_consistency.py` will not credit a registry-level claim for it without an external anchor. The row to add is a published Handbook 60 sodium-hazard table value. |
| **provenance** | `data_source: "measured"`; `model: "Richards 1954 / Ayers & Westcot 1985"`; `computed: True` |
| **validation_record** | `engine/validation/SOIL_SAR.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s18_scientific_validation.py::TestSoilChemistryIndependent` |
