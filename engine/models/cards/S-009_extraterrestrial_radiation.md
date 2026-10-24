# Model Card: S-009 — Extraterrestrial Radiation (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-009` |
| **name** | Extraterrestrial Radiation (C++ Symbol) |
| **version** | `1.0.0` |
| **scientific_domain** | Meteorology / Solar Radiation |
| **intended_use** | C++ kernel exposing FAO-56 eq. 21 extraterrestrial radiation (see CANON-011 for full description). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | See CANON-011. Ra = (24×60/π) × Gsc × dr × [ws·sin φ·sin δ + cos φ·cos δ·sin ws], Gsc = 0.082 MJ/m²/day. |
| **equation_conventions** | See CANON-011. Latitude in degrees, converted to radians. DOY 1–365. |
| **assumptions** | Same as CANON-011. |
| **applicability_domain** | Same as CANON-011. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `lat_deg` (float, −90..90), `doy` (int, 1..365) |
| **output_schema** | `ra` (float, MJ/m²/day, ≥0) |
| **units** | Latitude in degrees, Ra in MJ/m²/day. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation. |
| **solver_configuration** | C++ kernel (`climate.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-011. FAO-56 eq. 21; Haurwitz (1942). |
| **reference_cases** | See CANON-011 / `fao56_ra_extremes()`. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_climate_unit.cpp` (NOT run; no compiler). |
| **analytical_tests** | Not executable (no Python fallback). |
| **numerical_tests** | Not executable. |
| **physical_consistency_tests** | Not executable. |
| **empirical_validation** | Not executable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not measurable — no Python comparison path. |
| **known_limitations** | (1) No Python fallback — cannot parity-test. (2) C++ unit test not run. (3) See CANON-011 for scientific limitations. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/climate.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "Extraterrestrial Radiation C++ v1.0"`; `computed: True` |

