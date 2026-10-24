# ECO-03: Architecture Test Specification — Report 16
## Implementation-Ready Test Plan for ECO-04

---

## Executive Summary

This report specifies all tests required for ECO-04 implementation, based on verification of existing test coverage and architectural requirements.

---

## 1. Existing Test Inventory

### C++ Tests (11 unit test files + 9 benchmark files)

| File | Type | Status | Coverage |
|------|------|--------|----------|
| `test_climate_unit.cpp` | Unit | UNRUNNABLE | Hargreaves, extraterrestrial radiation, PM ET0 |
| `test_crop_water_unit.cpp` | Unit | UNRUNNABLE | Crop water simulation |
| `test_erosion_unit.cpp` | Unit | UNRUNNABLE | RUSLE erosion |
| `test_hydrology_unit.cpp` | Unit | UNRUNNABLE | Muskingum routing |
| `test_indices_unit.cpp` | Unit | UNRUNNABLE | NDVI, EVI, SAVI, NBR, NDWI |
| `test_nojin_calculator.cpp` | Unit | UNRUNNABLE | Nojin calculator |
| `test_richards_unit.cpp` | Unit | UNRUNNABLE | Richards equation |
| `test_saint_venant_unit.cpp` | Unit | UNRUNNABLE | Saint-Venant equation |
| `test_sampling_unit.cpp` | Unit | UNRUNNABLE | Latin hypercube, Monte Carlo |
| `test_sediment_unit.cpp` | Unit | UNRUNNABLE | Sediment yield |
| `test_soil_unit.cpp` | Unit | UNRUNNABLE | Soil physics |
| `test_advanced.cpp` | Unit | UNRUNNABLE | Combined/advanced tests |
| `test_hydroma.cpp` | Unit | UNRUNNABLE | Hydroma integration |
| `benchmark_climate.cpp` | Perf | NOT RUN | Climate performance |
| `benchmark_crop_water.cpp` | Perf | NOT RUN | Crop water performance |

**Status**: All UNRUNNABLE due to missing `database/` package

### Python Strict Tests (16 files)

| File | Type | Status | Coverage |
|------|------|--------|----------|
| `test_s00_baseline.py` | Baseline | UNRUNNABLE | Import baseline |
| `test_s01_import_integrity.py` | Import | UNRUNNABLE | Import integrity, dead code |
| `test_s02_climate_et0.py` | Numerical | UNRUNNABLE | FAO-56 ET0 |
| `test_s03_hydrology_runoff.py` | Numerical | UNRUNNABLE | SCS-CN, Muskingum |
| `test_s04_groundwater.py` | Numerical | UNRUNNABLE | Theis |
| `test_s05_soil_retention.py` | Numerical | UNRUNNABLE | Van Genuchten |
| `test_s06_watershed_design.py` | Numerical | PASS | Check dams, terraces |
| `test_s07_carbon.py` | Numerical | UNRUNNABLE | RothC |
| `test_s08_irrigation.py` | Numerical | UNRUNNABLE | Scheduling |
| `test_s09_dimensional_consistency.py` | Property | UNRUNNABLE | Units analysis |
| `test_s10_property_invariants.py` | Property | UNRUNNABLE | Math properties |
| `test_s11_parity_tripwires.py` | Parity | UNRUNNABLE | Backend parity |
| `test_s12_table_registration.py` | Integration | UNRUNNABLE | SOIL_PARAMETERS |
| `test_s13_soil_table.py` | Unit | UNRUNNABLE | Soil table |
| `test_s14_published_table.py` | Unit | UNRUNNABLE | Published params |
| `test_s15_provenance.py` | Unit | UNRUNNABLE | Provenance |

**Status**: 0 executable, 16 UNRUNNABLE

---

## 2. Required Tests for ECO-04

### 2.1 Import Boundary Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-IBT-001 | Engine cannot import from services | AST scan engine/ | No `from services` or `import services` | Any services import found | Python AST + pytest fixture | CRITICAL |
| T-IBT-002 | Services cannot import from database | AST scan services/ | No `from database` or `import database` | Any database import found | Python AST | CRITICAL |
| T-IBT-003 | AI cannot import from engine | AST scan services/ai/ | No `from engine` or `import engine` | Any engine import found | Python AST | CRITICAL |
| T-IBT-004 | Services cannot import from platform_core directly | AST scan | Only through Engine Gateway | Direct imports found | Python AST | HIGH |
| T-IBT-005 | No absolute imports of missing modules | AST scan | All imports resolve | ImportError at runtime | Python import sweep | HIGH |

