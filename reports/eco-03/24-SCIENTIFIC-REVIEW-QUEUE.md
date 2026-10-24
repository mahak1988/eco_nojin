# ECO-03: Scientific Review Queue — Report 24
## Items Requiring Scientific Peer Review

---

## Executive Summary

This report catalogs all items that require external scientific review before they can be used for decisions or canonized as canonical models.

---

## 1. Review Queue

| Queue ID | Priority | item_id | item_name | domain | reason | status | evidence | reviewer | deadline |
|----------|----------|---------|-----------|--------|--------|--------|----------|----------|----------|
| Q-001 | P0 | CANON-005 | Theis Solution | Hydrogeology | Series convergence undocumented; implementation may diverge for early time steps | REQUIRES_SCIENTIFIC_REVIEW | ECO-01/20 §CANON-005: "series convergence undocumented"; ECO-01/23 §P0 | Hydrogeology expert | Before ECO-04.4 |
| Q-002 | P0 | CANON-0XX | Climate Data Assimilation | Meteorology | Data assimilation weights undocumented; convergence not verified | REQUIRES_SCIENTIFIC_REVIEW | ECO-01 §119: "Climate Data Assimilation - Issues found" | Climate scientist | Before ECO-04.4 |
| Q-003 | P1 | CANON-0XX | Soil Salinity Model | Soil Science | No documented scientific basis; marked NOT_RECOMMENDED in ECO-01 | REQUIRES_SCIENTIFIC_REVIEW | ECO-01/20 §449: "Soil Salinity Model - No documented scientific basis" | Soil scientist | Before ECO-04.4 |
| Q-004 | P1 | CANON-007 | RUSLE LS Factor | Soil Science | Local LS factor calculation methods not validated | REQUIRES_SCIENTIFIC_REVIEW | ECO-01 §180: "RUSLE LS factor - REQUIRES REVIEW" | Erosion modeler | Before ECO-04.5 |
| Q-005 | P1 | CANON-014 | Model Registry | Governance | Coupled to services/api_gateway; must be isolated | REQUIRES_ENGINEERING_REVIEW | ECO-01/20 §346: "legacy_coupling: HIGH" | Platform team | Before ECO-04.5 |
| Q-006 | P1 | CANON-015 | Watershed Calculator | Hydrology | Coupled to services; must be isolated | REQUIRES_ENGINEERING_REVIEW | ECO-01/20 §364: "legacy_coupling: Low (some service imports)" | Platform team | Before ECO-04.5 |
| Q-007 | P1 | CANON-016 | C++ Climate Kernels | Numerical | Build system coupling; dual build dirs | REQUIRES_ENGINEERING_REVIEW | ECO-01/20 §388: "legacy_coupling: Moderate (cpp_bridge coupling)" | Engine team | Before ECO-04.5 |
| Q-008 | P2 | CANON-002 | Hargreaves ET0 | Climate | Validate against local Iranian weather station data | REQUIRES_VALIDATION | ECO-01 §113: "Hargreaves ET0 - VERIFIED" but local validation needed | Meteorologist | Before ECO-04.6 |
| Q-009 | P2 | CANON-020 | MODIS ET | Remote Sensing | Validate cloud cover contamination handling | REQUIRES_VALIDATION | ECO-01 §119: "MODIS ET - VERIFIED" | Remote sensing expert | Before ECO-04.6 |
| Q-010 | P2 | CANON-021 | Landsat | Remote Sensing | Validate spatial resolution for Iranian terrain | REQUIRES_VALIDATION | ECO-01 §119: "Landsat - VERIFIED" | Remote sensing expert | Before ECO-04.6 |
| Q-011 | P2 | CANON-010 | Water Balance | Engineering | Validate steady-state assumption for Iran conditions | REQUIRES_VALIDATION | ECO-01 §115: "Water Balance - Verified" | Water resources engineer | Before ECO-04.6 |
| Q-012 | P3 | CANON-003 | Thornthwaite PET | Climate | Validate applicability in arid climates | REQUIRES_VALIDATION | ECO-01 §113: "Thornthwaite PET - SCIENTIFICALLY_SUPPORTED" | Climatologist | After ECO-04 |
| Q-013 | P3 | CANON-011 | Solar Radiation | Climate | Validate atmospheric correction for Iran altitude | REQUIRES_VALIDATION | ECO-01 §119: "Radiation - Partially verified" | Solar radiation expert | After ECO-04 |

---

## 2. Review Process

### 2.1 Evidence Collection
1. Identify all implementations of the model
2. Document parameter constraints
3. List validation tests passed/failed
4. Gather observational data for comparison

### 2.2 Peer Review
1. Minimum 2 independent reviewers
2. Review must be documented
3. Review must include:
   - Method evaluation
   - Data adequacy assessment
   - Limitations identified
   - Recommendations for improvement

### 2.3 Decision
1. Review committee evaluates evidence
2. Decision: APPROVE / REQUEST_REVISIONS / REJECT
3. Decision documented with timestamp and reviewers

### 2.4 Integration
1. Approved models added to canonical registry
2. Review results stored in provenance
3. Model confidence updated

---

## 3. Review Priority Matrix

