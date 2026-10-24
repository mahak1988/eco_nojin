# ECO-01 Scientific Review Queue

**Document ID:** ECO-01-23-SCIENTIFIC-REVIEW-QUEUE  
**Scope:** engine/ + services/ scientific models requiring review  
**Purpose:** Prioritize and document models that require specialist scientific review

---

## 1. Priority Legend

| Priority | Definition |
|----------|-----------|
| P0 | Could invalidate important downstream results if incorrect |
| P1 | Important scientific uncertainty; affects major calculations |
| P2 | Important quality/validation gap; limits reliability |
| P3 | Improvement opportunity; nice to have |

---

## 2. Review Queue

### P0 - Critical Review Required

#### REVIEW-REQ-001: Theis Well Function

| Field | Value |
|-------|-------|
| **priority** | P0 |
| **model** | Theis Transient Groundwater Flow Solution |
| **location** | engine/hydra/models/groundwater_model.py:93-210 |
| **issue** | Well function series expansion convergence for small u (near-well, early time) |
| **impact** | Drawdown calculations may overflow or diverge, producing incorrect groundwater results that propagate to irrigation scheduling |
| **specific concern** | W(u) series convergence: for u→0, terms grow; need asymptotic approximation or error function |
| **required_analysis** | 1. Verify series convergence bounds against standard tables (Hantush, 1964) 2. Implement u threshold with fallback to exponential integral approximation 3. Add numerical error bounds |
| **assign_to** | Hydrogeologist |
| **deadline_priority** | Before any groundwater-dependent decision |

---

#### REVIEW-REQ-002: Climate Data Assimilation Weights

| Field | Value |
|-------|-------|
| **priority** | P0 |
| **model** | Climate Data Assimilation Pipeline |
| **location** | engine/hydra/climate/assimilation.py |
| **issue** | No documentation of source weighting methodology; weights may be arbitrary |
| **impact** | All downstream calculations (ET0, water demand, irrigation) affected by potentially biased climate inputs |
| **specific concern** | If weather station data is weighted equal to satellite estimates without accuracy consideration, results will be systematically biased |
| **required_analysis** | 1. Document weight assignment methodology 2. Verify weights align with data source accuracy 3. Implement uncertainty propagation from source weights |
| **assign_to** | Meteorologist / Climate Scientist |
| **deadline_priority** | Before climate-dependent calculations used in decisions |

---

#### REVIEW-REQ-003: Soil Salinity Model

| Field | Value |
|-------|-------|
| **priority** | P0 |
| **model** | Soil Salinity Model |
| **location** | engine/hydra/soil/salinity.py |
| **issue** | No documented scientific basis; equations appear empirical with no standard reference |
| **impact** | Salinity-based crop restrictions and irrigation water quality assessments may be incorrect |
| **specific_concern** | Without knowing the method, cannot verify if it matches FAO-56, Richards equation, or other standard approaches |
| **required_analysis** | 1. Document all equations and their sources 2. Verify against FAO-56 salinity methods 3. Compare with USDA ARS salinity methods |
| **assign_to** | Soil Scientist (salinity specialist) |
| **deadline_priority** | Before soil salinity affects irrigation decisions |

---

### P1 - Important Review Required

#### REVIEW-REQ-004: Radiation Model Albedo Assumption

| Field | Value |
|-------|-------|
| **priority** | P1 |
| **model** | Solar Radiation Model |
| **location** | engine/hydra/climate/radiation.py |
| **issue** | Albedo hardcoded at 0.23 without user override or surface-type consideration |
| **impact** | Net radiation and ET0 calculations may have systematic bias depending on surface type |
| **specific_concern** | Reference crop albedo is 0.23, but actual surfaces vary (water: 0.06, forest: 0.15, urban: 0.20-0.40) |
| **required_analysis** | 1. Verify albedo is appropriate for reference crop context 2. Consider surface-type-specific albedo 3. Document assumptions clearly |
| **assign_to** | Agronomist / Climatologist |
| **deadline_priority** | Before radiation feeds into ET0 |

---

#### REVIEW-REQ-005: Van Genuchten Newton-Raphson Solver

