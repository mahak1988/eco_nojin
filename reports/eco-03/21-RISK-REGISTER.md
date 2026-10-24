# ECO-03: Risk Register — Report 21
## Comprehensive Risk Assessment

---

## Executive Summary

This risk register covers all risks identified through ECO-03 forensic analysis. Risks are prioritized by probability and impact.

---

## 1. Risk Categories

| Category | Count |
|----------|-------|
| Scientific risk | 3 |
| Architectural risk | 8 |
| Dependency risk | 4 |
| Legacy risk | 3 |
| Security risk | 2 |
| Data integrity risk | 2 |
| Unit risk | 2 |
| Uncertainty risk | 3 |
| AI risk | 4 |
| Performance risk | 3 |
| C++ ABI risk | 2 |
| Service consolidation risk | 2 |
| Migration risk | 3 |
| Provenance risk | 2 |
| Knowledge integrity risk | 2 |
| Decision integrity risk | 2 |
| **Total** | **45** |

---

## 2. Scientific Risks (3)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-SCI-001 | Theis Solution series convergence undocumented | HIGH | HIGH | CRITICAL | CANON-005 marked REQUIRES_SCIENTIFIC_REVIEW; ECO-01 report notes "series convergence undocumented" | Require scientific peer review; add convergence proof | hydrogeology team | YES |
| RISK-SCI-002 | Temperature constant divergence (273.0 vs 273.16) | HIGH | HIGH | CRITICAL | climate.cpp:138 uses 273.0; cpp_bridge/__init__.py:435 uses 273.16 | Standardize on FAO-56 constant (273.0) in both C++ and Python | engine team | YES |
| RISK-SCI-003 | Sokal salinity model has no documented scientific basis | MEDIUM | MEDIUM | HIGH | ECO-01/20-CANONICAL-ASSETS.md lists "NOT_RECOMMENDED: Soil Salinity Model" | Remove from canonical registry; require scientific review | soil team | NO |

---

## 3. Architectural Risks (8)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-ARCH-001 | Engine→services imports violate ECO-LEGACY-001 | HIGH | HIGH | CRITICAL | engine/hydroma/generative_ai/__init__.py:20-22 imports services.ai.* | Remove imports; move generative_ai to services/ai/ | engine team | YES |
| RISK-ARCH-002 | Engine→database imports (missing database package) | HIGH | HIGH | CRITICAL | engine/data_connector.py:86; engine/resource_manager.py:45; engine/ports/session.py:162 | Provision database package or remove imports | engine team | YES |
| RISK-ARCH-003 | Services import engine directly (bypassing Gateway) | HIGH | MEDIUM | HIGH | 100+ grep matches for `from engine` in services/ | Implement Engine Gateway; enforce import guards | services team | YES |
| RISK-ARCH-004 | Import guards not implemented | HIGH | HIGH | CRITICAL | No `tools/detect_imports.py` or `tools/check_boundary.py` exist | Implement AST-based import guard in CI/CD | infrastructure team | YES |
| RISK-ARCH-005 | Engine Gateway not implemented | HIGH | HIGH | CRITICAL | Contract exists (ECO-02/contracts/EngineGatewayContract.md) but no implementation | Implement Engine Gateway module in ECO-04 | engine team | YES |
| RISK-ARCH-006 | Evidence Engine not implemented | HIGH | HIGH | CRITICAL | Contract exists but no evidence/ module | Implement Evidence Engine in ECO-04 | knowledge team | YES |
| RISK-ARCH-007 | Knowledge Engine (Daneshyar) not implemented | HIGH | HIGH | CRITICAL | Only services/daneshyar/ exists | Implement Knowledge Engine in ECO-04 | knowledge team | YES |
| RISK-ARCH-008 | Decision Engine (Tasmimyar) not implemented | HIGH | HIGH | CRITICAL | Only services/tasmimyar/ exists | Implement Decision Engine in ECO-04 | decision team | YES |

---

## 4. Dependency Risks (4)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-DEP-001 | Missing dependency manifest (no requirements.txt) | HIGH | MEDIUM | HIGH | INVENTORY.md §6: "No requirements.txt, pyproject.toml, setup.py found" | Create pyproject.toml with all dependencies | infrastructure team | YES |
| RISK-DEP-002 | Missing database package | HIGH | HIGH | CRITICAL | TEST-REPORT.md §2.1: ModuleNotFoundError: No module named 'database' | Provision or remove database dependency | infrastructure team | YES |
| RISK-DEP-003 | C++ extension (.pyd) not portable | MEDIUM | HIGH | HIGH | Only cp311 and cp312 Windows .pyd files exist | Document multi-platform build process | engine team | NO |
| RISK-DEP-004 | Missing cpp_bridge module referenced | LOW | MEDIUM | MEDIUM | INVENTORY.md §528: "cpp_bridge module may not exist" | Verify and fix cpp_bridge import | engine team | NO |

---

