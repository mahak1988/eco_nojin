# Model Card: CANON-014 — Model Registry

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-014` |
| **name** | Model Registry |
| **version** | `1.0.0` |
| **scientific_domain** | Meta (Model Management) |
| **intended_use** | Central registry of all engine models and their specifications, consumed by the gateway layer for model dispatch. Provides a single source of truth for model metadata, backends, and capabilities. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Not a scientific model. Defines `ModelSpec` dataclass with fields: model_id, name, version, domain, input_schema, output_schema, supported_backends, backend_priority. Registry maps model_id → ModelSpec. |
| **equation_conventions** | N/A. |
| **assumptions** | Models are registered at import time and remain static during a process lifetime. |
| **applicability_domain** | All models dispatched through the gateway layer. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | N/A — no model inputs. |
| **output_schema** | N/A — no model outputs. Provides the registry lookup for other models. |
| **units** | N/A. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — metadata registry. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Not applicable. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | N/A — engineering infrastructure. |
| **reference_cases** | N/A. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s12_formula_catalog.py` — checks registry compliance. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | All registered models have valid ModelSpec; no duplicate model_ids. |
| **empirical_validation** | Not applicable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not applicable. |
| **known_limitations** | **BLOCKER (B-NEW-002, P1)**: The registry at `engine/models/registry.py` does not exist — the directory is empty. A registry class exists at `engine/hydroma/models/expansion/registry.py` but requires numpy to import and registers 0 models. The `ModelSpec` class exists in the Gateway (lines 87–98 of `engine/gateway.py`) but has no populated registry to consume. All 22 CANON models lack registration. Gateway dispatch cannot function until this is resolved. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/models/registry.py` exists (735 lines: `ModelRegistry`, `get_registry()`, `get_model()`, `list_models()`, 72 registered models, 34 `model_type` values, 13 domains) and is the registry the Engine Gateway consumes (`engine/gateway/__init__.py:531-533`). The "does not exist / registers 0 models" claim recorded below (B-NEW-002) is stale: it described the state before this registry was written. `engine/hydroma/models/expansion/registry.py` remains a separate numpy-based expansion registry and is not this component. |
| **verification_status** | Verified — `get_registry()` returns 72 models with no duplicate ids, and every registered id resolves through the gateway's model lookup. Covered by `engine/tests/test_registry_status.py` and `strict_tests/test_s16_gateway_strict_contracts.py::TestGatewayRegistry`. |
| **validation_status** | Not applicable as a scientific model — no governing equations and no reference data. Contract-level checks instead: the 72 registered ids are the ids the services facade dispatches, and the structured per-model status (implementation/verification/validation, seeded from the model cards) is exported by `ModelRegistry.status_summary()`. |
| **provenance** | `data_source: "registry"`; `model: "Model Registry v1.0"`; `computed: False` |
