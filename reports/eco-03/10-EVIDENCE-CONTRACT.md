# ECO-03: Evidence Contract — Report 10
## Evidence Engine Specification

---

## Executive Summary

ECO-02/02/contracts/EvidenceContract.md defines the Evidence Engine contract. ECO-03 verification finds the Evidence Engine is **NOT IMPLEMENTED** — it exists as a design concept only.

---

## 1. Evidence Item Format (Required Fields)

| Field | Required | ECO-02 Definition | ECO-03 Code Status | Evidence |
|-------|----------|-------------------|-------------------|----------|
| `evidence_id` | YES | "EVID-YYYY-XXXXXX" | NOT IMPLEMENTED | No evidence_id in any result |
| `source_id` | YES | "CANON-XXX" | NOT IMPLEMENTED | No source_id field |
| `source_type` | YES | scientific_model/observational/etc | NOT IMPLEMENTED | No source_type classification |
| `epistemic_type` | YES | Epistemic classification | NOT IMPLEMENTED | No epistemic tagging |
| `timestamp` | YES | ISO 8601 | NOT IMPLEMENTED | No timestamp on results |
| `location` | YES | EPSG:4326 | NOT IMPLEMENTED | No location metadata |
| `unit` | YES | SI units | PARTIAL | UNIFORMAT defined, not enforced |
| `value` | YES | Data payload | YES | Model outputs have values |
| `quality` | YES | Quality score | NOT IMPLEMENTED | No quality metrics |
| `confidence` | YES | 0.0-1.0 | NOT IMPLEMENTED | No confidence on outputs |
| `provenance` | YES | Provenance chain | PARTIAL | `ResultProvenance` exists but minimal |
| `license` | YES | Data license | NOT IMPLEMENTED | No license tracking |
| `processing_history` | YES | Processing steps | NOT IMPLEMENTED | No processing history |
| `validation_status` | YES | validation result | NOT IMPLEMENTED | No validation status |

---

## 2. Evidence Chain Contract (VERIFIED)

### Chain Definition
```
Engine → Evidence → Decision → AI → User
```

### Current State Verification

| Link | Status | Evidence |
|------|--------|----------|
| Engine → Evidence | NOT ENFORCED | `engine/hydroma/wrapper.py` returns results without evidence tags |
| Evidence → Decision | NOT ENFORCED | No Evidence Engine; Tasmimyar receives data directly |
| Decision → AI | NOT ENFORCED | No architectural enforcement |
| AI → User | NOT ENFORCED | AI services (`services/ai/`) can access engine directly |

**Evidence**: 
- `engine/hydroma/wrapper.py` — returns raw computation results, no evidence tags
- `services/models/registry.py:22` — imports engine modules directly, bypassing Evidence Engine

**Status**: DESIGNED BUT NOT ENFORCED

---

## 3. Trust Level Assignment Rules

| Source Type | Default Trust | ECO-03 Verification | Evidence |
|-------------|---------------|---------------------|----------|
| VERIFIED models | HIGH | NOT ENFORCED | No trust level on outputs |
| SCIENTIFICALLY_SUPPORTED models | MEDIUM | NOT ENFORCED | No trust level on outputs |
| Observational data | HIGH | NOT ENFORCED | No observational metadata |
| Climate projections | MEDIUM | NOT ENFORCED | No source type tagging |
| AI predictions | LOW | NOT ENFORCED | AI has no trust classification |
| User input | VARIABLE | NOT ENFORCED | No user input tracking |

**Status**: NOT VERIFIED — trust levels defined but not assigned at runtime.

---

## 4. Evidence Collection (Current Implementation Status)

### What Exists
1. **`engine/hydroma/provenance.py`** — Minimal provenance tracking
   ```python
   class ResultProvenance:
       MODEL_OUTPUT = "model_output"
       OBSERVATION = "observation"
       # Missing: epistemic_type, confidence, validation_status, etc.
   ```

2. **No Evidence Engine module** — The concept exists only in documentation.

### What's Missing
- No `evidence/` package or module
- No evidence catalog or registry
- No evidence validation pipeline
- No trust level assignment
- No provenance chain enforcement
- No evidence distribution API

**Evidence**:
```bash
# Verify no evidence engine exists
Get-ChildItem "D:\HyDroMA\engine" -Recurse -Filter "evidence*" 
# Returns only: engine/hydroma/cpp_bridge/tests/test_benchmarks.py (file name contains "evidence")
# No evidence engine module exists
```

