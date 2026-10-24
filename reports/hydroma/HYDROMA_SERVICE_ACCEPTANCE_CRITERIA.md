# HYDROMA SERVICE ACCEPTANCE CRITERIA

**Generated**: 2026-10-09  
**Purpose**: Define acceptance criteria for HyDroMA services

---

## 1. Service Contract Template

Every service must define:
- **Purpose**: Clear statement of responsibility
- **Inputs**: Request format, validation rules
- **Outputs**: Response format, data types
- **Dependencies**: Only through Gateway facade or defined ports
- **Error behavior**: Documented error responses
- **Test coverage**: Acceptance test suite

---

## 2. Tasmimyar Decision Service

### Acceptance Criteria
| Criterion | Requirement | Status |
|-----------|-------------|--------|
| Tasmimyar-01 | Decision service has defined endpoints | ✅ POST /api/v1/decisions/recommend |
| Tasmimyar-02 | Decision engine separates from service | ✅ engine/tasmimyar + services/tasmimyar |
| Tasmimyar-03 | Decisions carry provenance | ✅ Evidence integration |
| Tasmimyar-04 | Criteria support weights and thresholds | ✅ DecisionCriterion with weight |
| Tasmimyar-05 | Decision results include confidence | ✅ DecisionOutcome has confidence |

---

## 3. Soil Router Service

### Acceptance Criteria
| Criterion | Requirement | Status |
|-----------|-------------|--------|
| Soil-01 | All soil endpoints return standardized response | ✅ GatewayResult format |
| Soil-02 | 13 soil tools accessible | ✅ Facades created |
| Soil-03 | Errors mapped to GatewayError | ✅ Error propagation |
| Soil-04 | No direct engine imports | ✅ 0 INV-003 violations |

---

## 4. Climate Router Service

### Acceptance Criteria
| Criterion | Requirement | Status |
|-----------|-------------|--------|
| Climate-01 | ET0 computation routes through Gateway | ✅ CANON-001, CANON-002 |
| Climate-02 | Weather data ingestion via facade | ✅ fetch_daily_weather proxy |
| Climate-03 | Satellite indices computed via C++ bridge | ✅ NDVI/NDWI via facade |

---

## 5. Integration Acceptance Criteria

| ID | Criterion | Status |
|----|-----------|--------|
| INT-01 | Requests reach scientific capability via public API | ✅ Facade pattern |
| INT-02 | Responses conform to valid schema | ✅ GatewayResult |
| INT-03 | Errors propagate as structured errors | ✅ GatewayError |
| INT-04 | Request IDs preserved across components | ⚠️ Partially (no distributed tracing) |
| INT-05 | Model version + data source traceable | ⚠️ Partial via Evidence |
| INT-06 | Uncertainty status preserved | ⚠️ Not deleted but not fully propagated |
| INT-07 | External service failures don't cause unknown behavior | ⚠️ Not fully tested |
| INT-08 | Contract changes via versioning | ❌ Not implemented |
| INT-09 | End-to-end tests for main paths | ✅ 4/5 e2e tests pass |
| INT-10 | Unverified external connections reported | ✅ BLOCKED status documented |

---

## 6. Architecture Acceptance Criteria

| ID | Criterion | Status |
|----|-----------|--------|
| ARCH-01 | Service dependency boundary respected | ✅ PASS (0 violations) |
| ARCH-02 | Gateway has real dispatch | ✅ PASS (68 model dispatch) |
| ARCH-03 | Registry manages models | ✅ PASS (68 registered) |
| ARCH-04 | Persistence has contract | ⚠️ PARTIAL (interface defined) |
| ARCH-05 | Evidence Engine tracks provenance | ✅ PASS |
| ARCH-06 | Knowledge Engine has testable behavior | ⚠️ PARTIAL (skeleton exists) |
| ARCH-07 | Decision Engine + Tasmimyar clearly bounded | ✅ PASS |
| ARCH-08 | APIs documented and versioned | ⚠️ PARTIAL |
| ARCH-09 | Architecture tests executed | ✅ PASS (217 tests) |
| ARCH-10 | External connections via explicit interfaces | ⚠️ PARTIAL |
| ARCH-11 | No direct blockchain dependency in core | ✅ PASS |
| ARCH-12 | Evidence and provenance traceable | ✅ PASS (5 evidence items)