## 5. Legacy Risks (3)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-LEG-001 | Path inconsistency (hydra/hydrama/hydorama) | HIGH | LOW | MEDIUM | ECO-01/00 §28: "both engine/hydra/ and engine/hydorama/ found" | Standardize on `engine/hydroma/` | engine team | NO |
| RISK-LEG-002 | services/hydroma has empty directories | MEDIUM | LOW | LOW | INVENTORY.md §499: "services/hydroma/* All subdirectories are empty" | Delete empty directories | services team | NO |
| RISK-LEG-003 | Two formula registries (DUPLICATE) | HIGH | MEDIUM | HIGH | engine/hydroma/formulas/catalog.py vs services/_contracts/formula.py | Merge into single canonical registry | knowledge team | NO |

---

## 6. Security Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-SEC-001 | AI could potentially access scientific computation | MEDIUM | HIGH | HIGH | engine/hydroma/generative_ai imports services.ai, which imports services.scientific_motors → engine.hydroma | Implement AI isolation boundary with import guards | ai team | YES |
| RISK-SEC-002 | No authentication boundary enforcement | MEDIUM | HIGH | HIGH | Auth is out of scope but engine imports database which implies auth coupling | Document auth boundary; ensure no engine→auth imports | security team | NO |

---

## 7. Data Integrity Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-DATA-001 | No provenance on model outputs | HIGH | HIGH | CRITICAL | engine/hydroma/provenance.py exists but minimal; no Evidence Engine | Implement evidence capture in Engine Gateway | provenance team | YES |
| RISK-DATA-002 | Trust levels not assigned to outputs | HIGH | HIGH | CRITICAL | No trust_level field on any result | Implement trust level assignment in Evidence Engine | evidence team | YES |

---

## 8. Unit Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-UNIT-001 | Temperature constant divergence | HIGH | HIGH | CRITICAL | C++: 273.0 vs Python: 273.16 | Standardize on one constant | engine team | YES |
| RISK-UNIT-002 | Unit conversions scattered across modules | HIGH | MEDIUM | HIGH | ECO-03 §4: Conversions in climate.cpp, soil/physics.py, watershed/calculator.py | Centralize in Engine Gateway | engine team | YES |

---

## 9. Uncertainty Risks (3)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-UNC-001 | No uncertainty propagation in model outputs | HIGH | HIGH | CRITICAL | No uncertainty field in any result type | Implement Uncertainty Engine | uncertainty team | YES |
| RISK-UNC-002 | Absence of uncertainty treated as certainty | HIGH | HIGH | CRITICAL | All model outputs return point estimates without warning | Require explicit uncertainty field; flag absence | engine team | YES |
| RISK-UNC-003 | No confidence intervals on scientific results | HIGH | MEDIUM | HIGH | No confidence field in provenance | Add confidence to ResultProvenance | provenance team | YES |

---

## 10. AI Risks (4)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-AI-001 | AI has indirect engine access via import chain | HIGH | HIGH | CRITICAL | engine/hydroma/generative_ai → services.ai → services.scientific_motors → engine.hydroma | Break import chain; isolate AI layer | ai team | YES |
| RISK-AI-002 | AI can modify scientific models | MEDIUM | HIGH | HIGH | No import guard prevents AI → model registry | Implement AI isolation boundary | ai team | YES |
| RISK-AI-003 | AI-generated recommendations bypass Tasmimyar | MEDIUM | HIGH | HIGH | No architectural enforcement of Tasmimyar oversight | Add import guard; route through Tasmimyar | ai team | YES |
| RISK-AI-004 | AI knowledge not distinguished from scientific knowledge | HIGH | MEDIUM | HIGH | No epistemic type tagging | Implement epistemic type system | knowledge team | YES |

---

## 11. Performance Risks (3)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-PERF-001 | C++ tests UNRUNNABLE | HIGH | HIGH | CRITICAL | No database package; all 21 C++ tests cannot run | Provision database package | infrastructure team | YES |
| RISK-PERF-002 | Performance claims unverified (10x-200x) | HIGH | MEDIUM | HIGH | No benchmark results in repository | Run benchmarks; document results | engine team | NO |
| RISK-PERF-003 | C++ Python fallback path untested | HIGH | MEDIUM | HIGH | All Python tests UNRUNNABLE | Run tests after fixing database | engine team | YES |

---

## 12. C++ ABI Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-ABI-001 | Dual build directories (build/ and build2/) | MEDIUM | MEDIUM | HIGH | engine/cpp_core/build2/ contains MSVC artifacts | Consolidate to single build directory | engine team | NO |
| RISK-ABI-002 | ABI version not tracked | HIGH | MEDIUM | HIGH | No ABI version checking in cpp_bridge | Add ABI version to .pyd; verify at load | engine team | NO |

---

## 13. Service Consolidation Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-SVC-001 | 75 services vs ECO-01 report 73 | LOW | LOW | LOW | 2 services missing from ECO-01 reports | Update service registry; account for all 75 | services team | NO |
| RISK-SVC-002 | Service consolidation not enforced | HIGH | MEDIUM | HIGH | 8 bounded contexts defined but no enforcement | Implement service boundary tests | services team | YES |

