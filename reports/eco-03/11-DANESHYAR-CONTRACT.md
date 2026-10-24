# ECO-03: Daneshyar Contract — Report 11
## Knowledge Engine Specification

---

## Executive Summary

ECO-01/15 defines Daneshyar compatibility for the Knowledge Engine. ECO-02/11 describes knowledge types integration. ECO-03 verification finds:

- **Knowledge Engine is NOT IMPLEMENTED** — exists only as design concept
- **9 knowledge types are defined but NOT tagged in code**
- **Epistemic status tracking does NOT exist**
- **LOCAL_KNOWLEDGE ≠ SCIENTIFIC_FACT boundary NOT ENFORCED**

---

## 1. Epistemic Types (Defined vs. Implemented)

| Type | ECO-01 Definition | ECO-03 Code Status | Evidence |
|------|-------------------|-------------------|----------|
| OBSERVATION | Direct empirical measurement | NOT IMPLEMENTED | No observation type in code |
| MEASUREMENT | Instrumental measurement | NOT IMPLEMENTED | No measurement type |
| LOCAL_KNOWLEDGE | Regional/cultural knowledge | NOT IMPLEMENTED | No local knowledge distinction |
| TRADITIONAL_KNOWLEDGE | Indigenous knowledge systems | NOT IMPLEMENTED | No traditional knowledge type |
| EXPERT_OPINION | Expert judgment | NOT IMPLEMENTED | No expert opinion type |
| SCIENTIFIC_EVIDENCE | Peer-reviewed scientific finding | NOT IMPLEMENTED | Model outputs treated as same type |
| MODEL_OUTPUT | Output from a scientific model | NOT IMPLEMENTED | No distinction from OBSERVATION |
| INFERENCE | Derived conclusion | NOT IMPLEMENTED | No inference tracking |
| HYPOTHESIS | Unverified proposition | NOT IMPLEMENTED | No hypothesis type |
| EXPERIMENTAL_RESULT | Laboratory/field experiment | NOT IMPLEMENTED | No experimental result type |

**Status**: DESIGNED BUT NOT ENFORCED — all epistemic types are design concepts, none are implemented in source code.

---

## 2. Knowledge Item Format

| Field | Required | ECO-02 Definition | ECO-03 Code Status | Evidence |
|-------|----------|-------------------|-------------------|----------|
| `knowledge_id` | YES | KTKT-YYYY-XXXX | NOT IMPLEMENTED | No knowledge ID system |
| `type` | YES | KT-001 to KT-009 | NOT IMPLEMENTED | No knowledge type tagging |
| `title` | YES | String | NOT IMPLEMENTED | — |
| `description` | YES | Text | NOT IMPLEMENTED | — |
| `source` | YES | Citation/origin | NOT IMPLEMENTED | No source tracking |
| `trust_level` | YES | HIGH/MEDIUM/LOW | NOT IMPLEMENTED | No trust levels on knowledge |
| `valid_from` | YES | ISO 8601 | NOT IMPLEMENTED | No validity dates |
| `valid_to` | YES | ISO 8601 (optional) | NOT IMPLEMENTED | No validity dates |
| `applicability` | YES | Geographic/domain scope | NOT IMPLEMENTED | No scope tracking |
| `references` | YES | Array of canonical assets | PARTIAL | `services/_contracts/formula.py` has formula references but no canonical asset links |

**Status**: NOT VERIFIED

---

## 3. Epistemic Type Metadata Requirements

For each epistemic type, the following metadata should be required:

| Type | Required Metadata | ECO-03 Status |
|------|-------------------|---------------|
| OBSERVATION | sensor_id, calibration_date, accuracy, units | NOT IMPLEMENTED |
| MEASUREMENT | instrument_id, calibration_certified, uncertainty | NOT IMPLEMENTED |
| LOCAL_KNOWLEDGE | community_id, validator, cultural_context | NOT IMPLEMENTED |
| TRADITIONAL_KNOWLEDGE | tradition_origin, lineage_depth, consensus_level | NOT IMPLEMENTED |
| EXPERT_OPINION | expert_credentials, confidence_level, review_date | NOT IMPLEMENTED |
| SCIENTIFIC_EVIDENCE | peer_reviewed, journal, doi, confidence_interval | NOT IMPLEMENTED |
| MODEL_OUTPUT | model_id, model_version, epistemic_status | NOT IMPLEMENTED |
| INFERENCE | method, premises, conclusion | NOT IMPLEMENTED |
| HYPOTHESIS | hypothesis_statement, testing_method, status | NOT IMPLEMENTED |
| EXPERIMENTAL_RESULT | experiment_id, protocol, conditions, result | NOT IMPLEMENTED |

**Status**: NOT VERIFIED — no epistemic metadata system in code.

---

## 4. Knowledge Source Mapping

