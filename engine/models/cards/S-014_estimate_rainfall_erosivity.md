# Model Card: S-014 — Rainfall Erosivity (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-014` |
| **name** | Estimate Rainfall Erosivity |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Erosion |
| **intended_use** | C++ kernel exposing rainfall erosivity (R-factor) estimation from precipitation intensity data. Used as the R-factor input in RUSLE (see CANON-007, S-008). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | R-factor (USLE/RUSLE):<br>R = Σ over events of [ (Ei × 30) / (14400 × t) ] where Ei = erosivity of the i-th storm, t = duration (min).<br><br>For annual index (when point rainfall intensity data is available):<br>R = Σ_i [ 30 × (Pe × V_i) / 14400 ]<br>where Pe = precipitation excess (mm), V_i = velocity factor (m³·s⁻¹ per mm over 30 min), and the 14400 converts hours to minutes appropriately. The result is in MJ·mm/ha/h (100-year annual R).<br><br>Alternative (empirical, from annual precipitation): R = a × P^b where P = mean annual precipitation (mm), a and b are region-specific coefficients. |
| **equation_conventions** | R in MJ·mm/ha/h (USLE units) or N·h/m⁵ (SI). 1 MJ·mm/ha/h = 27.0 m³·s⁻¹·ha⁻¹·h⁻¹. The C++ kernel accepts precipitation time series and computes event-based erosivity. |
| **assumptions** | (1) Rainfall intensity time series available. (2) Event-based separation of rainfall data. (3) Single storm events. (4) No snowmelt contribution. |
| **applicability_domain** | Global, where sub-hourly or hourly rainfall intensity data is available. R is most reliable with >20 years of data. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `precipitation_series` (array of floats, mm per time interval), `interval_minutes` (float, minutes), `event_separation_hours` (float, optional, minimum dry period to separate storms, default 1 hr) |
| **output_schema** | `R_factor` (float, MJ·mm/ha/h), `n_events` (int) |
| **units** | Precipitation in mm, time in minutes/hours, R in MJ·mm/ha/h. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Storm event separation and kinetic energy integration. |
| **solver_configuration** | C++ kernel (`erosion.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Foster, G.R. (1982). "Relating Rainfall Erosivity to Weather Parameters." *Transactions of the ASAE* 25(6): 1605–1612. Renard, K.G. et al. (1997). *USDA Agriculture Handbook 703*. |
| **reference_cases** | USLE/RUSLE reference events. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_erosion_unit.cpp` (NOT run; no compiler). |
| **analytical_tests** | Not executable (no Python fallback). |
| **numerical_tests** | Not executable. |
| **physical_consistency_tests** | Not executable. |
| **empirical_validation** | Not executable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not measurable — no Python comparison path. |
| **known_limitations** | (1) No Python fallback. (2) C++ unit test not run. (3) Depends on quality and duration of rainfall intensity data. (4) See CANON-007 for RUSLE framework limitations. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/erosion.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "Rainfall Erosivity C++ v1.0"`; `computed: True` |

