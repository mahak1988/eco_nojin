# Model Card: CANON-013 — Provenance Tracking

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-013` |
| **name** | Provenance Tracking |
| **version** | `1.0.0` |
| **scientific_domain** | Infrastructure |
| **intended_use** | Ensure every engine output carries explicit provenance: where the data came from (`data_source`), whether the engine actually ran to produce the value (`computed`), and which model/version produced it. Prevents fabricated outputs from being indistinguishable from real results. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Not a scientific model. Defines the `ResultProvenance` base class and `DataSource` enum with values: `simulated` (model ran), `measured` (from observations), `synthetic` (fabricated/test data). The `computed` flag distinguishes a real run from a mock/fallback. |
| **equation_conventions** | N/A. |
| **assumptions** | (1) `data_source` is never defaulted — the producing function must state it. (2) `computed` defaults to True but must be set False for mock/synthetic modes. |
| **applicability_domain** | All model output types in the engine. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | N/A — no model inputs. |
| **output_schema** | N/A — no model outputs. Provides the `ResultProvenance` mixin for other models. |
| **units** | N/A. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — infrastructure. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Not applicable — provenance tracking. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | N/A — infrastructure. Internal design documents: `engine/hydroma/simulation/contracts.py` (§2026 provenance rule). |
| **reference_cases** | N/A. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s15_provenance.py` — checks that all result types carry provenance fields, that data_source is never defaulted silently, and that computed=False is set for mock modes. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Provenance fields present on all outputs; data_source ∈ {simulated, measured, synthetic}. |
| **empirical_validation** | Not applicable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not applicable. |
| **known_limitations** | Three of 24 result types at time of writing still lack provenance (down from 21 with 3 carrying it, after introduction of this module). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/provenance.py`. |
| **verification_status** | Verified — all result types under `engine/` checked for provenance fields. |
| **validation_status** | N/A — infrastructure. |
| **provenance** | `data_source: "registry"`; `model: "Provenance v1.0"`; `computed: False` |
