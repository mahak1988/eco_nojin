# ECO-01 Unknown and Conflicts

**Document ID:** ECO-01-24-UNKNOWN-AND-CONFLICTS  
**Scope:** engine/ + services/ unknown elements and conflicts  
**Purpose:** Catalog all unknowns, conflicts, and uncertain findings

---

## 1. Critical Unknowns

These are unknowns that materially affect confidence in the analysis:

| Unknown ID | Description | Location | Impact | Status |
|-----------|-------------|----------|--------|--------|
| UNKNOWN-001 | Scientific methodology for Soil Salinity model | engine/hydroma/soil/salinity.py | HIGH | Documented equation missing |
| UNKNOWN-002 | Data assimilation weighting methodology | engine/hydroma/climate/assimilation.py | HIGH | Weights undocumented |
| UNKNOWN-003 | Theis well function convergence bounds | engine/hydoma/models/groundwater_model.py | HIGH | Numerical stability risk |
| UNKNOWN-004 | Input uncertainty for any scientific model | All models | HIGH | No uncertainty propagation |
| UNKNOWN-005 | Soil parameter sources for lookup tables | engine/hydoma/soil/ | MEDIUM | Parameters may be hard-coded |
| UNKNOWN-006 | Radiation albedo source/justification | engine/hydoma/climate/radiation.py | MEDIUM | Fixed at 0.23 |
| UNKNOWN-007 | RUSLE LS factor computation details | engine/hydoma/soil/erosion.py | MEDIUM | Method undocumented |
| UNKNOWN-008 | Climate projection method details | engine/hydoma/scenarios/climate_scenarios.py | MEDIUM | Simplified IPCC |
| UNKNOWN-009 | Crop coefficient curves exact source | engine/hydoma/agriculture/crop_coefficient.py | MEDIUM | Assumed FAO-56 |
| UNKNOWN-010 | EPIA decision logic internals | engine/hydoma/models/epia.py | LOW | Composite, partially documented |

---

## 2. Scientific Conflicts

### CONFLICT-001: Salinity Model vs. FAO Standards

| Field | Value |
|-------|-------|
| **conflict_id** | CONFLICT-001 |
| **description** | Soil salinity model uses undocumented equations that may not match FAO-56 salinity standards |
| **location** | engine/hydoma/soil/salinity.py:12-98 |
| **reference_standard** | FAO-56 Irrigation and Drainage Paper 29 (Salinity) |
| **current_implementation** | classify_salinity, calculate_leaching_requirement |
| **documented_equation** | Not clearly documented in code |
| **conflict_type** | EQUATION_IMPLEMENTATION_MISMATCH |
| **confidence** | MEDIUM |
| **impact** | Salinity classification and leaching requirements may be incorrect |
| **recommendation** | REQUIRES_SCIENTIFIC_REVIEW (P0) |
| **evidence** | No scientific references in salinity.py |

### CONFLICT-002: Climate Data Assimilation Weights

| Field | Value |
|-------|-------|
| **conflict_id** | CONFLICT-002 |
| **description** | Weights for combining climate data sources are undocumented |
| **location** | engine/hydoma/climate/assimilation.py |
| **reference_standard** | Best practice: accuracy-weighted ensemble |
| **current_implementation** | Weighted average (weights not documented) |
| **conflict_type** | ASSUMPTION_UNDOCUMENTED |
| **confidence** | HIGH (the weights exist but undocumented) |
| **impact** | Systematic bias in all climate-driven calculations |
| **recommendation** | REQUIRES_SCIENTIFIC_REVIEW (P0) |
| **evidence** | No methodology documentation; no validation |

### CONFLICT-003: Theis Well Function Series

| Field | Value |
|-------|-------|
| **conflict_id** | CONFLICT-003 |
| **description** | Series expansion for W(u) may not converge for small u values |
| **location** | engine/hydoma/models/groundwater_model.py:134-170 |
| **reference_standard** | Hantush (1964) well function approximations |
| **current_implementation** | Series expansion with unknown truncation |
| **conflict_type** | NUMERICAL_METHOD_RISK |
| **confidence** | MEDIUM |
| **impact** | Groundwater drawdown may be calculated incorrectly near wells |
| **recommendation** | REQUIRES_SCIENTIFIC_REVIEW (P0) |
| **evidence** | No convergence check; no asymptotic fallback |

### CONFLICT-004: Radiation Albedo

