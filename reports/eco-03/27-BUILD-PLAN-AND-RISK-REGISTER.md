# ECO-03: Build Plan & Risk Register — Report 27

---

## 1. ECO-04 Build Plan

| Sprint | Milestone | Deliverables | Dependencies |
|--------|-----------|-------------|--------------|
| ECO-04.1 | Resolve Blocking Violations | Remove engine→services import; Provision database package OR refactor; Create pyproject.toml; Verify import engine works; Run 1 baseline test | B-001, B-002, B-003, B-005 |
| ECO-04.2 | Implement Engine Gateway | Create engine/gateway/; Enforce request/response contracts; Unit test gateway | ECO-04.1 |
| ECO-04.3 | Implement Evidence Engine | Create knowledge/evidence/; EvidenceItem with trust levels; Provenance capture; Evidence contracts | ECO-04.2 |
| ECO-04.4 | Scientific Review | P0: Theis Series, Climate Data Assimilation; Update trust levels | All P0 complete |
| ECO-04.5 | Knowledge Engine | Epistemic types (OBSERVATION, MODEL_OUTPUT, DERIVED); Local knowledge distinction; Type enforcement | ECO-04.3 |
| ECO-04.6 | Uncertainty | Uncertainty type in all outputs; Propagation method; CI calculation | ECO-04.4 |
| ECO-04.7 | Decision Engine | Tasmimyar oversight; Decision element implementation | ECO-04.5 |
| ECO-04.8 | AI Isolation | Import guards; No AI in computation path; Test suite | ECO-04.1 |
| ECO-04.9 | Service Gateway | Services route through Gateway; Import guard enforcement | ECO-04.2 |
| ECO-04.10 | Full Test Suite | All 50+ tests runnable | ECO-04.1-ECO-04.9 |

---

## 2. Critical Path

```
ECO-04.1 (Fix blocking violations)
    ├── B-001: Remove engine→services import
    ├── B-002: Provision database package (or refactor)
    ├── B-003: Create pyproject.toml
    └── B-005: Verify `import engine` works
        ├── ECO-04.2 (Engine Gateway)
        │   └── ECO-04.3 (Evidence Engine)
        │       ├── ECO-04.4 (Scientific Review - P0)
        │       └── ECO-04.5 (Knowledge Engine)
        │           ├── ECO-04.6 (Uncertainty)
        │           └── ECO-04.7 (Decision Engine)
        └── ECO-04.8 (AI Isolation)
            └── ECO-04.9 (Service Gateway)
                └── ECO-04.10 (Full Test Suite)
```

**Minimum viable: ECO-04.1 → ECO-04.2 → ECO-04.3** for basic provenance tracking.

---

## 3. Risk Register (Updated)

| risk_id | risk | likelihood | impact | mitigation | owner | status |
|---------|------|-----------|--------|------------|-------|--------|
| RISK-001 | Engine→services import causes circular import | HIGH | BLOCKING | Remove generative_ai from engine before any changes | Architecture team | ACTIVE |
| RISK-002 | Missing database package prevents all testing | HIGH | BLOCKING | Provision minimal database package with required interfaces | Platform team | ACTIVE |
| RISK-003 | Temperature divergence between C++/Python | MEDIUM | HIGH | VERIFIED: both now use 273.16 for radiation, 273.0 for aerodynamic term | Engine team | RESOLVED |
| RISK-004 | Services bypass Gateway, corrupt provenance | HIGH | HIGH | Implement import guard + route through Gateway | Architecture team | PENDING |
| RISK-005 | Theis Solution diverges for early time steps | MEDIUM | MEDIUM | Requires scientific review before canonization | Science team | PENDING |
| RISK-006 | AI influences scientific computation | HIGH | BLOCKING | Enforce AI isolation boundary; import guard | AI team | PENDING |
| RISK-007 | Model registry coupled to services API | HIGH | HIGH | Decouple; move to Platform Core context | Platform team | PENDING |
| RISK-008 | Uncertainty not propagated | MEDIUM | HIGH | Implement UncertaintyType in all outputs | Engine team | PENDING |
| RISK-009 | No trust levels on evidence | MEDIUM | HIGH | Implement EvidenceItem with trust_level | Decision team | PENDING |
| RISK-010 | Epistemic types absent from outputs | MEDIUM | MEDIUM | Tag all data with epistemic type | Knowledge team | PENDING |
| RISK-011 | C++ Python bindings unstable | LOW | HIGH | Verify all 21 test scenarios; ensure fallback parity | Engine team | PENDING |
| RISK-012 | Circular dependency chain | HIGH | BLOCKING | engine→services.ai→services.scientific_motors→engine | Architecture team | ACTIVE |
| RISK-013 | Empty directories (hydra/, hydorama/) | LOW | LOW | Clean up before release | DevOps team | PENDING |
| RISK-014 | Services depend on legacy paths | MEDIUM | MEDIUM | Redirect through adapters | Platform team | PENDING |

---

## 4. Resource Requirements

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| Python | 3.11 | 3.12 | Both detected in codebase |
| C++ Compiler | C++17 | C++20 | pybind11 requires C++17+ |
| PostgreSQL | 14 | 15 | For database package |
| Redis | 6 | 7 | For caching/session |
| Worker processes | 2 | 4 | For parallel test execution |

---

## 5. Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| Engine importable | `python -c "import engine"` succeeds | ✅ |
| Tests runnable | ≥1 test executes without ModuleNotFoundError | ✅ |
| Import guards working | `python tools/check_boundary.py` runs and passes | ✅ |
| Engine Gateway exists | `engine/gateway/` module present with contracts | ✅ |
| Evidence Engine exists | `knowledge/evidence/` module with EvidenceItem | ✅ |
| AI isolation enforced | No `services.ai` imports in engine/ | ✅ |
| Database package resolved | All deferred imports resolve | ✅ |
| Uncertainty propagation | Sample model returns uncertainty | ✅ |

---

## 6. ECO-04 Go/No-Go Criteria

| Criterion | Must Pass | Failure Action |
|-----------|-----------|----------------|
| B-001 fixed (no engine→services imports) | YES | BLOCK ECO-04 |
| B-002 resolved (database package exists) | YES | BLOCK ECO-04 |
| B-003 manifest created (pyproject.toml) | YES | BLOCK ECO-04 |
| `import engine` succeeds | YES | BLOCK ECO-04 |
| ≥1 test executable | YES | BLOCK ECO-04 |
| Import guard tool exists and runs | YES | BLOCK ECO-04 |

---

*Generated: 2026-10-08*
*Status: 15 hard blockers remain; ECO-04 BLOCKED pending resolution*