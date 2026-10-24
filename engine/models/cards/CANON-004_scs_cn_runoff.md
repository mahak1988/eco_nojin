# Model Card: CANON-004 — SCS-CN Runoff

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-004` |
| **name** | SCS-CN Runoff (Soil Conservation Service Curve Number) |
| **version** | `1.0.0` |
| **scientific_domain** | Hydrology (Surface Runoff) |
| **intended_use** | Estimate direct runoff depth from rainfall excess using the NRCS Curve Number method. Supports both point-scale and spatial (raster) calculation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | SCS-CN method (USDA NRCS, SI form):<br>S = (25400 / CN) − 254  [mm]<br>Ia = 0.2 * S  [mm]<br>If P ≤ Ia: Q = 0<br>If P > Ia: Q = (P − Ia)² / (P + 0.8*S)  [mm]<br><br>Rational method (for peak flow estimation):<br>Qp = C * i * A<br>where i = P / duration [mm/hr], A in ha, Qp in m³/s = (C * i * A * 10) / 3600<br><br>The US-customary form S = (1000/CN) − 10 yields INCHES and must never be mixed with millimetre rainfall. |
| **equation_conventions** | All depths in millimetres (SI form). CN is dimensionless 30–100. Area in hectares. Peak flow converted to m³/s. The retention S and initial abstraction Ia are in mm when CN is used as given. |
| **assumptions** | (1) Homogeneous watershed of uniform CN. (2) Initial soil moisture condition is constant (SCS-CN does not explicitly model antecedent moisture). (3) Rainfall is uniform in space and time. (4) No snowmelt, no infiltration capacity variability. (5) Rational method assumes time of concentration ≥ storm duration. |
| **applicability_domain** | Pervious surfaces, agricultural and forested watersheds. CN range 30 (high infiltration) to 100 (impervious). Spatial version uses simplified land-use-to-CN lookup (4 classes: forest, pasture, urban, default). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `precipitation_mm` (float, mm, >0), `curve_number` (float, 30–100 or CurveNumberType enum), `area_ha` (float, ha, >0), `method` ("SCS-CN" or "Rational"), `storm_duration_h` (float, hours, 0.01–∞), `rational_coefficient` (float, 0–1) |
| **output_schema** | `volume_m3` (float, m³, ≥0), `peak_flow_m3s` (float, m³/s, ≥0 or None) |
| **units** | Precipitation in mm, area in ha, volume in m³, flow in m³/s, duration in hours. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — event-scale model. No initial state. |
| **boundary_conditions** | Not applicable — precipitation is a prescribed boundary input. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form analytical equation. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | USDA NRCS National Engineering Handbook, Part 630, Chapter 4 (1972). Technical Release 55 (TR-55): Urban Hydrology for Small Watersheds, Chapter 4 (1986). |
| **reference_cases** | NRCS SCS worked example: P=50 mm, CN=70 → S=108.857 mm, Ia=21.771 mm, Q=5.8128 mm. See `strict_tests/conftest.py:NRCS_SCS_CN_WORKED_EXAMPLE`. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s03_hydrology_runoff.py` — worked example, unit conversion (mm vs inches), independent rederivation, CN boundary values (30, 45, 60, 70, 78, 85, 95, 100), Rational method closed-form check. Also `tests/unit/test_scs_units_consistency.py`. |
| **analytical_tests** | NRCS worked example (Q=5.8128 mm for P=50, CN=70). |
| **numerical_tests** | Property-based testing over CN domain (30–100). |
| **physical_consistency_tests** | Q ≥ 0; Q = 0 when P ≤ Ia; S = 25400/CN − 254 (mm form); mm/inch forms differ by 25.4. |
| **empirical_validation** | Benchmarked against USDA SCS examples and TR-55 tables. Verified status per ECO-03.1. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on CN and P via property-based testing. No formal probabilistic UQ. |
| **known_limitations** | (1) CN has no lower bound enforcement — CN=0 raises ZeroDivisionError before the CN>100 guard. (2) Peak flow assumes uniform 1-hour storm; peak_flow_m3s divides volume by duration, conflating event volume with peak rate. (3) Spatial version uses a 4-way CN lookup, not NRCS TR-55 Table 2A (stub for CN mapping). (4) Soil texture argument in spatial CN map is accepted but never used. (5) Output filenames embed hash(dem_path) which is randomized per Python process — non-reproducible. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/models/runoff_model.py` (RunoffCalculator for point-scale, SpatialRunoffCalculator for raster). |
| **verification_status** | Verified — matches NRCS worked example to 1e-9 relative; mm/inch unit consistency pinned. |
| **validation_status** | Validated against USDA SCS/TR-55 examples. |
| **provenance** | `data_source: "simulated"`; `model: "SCS-CN / Rational (NRCS TR-55) v1.0"`; `computed: True` |
