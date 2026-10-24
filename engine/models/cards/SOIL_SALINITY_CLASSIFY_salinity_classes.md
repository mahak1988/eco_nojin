# Model Card: SOIL_SALINITY_CLASSIFY — Salinity Class Classification

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `SOIL_SALINITY_CLASSIFY` |
| **name** | Salinity Class Classification |
| **version** | `1.0.0` |
| **scientific_domain** | Soil salinity |
| **intended_use** | Place a soil in one of the five published saline classes from the electrical conductivity of its saturation extract. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | Classification rule, USDA Agriculture Handbook 60 (1954), ch. 3, restated as Table 1 of Ayers & Westcot, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985. With ECe the saturation-extract EC in dS/m: `ECe < 2 -> non_saline`; `2 <= ECe < 4 -> slightly_saline`; `4 <= ECe < 8 -> moderately_saline`; `8 <= ECe < 16 -> strongly_saline`; `ECe >= 16 -> very_strongly_saline`. |
| **equation_conventions** | The published classes are written as closed ranges ending at the break value, so a composition sitting exactly on a break value belongs to the higher class; the implementation assigns `ECe = 2.0` to `slightly_saline` and `ECe = 16.0` to `very_strongly_saline`. |
| **assumptions** | (1) The input is a saturation-extract conductivity, not a field bulk EC or a 1:5 extract EC. (2) Salinity alone classifies the soil; the exchangeable sodium percentage is a separate axis. |
| **applicability_domain** | Any non-negative ECe. The top class is unbounded, as in the published table. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `ec` (float, dS/m, >= 0) |
| **output_schema** | `classification` (one of the five published labels), `ec` (echoed) |
| **units** | EC in dS/m. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/soil/salinity.py::classify_salinity`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_soil_salinity_classify`. |
| **verification_status** | Verified — the rule is exhaustive over the published domain with no free parameters, and all five bands and all four break values are compared in `engine/validation/SOIL_SALINITY_CLASSIFY.md`. |
| **validation_status** | **VALIDATED_METHOD** — validated against the published USDA Handbook 60 salinity classes with the evidence record `engine/validation/SOIL_SALINITY_CLASSIFY.md`, whose reference classes are re-derived independently of the engine in `engine/validation/test_validation_records.py`. |
| **provenance** | `data_source: "measured"`; `model: "Richards 1954 / Ayers & Westcot 1985"`; `computed: True` |
| **validation_record** | `engine/validation/SOIL_SALINITY_CLASSIFY.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s18_scientific_validation.py::TestSoilChemistryIndependent` |