---

## 14. Migration Risks (3)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-MIG-001 | Legacy path inconsistencies | MEDIUM | LOW | MEDIUM | hydra/hydrama/hydorama naming | Standardize on hydroma/ | engine team | NO |
| RISK-MIG-002 | Migration order incorrect | MEDIUM | HIGH | HIGH | Proposed DAG may need adjustment | Validate DAG against actual dependencies | architecture team | NO |
| RISK-MIG-003 | Old smart contracts transferred to production | LOW | CRITICAL | CRITICAL | Smart contracts in services/blockchain/ | Mark as REFERENCE_ONLY; never transfer | blockchain team | YES |

---

## 15. Provenance Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-PROV-001 | Provenance not on AI outputs | HIGH | MEDIUM | HIGH | AI outputs have no provenance tags | Require provenance on all outputs | ai team | YES |
| RISK-PROV-002 | Provenance chain not traceable | HIGH | HIGH | CRITICAL | No evidence chain implementation | Implement Evidence Engine with full chain | evidence team | YES |

---

## 16. Knowledge Integrity Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-KNOW-001 | Local knowledge treated as scientific fact | HIGH | HIGH | CRITICAL | No epistemic type distinction | Implement epistemic type system | knowledge team | YES |
| RISK-KNOW-002 | AI knowledge not separated from scientific knowledge | HIGH | MEDIUM | HIGH | No trust level separation | Tag AI knowledge as KT-009 with LOW trust | ai team | YES |

---

## 17. Decision Integrity Risks (2)

| risk_id | description | probability | impact | severity | evidence | mitigation | owner | blocking? |
|---------|-------------|-------------|--------|----------|----------|------------|-------|-----------|
| RISK-DEC-001 | Recommendations without traceable evidence | HIGH | HIGH | CRITICAL | No evidence tracing to recommendations | Implement evidence traceability in Tasmimyar | decision team | YES |
| RISK-DEC-002 | No uncertainty in decision-making | HIGH | HIGH | CRITICAL | Tasmimyar inputs have no uncertainty | Integrate Uncertainty Engine with Decision Engine | decision team | YES |

---

## 18. Risk Summary by Severity

| Severity | Count | Blocking |
|----------|-------|----------|
| CRITICAL | 15 | 13 |
| HIGH | 16 | 11 |
| MEDIUM | 10 | 3 |
| LOW | 4 | 1 |
| **Total** | **45** | **28** |

---

## 19. Blocking Risk Summary

| risk_id | description | Category |
|---------|-------------|----------|
| RISK-SCI-001 | Theis solution requires scientific review | Scientific |
| RISK-SCI-002 | Temperature constant divergence | Unit |
| RISK-ARCH-001 | Engine→services import violation | Architectural |
| RISK-ARCH-002 | Missing database package | Dependency |
| RISK-ARCH-003 | Services bypass Engine Gateway | Architectural |
| RISK-ARCH-004 | Import guards not implemented | Architectural |
| RISK-ARCH-005 | Engine Gateway not implemented | Architectural |
| RISK-ARCH-006 | Evidence Engine not implemented | Architectural |
| RISK-ARCH-007 | Knowledge Engine not implemented | Architectural |
| RISK-ARCH-008 | Decision Engine not implemented | Architectural |
| RISK-DEP-001 | Missing dependency manifest | Dependency |
| RISK-DEP-002 | Missing database package | Dependency |
| RISK-DATA-001 | No provenance on outputs | Data Integrity |
| RISK-DATA-002 | No trust levels on outputs | Data Integrity |
| RISK-UNIT-001 | Temperature constant divergence | Unit |
| RISK-UNK-002 | Unit conversions scattered | Unit |
| RISK-UNC-001 | No uncertainty propagation | Uncertainty |
| RISK-UNC-002 | Absence of uncertainty = certainty | Uncertainty |
| RISK-UNC-003 | No confidence intervals | Uncertainty |
| RISK-AI-001 | AI indirect engine access | AI |
| RISK-AI-002 | AI can modify models | AI |
| RISK-AI-003 | AI bypasses Tasmimyar | AI |
| RISK-AI-004 | AI knowledge not distinguished | AI |
| RISK-PERF-001 | C++ tests UNRUNNABLE | Performance |
| RISK-PERF-003 | Python fallback untested | Performance |
| RISK-SVC-002 | Service consolidation not enforced | Service |
| RISK-PROV-002 | Provenance chain not traceable | Provenance |
| RISK-KNOW-001 | Local knowledge ≠ scientific fact | Knowledge |
| RISK-DEC-001 | Recommendations without evidence | Decision |
| RISK-DEC-002 | No uncertainty in decisions | Decision |
| RISK-MIG-003 | Smart contracts transferred | Migration |

---

*Report generated: 2026-10-08*
*Status: 28 blocking risks identified*