| Priority | Meaning | Count | Items |
|----------|---------|-------|-------|
| P0 | Blocks canonization | 2 | CANON-005 (Theis), Climate Data Assimilation |
| P1 | Affects accuracy/safety | 5 | Soil Salinity, RUSLE LS, Model Registry, Watershed Calculator, C++ Kernels |
| P2 | Affects local accuracy | 4 | Hargreaves, MODIS ET, Landsat, Water Balance |
| P3 | Improvement opportunity | 2 | Thornthwaite PET, Solar Radiation |

---

## 4. Review Status by Model

| CANON ID | Model | Review Required | Status | Reason |
|----------|-------|-----------------|--------|--------|
| CANON-001 | Penman-Monteith ET0 | NO | VERIFIED | Benchmarked against FAO examples |
| CANON-002 | Hargreaves ET0 | YES (P2) | REQUIRES_VALIDATION | Needs local validation |
| CANON-003 | Thornthwaite PET | YES (P3) | REQUIRES_VALIDATION | Arid climate applicability |
| CANON-004 | SCS-CN Runoff | NO | VERIFIED | Benchmarked against examples |
| CANON-005 | Theis Solution | YES (P0) | REQUIRES_SCIENTIFIC_REVIEW | Series convergence |
| CANON-006 | Van Genuchten | NO | VERIFIED | Benchmarked against parameters |
| CANON-007 | RUSLE Erosion | YES (P1) | REQUIRES_SCIENTIFIC_REVIEW | LS factor validation |
| CANON-008 | D8 Flow Direction | NO | VERIFIED | Benchmarked against standard |
| CANON-009 | Terrain Analysis | NO | VERIFIED | Benchmarked against tests |
| CANON-010 | Water Balance | YES (P2) | REQUIRES_VALIDATION | Steady-state assumption |
| CANON-011 | Solar Radiation | YES (P3) | REQUIRES_VALIDATION | Atmospheric correction |
| CANON-012 | Formula Catalog | NO | VERIFIED | Implementation verified |
| CANON-013 | Provenance Tracking | NO | VERIFIED | Implementation verified |
| CANON-014 | Model Registry | YES (P1) | REQUIRES_ENGINEERING_REVIEW | Service coupling |
| CANON-015 | Watershed Calculator | YES (P1) | REQUIRES_ENGINEERING_REVIEW | Service coupling |
| CANON-016 | C++ Climate Kernels | YES (P1) | REQUIRES_ENGINEERING_REVIEW | Build system |
| CANON-017 | C++ Soil Kernels | YES (P1) | REQUIRES_ENGINEERING_REVIEW | Build system |
| CANON-018 | CMIP6 Climate | YES (P0) | REQUIRES_SCIENTIFIC_REVIEW | Data assimilation |
| CANON-019 | GPM IMERG | NO | VERIFIED | Benchmarked |
| CANON-020 | MODIS ET | YES (P2) | REQUIRES_VALIDATION | Cloud contamination |
| CANON-021 | Landsat | YES (P2) | REQUIRES_VALIDATION | Resolution for terrain |
| CANON-022 | Sentinel-2 | NO | VERIFIED | Benchmarked |

---

## 5. Review Deadlines

| Milestone | Deadline | Review Items Due |
|-----------|----------|-----------------|
| ECO-04.4 Start | After blocking issues resolved | P0 items (Theis, Climate Data Assimilation) |
| ECO-04.5 Start | After Hydroma extraction | P1 items (Soil Salinity, RUSLE, Model Registry, Watershed, C++ Kernels) |
| ECO-04.6 Start | After Evidence/Knowledge engines | P2 items (Hargreaves, MODIS, Landsat, Water Balance) |
| Post-ECO-04 | Ongoing | P3 items (Thornthwaite, Solar Radiation) |

---

## 6. Scientific Review Committee

| Expert | Domain | Contact |
|--------|--------|---------|
| Hydrogeologist | Groundwater modeling | To be designated |
| Climatologist | Meteorology, ET0 | To be designated |
| Soil Scientist | Soil physics, erosion | To be designated |
| Remote Sensing Specialist | Satellite data processing | To be designated |
| Agricultural Engineer | Irrigation, crop modeling | To be designated |

---

## 7. Findings

1. **REQUIRES_SCIENTIFIC_REVIEW**: 13 of 22 models require some form of scientific review.

2. **BLOCKING**: 2 models (CANON-005 Theis, Climate Data Assimilation) are P0 and block canonization.

3. **CONFLICTING EVIDENCE**: ECO-02/03-SCIENTIFIC-MODEL-REGISTRY.md claims all 22 models classified with clear maturity levels. ECO-03 finds 13 models require review, contradicting the "VERIFIED" classification.

4. **NOT VERIFIED**: ECO-01/23-SCIENTIFIC-REVIEW-QUEUE.md claims "P0 items: 2 items, 50% resolved" — ECO-03 cannot verify this resolution status.

5. **BLOCKING**: Without scientific review completion, models cannot be trusted for decision-making in ECO-04.

---

*Report generated: 2026-10-08*
*Status: 13 items require review, 2 are BLOCKING (P0)*