### 2.2 Dependency Direction Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-DDT-001 | services→engine allowed | Dependency graph | services can import engine | Unexpected | pytest + importlib | HIGH |
| T-DDT-002 | engine→services blocked | AST scan | No engine imports services | services import found | Python AST | CRITICAL |
| T-DDT-003 | ai→engine blocked | AST scan | No ai imports engine | engine import found | Python AST | CRITICAL |
| T-DDT-004 | ai→evidence only | AST scan | ai imports only evidence module | Non-evidence import | Python AST | HIGH |
| T-DDT-005 | database→engine blocked | AST scan | No database imports engine | engine import found in database | Python AST | HIGH |

### 2.3 Engine Purity Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-EPT-001 | Engine has no UI imports | AST scan engine/ | No UI framework imports | FastAPI, Flask, React imports | Python AST | HIGH |
| T-EPT-002 | Engine has no auth imports | AST scan engine/ | No auth imports | Auth library imports | Python AST | HIGH |
| T-EPT-003 | Engine has no payment imports | AST scan engine/ | No payment imports | Payment library imports | Python AST | HIGH |
| T-EPT-004 | Engine has no blockchain imports | AST scan engine/ | No blockchain imports | Blockchain library imports | Python AST | HIGH |
| T-EPT-005 | Engine is importable standalone | `import engine` | Completes without database/ | ImportError | Direct import test | CRITICAL |

### 2.4 AI Isolation Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-AIT-001 | AI cannot import engine | AST scan services/ai/ | No engine imports | engine import found | Python AST | CRITICAL |
| T-AIT-002 | AI outputs carry LOW trust | Check AI output schema | trust_level=LOW | Missing or HIGH | Schema validation | HIGH |
| T-AIT-003 | AI recommendations go through Tasmimyar | Trace recommendation path | Must pass through decision engine | Direct to user | Integration test | CRITICAL |
| T-AIT-004 | AI cannot modify model registry | Attempt to modify CANON-XXX | Reject | Modification succeeds | Mutation test | CRITICAL |

### 2.5 Model Registry Integrity Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-MRT-001 | All 22 models registered | Model registry | 22 entries | Missing model | Unit test | HIGH |
| T-MRT-002 | Each model has CANON-XXX ID | Model registry | All have ID | Missing ID | Data validation | HIGH |
| T-MRT-003 | No duplicate model implementations | Code scan | Single implementation per model | Duplicate found | AST + grep | HIGH |
| T-MRT-004 | Model maturity matches registry | Model registry | Status matches source | Mismatch | Data comparison | HIGH |
| T-MRT-005 | Model versions are unique | Model registry | No duplicate versions | Duplicate found | Data validation | HIGH |

### 2.6 Unit Consistency Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-UCT-001 | All C++ kernel outputs in SI | C++ test outputs | SI units | Non-SI units | Output validation | HIGH |
| T-UCT-002 | Unit conversion centralized at Gateway | Source scan | No scattered conversions | Scattered conversions | AST + grep | HIGH |
| T-UCT-003 | Temperature constant consistency | C++ vs Python | 273.0 in both | Mismatch | Parity test | CRITICAL |
| T-UCT-004 | Dimensional analysis passes | Model inputs/outputs | Dimensions match | Dimension mismatch | Unit library | HIGH |

### 2.7 Provenance Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-PVT-001 | All results carry provenance | Model outputs | provenance present | Missing | Integration test | HIGH |
| T-PVT-002 | Provenance chain is traceable | Result with provenance | Full chain traceable | Broken chain | Trace test | HIGH |
| T-PVT-003 | Provenance is immutable | Modify provenance | Reject | Modification succeeds | Mutation test | HIGH |
| T-PVT-004 | Provenance includes CANON-XXX | Result provenance | model_id present | Missing | Data validation | HIGH |

### 2.8 Uncertainty Propagation Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-UPT-001 | All model outputs have uncertainty | Model outputs | uncertainty field present | Missing | Integration test | HIGH |
| T-UPT-002 | Absence of uncertainty ≠ certainty | Model without uncertainty | unknown uncertainty | Treated as certain | Runtime check | CRITICAL |
| T-UPT-003 | Uncertainty propagates through chain | Multi-step computation | Uncertainty accumulates | No propagation | Integration test | HIGH |
| T-UPT-004 | Confidence intervals are calculated | Model outputs | confidence_interval present | Missing | Data validation | HIGH |

