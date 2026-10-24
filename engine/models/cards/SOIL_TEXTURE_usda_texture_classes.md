# Model Card: SOIL_TEXTURE — USDA Soil Textural Class

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `SOIL_TEXTURE` |
| **name** | USDA Soil Textural Class |
| **version** | `1.0.0` |
| **scientific_domain** | Soil texture classification |
| **intended_use** | Assign one of the twelve USDA textural classes from the sand/silt/clay fractions, the key every texture-dependent parameter lookup in the engine is driven by. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | USDA-NRCS National Soil Survey Handbook Part 630, Soil Survey Manual, ch. 3 — the twelve-class textural triangle. The published class definitions are transcribed at `tests/reference_data/usda_texture_classes.csv`. |
| **equation_conventions** | Fractions in percent, summing to 100. A composition falls through to the documented `loam` fallback when no class range fits (`engine/hydroma/soil/taxonomy.py`). |
| **assumptions** | (1) The published class definitions are representable as axis-aligned clay/silt/sand range boxes. (2) A composition outside every box is usefully reported as `loam`, the most common soil class. |
| **applicability_domain** | Any `sand + silt + clay = 100` with non-negative fractions. All 5151 integer compositions on the triangle were compared against the published definitions. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `sand_pct` (float, %), `silt_pct` (float, %), `clay_pct` (float, %), summing to 100 |
| **output_schema** | `texture_class` (str, one of the twelve labels), `model_id`, `model_type` |
| **units** | Percent of the fine-earth fraction. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/soil/texture.py::classify_texture`, delegating to `engine/hydroma/soil/taxonomy.py::_determine_texture_class`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_soil_texture`. |
| **verification_status** | Implementation matches design — one classifier fed from one triangle (`TEXTURE_CLASSES`), no second copy to disagree with it. The taxonomy module's `AGREEMENT_FLOOR` check compares the two internal derivations against each other; it is not a comparison against the published table. |
| **validation_status** | **UNVALIDATED** — the classifier does not match its published reference. Over all 5151 integer compositions on the triangle it agrees with the published USDA class definitions on 4170 (80.96 %); it answers from a class range on 4369 (84.82 %) and falls through to the documented `loam` fallback on the remaining 782 (15.18 %), while the published definitions cover the whole grid. The comparison, the disagreement counts and the five commonest disagreement pairs are recorded in `engine/validation/SOIL_TEXTURE.md`, and the registry is left reporting UNVALIDATED until that record says otherwise. |
| **provenance** | `data_source: "computed"`; `model: "USDA-NRCS textural triangle"`; `computed: True` |
| **validation_record** | `engine/validation/SOIL_TEXTURE.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/tests/test_usda_texture_reference.py` |
