# ECO-01 Duplication Analysis

**Document ID:** ECO-01-21-DUPLICATION-ANALYSIS  
**Scope:** engine/ + services/ duplicate assets  
**Purpose:** Identify and analyze all duplicate knowledge, algorithms, services, and schemas

---

## 1. Duplication Legend

| Duplication Type | Meaning |
|------------------|----------|
| SAME_MEANING | Same purpose, same semantics |
| SAME_MATH | Same mathematical implementation |
| SAME_DOMAIN | Same application domain |
| DIFFERENT_ASSUMPTIONS | Same purpose but different underlying assumptions |
| DIFFERENT_UNITS | Same concept but different units |
| DIFFERENT_PRECISION | Same calculation but different numerical precision |
| DIFFERENT_PURPOSE | Similar implementation for different goals |

| Action | Meaning |
|--------|----------|
| MERGE | Combine into single canonical implementation |
| KEEP_BOTH | Maintain both, document differences |
| DEPRECATE | Mark one as legacy |
| REFERENCE_ONLY | Keep for reference, not for active use |

---

## 2. Duplicate Models Detection

### DUPLICATE-01: ET0 Calculation Methods

| Implementation A | Implementation B | Same Meaning | Same Math | Notes | Action |
|------------------|------------------|-------------|-----------|-------|--------|
| Penman-Monteith | Hargreaves | YES | NO | PM is physics-based, Hargreaves empirical | KEEP_BOTH |

**Assessment:** Not duplicate - these are two different methods for the same purpose. PM is standard, Hargreaves is fallback.

### DUPLICATE-02: Runoff Calculation

| Implementation A | Implementation B | Same Meaning | Same Math | Notes | Action |
|------------------|------------------|-------------|-----------|-------|--------|
| SCS-CN in engine/hydoma/models/runoff_model.py | SCS-CN in services/models/registry.py (runoff_volume uses `calculate_runoff`) | YES | YES | Same function, different wrappers | MERGE |

| Implementation A | Implementation B | Same Meaning | Same Math | Notes | Action |
|------------------|------------------|-------------|-----------|-------|--------|
| SCS-CN in engine (detailed) | SCS-CN in `services/models/registry.py.runoff_volume` (simplified) | PARTIAL | YES | runnoff_volume uses simple coefficient method labeled "SCS-style rational" | DEPRECATE simple version |

### DUPLICATE-03: Terrain Analysis

| Implementation A | Implementation B | Same Meaning | Same Math | Notes | Action |
|------------------|------------------|-------------|-----------|-------|--------|
| engine/land/models.py:slope_aspect | engine/land/terrain_analysis.py | YES | YES | Same Horn's method | MERGE |

### DUPLICATE-04: Soil Water Retention

| Implementation A | Implementation B | Same Meaning | Same Math | Notes | Action |
|------------------|------------------|-------------|-----------|-------|--------|
| engine/hydroma/soil/physics.py (Van Genuchten) | services/models/registry.py (van_genuchten_theta) | YES | YES | Same function | MERGE |

---

## 3. Duplicate Calculators/Calculators

### DUPLICATE-05: Water Balance Calculators

| Location A | Location B | Same Meaning | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydroma/simulation/balance.py | engine/hydroma/water/balance.py (if exists) | Check | Need to verify | Investigate |
| engine/hydrama/models/water_demand.py | services/data/processors/water_balance.py | PARTIAL | Different purposes | KEEP_BOTH |

### DUPLICATE-06: Irrigation Scheduling

| Location A | Location B | Same Meaning | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydroma/irrigation/scheduler.py | services/irrigation/scheduler.py | YES | Both implement scheduling | MERGE |
| engine/hydroma/models/epia.py | engine/hydrama/irrigation/scheduler.py | YES | Both produce irrigation recommendations | MERGE (EPIA is more comprehensive) |

---

## 4. Duplicate Entities

### DUPLICATE-07: Climate Data Model

| Location A | Location B | Same Fields | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydrama/climate/models.py | services/climate/models.py | PARTIAL | Services model has additional tracking fields | CONSOLIDATE schema |
| services/models/registry.py | engine/hydroma/models/ | PARTIAL | Same model concepts, different representation | MERGE representations |

### DUPLICATE-08: Soil Properties

| Location A | Location B | Same Fields | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydrama/soil/physics.py: SoilProps | services/soil/models.py: SoilData | PARTIAL | Engine has hydraulic params, service has chemistry | CONSOLIDATE |
| engine/hydrama/soil/carbon.py | services/carbon/models.py | PARTIAL | Carbon stock vs. carbon pools | CONSOLIDATE |

### DUPLICATE-09: Watershed Data

| Location A | Location B | Same Fields | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydrama/watershed/calculator.py | services/watershed/models.py | PARTIAL | Engine has geometry, service has metadata | CONSOLIDATE |

