# Model Card Template

> Copy this file to a new card (e.g. `CANON-XXX_<name>.md`) and fill every **required** field.
> Fields marked **applicable** must be filled when relevant to the model; otherwise state
> "Not applicable — [reason]" with a concrete justification (docs/specs/HYDROMA-MASTER §337).

---

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** *(required)* | `CANON-XXX` or `S-XXX` (C++ symbol) |
| **name** *(required)* | `[Human-readable model name]` |
| **version** *(required)* | `1.0.0` (or current version) |
| **scientific_domain** *(required)* | `[e.g. Evapotranspiration, Hydrology, Soil Physics, …]` |
| **intended_use** *(required)* | `[Primary purpose and audience]` |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** *(required)* | `[Full equation(s) in standard notation, traceable to source]` |
| **equation_conventions** *(required)* | `[Sign conventions, variable naming, parameter ordering]` |
| **assumptions** *(required)* | `[List of explicit assumptions, e.g. steady state, homogeneity]` |
| **applicability_domain** *(required)* | `[Spatial/temporal/domain limits, e.g. 5°–55° latitude, daily timestep]` |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** *(required)* | `[Structured list of required inputs: name, type, unit, valid range]` |
| **output_schema** *(required)* | `[Structured list of outputs: name, type, unit]` |
| **units** *(required)* | `[Summary of all units used; SI or otherwise stated explicitly]` |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** *(applicable)* | `[State variables at t=0, required values, or "Not applicable — …"]` |
| **boundary_conditions** *(applicable)* | `[Types of BCs (Dirichlet/Neumann/etc.), or "Not applicable — …"]` |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** *(applicable)* | `[Scheme: e.g. backward Euler, finite volume, explicit Euler]` |
| **solver_configuration** *(applicable)* | `[Linear/nonlinear solver, preconditioner, or "Not applicable — …"]` |
| **convergence_criteria** *(applicable)* | `[Tolerances, max iterations, or "Not applicable — …"]` |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** *(required)* | `[List of cited standard references with DOIs/versions where available]` |
| **reference_cases** *(required)* | `[Named benchmark cases the implementation is checked against]` |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** *(required)* | `[Test file path(s) and what is covered]` |
| **analytical_tests** *(applicable)* | `[Analytical solutions checked, or "Not applicable — …"]` |
| **numerical_tests** *(required)* | `[Numerical test cases and expected values]` |
| **physical_consistency_tests** *(required)* | `[Physical bounds, monotonicity, sign, symmetry checks]` |
| **empirical_validation** *(applicable)* | `[Field data comparison results, or "Not applicable — …"]` |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** *(required)* | `[How uncertainty is quantified: Monte Carlo, error propagation, etc.]` |
| **known_limitations** *(required)* | `[Known scientific or implementation limitations]` |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** *(required)* | `[e.g. Production, Verified, Stub, Not implemented, In review]` |
| **verification_status** *(required)* | `[Code matches design? Evidence.]` |
| **validation_status** *(required)* | `[Matches reference/scientific truth? Evidence-based, never assumed.]` |
| **provenance** *(required)* | `[data_source: simulated/measured; model: name+version; computed: bool]` |

---

## Important Rules (docs/specs/HYDROMA-MASTER §338–347)

1. Equations must be traceable to authoritative sources.
2. Assumptions and applicability domain must be explicit.
3. All inputs and outputs must have defined units and meaning.
4. Initial conditions and boundary conditions must be recorded for models that need them.
5. The numerical method must be identifiable and reproducible.
6. Acceptance criteria must be appropriate to the model.
7. Validation status must be based on evidence, not assumptions.
8. A model not verified must not be presented as verified.
