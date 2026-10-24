# ECO-02: Conceptual Scenarios Validation

## Architecture Scenarios 51-66: Boundary and Integration Tests

---

## Source Evidence
- ECO-02.md Section 51-66 (Conceptual Scenarios)
- ECO-01/11-CPP-PYTHON-BOUNDARY.md
- ECO-01/22-LEGACY-DEPENDENCY-STRATEGY.md
- ECO-01/12-AI-FORENSICS.md

---

## Scenario 51: ET Computation Flow

### Description
Penman-Monteith ET0 computation through the full architecture stack.

### Steps
1. User requests ET calculation via API
2. Application Orchestration routes to Domain Services
3. Domain Services call Engine Gateway
4. Engine Gateway calls Scientific Engine (Python)
5. Scientific Engine calls C++ kernel via ctypes
6. Buffer Protocol transfers numpy array zero-copy
7. C++ kernel computes, returns result
8. Engine Gateway validates SI units, tags provenance
9. Evidence Engine registers tagged evidence
10. Decision Engine uses evidence for irrigation scheduling

### Expected Result
- Computation completes in <10s for 1M grid points
- Provenance tag includes CANON-001 reference
- Trust level: HIGH
- No direct services→engine imports

### Verification
Run: `pytest tests/test_et_flow.py::test_scenario_51`

---

## Scenario 52: AI Augmentation Request

### Description
AI provides irrigation recommendation augmentation through isolated path.

### Steps
1. Scientific Engine computes ET (CANON-001)
2. Evidence Engine tags result (trust: HIGH)
3. Decision Engine includes evidence in decision context
4. Decision Engine passes validated evidence to AI layer
5. AI processes evidence, generates augmentation
6. AI output returned to Decision Engine
7. Decision Engine validates AI output against policy rules

### Expected Result
- AI never directly accesses Scientific Engine
- All AI inputs carry provenance tags
- AI output trust level: LOW
- Decision Engine filters AI output

### Verification
Run: `pytest tests/test_ai_isolation.py::test_scenario_52`

---

## Scenario 53: Groundwater Model Integration

### Description
MODFLOW groundwater model coupled with SWAT watershed model.

### Steps
1. SWAT computes surface water runoff
2. Evidence Engine tags SWAT output
3. Groundwater Service extracts boundary conditions
4. C++ groundwater kernel (MODFLOW) receives data
5. Buffer protocol transfers coupling data
6. MODFLOW computes groundwater flow
7. Evidence Engine tags groundwater output
8. Decision Engine considers both surface and groundwater

### Expected Result
- Coupling data carries provenance from both models
- Units converted via UNIFORMAT at boundary
- No circular dependencies

### Verification
Run: `pytest tests/test_coupling.py::test_scenario_53`

---

## Scenario 54: Climate Scenario Evaluation

### Description
Evaluating water availability under RCP 8.5 climate scenario.

### Steps
1. CMIP6 (CANON-018) provides climate projections
2. Evidence Engine validates ensemble consistency
3. WRF downscales climate data (CANON-014)
4. Penman-Monteith computes ET under future climate
5. FAO-56 computes crop water demand (CANON-009)
6. Decision Engine evaluates scenario SCEN-003
7. Results compared against SCEN-001 (baseline)

### Expected Result
- Ensemble spread quantifies uncertainty
- All evidence carries scenario provenance
- Trust level: MEDIUM (climate projections)

### Verification
Run: `pytest tests/test_scenario_evaluation.py::test_scenario_54`

---

## Scenario 55: Service Consolidation Migration

### Description
Migrating from 73 services to 8 bounded contexts.

### Steps
1. Identify duplicate infrastructure services
2. Create Platform Core module
3. Migrate config/logging to Platform Core
4. Verify no import violations (ECO-LEGACY-001)
5. Update Evidence Engine integration points
6. Run integration tests

### Expected Result
- 73 services → 8 bounded context modules
- Zero import violations detected
- All existing functionality preserved

### Verification
Run: `python tools/check_imports.py --root . --report`

---

## Scenario 56: Model Duplication Resolution

### Description
Resolving CONFLICT-001 (duplicate Penman-Monteith).

### Steps
1. Identify all Penman-Monteith implementations
2. Select canonical (CANON-001)
3. Deprecate legacy implementations with redirect
4. Update all callers to use canonical
5. Verify output consistency

### Expected Result
- Single Penman-Monteith implementation
- All callers use CANON-001
- No functional regression

### Verification
Run: `pytest tests/test_canonical_mapping.py::test_scenario_56`

---

## Scenario 57: Evidence Validation Pipeline

### Description
New evidence entering the system must be validated.

### Steps
1. Scientific Engine emits computation result
2. Evidence Engine receives for validation
3. Format validation (JSON schema)
4. Unit validation (SI compliance)
5. Provenance chain completeness check
6. Trust level assignment based on source
7. Store in evidence database

### Expected Result
- All evidence has valid format
- Units in SI
- Complete provenance chain
- Correct trust level

### Verification
Run: `pytest tests/test_evidence_pipeline.py::test_scenario_57`

