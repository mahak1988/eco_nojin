# ECO-02: Canonical Architecture Definition
## اکو نوژین - Architecture for Water Resources Management in Iran

---

## 1. Canonical 7-Layer Architecture

### Layer 1: Product Experience
- **Purpose**: User-facing interfaces and presentation
- **Out of Scope** per ECO-01/00-FINAL-VALIDATION.md: Frontend frameworks, UI/UX design
- **Evidence**: ECO-01 §5.1, SEC-SECURITY-KNOWLEDGE.md

### Layer 2: Application Orchestration
- **Purpose**: Workflow coordination, API gateway, request routing
- **Evidence**: ECO-01/13-SERVICE-ASSET-MAP.md (73 services, 63% infrastructure)

### Layer 3: Decision (Tasmimyar)
- **Purpose**: Policy evaluation, decision engine
- **Evidence**: ECO-01/16-TASMIMYAR-COMPATIBILITY.md (11 decision elements)
- **Constraint**: Must not touch scientific core directly; goes through Evidence Engine

### Layer 4: Knowledge (Daneshyar)
- **Purpose**: Knowledge graph, canonical asset registry, epistemic status tracking
- **Evidence**: ECO-01/15-DANESHYAR-COMPATIBILITY.md (9 knowledge types)
- **Evidence**: ECO-01/20-CANONICAL-ASSETS.md (CANON-XXX assets)

### Layer 5: Evidence Engine (Provenance)
- **Purpose**: Evidence collection, validation, audit trail
- **Evidence**: ECO-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md
- **Chain**: Engine → Evidence → Decision → AI → User

### Layer 6: Domain Services (Hydroma)
- **Purpose**: Domain-bounded microservices, consolidated from 73 services
- **Evidence**: ECO-01/14-SERVICE-CONSOLIDATION-ANALYSIS.md
- **Evidence**: ECO-01/10-HYDROMA-FORENSICS.md (Hydroma 4-layer model)

### Layer 7: Engine Gateway
- **Purpose**: Python entry point, C++ boundary management, ctypes/pybind11 bridge
- **Evidence**: ECO-01/11-CPP-PYTHON-BOUNDARY.md
- **Critical Fix**: ECO-LEGACY-001 - Remove engine/→services/ imports

### Layer 8: Hydroma Scientific Engine
- **Purpose**: Scientific computation orchestration (Python)
- **Evidence**: ECO-01/07-MODEL-QUALITY-MATRIX.md (22 models)
- **Evidence**: reports/engine-services/SCIENTIFIC-MODEL-REGISTRY.md

### Layer 9: Numerical Computation (C++ Kernels)
- **Purpose**: High-performance numerical computation
- **Evidence**: ECO-01 §4.2, reports/engine-services/INVENTORY.md (10 .cpp, 10 .h, 21 tests)

---

## 2. Layer Contracts and Boundaries

### Boundary Rules
1. **Python orchestrates, C++ computes** - ECO-01/11-CPP-PYTHON-BOUNDARY.md
2. **C++/Python boundary via ctypes/pybind11/buffer protocol** - ECO-01 §4.3
3. **AI is experimental, isolated from scientific core** - ECO-01/12-AI-FORENSICS.md
4. **No engine/→services/ imports** - ECO-LEGACY-001
5. **Scientific model maturity scale**: VERIFIED → SCIENTIFICALLY_SUPPORTED → IMPLEMENTATION_VERIFIED → CODE_ONLY → STUB - ECO-01/07

### Dependency Directions
```
Product Experience → Application Orchestration → Decision
                                                  ↓
Knowledge ← Evidence Engine ← Domain Services ← Engine Gateway ← Hydroma Engine ← C++ Kernels
```

---

## 3. Scientific Model Maturity Scale

| Status | Definition | Action |
|--------|------------|--------|
| VERIFIED | Scientifically validated, peer-reviewed | CORE |
| SCIENTIFICALLY_SUPPORTED | Theory supported, partial validation | IMPORTANT |
| IMPLEMENTATION_VERIFIED | Code matches implementation, not field-validated | OPTIONAL |
| CODE_ONLY | Implementation only, no scientific backing | RESEARCH |
| STUB | Placeholder, not functional | LEGACY/REMOVE |

**Source**: ECO-01/07-MODEL-QUALITY-MATRIX.md, ECO-01/19-TECHNOLOGY-STRATEGY.md

---

## 4. Technology Strategy Framework

| Category | Definition | Examples |
|----------|------------|----------|
| CORE | Mission-critical, must maintain | Hydroma engine, C++ kernels, C++/Python boundary |
| IMPORTANT | Necessary, optimize but maintain | Evidence engine, decision engine |
| OPTIONAL | Useful but not essential | Some AI components |
| RESEARCH | Experimental, isolate | AI augmentation modules |
| LEGACY | Deprecated, plan removal | Services violating ECO-LEGACY-001 |
| REMOVE | Critical violation | Any engine/→services/ imports |

**Source**: ECO-01/19-TECHNOLOGY-STRATEGY.md

---

## 5. Canonical Asset Registry

### CANON-001: Penman-Monteith ET0
- **Type**: Scientific Model (Reference ET)
- **Maturity**: VERIFIED
- **Status**: CORE
- **Source**: ECO-01/20-CANONICAL-ASSETS.md

### CANON-002: Hargreaves ET0
- **Type**: Scientific Model (Alternative ET)
- **Maturity**: SCIENTIFICALLY_SUPPORTED
- **Status**: IMPORTANT

### CANON-003: Thornthwaite PET
- **Type**: Scientific Model (Potential ET)
- **Maturity**: SCIENTIFICALLY_SUPPORTED
- **Status**: IMPORTANT

### CANON-004-CANON-007: ... [continuing pattern]
- **Source**: ECO-01/20-CANONICAL-ASSETS.md

---

## 6. AI Isolation Principle

**AI cannot touch scientific core directly.** Chain: Engine → Evidence → Decision → AI → User

- AI components are classified as RESEARCH/OPTIONAL
- AI must not modify canonical scientific models
- AI augmentation exists as optional layer above Decision layer
- **Evidence**: ECO-01/12-AI-FORENSICS.md

---

## 7. Service Consolidation Plan

- **Current**: 73 services across services/ directory
- **Target**: Consolidated into bounded-context modules
- **Infrastructure services**: ~45 instances (63%)
- **Domain services**: ~28 instances
- **Plan**: Merge infrastructure services into shared platform layer
- **Evidence**: ECO-01/13-SERVICE-ASSET-MAP.md, ECO-01/14-SERVICE-CONSOLIDATION-ANALYSIS.md

---

## 8. Legacy Dependency Violation (ECO-LEGACY-001)

**Critical**: Any import from `engine/` to `services/` must be removed immediately.
- **Impact**: Breaks isolation boundary, prevents engine as library
- **Fix**: Redirect through Engine Gateway layer
- **Evidence**: ECO-01/22-LEGACY-DEPENDENCY-STRATEGY.md

---

## 9. Security Considerations

- Security is cross-cutting concern
- Auth is OUT OF SCOPE per ECO-01/00-FINAL-VALIDATION.md
- Data protection at Evidence/Provenance layer
- **Evidence**: SEC-SECURITY-KNOWLEDGE.md

---

## 10. Performance Considerations

- C++ kernels handle numerical computation
- Python orchestrates with minimal overhead
- Buffer protocol for zero-copy data transfer
- **Evidence**: PERF-PERFORMANCE-KNOWLEDGE.md

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, based on ECO-01 forensic analysis*