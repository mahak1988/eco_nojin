# Model Card: CANON-012 — Formula Catalog

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-012` |
| **name** | Formula Catalog |
| **version** | `1.0.0` |
| **scientific_domain** | Meta / Utility |
| **intended_use** | Registry of all implemented formula modules with their backend parity state, reference cases, and implementation quality. Ensures no formula is served on a request path while divergent. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Not a scientific model. Governs the registration and dispatch of formula records. Each FormulaRecord carries: quantity, canonical source, literature_ref, units, domain (scalar/array/both), backend_priority, parity_tests, reference_values, status (verified/stub/divergent), and notes. |
| **equation_conventions** | N/A — metadata registry. |
| **assumptions** | N/A. |
| **applicability_domain** | All formula implementations in the engine. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | N/A — no model inputs. |
| **output_schema** | N/A — no model outputs. |
| **units** | N/A. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — utility module. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Not applicable — registry module. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | N/A — utility/infrastructure. |
| **reference_cases** | N/A — not a scientific model. Records reference cases for each formula it catalogs. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `tests/unit/test_formula_registry.py` — verifies all records have required fields, backends_impl is consistent with backend_priority, status reflects measured state. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Not applicable. |
| **empirical_validation** | Not applicable — N/A status. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not applicable. |
| **known_limitations** | N/A — non-scientific utility. Acts as a gate: formulas with status `divergent` cannot be served on a request path. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/formulas/catalog.py`. |
| **verification_status** | Verified — all records have required fields; status reflects measured parity state. |
| **validation_status** | N/A — infrastructure, not a scientific model. |
| **provenance** | `data_source: "registry"`; `model: "Formula Catalog v1.0"`; `computed: False` |