---

## 5. Validation Pipeline

### ECO-02 Contract
```python
class EvidenceValidator:
    def validate(self, evidence_item) -> EvidenceItem:
        """Pipeline: 1. Format → 2. Unit → 3. Provenance → 4. Trust → 5. Storage"""
```

### ECO-03 Verification
**Status**: NOT VERIFIED

- No `EvidenceValidator` class exists in codebase
- No validation pipeline implementation
- Only `test_s09_dimensional_consistency.py` attempts dimensional validation but is UNRUNNABLE

---

## 6. Cross-Validation Protocol

| Evidence Source | Validates Against | ECO-03 Status |
|-----------------|-------------------|---------------|
| MODIS ET vs Penman-Monteith | Monthly | NOT IMPLEMENTED |
| GPM IMERG vs Rain gauge | Daily | NOT IMPLEMENTED |
| CMIP6 vs Weather station | Monthly | NOT IMPLEMENTED |
| AI predictions vs Scientific models | Real-time | NOT IMPLEMENTED |

**Status**: NOT VERIFIED — cross-validation protocol defined but no implementation.

---

## 7. Evidence Item Creation Flow (Required)

1. Scientific model completes computation
2. Model output wrapped with metadata:
   - `source_id` = CANON-XXX
   - `source_type` = "scientific_model"
   - `epistemic_type` = "MODEL_OUTPUT"
   - `confidence` = based on model maturity
   - `unit` = SI unit
   - `provenance_chain` = [upstream evidence IDs]
   - `timestamp` = ISO 8601
3. Evidence item stored in immutable evidence store
4. Evidence item distributed via Evidence Engine API

**Status**: DESIGNED BUT NOT ENFORCED — no implementation exists.

---

## 8. Evidence Engine Distribution API (Required)

```python
# engine/evidence/__init__.py (TO BE IMPLEMENTED)

class EvidenceItem:
    evidence_id: str          # EVID-YYYY-XXXXXX
    source_id: str            # CANON-XXX
    source_type: str          # scientific_model, observational, etc.
    epistemic_type: str       # OBSERVATION, MODEL_OUTPUT, etc.
    timestamp: str            # ISO 8601
    location: str             # EPSG:4326
    unit: str                 # SI units
    value: Any                # data payload
    quality: float            # 0.0-1.0
    confidence: float         # 0.0-1.0
    provenance: dict          # provenance chain
    license: str              # data license
    processing_history: list  # processing steps
    validation_status: str    # PASS/FAIL/UNKNOWN

class EvidenceEngine:
    def get_evidence(self, criteria) -> List[EvidenceItem]:
        pass
    
    def emit_evidence(self, item: EvidenceItem) -> str:
        pass
    
    def validate_chain(self, evidence_ids: List[str]) -> bool:
        pass
```

---

## 9. Findings

1. **NOT VERIFIED**: Evidence Engine is defined as a contract but NO implementation exists in code.

2. **DESIGNED BUT NOT ENFORCED**: Evidence chain `Engine → Evidence → Decision → AI → User` is documented but not enforced. Services import engine directly, bypassing Evidence Engine.

3. **NOT VERIFIED**: Trust level assignment is defined but no runtime assignment exists.

4. **NOT VERIFIED**: Cross-validation protocol is defined but not implemented.

5. **BLOCKING**: Without an Evidence Engine, the architectural dependency chain cannot be enforced. This is a prerequisite for ECO-04.

6. **CONFLICTING EVIDENCE**: ECO-02/00 claims "[x] Evidence Engine (provenance) — Verified" but NO Evidence Engine module exists in source code.

---

## 10. Evidence Invariants

| Invariant | Status | Evidence |
|-----------|--------|----------|
| All results carry provenance | VIOLATED | Model outputs returned without evidence tags |
| Evidence chain is traceable | NOT ENFORCED | No evidence chain implementation |
| Trust levels are assigned | NOT ENFORCED | No trust level field on outputs |
| Epistemic type is classified | NOT ENFORCED | No epistemic type field |
| Confidence is propagated | NOT ENFORCED | No confidence field |

---

*Report generated: 2026-10-08*
*Status: NOT VERIFIED — requires implementation in ECO-04*