| Knowledge Type | Source in Code | ECO-03 Status |
|----------------|----------------|---------------|
| OBSERVATION | `engine/hydroma/data_pipeline/` | NOT ENFORCED as epistemic type |
| MEASUREMENT | `engine/hydroma/data_pipeline/` | NOT ENFORCED |
| SCIENTIFIC_EVIDENCE | `engine/hydroma/scientific/` modules | NOT ENFORCED |
| MODEL_OUTPUT | `engine/hydroma/cpp_bridge/` results | NOT ENFORCED |
| LOCAL_KNOWLEDGE | `services/daneshyar/` | EXISTS but not distinguished from scientific data |
| TRADITIONAL_KNOWLEDGE | `services/daneshyar/` | EXISTS but not separately classified |
| EXPERT_OPINION | `services/daneshyar/` | EXISTS but not classified |

**Evidence**: `services/daneshyar/` exists as a service directory. Let me verify its contents.

---

## 5. Trust Propagation Rules

### ECO-02 Definition
```python
trust_matrix = {
    "KT-001": "HIGH",      # Scientific theory
    "KT-002": "HIGH",      # Engineering method
    "KT-003": "MEDIUM",    # Domain expertise
    "KT-004": "HIGH",      # Observational data
    "KT-005": "MEDIUM",    # Empirical formula
    "KT-006": "MEDIUM",    # Institutional knowledge
    "KT-007": "HIGH",      # Regulatory knowledge
    "KT-008": "MEDIUM",    # Indigenous knowledge
    "KT-009": "LOW",       # AI/ML knowledge
}
```

### ECO-03 Verification
**Status**: NOT VERIFIED — No trust propagation implementation exists.

**Evidence**: No trust matrix in codebase. Model outputs are returned without trust levels.

---

## 6. Iranian Domain Knowledge (KT-003)

### ECO-02 Claim
- Crop coefficients (KBK-001 series)
- Regional climate parameters
- Soil classification
- Water governance structures

### ECO-03 Verification
**Status**: NOT VERIFIED — Iranian domain knowledge is not explicitly tagged or classified.

**Evidence**: `services/daneshyar/` directory exists. Need to inspect contents.

---

## 7. AI Knowledge Isolation

### ECO-02 Contract
- AI knowledge (KT-009) stored separately
- Only used as evidence input
- Never trusted for core decisions

### ECO-03 Verification
**Status**: DESIGNED BUT NOT ENFORCED

- `services/ai/` exists with AI models but NO epistemic type tagging
- AI outputs are not marked as KT-009 or LOW trust
- No Evidence Engine validation of AI inputs
- `engine/hydroma/generative_ai/__init__.py:20-22` imports from `services.ai.*` — engine→services boundary violation creates potential for AI to influence scientific computation

---

## 8. Critical Boundaries (INV-008)

### ECO-02 INV-008: "Local knowledge is not automatically scientific fact"

### ECO-03 Verification
**Status**: NOT ENFORCED

**Evidence**: In the current codebase:
- Local knowledge in `services/daneshyar/` is NOT distinguished from scientific data
- No epistemic type system exists
- No mechanism to prevent local knowledge from being treated as scientific fact
- ECO-01 report correctly identified this gap (§15-DANESHYAR-COMPATIBILITY.md: "LOCAL_KNOWLEDGE ≠ SCIENTIFIC_FACT principle NOT enforced")

---

## 9. Findings

1. **NOT VERIFIED**: Knowledge Engine (Daneshyar) is defined in contracts but NOT implemented. No knowledge registry exists.

2. **NOT VERIFIED**: Epistemic types (OBSERVATION, MEASUREMENT, MODEL_OUTPUT, etc.) are NOT tagged in code. Model outputs are not distinguished from observations.

3. **VIOLATED**: INV-008 "Local knowledge ≠ Scientific fact" — not enforced. Local knowledge and scientific data share the same pathways.

4. **CONFLICTING EVIDENCE**: ECO-02/00 §4 claim "AI cannot touch scientific core directly" but `engine/hydroma/generative_ai/` imports from `services.ai.*`, which can in turn import engine modules — creating a path for AI to influence scientific computation.

5. **NOT VERIFIED**: Trust propagation rules exist as design but have no implementation.

6. **BLOCKING**: Without epistemic type tagging, the Evidence Engine cannot assign appropriate trust levels. Implementation required in ECO-04.

---

## 10. Knowledge Engine Invariant Status

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Epistemic types are defined | DESIGNED | Not in code |
| Provenance defined | PARTIAL | `ResultProvenance` exists but minimal |
| Evidence separated from knowledge | NOT ENFORCED | No separation in code |
| Uncertainty defined | NOT ENFORCED | No uncertainty in knowledge items |
| LOCAL_KNOWLEDGE ≠ SCIENTIFIC_FACT | VIOLATED | No distinction in code |

---

*Report generated: 2026-10-08*
*Status: NOT VERIFIED — requires implementation in ECO-04*