| Field | Value |
|-------|-------|
| **conflict_id** | CONFLICT-004 |
| **description** | Radiation model hardcodes albedo at 0.23 without justification |
| **location** | engine/hydoma/climate/radiation.py |
| **reference_standard** | FAO-56 assumes albedo = 0.23 for reference crop |
| **current_implementation** | Hardcoded 0.23 |
| **conflict_type** | ASSUMPTION_HARDCODED |
| **confidence** | HIGH (matches FAO-56 reference crop, but not documented) |
| **impact** | Net radiation calculation assumes reference crop surface |
| **recommendation** | DOCUMENT ASSUMPTION, add surface type parameter |
| **evidence** | FAO-56 Allen et al. (1998) uses 0.23 for reference crop |

---

## 3. Unit Conflicts

### UNIT-CONFLICT-001: Salinity Units

| Field | Value |
|-------|-------|
| **conflict_id** | UNIT-CONFLICT-001 |
| **description** | Salinity units may mix dS/m and mmol/L |
| **location** | engine/hydoma/soil/salinity.py |
| **expected** | dS/m (standard for soil salinity) |
| **found** | Mixed references; unclear which unit input expects |
| **unit_status** | CONVERSION_REQUIRED |
| **confidence** | LOW |

### UNIT-CONFLICT-002: Carbon Units

| Field | Value |
|-------|-------|
| **conflict_id** | UNIT-CONFLICT-002 |
| **description** | Carbon stock conversion may use incorrect bulk density units |
| **location** | engine/hydoma/soil/carbon.py:56-134 |
| **expected** | Carbon stock in Mg C/ha |
| **found** | Bulk density in g/cm³ vs kg/m³ potentially mixed |
| **unit_status** | CONVERSION_REQUIRED |
| **confidence** | MEDIUM |

### UNIT-CONFLICT-003: Pressure Units

| Field | Value |
|-------|-------|
| **conflict_id** | UNIT-CONFLICT-003 |
| **description** | Soil water pressure may be in kPa or cm water head |
| **location** | engine/hydoma/soil/physics.py (Van Genuchten) |
| **expected** | kPa for Van Genuchten parameters |
| **found** | Potential mixing with cm (1 kPa = 10.2 cm) |
| **unit_status** | CONVERSION_REQUIRED |
| **confidence** | LOW |

---

## 4. Unknown Knowledge Types

### Missing Knowledge Representations

| Knowledge Type | Currently Represented | Gap |
|----------------|----------------------|-----|
| Local Knowledge | Not distinguished from scientific data | Need local knowledge entity with provenance |
| Traditional Knowledge | None | Need traditional knowledge entity |
| Expert Opinion | None | Need opinion model |
| Hypothesis | None | Need hypothesis tracking |
| Experimental Results | None | Need experiment result model |
| Inference | None | Need inference tracking |
| Evidence (in Daneshyar sense) | None | Need evidence classification |

### Undocumented Scientific References

| Model | Has References? | Location | Confidence |
|-------|-----------------|----------|------------|
| Penman-Monteith | YES | Documented in tests | HIGH |
| Hargreaves | YES | Documented in comments | HIGH |
| SCS-CN | YES | Documented in tests | HIGH |
| Darcy Flow | YES | Documented in docstring | HIGH |
| Theis Solution | YES | Documented | HIGH |
| Van Genuchten | YES | Documented | HIGH |
| Soil Salinity | NO | — | CONFLICT |
| RUSLE | YES | Documented | HIGH |
| Radiation | YES (partially) | Referenced FAO-56 | MEDIUM |
| Climate Assimilation | NO | — | UNKNOWN |
| Pump Curves | NO | — | UNKNOWN |
| Frequency Analysis | NO | — | UNKNOWN |
| Kalman Filter | No validation of method | — | UNKNOWN |
| Spatial Interpolation | No reference to standard methods | — | UNKNOWN |

---

## 5. Assumption Documentation

### Documented Assumptions

| Model | Assumption | Documented? | Location |
|-------|------------|-------------|----------|
| Penman-Monteith | Reference crop 0.12m, well-watered | YES | et_calculator.py:6-25 |
| SCS-CN | Homogeneous watershed | YES | runoff_model.py:15-20 |
| Darcy | Steady-state, laminar flow | YES | groundwater_model.py:12-18 |
| Van Genuchten | No hysteresis | YES | physics.py:45-50 |
| Theis | Confined aquifer, infinite extent | YES | groundwater_model.py:95-100 |
| RUSLE | Steady-state, annual average | YES | erosion.py:5-10 |
| Terrain Analysis | Planar within 3x3 window | YES | models.py:45-50 |