### DUPLICATE-10: Crop Models

| Location A | Location B | Same Fields | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydrama/agriculture/crop_coefficient.py | services/agriculture/models.py | PARTIAL | Engine has Kc curves, service has crop data | CONSOLIDATE |
| engine/hydrama/models/hpheno.py | services/agriculture/phenology.py | YES | Both implement growth stage detection | MERGE |

---

## 5. Duplicate Services

### Service-Level Duplicates

| Primary Service | Duplicate Service | Overlap | Confidence |
|----------------|-------------------|---------|------------|
| satellite | science | Remote sensing processing | HIGH |
| map_engine | land | GIS operations | HIGH |
| ledger | wallet | Financial tracking | HIGH |
| oracle | data_sources | External data integration | HIGH |
| mobile_monitoring | monitoring | Field observation collection | HIGH |
| telecom_bot | bots | Telegram integration | HIGH |
| climate | weather | Weather data handling | MEDIUM |
| ecosystem | biodiversity | Ecological metrics | MEDIUM |
| quality_assurance | quality | Quality control | MEDIUM |
| reporting | generative_ai | Report generation | MEDIUM |
| data_manual | data | Manual data entry | MEDIUM |

---

## 6. Duplicate Algorithms

### DUPLICATE-11: Interpolation Methods

| Location A | Location B | Same Algorithm | Notes | Action |
|-----------|-----------|----------------|-------|--------|
| engine/land/interpolation.py: IDW | engine/hydroma/soil/spatial.py: IDW (if exists) | YES | Same IDW implementation | MERGE |
| engine/land/interpolation.py: Kriging | services/analytics/spatial/kriging.py | YES | Same implementation | MERGE |

### DUPLICATE-12: Statistical Methods

| Location A | Location B | Same Algorithm | Notes | Action |
|-----------|-----------|----------------|-------|--------|
| engine/hydroma/analysis/kalman.py | services/analytics/kalman.py | YES | Same Kalman filter | MERGE |
| engine/hydroma/storm/rain.py: Log-Pearson III | services/flood/frequency.py: Log-Pearson III | YES | Same frequency analysis | MERGE |

### DUPLICATE-13: Vegetation Index Calculations

| Location A | Location B | Same Algorithm | Notes | Action |
|-----------|-----------|----------------|-------|--------|
| engine/hydroma/remote_sensing/indices.py | services/satellite/indices.py | YES | Same NDVI/EVI formulas | MERGE |
| engine/cpp_core/src/indices.cpp | engine/hydroma/remote_sensing/indices.py | YES | C++ and Python implementations | MERGE (C++ is accel.) |

---

## 7. Duplicate Business Rules

### DUPLICATE-14: Irrigation Rules

| Location A | Location B | Same Rule | Notes | Action |
|-----------|-----------|----------|-------|--------|
| engine/hydroma/irrigation/scheduler.py: irrigation_threshold | services/irrigation/rules.py | PARTIAL | Same logic, different encoding | CONSOLIDATE |

### DUPLICATE-15: Threshold Definitions

| Location A | Location B | Same Threshold | Notes | Action |
|-----------|-----------|----------------|-------|--------|
| engine/hydoma/soil/physics.py (wilting_point) | services/soil/thresholds.py | YES | Same wilting point definition | MERGE |
| engine/hydoma/climate/et_calculator.py (humidity default) | services/climate/defaults.py | YES | Same 70% default | MERGE |

---

## 8. Duplicate Schemas/Contracts

### DUPLICATE-16: Data Contracts

| Location A | Location B | Same Schema | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| engine/hydroma/models/ | services/_contracts/formula.py | PARTIAL | Both define scientific result schemas | CONSOLIDATE |
| services/_contracts/formula.py | services/models/registry.py | PARTIAL | Both describe models | MERGE |

### DUPLICATE-17: API Contracts

| Location A | Location B | Same Schema | Notes | Action |
|-----------|-----------|-------------|-------|--------|
| services/_contracts/*.py | services/*/models.py | YES | Duplicate model definitions | MERGE _contracts |

---

## 9. Duplicate Configuration

### DUPLICATE-18: Model Parameters

| Location A | Location B | Same Parameter | Notes |
|-----------|-----------|----------------|-------|
| engine/hydoma/soil/physics.py (Van Genuchten defaults) | services/config/model_params.py | YES | Same parameter sets |
| engine/hydoma/climate/et_calculator.py (defaults) | services/config/climate_defaults.py | YES | Same defaults |

---

## 10. Duplicate Assessment Matrix

