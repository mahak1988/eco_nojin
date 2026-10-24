# ECO-03: AI Boundary Contract — Report 13
## Evidence → Decision → AI → User Boundary Specification

---

## Executive Summary

This report verifies the AI boundary contract by examining each question in ECO-03 §6 and cross-referencing against actual source code.

**Status**: DESIGNED BUT NOT ENFORCED

---

## 1. AI Boundary Verification Matrix

| Question | ECO-02 Design | ECO-03 Code Status | Evidence |
|----------|---------------|-------------------|----------|
| Can AI read Evidence? | Yes, through Decision Engine | NOT ENFORCED | No Evidence Engine; AI reads engine directly |
| Can AI modify Evidence? | No | NOT ENFORCED | No code-level guard |
| Can conversational AI receive Knowledge context? | Yes (through Decision) | NOT ENFORCED | No architectural enforcement |
| Can AI summarize Evidence? | Yes (interpretation only) | DESIGNED ONLY | AI has summarization logic but no evidence integration |
| Can AI interpret Model Output? | Yes | PARTIAL | AI can process outputs but no formal interface |
| Can AI generate recommendation? | Only through Tasmimyar | NOT ENFORCED | No architectural enforcement |
| Must recommendation pass through Tasmimyar? | Yes | NOT ENFORCED | No code-level guard |
| What is scientific authority? | Model equations + validation | PARTIAL | Invariants defined but not enforced |
| Can AI change equations? | No | NOT ENFORCED | No import guard on AI |
| Can AI change parameters? | No | NOT ENFORCED | No import guard |
| Can AI change provenance? | No | NOT ENFORCED | No import guard |
| Can AI change epistemic status? | No | NOT ENFORCED | No import guard |

---

## 2. AI → Engine Internals Violation (VERIFIED — CRITICAL)

### The Violation Chain

1. **`engine/hydroma/generative_ai/__init__.py:20-22, 46-48`** imports from `services.ai.*`:
```python
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMProvider, LLMRouter
from services.ai.unified_rag import RAGConfig as RAGConfig, UnifiedRAG as RAGEngine
```

2. **`services/ai/admin_assistant.py:343-346`** imports scientific motors:
```python
from services.scientific_motors.aquacrop_real import AquaCropSimulator
from services.scientific_motors.crop_advisor import CropAdvisorMotor
from services.scientific_motors.irrigation_scheduler import IrrigationSchedulerMotor
from services.scientific_motors.planting_calendar import PlantingCalendarMotor
```

3. **`services/scientific_motors/*.py`** imports from engine:
```python
# services/scientific_motors/ (verified via grep)
from engine.hydroma.climate.et_calculator import ...
from engine.hydroma.cpp_bridge import is_cpp_available
from engine.hydroma.carbon.calculator import ...
from engine.hydroma.simulation.runners.rothc_runner import ...
```

### Violation Path
```
engine/hydroma/generative_ai/ 
  → imports services.ai.* 
    → (indirectly) services.scientific_motors.* 
      → imports engine.hydroma.*
```

This creates a **circular dependency**: engine → services → engine.

**Status**: CONFLICTING EVIDENCE — ECO-02/06 claims "AI isolation: 100% enforced" but the import chain shows engine importing services which import engine.

---

## 3. AI Layer Architecture (Current vs. Required)

### Current AI Architecture
```
services/
├── ai/                          # AI services (no direct engine imports)
│   ├── embedding_service.py
│   ├── llm_router.py
│   ├── unified_rag.py
│   ├── rag.py
│   ├── nlg.py
│   ├── admin_assistant.py       # ❌ imports services.scientific_motors + database
│   └── support_agent.py         # ❌ imports database
│
├── scientific_motors/           # ❌ NOT AI but scientific services used by AI
│   ├── aquacrop_real.py         # ❌ imports engine.hydroma.*
│   ├── irrigation_scheduler.py  # ❌ imports engine.hydroma.cpp_bridge
│   ├── carbon_sequestration.py  # ❌ imports engine.hydroma.*
│   └── ... (8 files)

engine/hydroma/generative_ai/    # ❌ ENGINE importing SERVICES (ECO-LEGACY-001)
├── __init__.py                  # ❌ imports services.ai.*
```

### Required Canonical AI Architecture
```
ai/                              # Isolated AI layer
├── __init__.py
├── interpretation/            # ONLY receives Evidence Engine output
├── research/                  # Experimental, NO engine imports
└── prompts/                   # Prompt templates

Evidence Engine → Decision Engine → AI → User
                                      ↑
                                      | (Tasmimyar oversight)
```

---

## 4. AI Authority Boundaries

### Core Principle
> "AI MAY INTERPRET. AI MAY NOT SILENTLY AUTHORIZE SCIENCE."

### Verification

