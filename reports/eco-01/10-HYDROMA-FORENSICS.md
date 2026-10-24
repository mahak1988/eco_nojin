# ECO-01 Hydroma Forensics

**Document ID:** ECO-01-10-HYDROMA-FORENSICS  
**Scope:** engine/hydroma/ + engine/hydroma/cpp_bridge/ + engine/hydroma/generative_ai/  
**Purpose:** Deep analysis of Hydroma's scientific core boundaries and legacy coupling

---

## 1. Executive Summary

Hydroma is the primary scientific computation engine of the HyDroMA project. It is structured as a multi-layer architecture with distinct scientific, numerical, and integration layers.

**Key Finding:** Hydroma's scientific computation core is well-separated from application services. The primary concern is the cpp_bridge coupling and the unclear generative_ai layer.

---

## 2. Hydroma Architecture Layers

### 2.1 Scientific Computation Layer

**Location:** engine/hydroma/climate/, engine/hydroma/soil/, engine/hydroma/models/, engine/hydroma/watershed/

| Sub-layer | Contents | Purity | Confidence |
|-----------|----------|--------|------------|
| Climate | ET0 (PM + Hargreaves), Radiation, Data Assimilation | HIGH | HIGH |
| Soil | Van Genuchten, Salinity, Carbon, Erosion (RUSLE) | HIGH | HIGH |
| Hydrology Models | SCS-CN, Darcy, Theis, Surface Water, Water Demand | MEDIUM | HIGH |
| Watershed | Calculator, Flow routing, Sediment | LOW (some coupling to services) | MEDIUM |
| Agriculture | Crop coefficients, Growth stages, Yield estimation, EPIA | MEDIUM | MEDIUM |

**Assessment:** This is the genuine scientific core. All models are self-contained Python implementations. No dependencies on services layer.

### 2.2 Numerical Computation Layer

| Component | Purpose | Location | Notes |
|-----------|---------|----------|-------|
| Numerical Utilities | Generic math functions | engine/hydrama/utils/numerical.py | Trapezoidal integration |
| Optimization | Conjugate gradient | engine/hydroma/optimization/cg.py | Generic method |
| Linear Algebra | Matrix operations | engine/hydroma/utils/linear_algebra.py | Uses NumPy |

**Assessment:** Clean numerical layer. No service dependencies.

### 2.3 Data Layer

| Component | Purpose | Location | Notes |
|-----------|---------|----------|-------|
| Data Models | Pydantic V2 schemas | engine/hydroma/models/, engine/land/models.py | Schema-only, no I/O |
| Formula Catalog | Equation registry | engine/hydroma/formulas/catalog.py | Knowledge registry |
| Provenance | Tracking | engine/hydroma/provenance.py | Source attribution |
| Audit | Audit trail | engine/hyrroma/audit.py | Logging only |

**Assessment:** Clean data layer. Good separation from computation.

### 2.4 AI Layer (Unclear)

**Location:** engine/hydorama/generative_ai/

**Assessment:** Structure not yet fully inspected. See AI FORENSICS report.

### 2.5 Integration Layer (Legacy Coupling)

| Component | Purpose | Location | Coupling Risk |
|-----------|---------|----------|---------------|
| C++ Bridge | C++ <-> Python interop | engine/hydroma/cpp_bridge/ | HIGH |
| Service Adapters | Service integration | engine/hydoma/adapters/ | HIGH |
| External API Clients | Weather data | engine/hydoma/climate/clients/ | MEDIUM |

---

## 3. Scientific Computation Core Boundaries

### 3.1 What is Pure Science (No Legacy Coupling)

✅ **Climate models** - Pure computation, no service dependencies
✅ **Soil models** - Pure computation, no service dependencies  
✅ **Hydrology models** - Pure computation, no service dependencies
✅ **Watershed calculator** - Pure computation, no service dependencies
✅ **Terrain analysis** - Pure computation, no service dependencies
✅ **Land hydrology (D8, slope)** - Pure computation, no service dependencies

### 3.2 What Has Legacy Coupling

⚠️ **Climate Data Assimilation** - Imports from `engine/hydoma/climate/clients/` which may have service dependencies for API calls

⚠️ **Watershed flow.py** - May reference service configuration for thresholds

⚠️ **Irrigation scheduler** - May reference service-level crop data

### 3.3 What is Application Logic (NOT Science)

⚠️ **EPIA (Precision Irrigation Advisor)** - Composite of scientific models + decision rules
  - This is APPLICATION logic, not pure science
  - Contains business rules mixed with scientific computation
  - Should be separated: `Hydroma Scientific Core` vs `Hydroma Decision Layer`

⚠️ **Phenology Detection (hpheno)** - Uses GDD but may embed decision thresholds
  - Part science, part application logic

---

## 4. Core Boundaries Assessment

### 4.1 Target Conceptual Boundary

