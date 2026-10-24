# ECO-03: Implementation Blockers — Report 25
## Hard Blockers for ECO-04

---

## Executive Summary

This report identifies all hard blockers that prevent progression to ECO-04 (Controlled Implementation). The architecture is NOT READY_FOR_ECO_04.

---

## 1. Hard Blockers (Cannot Start ECO-04)

| blocker_id | description | category | evidence | resolution_required |
|------------|-------------|----------|----------|---------------------|
| B-001 | Engine→Services import violation | Architectural | `engine/hydroma/generative_ai/__init__.py:20-22,46-48` imports from `services.ai.*` | FIXED — moved to `services/ai/generative_ai/`, removed from engine |
| B-002 | Missing `database/` package | Dependency | `engine/data_connector.py:86` imports `database.hub`; package not in repository | FIXED — created minimal `database/` stub package |
| B-003 | Missing dependency manifest | Dependency | No `requirements.txt`, `pyproject.toml`, or `setup.py` | FIXED — created `pyproject.toml` |
| B-005 | No import guard enforcement | Architectural | `tools/detect_imports.py` and `tools/check_boundary.py` do NOT exist | MUST IMPLEMENT |
| B-006 | No Engine Gateway implementation | Architectural | Contract exists but no `engine/gateway/` module | MUST IMPLEMENT |
| B-007 | No Evidence Engine implementation | Architectural | Contract exists but no `knowledge/evidence/` module | MUST IMPLEMENT |
| B-008 | No uncertainty propagation | Uncertainty | All outputs lack uncertainty metadata | MUST IMPLEMENT |
| B-009 | No epistemic type tagging | Knowledge | No epistemic types in code | MUST IMPLEMENT |
| B-010 | AI isolation not enforced | AI | No import guard; circular import path exists | MUST FIX |
| B-011 | All 21 C++ tests UNRUNNABLE | Testing | Missing `database/` package | IMPROVED — `import engine` now succeeds; tests still need numpy/dependencies installed |
| B-012 | Services bypass Engine Gateway | Architectural | 100+ direct engine imports in services/ | MUST ENFORCE gateway pattern |
| B-013 | No provenance on model outputs | Data Integrity | No evidence tags on outputs | MUST IMPLEMENT |
| B-014 | No trust levels on outputs | Data Integrity | No trust_level field on results | MUST IMPLEMENT |
| B-015 | Theis Solution (CANON-005) unverified | Scientific | Series convergence undocumented | Requires scientific review |

---

## 2. Resolved Blockers (Already Fixed)

| blocker_id | description | category | evidence | status |
|------------|-------------|----------|----------|--------|
| B-004 | Temperature constant divergence | Scientific | Fixed: both C++ and Python now use 273.16 for radiation and 273.0 for aerodynamic term (per FAO-56) | RESOLVED |
| B-016 | cpp_bindings.py duplication | Architectural | RESOLVED: `cpp_bindings.py` now delegates to `cpp_bridge` | RESOLVED |
| B-017 | adapters/ package missing | Dependency | RESOLVED: `adapters/engine_adapter.py` created during ECO-00 audit | RESOLVED |

---

## 3. Detailed Blocker Analysis

### B-001: Engine → Services Import (CRITICAL)

**File**: `engine/hydroma/generative_ai/__init__.py:20-22, 46-48`

**Evidence**:
```python
# Lazy import (lines 20-22)
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMProvider, LLMRouter
from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine

# Eager import (lines 46-48) — same imports repeated
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMProvider, LLMRouter
from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine
```

**Impact**: Creates circular dependency `engine → services → engine`. Breaks `import engine` in isolation.

**Resolution**: 
1. Remove `engine/hydroma/generative_ai/` module from engine
2. Move to `services/ai/generative_ai/`
3. Ensure `services/ai/` does NOT import from engine directly
4. Verify circular import is broken

**Blocker Type**: HARD BLOCKER — ECO-04 must fix this

---

### B-002: Missing Database Package (CRITICAL)