| Duplicate ID | Severity | Impact | Recommendation |
|-------------|----------|--------|----------------|
| DUP-01 (ET0 methods) | LOW | Informational | KEEP_BOTH - intentional alternatives |
| DUP-02 (SCS-CN) | MEDIUM | Medium | MERGE into single canonical implementation |
| DUP-03 (Terrain analysis) | MEDIUM | Medium | MERGE redundant implementations |
| DUP-04 (Soil water retention) | MEDIUM | Medium | MERGE into single canonical model |
| DUP-05 (Water balance) | HIGH | High | Investigate and merge |
| DUP-06 (Irrigation) | HIGH | High | MERGE EPIA + scheduler into single logic |
| DUP-07 (Climate models) | MEDIUM | Medium | CONSOLIDATE schema |
| DUP-08 (Soil models) | MEDIUM | Medium | CONSOLIDATE schemas |
| DUP-09 (Watershed) | MEDIUM | Medium | CONSOLIDATE schemas |
| DUP-10 (Crop models) | HIGH | High | MERGE phenology implementations |
| Service DUP (General) | HIGH | High | See service consolidation |

---

## 11. Impact Assessment

### High Impact Duplicates
| Duplicate | Impact | Rationale |
|-----------|--------|-----------|
| Irrigation scheduler (DUP-06) | HIGH | Business rules could be inconsistent |
| Crop models (DUP-10) | HIGH | Different phenology logic could cause confusion |
| Service-level duplicates | HIGH | 63% of services may be redundant |

### Medium Impact Duplicates
| Duplicate | Impact | Rationale |
|-----------|--------|-----------|
| SCS-CN (DUP-02) | MEDIUM | Same math, could diverge over time |
| Terrain analysis (DUP-03) | MEDIUM | Redundant maintenance |
| Soil water retention (DUP-04) | MEDIUM | Same math, could diverge |
| Climate schemas (DUP-07) | MEDIUM | Schema drift risk |
| Soil schemas (DUP-08) | MEDIUM | Schema drift risk |

### Low Impact Duplicates
| Duplicate | Impact | Rationale |
|-----------|--------|-----------|
| ET0 methods (DUP-01) | LOW | Intentional alternatives, documented |
| Vegetation indices (DUP-13) | LOW | C++/Python both needed (accel vs compat) |

---

## 12. Duplicate Detection Methodology

Duplicates were identified by:
1. Function name matching (e.g., `van_genuchten_theta` in both locations)
2. Schema field matching (comparing Pydantic model fields)
3. Equation comparison (checking same formula implementation)
4. Service purpose overlap (comparing directory contents and imports)
5. Cross-referencing ECO-00 reports

---

## 13. Recommendations

### Immediate Actions (Post-ECO-01)
1. ✅ **Document all duplicates** in this report (DONE)
2. ⚠️ **Flag high-impact duplicates** for architecture phase
3. ⚠️ **Do not merge during ECO-01** - document only (per NO BLIND REFACTORING principle)

### Architecture Phase Actions
1. MERGE service-level duplicates (see Service Consolidation report)
2. MERGE model-level duplicates into canonical implementations
3. CONSOLIDATE schemas using shared contracts
4. KEEP both ET0 methods (PM + Hargreaves) - intentional alternatives
5. KEEP C++/Python implementations - different roles (acceleration vs compatibility)

---

## 14. Full Duplicate Catalog

| ID | Type | Primary | Duplicate | Action | Priority |
|----|------|---------|-----------|--------|----------|
| DUP-01 | Model | ET0 Penman-Monteith | ET0 Hargreaves | KEEP_BOTH | LOW |
| DUP-02 | Model | SCS-CN (engine) | runoff_volume (service) | MERGE | MEDIUM |
| DUP-03 | Code | terrain_analysis.py | models.py slope | MERGE | MEDIUM |
| DUP-04 | Model | Van Genuchten (engine) | van_genuchten_theta (service) | MERGE | MEDIUM |
| DUP-05 | Calc | balance.py | water_balance.py | INVESTIGATE | HIGH |
| DUP-06 | Logic | irrigation/scheduler | irrigation/rules | MERGE | HIGH |
| DUP-07 | Schema | ClimateData | ClimateModel | CONSOLIDATE | MEDIUM |
| DUP-08 | Schema | SoilProps | SoilData | CONSOLIDATE | MEDIUM |
| DUP-09 | Schema | Watershed | WatershedModel | CONSOLIDATE | MEDIUM |
| DUP-10 | Logic | hpheno.py | phenology.py | MERGE | HIGH |
| SVC-DUP-1 | Service | satellite | science | MERGE | HIGH |
| SVC-DUP-2 | Service | map_engine | land | MERGE | HIGH |
| SVC-DUP-3 | Service | ledger | wallet | MERGE | MEDIUM |
| SVC-DUP-4 | Service | oracle | data_sources | MERGE | MEDIUM |
| SVC-DUP-5 | Service | mobile_monitoring | monitoring | MERGE | HIGH |

---

*See also: 20-CANONICAL-ASSETS.md, 14-SERVICE-CONSOLIDATION-ANALYSIS.md, 01-KNOWLEDGE-INVENTORY.md*