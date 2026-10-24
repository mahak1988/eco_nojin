# Model Card: CANON-003 — Thornthwaite Potential Evapotranspiration

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-003` |
| **name** | Thornthwaite Potential Evapotravascriptranspiration |
| **version** | `1.0.0` |
| **scientific_domain** | Evapotranspiration |
| **intended_use** | Estimate potential evapotranspiration (PET) using only temperature and latitude. Used for climate classification, water balance estimation, and climate change impact studies where meteorological data is limited. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Thornthwaite (1948):<br>PET = 1.6 * (10 * T / I)^a * (daylight_hours / 12) * (L / 12)<br>where T = mean monthly temperature (°C), I = annual heat index = Σ(T_month/5)^1.514, L = day length (hours) at the month's midpoint, a = exponent = (0.492 + 0.403 * ln(I) + 0.068 * ln(I)²) / 100 for I > 0.<br>Monthly PET is scaled to daily by dividing by days in the month. Units: PET in cm/month, converted to mm/day. |
| **equation_conventions** | PET computed on a monthly basis. Negative or zero temperatures contribute 0 to the heat index. If I = 0 (all months ≤ 0°C), PET = 0 and 'a' is undefined. T in °C, PET in cm/month. |
| **assumptions** | (1) Reference surface is a hypothetical "climatic climax" grass. (2) No explicit radiation term — solar radiation is implicitly estimated via temperature. (3) No wind or humidity dependence. (4) Steady-state monthly equilibrium. |
| **applicability_domain** | Originally developed for temperate grasslands. Valid for −40° to 40° latitude. Best suited for climate classification (Thornthwaite classification) and long-term water balance studies. Not recommended for daily ET estimation or irrigated agriculture. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | Monthly `tmean` (list of 12 floats, °C, −50..50), `latitude` (float, degrees, −90..90), `days_in_month` (list of 12 ints). |
| **output_schema** | `pet_monthly` (array of 12 floats, mm/day), `pet_annual` (float, mm/year) |
| **units** | Temperature in °C, latitude in degrees, PET in mm/day (monthly average) or mm/year (annual). |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — diagnostic model, no state variables. |
| **boundary_conditions** | Not applicable — temperature and latitude are boundary inputs, not boundary-value conditions. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form analytical equation with precomputed heat index. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Thornthwaite, C.W. (1948). "An Interannual Water Balance Climate Model." *Proceedings of the American Philosophical Society* 92(2): 203–224. Also: Thornthwaite, C.W., Mather, J.R. (1946). "The Water Balance." *Drought and Conservation* 8: 263–284. |
| **reference_cases** | No external reference case data available in conftest.py. No known benchmark examples in the strict test suite. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s02_climate_et0.py` (alt) — partial coverage via climate test suite. No dedicated test file. |
| **analytical_tests** | None — no analytical reference case in the repository. |
| **numerical_tests** | None. |
| **physical_consistency_tests** | PET ≥ 0 for valid inputs. Heat index I ≥ 0. |
| **empirical_validation** | Not validated against local data. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity analysis recommended but not implemented. |
| **known_limitations** | (1) Scientific status: SCIENTIFICALLY_SUPPORTED — theoretical basis exists but no benchmarking. (2) No reference data in conftest.py. (3) Known to underestimate PET in arid climates and overestimate in humid climates due to the lack of wind and humidity terms. (4) The exponent 'a' diverges for very low heat index values. (5) Not suitable for irrigation scheduling. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — referenced in `engine/hydroma/climate/et_calculator.py` and ECO-03.1. |
| **verification_status** | Implementation exists; scientific review pending. |
| **validation_status** | Scientifically supported but not benchmarked against empirical data. |
| **provenance** | `data_source: "simulated"`; `model: "Thornthwaite PET v1.0"`; `computed: True` |