**Evidence**:
- `engine/data_connector.py:86`: `from database.hub import hub` (deferred import)
- `engine/resource_manager.py:45,70,83`: `from database.hub import hub` (deferred)
- `engine/ports/session.py:162`: `from database.config import SessionLocal`
- `engine/hydroma/biofertilizer/models.py:32`: `from database.base import Base`
- Test result: `python -c "import engine"` → `ModuleNotFoundError: No module named 'database'`

**Impact**: 100% of engine tests UNRUNNABLE. All 21 C++ tests blocked. All 16 Python strict tests blocked.

**Resolution Options**:
1. **Provision** `database/` package with required interfaces
2. **Refactor** engine to remove database dependency
3. **Mock** database in test environment

**Blocker Type**: HARD BLOCKER

---

### B-003: Missing Dependency Manifest (HIGH)

**Evidence**: `reports/engine-services/INVENTORY.md §6`:
> "No requirements.txt, pyproject.toml, setup.py, or similar dependency manifest was found"

**Impact**: Cannot reproduce builds; cannot install dependencies reliably; cannot run tests in CI.

**Resolution**: Create `pyproject.toml` with all inferred dependencies.

**Blocker Type**: HARD BLOCKER

---

### B-005: No Import Guard Enforcement (CRITICAL)

**Evidence**: 
- `engine/strict_tests/test_s01_import_integrity.py` only checks internal engine imports
- `tools/detect_imports.py` and `tools/check_boundary.py` referenced in ECO-02/15 do NOT exist
- No AST-based import guard at CI/CD level

**Impact**: Architecture violations go undetected. New violations accumulate silently.

**Resolution**: Implement import guard tool + CI integration.

**Blocker Type**: HARD BLOCKER

---

### B-006: No Engine Gateway Implementation (CRITICAL)

**Evidence**: ECO-02/EngineGatewayContract.md defines the contract. No `engine/gateway/` module exists.

**Impact**: Services import engine directly; no request validation, unit normalization, or provenance capture at boundary.

**Resolution**: Implement Engine Gateway module in ECO-04.

**Blocker Type**: HARD BLOCKER

---

### B-007: No Evidence Engine Implementation (CRITICAL)

**Evidence**: ECO-02/EvidenceContract.md defines the contract. No `knowledge/evidence/` module exists.

**Impact**: No provenance tracking, no trust levels, no evidence chain enforcement.

**Resolution**: Implement Evidence Engine in ECO-04.

**Blocker Type**: HARD BLOCKER

---

### B-008: No Uncertainty Propagation (CRITICAL)

**Evidence**: All model outputs are point estimates with `double` or `vector<double>` return types. No uncertainty metadata anywhere in code.

**Impact**: Results cannot be trusted for decision-making; VIOLATES INV-011.

**Resolution**: Add uncertainty fields to all model outputs; implement uncertainty propagation.

**Blocker Type**: HARD BLOCKER

---

### B-009: No Epistemic Type Tagging (CRITICAL)

**Evidence**: No epistemic type system (OBSERVATION, MODEL_OUTPUT, etc.) exists in code. `ResultProvenance` in `engine/hydroma/provenance.py` has only 2 constants.

**Impact**: Cannot distinguish model output from observation; VIOLATES INV-007.

**Resolution**: Implement epistemic type system with tagging on all data.

**Blocker Type**: HARD BLOCKER

---

### B-010: AI Isolation Not Enforced (CRITICAL)

**Evidence**: 
- `engine/hydroma/generative_ai/__init__.py` imports from `services.ai.*`
- `services/ai/admin_assistant.py:343` imports from `services.scientific_motors.*`
- `services/scientific_motors/*.py` imports from `engine.hydroma.*`

Circular import chain: `engine → services.ai → services.scientific_motors → engine`

**Impact**: AI can potentially influence scientific computation through import chain.

**Resolution**: Fix import chain; implement AI isolation boundary.

**Blocker Type**: HARD BLOCKER

---

### B-011: All Tests UNRUNNABLE (CRITICAL)

**Evidence**: `reports/engine-services/TEST-REPORT.md §3`: **Root blocker: `database/` package is missing**. 0 of ~50+ tests executable.

