# Model Card: SOIL_ESP — Exchangeable Sodium Percent

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `SOIL_ESP` |
| **name** | Exchangeable Sodium Percent |
| **version** | `1.0.0` |
| **scientific_domain** | Soil sodicity |
| **intended_use** | Report the exchangeable sodium percentage of a soil from its exchangeable sodium and cation exchange capacity, and classify it against the sodic threshold. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | ESP = 100 * exchangeable Na / CEC — USDA Agriculture Handbook 60 (1954), ch. 5. Bands: normal < 10, moderately sodic 10 – 15, sodic >= 15 (the Handbook 60 definitional line at 15 is reported as `threshold`, the management/amendment line at 10 as `amendment_threshold`). |
| **equation_conventions** | Both quantities are in meq/100 g, so the ratio is dimensionless and the result a percentage. |
| **assumptions** | (1) Exchangeable sodium and CEC are measured on the same sample at the same pH. (2) The CEC is a measured total, not a texture-derived estimate. |
| **applicability_domain** | Mineral soils with a measurable exchange complex; `exchangeable Na >= 0` and `CEC > 0`. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `na` (float, meq/100 g, >= 0), `cex` (float, meq/100 g, CEC, > 0) |
| **output_schema** | `esp` (float, %, rounded to 2 decimals), `classification`, `threshold`, `amendment_threshold` |
| **units** | Inputs in meq/100 g; output as a percentage. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/soil/chemistry.py::calculate_esp`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_soil_esp`. |
| **verification_status** | Verified — the implementation reproduces the published ratio within its reported rounding granularity over four comparison cases spanning both published decision lines; see `engine/validation/SOIL_ESP.md`. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation evaluates the published USDA Agriculture Handbook 60 exchangeable-sodium definition exactly over four comparison cases spanning both published decision lines; the evidence record is `engine/validation/SOIL_ESP.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The registry is left at `unvalidated` for this model, because the machine-readable evidence register (`reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`, row `SAR_ESP_LEACHING`) records this family as method-conformance evidence and `engine/tests/test_machine_evidence_consistency.py` will not credit a registry-level claim for it without an external anchor. The row to add is a published exchangeable-sodium table value or a laboratory exchangeable-cation measurement. |
| **provenance** | `data_source: "measured"`; `model: "Richards 1954"`; `computed: True` |
| **validation_record** | `engine/validation/SOIL_ESP.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s18_scientific_validation.py::TestSoilChemistryIndependent` |
