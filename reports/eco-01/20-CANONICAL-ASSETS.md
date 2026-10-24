# ECO-01 Canonical Assets

**Document ID:** ECO-01-20-CANONICAL-ASSETS  
**Scope:** engine/ + services/ high-value knowledge assets  
**Purpose:** Define canonical identity for all high-value assets for future Eco Nojin architecture

---

## 1. Canonical Asset Registry

### Asset CANON-001: Penman-Monteith ET0

| Field | Value |
|-------|-------|
| **asset_id** | CANON-001 |
| **asset_name** | FAO-56 Penman-Monteith Reference Evapotranspiration |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Climate / Agriculture |
| **current_location** | engine/hydra/climate/et_calculator.py:54-289 |
| **knowledge_status** | SCIENTIFICALLY_SUPPORTED |
| **scientific_status** | SCIENTIFICALLY_SUPPORTED |
| **technical_status** | VERIFIED |
| **provenance** | FAO-56 (Allen et al., 1998); implementation verified against FAO examples | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Climate Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-CLIMATE-ET0`  
**Status:** CANDIDATE  
**Scientific basis:** FAO-56 Penman-Monteith for reference crop ET0  
**Implementation:** Deterministic analytical calculation in Python with C++ acceleration  
**Future role:** Core climate model in Eco Nojin  
**Legacy implementations:** services/models/registry.py (et0_hargreaves is separate model)

---

### Asset CANON-002: Hargreaves ET0

| Field | Value |
|-------|-------|
| **asset_id** | CANON-002 |
| **asset_name** | Hargreaves-Samani ET0 |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Climate / Agriculture |
| **current_location** | engine/hydra/climate/et_calculator.py:300-380 |
| **knowledge_status** | SCIENTIFICALLY_SUPPORTED |
| **scientific_status** | SCIENTIFICALLY_SUPPORTED |
| **technical_status** | VERIFIED |
| **provenance** | Hargreaves & Samani (1985); implementation verified | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | MEDIUM |
| **legacy_coupling** | None |
| **future_role** | Fallback ET0 method (when radiation data unavailable) |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-CLIMATE-ET0-HARGREAVES`  
**Status:** CANDIDATE  
**Future role:** Alternative ET0 calculation for data-scarce regions

---

### Asset CANON-003: SCS-CN Runoff

| Field | Value |
|-------|-------|
| **asset_id** | CANON-003 |
| **asset_name** | SCS Curve Number Runoff |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Hydrology |
| **current_location** | engine/hydra/models/runoff_model.py:12-145 |
| **knowledge_status** | SCIENTIFICALLY_SUPPORTED |
| **scientific_status** | SCIENTIFICALLY_SUPPORTED |
| **technical_status** | VERIFIED |
| **provenance** | USDA SCS (1972), NRCS standards; verified against examples | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Hydrology Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-HYDROLOGY-SCS-CN`

---

### Asset CANON-004: Darcy Groundwater Flow

| Field | Value |
|-------|-------|
| **asset_id** | CANON-004 |
| **asset_name** | Darcy Groundwater Flow |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Hydrogeology |
| **current_location** | engine/hydra/models/groundwater_model.py:8-92 |
| **knowledge_status** | SCIENTIFICALLY_SUPPORTED |
| **scientific_status** | SCIENTIFICALLY_SUPPORTED |
| **technical_status** | VERIFIED |
| **provenance** | Darcy's Law (1856); standard hydrogeology | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Hydrology Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-HYDROLOGY-DARCY`

---

### Asset CANON-005: Theis Solution

| Field | Value |
|-------|-------|
| **asset_id** | CANON-005 |
| **asset_name** | Theis Transient Groundwater Flow |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Hydrogeology |
| **current_location** | engine/hydra/models/groundwater_model.py:93-210 |
| **knowledge_status** | REQUIRES_SCIENTIFIC_REVIEW |
| **scientific_status** | REQUIRES_SCIENTIFIC_REVIEW |
| **technical_status** | CODE_ONLY |
| **provenance** | Theis (1935); series convergence undocumented | MEDIUM confidence |
| **confidence** | MEDIUM |
| **reuse_value** | HIGH (if verified) |
| **legacy_coupling** | None |
| **future_role** | Hydroma Hydrology Engine (after verification) |
| **recommended_action** | VALIDATE |
| **review_required** | Yes - critical |

**Canonical Identity:** `HYDROMA-HYDROLOGY-THEIS`  
**Note:** Cannot be canonicalized until series convergence verified

---

### Asset CANON-006: Van Genuchten Soil Water Retention

| Field | Value |
|-------|-------|
| **asset_id** | CANON-006 |
| **asset_name** | Van Genuchten Soil Water Retention |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Soil Physics |
| **current_location** | engine/hydra/soil/physics.py:45-167 |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | van Genuchten (1980); verified against parameters; Newton-Raphson solver | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Soil Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-SOIL-WATER-RETENTION`

---

### Asset CANON-007: RUSLE Soil Erosion

| Field | Value |
|-------|-------|
| **asset_id** | CANON-007 |
| **asset_name** | RUSLE Soil Erosion |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Soil Science |
| **current_location** | engine/hydra/soil/erosion.py:5-112 |
| **knowledge_status** | SCIENTIFICALLY_SUPPORTED |
| **scientific_status** | SCIENTIFICALLY_SUPPORTED |
| **technical_status** | VERIFIED |
| **provenance** | Renard et al. (1997); NRCS standard | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Soil Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-SOIL-EROSION`

