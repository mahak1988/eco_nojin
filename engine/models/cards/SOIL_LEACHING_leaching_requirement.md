# Model Card: SOIL_LEACHING — Leaching Requirement

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `SOIL_LEACHING` |
| **name** | Leaching Requirement |
| **version** | `1.0.0` |
| **scientific_domain** | Soil salinity |
| **intended_use** | Report the leaching fraction a crop needs to hold root-zone salinity at its threshold, from the irrigation-water and soil conductivity. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | LR = ECw / (5 * ECe_target - ECw) — Rhoades (1974), restated in Ayers & Westcot, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985, ch. 5. `ECw` is the irrigation-water EC and `ECe_target` the crop's threshold saturation-extract EC. |
| **equation_conventions** | Both conductivities are in dS/m; the result is a dimensionless fraction of the applied water. The implementation rounds the reported `leaching_fraction` to three decimals. |
| **assumptions** | (1) Steady-state leaching. (2) Spatially uniform application. (3) No rainfall contribution — the published procedure adds a rainfall correction this model does not apply. |
| **applicability_domain** | `ec_soil > ec_water`, `ec_soil > target_ec`, and `5 * target_ec > ec_water`. Above `LR = 0.95` the implementation clamps to 0.95, which departs from the published equation by up to 5 percentage points; that region is excluded from the validation record. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `ec_soil` (float, dS/m), `ec_water` (float, dS/m), `target_ec` (float, dS/m, default 4.0 — a design assumption of the route, not a published figure) |
| **output_schema** | `leaching_fraction`, `leaching_percentage`, `leaching_required` (bool), `interpretation` |
| **units** | Conductivities in dS/m; the requirement as a fraction and a percentage. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/soil/salinity.py::calculate_leaching_requirement`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_soil_leaching`. |
| **verification_status** | Verified — the implementation reproduces the published closed form within its reported rounding granularity over seven comparison cases spanning water qualities from 0.5 to 3.0 dS/m; see `engine/validation/SOIL_LEACHING.md`. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation reproduces the published Rhoades / FAO-29 leaching-requirement closed form exactly over seven comparison cases spanning water qualities from 0.5 to 3.0 dS/m; the evidence record is `engine/validation/SOIL_LEACHING.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The registry is left at `unvalidated` for this model, because the machine-readable evidence register (`reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`, row `SAR_ESP_LEACHING`) records this family as method-conformance evidence and `engine/tests/test_machine_evidence_consistency.py` will not credit a registry-level claim for it without an external anchor. The row to add is a published FAO-29 chapter 5 worked leaching-requirement value. |
| **provenance** | `data_source: "computed"`; `model: "Rhoades 1974 / Ayers & Westcot 1985"`; `computed: True` |
| **validation_record** | `engine/validation/SOIL_LEACHING.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s18_scientific_validation.py::TestSoilChemistryIndependent` |