| Field | Value |
|-------|-------|
| **priority** | P1 |
| **model** | Van Genuchten Inverse Solver |
| **location** | engine/hydra/soil/physics.py:89-167 |
| **issue** | Newton-Raphson convergence behavior undocumented; edge cases at n=1 or psi=0 |
| **impact** | Soil moisture calculations may fail unexpectedly for certain soil types |
| **specific_concern** | m = 1 - 1/n → 0 as n→1; division by zero possible; initial guess may be poor for extreme psi |
| **required_analysis** | 1. Test convergence for various soil types 2. Document failure modes 3. Add fallback solver for divergent cases |
| **assign_to** | Soil Physicist |
| **deadline_priority** | Before soil moisture used in irrigation scheduling |

---

#### REVIEW-REQ-006: RUSLE LS Factor Computation

| Field | Value |
|-------|-------|
| **priority** | P1 |
| **model** | RUSLE Soil Erosion |
| **location** | engine/hydra/soil/erosion.py |
| **issue** | LS factor computation method not documented; may not follow standard RUSLE2 or Renard methodology |
| **impact** | Erosion estimates may be inaccurate depending on slope length algorithm |
| **specific_concern** | RUSLE LS factor has specific formula: (λ/22.13)^m × (65.41×sin(θ) + 4.56×sin(θ)^0.35) for slope in degrees; verify implementation |
| **required_analysis** | 1. Document LS factor formula exactly as implemented 2. Compare with RUSLE2 documentation 3. Validate against known watershed data |
| **assign_to** | Soil Scientist / Erosion Specialist |
| **deadline_priority** | Before erosion used in design |

---

### P2 - Quality/Validation Gap

#### REVIEW-REQ-007: Pump Curve Analysis

| Field | Value |
|-------|-------|
| **priority** | P2 |
| **model** | Pump Curve Analysis |
| **location** | engine/hydra/hydraulics/pump.py |
| **issue** | No validation against manufacturer curves; iteration method may converge to wrong solution |
| **impact** | Pump selection may produce suboptimal or non-physical results |
| **specific_concern** | Quadratic pump curve fitting; operating point calculation; no handling of variable speed pumps |
| **required_analysis** | 1. Validate against manufacturer catalog curves 2. Test with known pump curves 3. Document convergence behavior |
| **assign_to** | Hydraulic Engineer |
| **deadline_priority** | Before pump design used |

---

#### REVIEW-REQ-008: Reservoir Pool Routing

| Field | Value |
|-------|-------|
| **priority** | P2 |
| **model** | Reservoir Pool Routing (Modified Puls) |
| **location** | engine/hydra/reservoir/pool_routing.py |
| **issue** | No validation against standard routing examples; storage-outflow curve fitting not documented |
| **impact** | Flood routing results may have significant errors |
| **specific_concern** | Modified Puls method requires monotonically increasing storage-outflow relationship; non-monotonic curves can cause instability |
| **required_analysis** | 1. Validate against textbook examples 2. Test stability for various inflow hydrographs 3. Document storage curve requirements |
| **assign_to** | Hydrologist / Hydraulic Engineer |
| **deadline_priority** | Before flood routing used |

---

#### REVIEW-REQ-009: Frequency Analysis

| Field | Value |
|-------|-------|
| **priority** | P2 |
| **model** | Log-Pearson Type III Frequency Analysis |
| **location** | engine/hydra/flood/frequency.py |
| **issue** | Frequency factor method implementation not verified against USGS guidance |
| **impact** | Flood frequency estimates may be inaccurate |
| **specific_concern** | LPIII requires specific frequency factor tables based on skewness; verify coefficient computation |
| **required_analysis** | 1. Verify frequency factors against USGS Bulletin 17C 2. Test against known flood data 3. Document skewness treatment |
| **assign_to** | Hydrologist |
| **deadline_priority** | Before flood design |

---

### P3 - Improvement Opportunities

#### REVIEW-REQ-010: Kalman Filter Implementation

| Field | Value |
|-------|-------|
| **priority** | P3 |
| **model** | Kalman Filter |
| **location** | engine/hydra/analysis/kalman.py |
| **issue** | Linear Kalman filter; no handling of non-linear systems (Extended/Unscented Kalman) |
| **impact** | Limited applicability for non-linear hydrological processes |
| **specific_concern** | Standard Kalman filter assumes linear system; hydrology is often non-linear |
| **required_analysis** | 1. Document applicability conditions 2. Consider EKF/UKF for non-linear cases |
| **assign_to** | Data Assimilation Specialist |
| **deadline_priority** | Future enhancement |