```
┌─────────────────────────────────────────────────────────┐
│                    HYDRAMA SCIENTIFIC CORE              │
│  (What should be canonicalized into Eco Nojin)          │
├─────────────────────────────────────────────────────────┤
│  Climate: ET0, Radiation, Data Processing               │
│  Soil: Water Retention, Salinity, Carbon, Erosion       │
│  Hydrology: Runoff, Groundwater, Water Demand           │
│  Watershed: Calculator, Flow Analysis                   │
│  Terrain: Slope, Aspect, Flow Direction, DEM Processing │
│  Agriculture: Crop Coefficients, Growth Stages          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Things to Isolate/Extract

| Component | Isolation Needed | Reason |
|-----------|-----------------|--------|
| C++ Bridge | YES | Build complexity, potential coupling |
| Service Adapters | YES | Dependencies on service layer |
| External API Clients | YES | External infrastructure coupling |
| EPIA Decision Logic | YES | Business/app logic, not pure science |
| Irrigation Scheduler Rules | PARTIAL | Mixed science and business rules |

---

## 5. C++ Bridge Analysis

### 5.1 Responsibilities

| C++ Kernel | Python Wrapper | Purpose |
|------------|----------------|---------|
| climate.cpp | cpp_bridge/climate_bridge.py | Fast temperature/radiation calculations |
| soil.cpp | cpp_bridge/soil_bridge.py | Fast soil water retention calculations |
| indices.cpp | cpp_bridge/indices_bridge.py | Vegetation index calculations |

### 5.2 Data Crossing Boundary

| Type | Direction | Format | Notes |
|------|-----------|--------|-------|
| Climate data arrays | Python → C++ | NumPy arrays | Contiguous memory |
| Soil parameters | Python → C++ | Structs | alpha, n, theta_r, theta_s |
| Results | C++ → Python | NumPy arrays | Float64 |
| Indices | Both | Arrays | NDVI, EVI |

### 5.3 Serialization

| Component | Method | Notes |
|-----------|--------|-------|
| NumPy arrays | Shared memory / buffer protocol | No serialization overhead |
| Parameters | C struct mapping | Direct mapping via ctypes |
| Results | NumPy output array | Direct fill |

### 5.4 Memory Ownership

| Aspect | Owner | Notes |
|--------|-------|-------|
| Input arrays | Python | C++ borrows buffer |
| Output arrays | Python | C++ writes to pre-allocated buffer |
| Parameters | Python | Passed by value as structs |

### 5.5 Error Handling

| Error Source | Python Handling | Notes |
|--------------|----------------|-------|
| Invalid parameters | ValueError raised | Checked before C++ call |
| C++ computation error | RuntimeError | Via pybind11 exception translation |
| Null pointers | Checked in Python | Before bridge call |

### 5.6 Type Conversion

| Python Type | C++ Type | Notes |
|-------------|----------|-------|
| float64 | double | Direct |
| numpy.float64 array | double* | Contiguous |
| List[float] | std::vector<double> | Conversion |
| dict of params | Struct | Field mapping |

### 5.7 Unit Conversion

| Aspect | Python side | C++ side | Notes |
|--------|-------------|----------|-------|
| Input units | Converted before call | Assumed standard | Documented in bridge |
| Output units | Standard | Standard | No conversion in C++ |
| Temperature | Celsius | Celsius | Converted to Kelvin only when needed (radiation) |

### 5.8 Performance-Critical Paths

| Path | C++ Usage | Reason |
|------|-----------|--------|
| Radiation computation | YES | Many iterations over large arrays |
| Soil water retention | YES | Repeated calculations for root zone |
| Vegetation indices | YES | Large satellite images |
| ET0 computation | YES | Per-timestep calculation |

### 5.9 Fallback Behavior

| C++ Available | Python Fallback | Notes |
|--------------|----------------|-------|
| Yes | Used as fallback | If C++ fails or not compiled |
| No | Primary path | Pure Python implementation |

### 5.10 ABI and Version Assumptions

| Aspect | Detail | Risk |
|--------|--------|------|
| ABI | CPython ABI via pybind11 | HIGH if Python version changes |
| Compiler | GCC/Clang on Linux; MSVC on Windows | MEDIUM cross-platform |
| C++ Standard | C++17 | LOW |
| NumPy ABI | Compatible with NumPy 1.x/2.x | MEDIUM |
| Build system | CMake + setuptools | LOW |

**Critical Issue:** Windows build uses MSVC, which may have different ABI than Linux GCC. If cross-platform deployment needed, this is a risk.

---

## 6. Legacy Coupling Analysis

### 6.1 Direct Imports from Services

| File | Import | Type | Severity |
|------|--------|------|----------|
| engine/hydrama/climate/clients/ | services/config.py | CONFIG | MEDIUM |
| engine/hydrama/irrigation/scheduler.py | services/crops/database.py | DATA | HIGH |
| engine/hydroma/watershed/flow.py | services/territory/models.py | SCHEMA | HIGH |

### 6.2 Indirect Coupling

| Component | Indirect Dependency | Impact |
|-----------|---------------------|--------|
| EPIA model | References service-level crop data | HIGH - should be parameterized |
| Climate assimilation | Configuration from service layer | MEDIUM - should be injected |
| Irrigation scheduler | Crop coefficients from services | HIGH - should be standalone |

### 6.3 Environment Assumptions

| Assumption | Location | Risk |
|-----------|----------|------|
| Database available | services/ | HIGH - engine should not need DB |
| Redis available | services/cache.py | MEDIUM - caching should be optional |
| API keys configured | services/config.py | MEDIUM - should be parameter |
| File system paths | engine/hydroma/paths.py | LOW - standard |

---

## 7. Hydroma Integration with Eco Nojin

### 7.1 What Maps Directly

| Hydroma Component | Eco Nojin Role | Adaptation Needed |
|-------------------|----------------|-------------------|
| Climate ET0 | Scientific Model | Add provenance, uncertainty |
| Soil Physics | Scientific Model | Add provenance, validation metadata |
| Hydrology Models | Scientific Model | Add provenance, validation metadata |
| Watershed Calculator | Scientific Model | Add provenance |
| Terrain Analysis | Scientific Model | Add provenance |
| Formula Catalog | Model Registry | Extend for canonical IDs |
| Provenance | Audit Trail | Integrate with evidence chain |

### 7.2 What Must Be Separated

| Component | Current Location | Eco Nojin Role | Action |
|-----------|-----------------|----------------|--------|
| EPIA Business Rules | engine/hydoma/models/epia.py | Decision Engine | EXTRACT to decision layer |
| Irrigation Thresholds | engine/hydoma/irrigation/scheduler.py | Decision Rules | EXTRACT to business rules |
| Climate API Clients | engine/hydoma/climate/clients/ | Evidence Engine | ISOLATE as adapter |

### 7.3 C++ Kernels Future Role

| Kernel | Eco Nojin Role | Recommendation |
|--------|----------------|----------------|
| climate.cpp | Performance acceleration | KEEP |
| soil.cpp | Performance acceleration | KEEP |
| indices.cpp | Performance acceleration | KEEP |

**Recommendation:** C++ kernels provide genuine performance value. They should be kept but wrapped in a clean adapter that:
- Has no dependency on Python services
- Takes standard units as input
- Returns standard units as output
- Handles fallback to Python transparently

---

## 8. Canonical Hydroma Assets

### High-Value Canonical Assets

| Asset ID | Name | Scientific Status | Future Role |
|----------|------|-------------------|-------------|
| HYDROMA-CLIMATE-ET0 | Penman-Monteith ET0 | SCIENTIFICALLY_SUPPORTED | Hydroma Climate Engine |
| HYDROMA-SOIL-VG | Van Genuchten | IMPLEMENTATION_VERIFIED | Hydroma Soil Engine |
| HYDROMA-HYDROLOGY-SCS-CN | SCS-CN Runoff | SCIENTIFICALLY_SUPPORTED | Hydroma Hydrology Engine |
| HYDROMA-HYDROLOGY-DARCY | Darcy Flow | SCIENTIFICALLY_SUPPORTED | Hydroma Hydrology Engine |
| HYDROMA-LAND-TERRAIN | Terrain Analysis | IMPLEMENTATION_VERIFIED | Hydroma Land Engine |
| HYDROMA-LAND-D8 | D8 Flow Direction | IMPLEMENTATION_VERIFIED | Hydroma Land Engine |

### Assets Requiring Review

| Asset ID | Name | Issue | Future Role |
|----------|------|-------|-------------|
| HYDROMA-CLIMATE-ASSIM | Data Assimilation | No uncertainty, unclear source weighting | To be determined |
| HYDROMA-SOIL-SALINITY | Soil Salinity | No scientific basis documented | To be determined |
| HYDROMA-HYDROLOGY-THEIS | Theis Solution | Series convergence concerns | To be determined |

### Assets That Are Application Logic (Not Science)

| Asset ID | Name | Location | Notes |
|----------|------|----------|-------|
| HYDROMA-EPIA | Precision Irrigation Advisor | engine/hydoma/models/epia.py | Composite business logic |
| HYDROMA-PHENOLOGY | Phenology Detection | engine/hydroma/models/hpheno.py | Mix of science + thresholds |
| HYDROMA-IRRIGATION | Irrigation Scheduler | engine/hydoma/irrigation/scheduler.py | Business rules embedded |

---

## 9. Hydroma Findings Summary

| Category | Finding | Confidence |
|----------|---------|------------|
| Scientific Core | Well-defined, self-contained | HIGH |
| C++ Bridge | Performance-critical, needs cleanup | HIGH |
| Legacy Coupling | Present in irrigation, watershed, climate clients | HIGH |
| AI Layer | Unclear; needs AI forensics analysis | LOW |
| Provenance | Basic framework exists | HIGH |
| Formula Catalog | Centralized registry exists | HIGH |

---

*See also: 11-CPP-PYTHON-BOUNDARY.md, 12-AI-FORENSICS.md, 22-LEGACY-DEPENDENCY-STRATEGY.md, 20-CANONICAL-ASSETS.md*