### 2.9 Epistemic Type Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-ETT-001 | OBSERVATION ≠ MODEL_OUTPUT | Knowledge items | Different classification | Same classification | Type check | CRITICAL |
| T-ETT-002 | LOCAL_KNOWLEDGE ≠ SCIENTIFIC_FACT | Knowledge items | Different trust level | Same trust | Data validation | CRITICAL |
| T-ETT-003 | INFERENCE ≠ MEASUREMENT | Knowledge items | Different epistemic type | Same type | Type check | HIGH |
| T-ETT-004 | All knowledge items tagged | Knowledge registry | Has epistemic_type | Missing | Data validation | HIGH |

### 2.10 Service Ownership Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-SOT-001 | Each service has defined owner | Service registry | owner present | Missing | Data validation | HIGH |
| T-SOT-002 | Services respect bounded context | Service imports | No cross-context imports | Cross imports found | AST + mapping | HIGH |
| T-SOT-003 | All 75 services accounted for | Service registry | 75 entries | Missing service | Count check | HIGH |

### 2.11 C++/Python Boundary Tests

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-CPT-001 | C++ functions match Python fallbacks | Function comparison | Same signature | Mismatch | Signature check | HIGH |
| T-CPT-002 | Numerical parity C++/Python | Same inputs | Identical results | Difference > epsilon | Parity test | CRITICAL |
| T-CPT-003 | Temperature constant matches | C++ vs Python source | Both use 273.0 | Mismatch | Source inspection | HIGH |
| T-CPT-004 | Error handling consistent | C++ exception vs Python | Same exception type | Mismatch | Exception test | HIGH |

### 2.12 Legacy Dependency Detection

| test_id | purpose | input | expected_result | failure_condition | automation_method | priority |
|---------|---------|-------|-----------------|-------------------|-------------------|----------|
| T-LDD-001 | No engine→services imports | AST scan engine/ | No services imports | services import found | Python AST | CRITICAL |
| T-LDD-002 | No engine→database imports | AST scan engine/ | No database imports | database import found | Python AST | CRITICAL |
| T-LDD-003 | No engine→frontend imports | AST scan engine/ | No UI imports | UI import found | Python AST | HIGH |
| T-LDD-004 | No smart contract transfers | Source scan | Reference only | Production usage | File scan | HIGH |
| T-LDD-005 | services/hydroma empties removed | Directory scan | Directories deleted | Empty dirs remain | FileSystem check | LOW |

---

## 3. Test Execution Strategy

### Phase 1: Architecture Enforcement (Run first)
- T-IBT-001 through T-IBT-005 (import boundary tests)
- T-LDD-001 through T-LDD-005 (legacy dependency tests)
- Must pass before any other tests run

### Phase 2: Unit Validation
- T-UCT-001 through T-UCT-004 (unit consistency)
- T-CPT-001 through T-CPT-004 (C++/Python boundary)
- T-MRT-001 through T-MRT-005 (model registry integrity)

### Phase 3: Integration Validation
- T-EPT-001 through T-EPT-005 (engine purity)
- T-AIT-001 through T-AIT-004 (AI isolation)
- T-PVT-001 through T-PVT-004 (provenance)
- T-UPT-001 through T-UPT-004 (uncertainty propagation)
- T-ETT-001 through T-ETT-004 (epistemic types)

### Phase 4: Continuous Monitoring
- All tests run in CI/CD on every commit
- Architecture tests block merge on failure
- Performance tests run nightly

---

## 4. Findings

1. **NOT VERIFIED**: 37 of 50+ existing tests are UNRUNNABLE due to missing `database/` package.

2. **VERIFIED**: 1 test passes (`test_s06_watershed_design.py`).

3. **DESIGNED BUT NOT ENFORCED**: Import boundary tests exist conceptually (ECO-02/15 references `detect_imports.py`) but the script does NOT exist in codebase.

4. **BLOCKING**: All C++ tests UNRUNNABLE — no test execution infrastructure.

5. **PARTIAL**: `test_s11_parity_tripwires.py` exists for C++/Python parity but is UNRUNNABLE.

---

*Report generated: 2026-10-08*
*Status: NOT VERIFIED — tests cannot execute*