---

#### REVIEW-REQ-011: Spatial Interpolation Methods

| Field | Value |
|-------|-------|
| **priority** | P3 |
| **model** | Spatial Interpolation |
| **location** | engine/land/interpolation.py |
| **issue** | IDW and Kriging implementations not validated against standard GIS tools |
| **impact** | Interpolated surfaces may have artifacts |
| **specific_concern** | IDW power parameter selection; Kriging variogram model; edge effects |
| **required_analysis** | 1. Benchmark against ArcGIS/QGIS 2. Validate with cross-validation 3. Document parameter defaults |
| **assign_to** | GIS Specialist |
| **deadline_priority** | Before spatial interpolation used for decisions |

---

## 3. Review Queue Summary

| Priority | Count | Total Time Estimate |
|----------|-------|---------------------|
| P0 | 3 | 3-5 days |
| P1 | 3 | 2-3 days |
| P2 | 3 | 1-2 days each |
| P3 | 2 | 1-2 days each |

---

## 4. Review Queue Detail

### Complete Review Queue Table

| ID | Model | Priority | Issue | Location | Confidence Required |
|----|-------|----------|-------|----------|---------------------|
| REVIEW-001 | Theis Solution | P0 | Series convergence | groundwater_model.py:93 | Hydrogeologist |
| REVIEW-002 | Climate Assimilation | P0 | Weighting methodology | assimilation.py | Climate Scientist |
| REVIEW-003 | Soil Salinity | P0 | No scientific basis | salinity.py | Soil Scientist |
| REVIEW-004 | Radiation Model | P1 | Albedo assumption | radiation.py | Agronomist |
| REVIEW-005 | Van Genuchten | P1 | Newton-Raphson solver | physics.py:89 | Soil Physicist |
| REVIEW-006 | RUSLE | P1 | LS factor method | erosion.py | Erosion Specialist |
| REVIEW-007 | Pump Curves | P2 | Validation | pump.py | Hydraulic Engineer |
| REVIEW-008 | Pool Routing | P2 | Modified Puls stability | pool_routing.py | Hydrologist |
| REVIEW-009 | Frequency Analysis | P2 | LPIII factors | frequency.py | Hydrologist |
| REVIEW-010 | Kalman Filter | P3 | Linear assumption | kalman.py | Data Assimilation |
| REVIEW-011 | Interpolation | P3 | IDW/Kriging validation | interpolation.py | GIS Specialist |

---

## 5. Review Process

### 5.1 Review Steps

1. **Document** - Extract all equations and parameters
2. **Compare** - Compare with standard reference
3. **Validate** - Test against standard examples
4. **Assess** - Determine impact on downstream models
5. **Recommend** - Update, deprecate, or validate
6. **Document in registry** - Update scientific status

### 5.2 Evidence Requirements

| Evidence Type | Required For |
|--------------|--------------|
| Published reference | All review items |
| Standard test cases | P0, P1 items |
| Validation dataset | P1, P2 items |
| Error bounds | P0 items |
| Convergence analysis | P0, P1 items |

---

## 6. Downstream Impact Analysis

### REVIEW-001 (Theis) → Downstream Impact
- Irrigation scheduling (groundwater pumping)
- Water balance (groundwater contribution)
- Watershed design (baseflow)

### REVIEW-002 (Assimilation) → Downstream Impact
- ALL climate-dependent models
- ET0 calculations
- Water demand estimation
- Irrigation scheduling

### REVIEW-003 (Salinity) → Downstream Impact
- Irrigation water quality
- Crop salt tolerance
- Soil management recommendations

---

## 7. Tracking Template

Each review should produce an entry in the following format:

```
REVIEW-COMPLETE-XXX: Model Name
Date: YYYY-MM-DD
Reviewer: [Name, Role]
Findings: [Summary]
Comparison: [Reference vs. implementation]
Validation: [Test results]
Impact: [Downstream effects]
Status Change: [Old status → New status]
Recommendation: [CANONICALIZE / VALIDATE / REJECT]
```

---

*See also: 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md, 24-UNKNOWN-AND-CONFLICTS.md*