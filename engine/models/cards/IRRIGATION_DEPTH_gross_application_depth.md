# Model Card: IRRIGATION_DEPTH — Net and Gross Application Depth

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `IRRIGATION_DEPTH` |
| **name** | Net and Gross Application Depth |
| **version** | `1.0.0` |
| **scientific_domain** | Irrigation scheduling |
| **intended_use** | Convert a period's crop water requirement and effective rainfall into the gross depth an irrigation system has to apply. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | NIR = ETc - Pe; GAR = NIR / Ea — FAO Irrigation and Drainage Paper 56 (Allen et al. 1998), Annex 2, read with Keller & Bliesner (1990). `Ea` is the application efficiency and `Pe` the effective rainfall. |
| **equation_conventions** | `Ea` is a **fraction** in (0, 1], not a percentage: a percentage written where a fraction belongs is a factor of 100 on the schedule, and the bounds are enforced rather than merely documented. `Pe >= 0` and `ETc >= 0`; the net term is floored at zero so a rain that covers the demand gives a zero depth rather than a negative one. |
| **assumptions** | (1) `ETc` is a period total, not a daily rate. (2) No capillary-rise or percolation credit beyond the rainfall term. (3) The efficiency is a design number for the system, not a measurement of it. |
| **applicability_domain** | `0 < Ea <= 1`, `Pe >= 0`, `ETc >= 0`. At `Ea = 0` no water reaches the root zone, so the required gross depth is unbounded and the implementation raises instead of reporting 0.0. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `etc_mm` (float, mm, >= 0), `efficiency` (float, fraction, in (0, 1]), `effective_rain_mm` (float, mm, >= 0) |
| **output_schema** | `depth_mm` (float, mm), `units` |
| **units** | Depths in mm; efficiency dimensionless as a fraction. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/irrigation/scheduler.py::calculate_application_depth`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_route_irrigation_depth_from_inputs`. |
| **verification_status** | Verified — the implementation reproduces the published two-step relation exactly over five comparison cases spanning both branches of the `max(0, ETc - Pe)` term; see `engine/validation/IRRIGATION_DEPTH.md`. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** — the implementation reproduces the published FAO-56 Annex 2 / Keller & Bliesner net and gross application depth relation exactly over five comparison cases spanning both branches of the `max(0, ETc - Pe)` term; the evidence record is `engine/validation/IRRIGATION_DEPTH.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The registry is left at `unvalidated` for this model, because the machine-readable evidence register has no external-anchor row for the irrigation-scheduling family and `engine/tests/test_machine_evidence_consistency.py` will not credit a registry-level claim for it without one. The row to add is a published measured irrigation depth against a metered application. |
| **provenance** | `data_source: "computed"`; `model: "FAO-56 Annex 2 / Keller & Bliesner 1990"`; `computed: True` |
| **validation_record** | `engine/validation/IRRIGATION_DEPTH.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s08_irrigation.py` |