---

## Scenario 58: Decision Engine Policy Violation

### Description
Policy rule violation detected in water allocation decision.

### Steps
1. Evidence Engine provides validated water data
2. Decision Engine evaluates resource allocation
3. DE-001 (Policy Rules) checks environmental limits
4. DE-011 (Environmental Limits) detects violation
5. Decision Engine flags non-compliance
6. Stakeholder notified through Product Experience

### Expected Result
- Violation detected before action
- Full provenance trace available
- User notified with explanation

### Verification
Run: `pytest tests/test_policy_violation.py::test_scenario_58`

---

## Scenario 59: Boundary Protocol Error Handling

### Description
C++ kernel returns error (invalid input).

### Steps
1. Python sends invalid data to Engine Gateway
2. Gateway validates input (UNIFORMAT)
3. Gateway converts and sends to C++
4. C++ kernel detects error, returns error code
5. Gateway translates to Python exception
6. Evidence Engine logs with provenance
7. User notified with recoverable error message

### Expected Result
- Clean error propagation
- Evidence logged
- System remains stable

### Verification
Run: `pytest tests/test_boundary_errors.py::test_scenario_59`

---

## Scenario 60: Research Gap Tracking

### Description
New research gap identified in crop coefficient estimation.

### Steps
1. Evidence Engine detects low confidence in KT-003 data
2. Gap auto-registered in Research Gaps Registry
3. Gap assigned priority P1
4. Assigned to agronomist
5. Linked to CANON-004 (Blaney-Crop)
6. Review queue updated

### Expected Result
- Gap captured with metadata
- Assigned owner and timeline
- Linked to affected models

### Verification
Run: `pytest tests/test_gap_tracking.py::test_scenario_60`

---

## Scenario 61: Scientific Review Process

### Description
Peer review of a model upgrade candidate.

### Steps
1. Model AUDIT-MODEL-016 (RegCM) candidate for maturity upgrade
2. Evidence Engine validates new benchmarks
3. Review queue assigns P1 priority
4. Two peer reviewers evaluate
5. Decision: APPROVE upgrade to SCIENTIFICALLY_SUPPORTED
6. Registry updated

### Expected Result
- Rigorous review process
- Documented decision
- Updated model registry

### Verification
Run: `pytest tests/test_review_process.py::test_scenario_61`

---

## Scenario 62: Knowledge Type Integration

### Description
Indigenous knowledge (KT-008) integrated into floodplain management.

### Steps
1. Indigenous knowledge item registered in Daneshyar
2. Trust level assigned: MEDIUM
3. Knowledge linked to KT-003 (Domain Expertise)
4. Evidence Engine incorporates into flood model
5. Decision Engine considers in allocation
6. Full provenance tracked

### Expected Result
- Indigenous knowledge properly tagged
- Trust level propagated correctly
- Decision includes indigenous insights

### Verification
Run: `pytest tests/test_knowledge_integration.py::test_scenario_62`

---

## Scenario 63: UNIFORMAT Unit Conversion

### Description
Imperial unit input converted to SI at boundary.

### Steps
1. User provides temperature in Fahrenheit
2. Engine Gateway detects non-SI unit
3. Gateway converts to Kelvin via UNIFORMAT
4. C++ kernel receives Kelvin input
5. Output computed and tagged with SI units
6. Evidence Engine logs conversion in provenance

### Expected Result
- No calculation errors
- Conversion logged
- Output in SI

### Verification
Run: `pytest tests/test_unical_format.py::test_scenario_63`

---

## Scenario 64: Import Violation Detection

### Description
Legacy import violation detected at CI/CD.

### Steps
1. Developer commits code with engine/→services/ import
2. CI/CD pre-commit hook detects violation
3. Import guard raises ImportError
4. Commit blocked
5. Developer notified with ECO-LEGACY-001 reference

### Expected Result
- Violation detected immediately
- Commit blocked
- Clear error message

### Verification
Run: `python tools/check_imports.py --root . --fail-fast`

---

## Scenario 65: Duplication Detection

### Description
Static analysis detects duplicate algorithm.

### Steps
1. Developer adds new ET implementation
2. Similarity scan detects 90% match with CANON-001
3. Review system flags as duplicate
4. Developer redirected to canonical
5. PR blocked until duplication resolved

### Expected Result
- Duplicate prevented
- Canonical used instead

### Verification
Run: `python tools/similarity_scan.py --dir engine/ services/`

---

## Scenario 66: Full Architecture Verification

### Description
End-to-end verification of all architecture invariants.

### Steps
1. Run all boundary checks
2. Verify import guards active
3. Verify AI isolation enforced
4. Verify evidence chain intact
5. Verify model maturity classifications
6. Verify canonical asset registry
7. Verify service consolidation plan

### Expected Result
- All architecture invariants maintained
- No critical violations
- Documentation up-to-date

### Verification
Run: `python tools/verify_architecture.py --all-checks`

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01 all reports*
*These scenarios verify architecture correctness — they do not implement the platform*
