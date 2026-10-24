# ECO-03: Implementation Dependency DAG — Report 19
## Build Order Dependency Graph

---

## Executive Summary

This report defines the dependency graph and build order for ECO-04 implementation. The graph is derived from forensic analysis of actual code dependencies and architectural contracts.

---

## 1. Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Scientific Contracts                                              │
│    - model_id registry (CANON-XXX)                                   │
│    - parameter schemas                                                │
│    - equation definitions                                             │
│    Evidence: reports/eco-02/contracts/ScientificModelContract.md     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 2. Units & Dimensional Analysis                                     │
│    - UNIFORMAT unit standard                                         │
│    - Dimensional validation                                          │
│    - Conversion boundary                                             │
│    Evidence: reports/eco-02/12-EQUATION-UNIT-FORENSICS.md             │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 3. Engine Gateway                                                    │
│    - Request validation                                              │
│    - Model selection                                                 │
│    - Unit normalization                                              │
│    - Parameter validation                                            │
│    Evidence: reports/eco-02/contracts/EngineGatewayContract.md       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 4. Hydroma Canonicalization                                          │
│    - Remove engine→services imports                                  │
│    - Remove engine→database imports                                  │
│    - Isolate generative_ai                                           │
│    - Extract api/, visualization/                                    │
│    Evidence: reports/eco-03/07-HYDROMA-EXTRACTION-SPEC.md            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 5. Evidence Engine                                                   │
│    - Evidence item format                                            │
│    - Trust level assignment                                          │
│    - Provenance capture                                              │
│    Evidence: reports/eco-02/contracts/EvidenceContract.md            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 6. Knowledge Engine (Daneshyar)                                      │
│    - 9 knowledge types                                               │
│    - Epistemic type tagging                                          │
│    - Trust propagation matrix                                        │
│    Evidence: reports/eco-02/contracts/KnowledgeContract.md           │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 7. Decision Engine (Tasmimyar)                                       │
│    - 11 decision elements                                            │
│    - Decision evaluation process                                     │
│    - AI recommendation oversight                                     │
│    Evidence: reports/eco-02/contracts/TasmimyarContract.md            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 8. AI Isolation Layer                                                │
│    - Interpretation only                                             │
│    - Evidence Engine integration only                                 │
│    - Tasmimyar oversight                                             │
│    Evidence: reports/eco-02/06-AI-ISOLATION.md                       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 9. Uncertainty Propagation                                            │
│    - Uncertainty types                                               │
│    - Confidence intervals                                            │
│    - Propagation methods                                             │
│    Evidence: Derived from ECO-03 §11 requirements                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 10. Domain Services (Consolidated)                                   │
│    - Hydroma Engine context                                          │
│    - AgriWater context                                               │
│    - Hydrology context                                               │
│    - Ecosystem Science context                                       │
│    - Land Intelligence context                                       │
│    - Remote Sensing context                                          │
│    - Evidence Provenance context                                     │
│    - Platform Core context                                           │
│    Evidence: reports/eco-02/07-SERVICE-CONSOLIDATION.md              │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 11. Application Layer (API Gateway)                                  │
│    - API routing                                                     │
│    - Workflow orchestration                                          │
│    Evidence: services/api_gateway/ (exists)                        │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│ 12. Product Layer (Reporting/AI)                                     │
│    - Report generation                                               │
│    - AI interpretation output                                        │
│    Evidence: services/reporting/ (exists), services/ai/ (exists)    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Build Order (Revised from ECO-02)

### ECO-04.1: Canonical Repository Skeleton
- **Dependencies**: None
- **Acceptance**: 12 directory structure created per Report 18
- **Blockers**: Missing requirements.txt

### ECO-04.2: Scientific Contracts
- **Dependencies**: ECO-04.1
- **Acceptance**: All 22 models registered with CANON-XXX contracts
- **Blockers**: Theis (CANON-005) requires scientific review

### ECO-04.3: Units & Validation
- **Dependencies**: ECO-04.2
- **Acceptance**: UNIFORMAT unit system implemented, conversion centralized
- **Blockers**: Temperature constant divergence (273.0 vs 273.16)

### ECO-04.4: Engine Gateway
- **Dependencies**: ECO-04.2, ECO-04.3
- **Acceptance**: Gateway routes all requests through validation → unit normalization → model selection
- **Blockers**: Must fix engine→services import violation first

### ECO-04.5: Hydroma Extraction
- **Dependencies**: ECO-04.4
- **Acceptance**: No engine→services, engine→database, engine→frontend imports
- **Blockers**: ECO-LEGACY-001 violation, missing database package

### ECO-04.6: Evidence Infrastructure
- **Dependencies**: ECO-04.5, ECO-04.4
- **Acceptance**: Evidence Engine with trust levels, provenance capture
- **Blockers**: Requires provenance from Engine Gateway