---

### Asset CANON-008: D8 Flow Direction

| Field | Value |
|-------|-------|
| **asset_id** | CANON-008 |
| **asset_name** | D8 Flow Direction |
| **asset_type** | GIS_METHOD |
| **domain** | GIS / Hydrology |
| **current_location** | engine/land/hydrology.py:50-89 |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | O'Callaghan & Mark (1984); verified tests | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Land Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-LAND-D8-FLOW`

---

### Asset CANON-009: Terrain Analysis

| Field | Value |
|-------|-------|
| **asset_id** | CANON-009 |
| **asset_name** | Terrain Analysis Suite |
| **asset_type** | GIS_METHOD |
| **domain** | GIS / Geomorphology |
| **current_location** | engine/land/terrain_analysis.py:15-178, engine/land/models.py:45-112 |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | Horn (1981) and standard geomorphometry | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Land Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-LAND-TERRAIN`

---

### Asset CANON-010: Water Balance

| Field | Value |
|-------|-------|
| **asset_id** | CANON-010 |
| **asset_name** | Water Balance Calculator |
| **asset_type** | ENGINEERING_MODEL |
| **domain** | Water Resources |
| **current_location** | engine/hydra/simulation/balance.py:20-134 |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | Mass balance conservation; verified tests | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Simulation Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-SIM-WATER-BALANCE`

---

### Asset CANON-011: Radiation Model

| Field | Value |
|-------|-------|
| **asset_id** | CANON-011 |
| **asset_name** | Solar Radiation Model |
| **asset_type** | SCIENTIFIC_MODEL |
| **domain** | Climate |
| **current_location** | engine/hydra/climate/radiation.py |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | FAO-56 radiation equations; Allen et al. (1998) | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Hydroma Climate Engine |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-CLIMATE-RADIATION`

---

### Asset CANON-012: Formula Catalog

| Field | Value |
|-------|-------|
| **asset_id** | CANON-012 |
| **asset_name** | Formula Catalog and Registry |
| **asset_type** | DOMAIN_KNOWLEDGE |
| **domain** | Engineering |
| **current_location** | engine/hydra/formulas/catalog.py |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | Centralized equation registry with provenance tracking | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Knowledge catalog for all scientific equations |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-KNOWLEDGE-FORMULA-CATALOG`

---

### Asset CANON-013: Provenance Engine

| Field | Value |
|-------|-------|
| **asset_id** | CANON-013 |
| **asset_name** | Provenance Tracking System |
| **asset_type** | PROVENANCE_RULE |
| **domain** | Governance |
| **current_location** | engine/hydra/provenance.py |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | Custom provenance tracking with ResultProvenance enum | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | None |
| **future_role** | Traceability and audit for all knowledge assets |
| **recommended_action** | CANONICALIZE |
| **review_required** | No |

**Canonical Identity:** `HYDROMA-KNOWLEDGE-PROVENANCE`

---

### Asset CANON-014: Model Registry (Services)

| Field | Value |
|-------|-------|
| **asset_id** | CANON-014 |
| **asset_name** | Scientific Model Registry |
| **asset_type** | DOMAIN_KNOWLEDGE |
| **domain** | Governance |
| **current_location** | services/models/registry.py |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | 22 models with fidelity labels, model cards, validation metadata | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | HIGH (imports from services/api_gateway) |
| **future_role** | Canonical model registry for Eco Nojin |
| **recommended_action** | CANONICALIZE (with refactoring to remove coupling) |
| **review_required** | Yes - service coupling |

**Canonical Identity:** `Eco-Nojn-MODEL-REGISTRY`  
**Note:** Must isolate from api_gateway router imports

---

### Asset CANON-015: Watershed Calculator

| Field | Value |
|-------|-------|
| **asset_id** | CANON-015 |
| **asset_name** | Watershed Structure Calculator |
| **asset_type** | ENGINEERING_MODEL |
| **domain** | Hydrology |
| **current_location** | engine/hydra/watershed/calculator.py:15-234 |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | VERIFIED |
| **provenance** | Watershed design methods; verified tests | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | Low (some service imports) |
| **future_role** | Hydroma Watershed Engine |
| **recommended_action** | CANONICALIZE (after removing service coupling) |
| **review_required** | Yes - service coupling |

**Canonical Identity:** `HYDROMA-WATERSHED-DESIGN`

---

### Asset CANON-016: C++ Climate Kernels