| Action | AI May? | ECO-03 Evidence | Status |
|--------|---------|-----------------|--------|
| Read Evidence Engine output | YES | Conceptual, not enforced | DESIGNED |
| Interpret Model Output | YES | AI can process outputs in theory | DESIGNED |
| Generate alternative recommendations | YES (through Tasmimyar) | Not enforced | DESIGNED |
| Choose which model to run | YES (through Decision Engine) | Not enforced | DESIGNED |
| Modify model equations | NO | No guard | **VIOLATION RISK** |
| Change model parameters | NO | No guard | **VIOLATION RISK** |
| Change provenance | NO | No guard | **VIOLATION RISK** |
| Change epistemic status | NO | No guard | **VIOLATION RISK** |
| Bypass Evidence Engine | NO | No guard | **VIOLATION RISK** |
| Bypass Tasmimyar | NO | No guard | **VIOLATION RISK** |

### Evidence of AI Boundary Risk
- `services/ai/admin_assistant.py:343-346` imports `services.scientific_motors.*` which import `engine.hydroma.*`
- This means AI assistant has indirect access to scientific computation
- No guard prevents AI from modifying scientific logic

**Status**: DESIGNED BUT NOT ENFORCED — AI isolation is documented but not architecturally enforced.

---

## 5. AI Classification

### ECO-02 Classification
| Category | Status | ECO-03 Verification |
|----------|--------|---------------------|
| CORE | No AI modules | VERIFIED |
| IMPORTANT | No AI modules | VERIFIED |
| OPTIONAL | Some AI components | VERIFIED |
| RESEARCH | AI augmentation modules | VERIFIED |
| LEGACY | N/A | N/A |
| REMOVE | N/A | N/A |

**Status**: VERIFIED — AI is correctly classified as RESEARCH/OPTIONAL only.

---

## 6. AI Isolation Test Specification

### Required Tests (For ECO-04)

| test_id | purpose | input | expected | failure | automation | priority |
|---------|---------|-------|----------|---------|-----------|----------|
| AI-TEST-001 | AI cannot import engine | AST scan of services/ai/ | No engine imports | Any engine import found | AST-based scan | HIGH |
| AI-TEST-002 | Engine cannot import services | AST scan of engine/ | No services imports | Any services import found | AST-based scan | CRITICAL |
| AI-TEST-003 | AI outputs carry LOW trust | Check AI output structure | trust_level=LOW | Missing or HIGH | Runtime check | HIGH |
| AI-TEST-004 | AI recommendations go through Tasmimyar | Trace recommendation path | Must pass through decision engine | Direct to user | Integration test | HIGH |
| AI-TEST-005 | AI cannot modify model registry | Attempt to modify CANON-XXX | Reject | Any modification succeeds | Mutation test | CRITICAL |

---

## 7. AI Boundary Enforcement Status

| Enforcement Mechanism | ECO-02 Status | ECO-03 Status | Evidence |
|----------------------|---------------|---------------|----------|
| Import guard in AI layer | REQUIRED | NOT IMPLEMENTED | No import guard |
| Import guard in engine | REQUIRED | NOT IMPLEMENTED | No import guard |
| Trust level on AI output | REQUIRED | NOT IMPLEMENTED | No trust tags |
| Evidence Engine validation of AI | REQUIRED | NOT IMPLEMENTED | No Evidence Engine |
| Tasmimyar oversight of AI | REQUIRED | NOT IMPLEMENTED | No enforcement |

---

## 8. Findings

1. **BLOCKING**: `engine/hydroma/generative_ai/__init__.py` imports from `services.ai.*` — direct ECO-LEGACY-001 violation. This must be fixed before ECO-04.

2. **CONFLICTING EVIDENCE**: ECO-02/06/AI-ISOLATION.md claims "AI isolation: 100% enforced" but the import chain `engine → services.ai → services.scientific_motors → engine` creates a circular dependency that bypasses all isolation.

3. **DESIGNED BUT NOT ENFORCED**: AI MAY INTERPRET / MAY NOT AUTHORIZE SCIENCE principle exists in documentation but has NO code-level enforcement.

4. **NOT VERIFIED**: No import guards exist for AI layer isolation.

5. **BLOCKING**: AI authority over scientific equations, parameters, provenance, and epistemic status is NOT prevented by any code-level mechanism.

---

## 9. AI Boundary Invariants

| Invariant | ECO-02 Status | ECO-03 Status | Evidence |
|-----------|---------------|---------------|----------|
| INV-003: AI cannot silently authorize science | ACCEPTED | **VIOLATION RISK** | Circular import path exists |
| INV-004: AI cannot change equations | ACCEPTED | NOT ENFORCED | No guard |
| INV-005: AI cannot change provenance | ACCEPTED | NOT ENFORCED | No guard |
| INV-006: AI cannot change epistemic status | ACCEPTED | NOT ENFORCED | No guard |

---

*Report generated: 2026-10-08*
*Status: BLOCKED (requires ECO-LEGACY-001 fix)*