### Undocumented Assumptions

| Model | Undocumented Assumption | Risk |
|-------|------------------------|------|
| Climate Assimilation | Source reliability ranking | HIGH |
| Radiation | Clear-sky conditions | MEDIUM |
| Irrigation Scheduler | Safety factor value | MEDIUM |
| EPIA | Decision thresholds | MEDIUM |
| Water Demand | Effective precipitation method | MEDIUM |
| Soil Salinity | Method basis | HIGH |
| All models | Independence of parameters | MEDIUM |

---

## 6. Conflict Resolution Log

| Conflict | Resolution Status | Notes |
|----------|------------------|-------|
| CONFLICT-001 (Salinity) | UNRESOLVED | Requires scientific review |
| CONFLICT-002 (Assimilation) | UNRESOLVED | Requires climate scientist review |
| CONFLICT-003 (Theis) | UNRESOLVED | Requires hydrogeologist review |
| CONFLICT-004 (Albedo) | PARTIALLY RESOLVED | Assumption matches FAO-56; documentation needed |
| UNIT-CONFLICT-001 | UNRESOLVED | Need to verify salinity units |
| UNIT-CONFLICT-002 | UNRESOLVED | Need to verify carbon units |
| UNIT-CONFLICT-003 | UNRESOLVED | Need to verify pressure units |

---

## 7. Unknown Count by Severity

| Severity | Count |
|----------|-------|
| Critical (P0) | 4 |
| Important (P1) | 3 |
| Medium (P2) | 2 |
| Low (P3) | 1 |
| **Total** | **10** |

---

## 8. Unknown Count by Category

| Category | Count |
|----------|-------|
| Scientific Methodology | 4 |
| Parameter Sources | 2 |
| Unit Consistency | 3 |
| Algorithm Convergence | 1 |
| Assumption Documentation | 4 |
| Scientific References | 8 |
| Knowledge Type Representation | 7 |
| **Total Unknowns** | **10** |
| **Total Conflicts** | **7** |

---

## 9. Scientific Conflicts Impact Matrix

| Conflict | Affects ET0 | Affects Runoff | Affects Irrigation | Affects Watershed | Affects Carbon | Overall Risk |
|----------|------------|----------------|-------------------|-------------------|----------------|--------------|
| Salinity | NO | NO | YES | NO | NO | HIGH |
| Assimilation | YES | YES | YES | YES | NO | CRITICAL |
| Theis | NO | NO | YES | NO | NO | HIGH |
| Albedo | YES | NO | YES | NO | NO | MEDIUM |
| Unit (Salinity) | NO | NO | YES | NO | NO | HIGH |
| Unit (Carbon) | NO | NO | NO | NO | YES | MEDIUM |
| Unit (Pressure) | NO | NO | YES | NO | NO | HIGH |

---

## 10. Critical Unknown Details

### UNKNOWN-001: Soil Salinity Scientific Method

**Description:** The salinity.py file does not contain enough information to determine which scientific standard it implements.

**Evidence:**
- File exists: engine/hydoma/soil/salinity.py:12-98
- Imports: No scientific references in docstrings
- Functions: `classify_salinity(ec)`, `calculate_leaching_requirement(ec_soil, ec_water)`
- Tests: 2 test cases, but do not reference standard values

**Impact:** Cannot verify if salinity-based decisions are scientifically sound.

**Status:** UNKNOWN - requires hydrologist/soil scientist review

### UNKNOWN-002: Climate Data Assimilation Weights

**Description:** The assimilation.py file uses weighted averaging, but weights are not documented.

**Evidence:**
- File: engine/hydoma/climate/assimilation.py
- Contains: "weighted average" but no weight calculation
- No methodology reference

**Impact:** Potential systematic bias in all climate inputs.

**Status:** UNKNOWN - requires climate scientist review

### UNKNOWN-003: Theis Series Convergence

**Description:** The Well function series expansion has undocumented convergence behavior.

**Evidence:**
- File: engine/hydoma/models/groundwater_model.py:93-210
- Implementation: Series expansion of E₁(u)
- No convergence check, no truncation documentation

**Impact:** Potential numerical overflow for near-well calculations.

**Status:** UNKNOWN - requires numerical methods/hydrogeology review

---

*See also: 23-SCIENTIFIC-REVIEW-QUEUE.md, 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md, 25-RECOMMENDED-NEXT-PHASE.md*