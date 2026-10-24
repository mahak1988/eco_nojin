# Model Card: S-010 — FAO-56 Net Radiation (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-010` |
| **name** | FAO-56 Net Radiation |
| **version** | `1.0.0` |
| **scientific_domain** | Meteorology / Radiation |
| **intended_use** | C++ kernel exposing the FAO-56 net radiation calculation (Rn = Rns − Rnl), used as an intermediate component of the Penman-Monteith equation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | FAO-56 eqs. 20, 36–45:<br>Rns = (1 − α) × Rs  [mm/day equivalent or MJ/m²/day]<br>Rnl = 4.903e-9 × [(Tmax+273.16)⁴ + (Tmin+273.16)⁴] / 2 × (0.34 − 0.14×sqrt(ea)) × (1.35×(Rs/Rso) − 0.35)<br>Rn = Rns − Rnl<br>where α = 0.23 (dry soil albedo), Rs = solar radiation, Rso = clear-sky radiation, ea = actual vapour pressure, Tmax/Tmin in °C. |
| **equation_conventions** | Rnl in MJ/m²/day. 4.903e-9 converts K⁴ to MJ/m²/day. Rs/Rso clipped to [0.3, 1.0]. Rso = (0.75 + 2e-5×z) × Ra. |
| **assumptions** | (1) α = 0.23 (standard FAO-56 value). (2) Clear-sky transmissivity varies with elevation. (3) Night-time soil heat flux G ≈ 0 for daily step. |
| **applicability_domain** | Same as CANON-001 (Penman-Monteith). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `tmin` (°C), `tmax` (°C), `ea` (kPa), `rs` (MJ/m²/day), `elevation_m` (m), `lat_deg` (degrees), `doy` (int) |
| **output_schema** | `rn` (MJ/m²/day), `rns` (MJ/m²/day), `rnl` (MJ/m²/day) |
| **units** | Radiation in MJ/m²/day, temperature in °C, elevation in m. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of closed-form equations. |
| **solver_configuration** | C++ kernel (`climate.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | FAO-56 eqs. 20, 36–45. Allen et al. (1998). |
| **reference_cases** | FAO-56 worked example. |

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
| **known_limitations** | (1) No Python fallback. (2) C++ unit test not run. (3) Cloudiness factor clipping must match CANON-001. (4) Tmax/Tmin in the Stefan-Boltzmann calculation use +273.16 (not 273) — this differs from the PM temperature conversion constant, as per FAO-56 eq. 20 (absolute zero reference). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/climate.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "FAO-56 Net Radiation C++ v1.0"`; `computed: True` |

