# Model Card: S-006 — Hargreaves ET0 (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-006` |
| **name** | Hargreaves ET0 (C++ Symbol) |
| **version** | `1.0.0` |
| **scientific_domain** | Evapotranspiration |
| **intended_use** | C++ kernel exposing the Hargreaves reference ET0 calculation (see CANON-002 for full scientific description). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | See CANON-002. ET0 = 0.0023 × (Tmean + 17.8) × (Tmax − Tmin)^0.6 × Ra^0.5 [mm/day]. |
| **equation_conventions** | Same as CANON-002. |
| **assumptions** | Same as CANON-002. |
| **applicability_domain** | Same as CANON-002. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `tmin` (float, °C), `tmax` (float, °C), `lat_deg` (float, degrees), `doy` (int), ... |
| **output_schema** | `et0` (float, mm/day, ≥0) |
| **units** | Temperature in °C, latitude in degrees. Output in mm/day. |

---

## 4. Initial & Boundary Conditions

Not applicable — daily diagnostic.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of Hargreaves equation. |
| **solver_configuration** | C++ kernel only (`climate.cpp`). No Python fallback (`_py_not_implemented`). No Numba twin. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-002. |
| **reference_cases** | See CANON-002 / `FAO56_REFERENCE_DAY`. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_climate_unit.cpp` — C++ unit test (NOT run; no compiler). |
| **analytical_tests** | FAO-56 reference day (if C++ test could run). |
| **numerical_tests** | Not executable (no compiler). |
| **physical_consistency_tests** | Not executable. |
| **empirical_validation** | Not locally calibrated. See CANON-002. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not measurable — no Python fallback to test against. |
| **known_limitations** | (1) Exposed natively with no Python fallback — cannot be parity-tested. (2) C++ unit test exists but NOT run (no compiler). (3) Scientific review pending for non-temperate regions. (4) See CANON-002 for full limitations. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/climate.cpp`. Bridge: `engine/hydroma/cpp_bridge/__init__.py` (no fallback). |
| **verification_status** | Cannot verify at runtime — the bridge exposes this symbol with no Python fallback, so no C++/Python parity check exists for it. The "no compiler to rebuild" claim recorded for this line is stale for this host, where `engine.hydroma.cpp_bridge.backend_status()` reports `{'backend': 'cpp', 'cpp_available': True}` (the prebuilt extension loads; the toolchain is never invoked, so it is not rebuilt). The FAO-56 eq. 52 comparison run by the validation corpus checks the equation, not this kernel. |
| **validation_status** | Pending scientific review (see CANON-002). |
| **provenance** | `data_source: "simulated"`; `model: "Hargreaves ET0 C++ v1.0"`; `computed: True` |