| Field | Value |
|-------|-------|
| **asset_id** | CANON-016 |
| **asset_name** | C++ Climate Computation Kernels |
| **asset_type** | NUMERICAL_METHOD |
| **domain** | Engineering |
| **current_location** | engine/cpp_core/src/climate.cpp, engine/hydra/cpp_bridge/ |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | CODE_ONLY (performance optimization) |
| **provenance** | Optimized implementations of climate calculations | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH (for performance) |
| **legacy_coupling** | Moderate (cpp_bridge coupling) |
| **future_role** | Performance acceleration for Hydroma Climate Engine |
| **recommended_action** | KEEP_WITH_REFACTOR |
| **review_required** | Yes - build system |

**Canonical Identity:** `HYDROMA-CLIMATE-KERNELS`

---

### Asset CANON-017: C++ Soil Kernels

| Field | Value |
|-------|-------|
| **asset_id** | CANON-017 |
| **asset_name** | C++ Soil Physics Kernels |
| **asset_type** | NUMERICAL_METHOD |
| **domain** | Engineering |
| **current_location** | engine/cpp_core/src/soil.cpp, engine/hydra/cpp_bridge/ |
| **knowledge_status** | IMPLEMENTATION_VERIFIED |
| **scientific_status** | IMPLEMENTATION_VERIFIED |
| **technical_status** | CODE_ONLY |
| **provenance** | Optimized Van Genuchten implementations | HIGH confidence |
| **confidence** | HIGH |
| **reuse_value** | HIGH |
| **legacy_coupling** | Moderate |
| **future_role** | Performance acceleration for Hydroma Soil Engine |
| **recommended_action** | KEEP_WITH_REFACTOR |
| **review_required** | Yes - build system |

**Canonical Identity:** `HYDROMA-SOIL-KERNELS`

---

## 3. Assets Requiring Action

### REQUIRES_VALIDATION (Before Canonization)

| Asset ID | Asset | Reason |
|----------|-------|--------|
| CANON-005 | Theis Solution | Series convergence concerns |
| CANON-008 | (Reserved) | - |

### REQUIRES_REFACTORING (Before Canonization)

| Asset ID | Asset | Reason |
|----------|-------|--------|
| CANON-014 | Model Registry | Service/api_gateway coupling |
| CANON-015 | Watershed Calculator | Service coupling |
| CANON-016 | C++ Climate Kernels | Build system coupling |
| CANON-017 | C++ Soil Kernels | Build system coupling |

### NOT_RECOMMENDED

| Asset | Reason |
|-------|--------|
| Soil Salinity Model | No documented scientific basis |
| Quantum Efficiency | Experimental, unvalidated |
| MRF Segmentation | Experimental, no validation |
| Haar Wavelet | Experimental, no validation |
| Kalman Filter | No convergence guarantees documented |
| Frequency Analysis | Limited documentation |

---

## 4. Canonical Asset Summary

| Status | Count |
|--------|-------|
| CANONICALIZE (ready) | 11 |
| CANONICALIZE (with refactoring) | 3 |
| VALIDATE (before canonization) | 1 |
| NOT RECOMMENDED | 12 |

---

## 5. Canonical Asset Catalog (Machine-Readable)

```
CANON-001 | HYDROMA-CLIMATE-ET0 | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-002 | HYDROMA-CLIMATE-ET0-HARGREAVES | SCIENTIFIC_MODEL | CANONICALIZE | MEDIUM
CANON-003 | HYDROMA-HYDROLOGY-SCS-CN | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-004 | HYDROMA-HYDROLOGY-DARCY | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-005 | HYDROMA-HYDROLOGY-THEIS | SCIENTIFIC_MODEL | VALIDATE | HIGH
CANON-006 | HYDROMA-SOIL-WATER-RETENTION | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-007 | HYDROMA-SOIL-EROSION | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-008 | HYDROMA-LAND-D8-FLOW | GIS_METHOD | CANONICALIZE | HIGH
CANON-009 | HYDROMA-LAND-TERRAIN | GIS_METHOD | CANONICALIZE | HIGH
CANON-010 | HYDROMA-SIM-WATER-BALANCE | ENGINEERING_MODEL | CANONICALIZE | HIGH
CANON-011 | HYDROMA-CLIMATE-RADIATION | SCIENTIFIC_MODEL | CANONICALIZE | HIGH
CANON-012 | HYDROMA-KNOWLEDGE-FORMULA-CATALOG | DOMAIN_KNOWLEDGE | CANONICALIZE | HIGH
CANON-013 | HYDROMA-KNOWLEDGE-PROVENANCE | PROVENANCE_RULE | CANONICALIZE | HIGH
CANON-014 | ECO-NOJIN-MODEL-REGISTRY | DOMAIN_KNOWLEDGE | CANONICALIZE (refactor) | HIGH
CANON-015 | HYDROMA-WATERSHED-DESIGN | ENGINEERING_MODEL | CANONICALIZE (refactor) | HIGH
CANON-016 | HYDROMA-CLIMATE-KERNELS | NUMERICAL_METHOD | KEEP_WITH_REFACTOR | HIGH
CANON-017 | HYDROMA-SOIL-KERNELS | NUMERICAL_METHOD | KEEP_WITH_REFACTOR | HIGH
```

---

*See also: 01-KNOWLEDGE-INVENTORY.md, 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 13-SERVICE-ASSET-MAP.md, 21-DUPLICATION-ANALYSIS.md*