**Impact**: Cannot verify any code changes; no CI/CD feedback.

**Resolution**: Provision database package or refactor engine to remove dependency.

**Blocker Type**: HARD BLOCKER

---

### B-012: Services Bypass Engine Gateway (HIGH)

**Evidence**: 100+ imports from `services/` to `engine.*` found via grep. No gateway routing.

**Impact**: No request validation, unit normalization, or provenance capture.

**Resolution**: Implement Engine Gateway; add import guard to enforce gateway pattern.

**Blocker Type**: HARD BLOCKER

---

### B-013: No Provenance on Model Outputs (HIGH)

**Evidence**: `engine/hydroma/wrapper.py` returns results without provenance tags. `engine/hydroma/provenance.py` has minimal `ResultProvenance` class.

**Impact**: Cannot trace results to source; audit trail incomplete.

**Resolution**: Add provenance to all model outputs.

**Blocker Type**: HARD BLOCKER

---

### B-014: No Trust Levels on Outputs (HIGH)

**Evidence**: No `trust_level` field on any output. Evidence Engine contract defines trust levels but no implementation.

**Impact**: Cannot weight evidence appropriately in decisions.

**Resolution**: Implement trust level assignment.

**Blocker Type**: HARD BLOCKER

---

### B-015: Theis Solution Unverified (HIGH)

**Evidence**: ECO-01/20-CANONICAL-ASSETS.md CANON-005: "series convergence undocumented". ECO-01/23 §3: "P0 (critical) — 2 items, 50% resolved".

**Impact**: CANON-005 cannot be canonized until reviewed.

**Resolution**: Scientific review of Theis series convergence.

**Blocker Type**: SCIENTIFIC BLOCKER

---

## 4. Blocker Summary by Category

| Category | Blocking Count | Non-blocking Count |
|----------|----------------|-------------------|
| Architectural | 7 | 0 |
| Dependency | 1 | 0 |
| Uncertainty | 1 | 0 |
| Knowledge | 1 | 0 |
| AI | 1 | 0 |
| Testing | 1 | 0 |
| Data Integrity | 2 | 0 |
| Scientific | 1 | 0 |
| **Total** | **15** | **0** |

---

## 5. Blocker Resolution Priority

### P0 (Must fix before ECO-04)
1. B-001: Remove engine→services import
2. B-002: Provision database package or remove dependency
3. B-003: Create dependency manifest
4. B-005: Implement import guards
5. B-011: Make tests runnable (depends on B-002)

### P1 (Must fix in ECO-04.1-EOC-04.5)
6. B-006: Implement Engine Gateway
7. B-007: Implement Evidence Engine
8. B-008: Implement uncertainty propagation
9. B-009: Implement epistemic type tagging
10. B-010: Fix AI isolation violations
11. B-012: Enforce gateway pattern for services
12. B-013: Add provenance to outputs
13. B-014: Add trust levels to outputs

### P2 (Must fix in ECO-04.4)
14. B-015: Complete Theis scientific review

---

## 6. Readiness Assessment

| Readiness Criterion | Status |
|---------------------|--------|
| Engine importable | NOT VERIFIED |
| Tests runnable | NOT VERIFIED |
| Engine Gateway exists | NOT VERIFIED |
| Evidence Engine exists | NOT VERIFIED |
| Import guards working | NOT VERIFIED |
| AI isolation enforced | NOT VERIFIED |
| Uncertainty propagation | NOT VERIFIED |
| Epistemic type tagging | NOT VERIFIED |
| Provenance on all outputs | NOT VERIFIED |
| Trust levels on all outputs | NOT VERIFIED |

**Overall Assessment**: NOT READY_FOR_ECO_04

**Reasons**:
1. 12 remaining hard blockers (3 FIXED: B-001, B-002, B-003)
2. Tests still require numpy and other dependencies to be installed
3. Architectural enforcement mechanisms (import guards) missing
4. All knowledge/decision/evidence engines exist as design documents only

---

*Report generated: 2026-10-08*
*Status: BLOCKED — 12 remaining hard blockers prevent ECO-04*