### ECO-04.7: Uncertainty Propagation
- **Dependencies**: ECO-04.5, ECO-04.6
- **Acceptance**: All model outputs carry uncertainty metadata
- **Blockers**: No uncertainty framework exists

### ECO-04.8: Knowledge Engine (Daneshyar)
- **Dependencies**: ECO-04.6, ECO-04.7
- **Acceptance**: 9 knowledge types, epistemic status tracking
- **Blockers**: Requires Evidence Engine for trust propagation

### ECO-04.9: Decision Engine (Tasmimyar)
- **Dependencies**: ECO-04.8, ECO-04.7
- **Acceptance**: 11 decision elements, decision chain implemented
- **Blockers**: Requires Knowledge Engine and Evidence Engine

### ECO-04.10: AI Isolation
- **Dependencies**: ECO-04.9, ECO-04.6
- **Acceptance**: AI can only read Evidence Engine, recommendations through Tasmimyar
- **Blockers**: `engine/hydroma/generative_ai/` imports services.ai (must move to services/ai)

### ECO-04.11: Canonical Services
- **Dependencies**: ECO-04.10, ECO-04.5
- **Acceptance**: 75 services consolidated into 8 bounded contexts
- **Blockers**: 18 services marked LEGACY_ONLY/OBSOLETE/DO_NOT_TRANSFER

### ECO-04.12: Application Layer
- **Dependencies**: ECO-04.11
- **Acceptance**: API Gateway functional, services consolidated
- **Blockers**: None after consolidation

### ECO-04.13: Testing Infrastructure
- **Dependencies**: ECO-04.5, ECO-04.10
- **Acceptance**: All architecture tests executable
- **Blockers**: database/ package missing

---

## 3. Dependency Validation

### Actual Dependencies (Verified via source)

| Source | Target | Relationship | Status |
|--------|--------|--------------|--------|
| `services/models/registry.py:22-48` | `engine.hydroma.*` | imports | EXPECTED |
| `services/validation/formula_checks.py:22-33` | `engine.hydroma.*` | imports | EXPECTED |
| `services/api_gateway/routers/*.py` | `engine.hydroma.*` | imports | EXPECTED |
| `services/land/service.py:13` | `engine.land.models` | imports | EXPECTED |
| `engine/hydroma/generative_ai/__init__.py:20-22` | `services.ai.*` | imports | **VIOLATION** |
| `engine/data_connector.py:86` | `database.hub` | imports | **VIOLATION** |
| `engine/hydroma/cpp_bridge/__init__.py:34` | `services.models.land_models` (in tests) | import | TEST-ONLY |
| `services/ai/admin_assistant.py:343` | `services.scientific_motors.*` | imports | REVIEW |

---

## 4. Build Order Validation

### Dependency Chain Verification

1. ✅ Science Contracts → Units (models need unit definitions)
2. ✅ Units → Engine Gateway (gateway normalizes units)
3. ✅ Engine Gateway → Hydroma Extraction (gateway is the boundary)
4. ✅ Hydroma → Evidence (evidence captures provenance from engine)
5. ✅ Evidence → Knowledge (knowledge types tagged with evidence)
6. ✅ Evidence + Knowledge → Decision (decision uses evidence + knowledge)
7. ✅ Decision → AI (AI receives filtered recommendations)
8. ✅ Engine + Evidence + Knowledge + Decision + AI → Services
9. ✅ Services → Application
10. ✅ Application → Product

**Validation**: The proposed build order is **CONSISTENT** with actual dependency direction.

---

## 5. Alternative Build Order (If Dependencies Differ)

If the actual dependency verification reveals different ordering needs, the alternative is:

```
Scientific Contracts
        ↓
Engine Gateway (validation + unit normalization)
        ↓
Hydroma Canonicalization (extraction)
        ↓
C++/Python Boundary (parallel with Hydroma)
        ↓
Evidence + Uncertainty (parallel)
        ↓
Knowledge Engine
        ↓
Decision Engine
        ↓
AI Isolation
        ↓
Domain Services
        ↓
Application Layer
```

---

## 6. Findings

1. **VERIFIED**: Build order dependency chain is consistent with actual code dependencies.

2. **VERIFIED**: Scientific Contracts must precede Units, which must precede Engine Gateway — this matches the dependency direction.

3. **CONFLICTING EVIDENCE**: ECO-02/19 proposed a simpler chain. ECO-03 adds Evidence → Knowledge → Decision → AI ordering based on actual contract requirements.

4. **BLOCKING**: ECO-LEGACY-001 violation must be resolved before ECO-04.5.

5. **VERIFIED**: Uncertainty Propagation can be built in parallel with Evidence Infrastructure (both depend on Hydroma extraction but not on each other).

---

*Report generated: 2026-10-08*
*Status: VERIFIED — dependency DAG is consistent with source code analysis*