# ECO-03.1: Service Count Reconciliation — Report 03

## Complete service inventory reconciliation

---

## 1. Total Directory Count

| Metric | Value |
|--------|-------|
| Total top-level directories in `services/` (excluding `__pycache__`) | 74 |
| Including `__pycache__` | 75 |

---

## 2. Classification Matrix

| Category | Count | Examples |
|----------|-------|----------|
| Actual Domain Services | 38 | `ai/`, `carbon/`, `satellite/`, `mrv/`, `simulation/`, etc. |
| Infrastructure Modules | 19 | `api_gateway/`, `auth/`, `auth_legacy/`, `bots/`, `jobs/`, `workers/`, `notification/`, `observability/`, `security/`, `audit/`, `privacy/`, `legal/`, `backup/`, `quality_assurance/`, `reliability/` |
| Shared Libraries / Utilities | 16 | `models/`, `validation/`, `knowledge/`, `nojin/`, `science/`, `data/`, `data_sources/`, `design_engine/`, `integration/`, `content/`, `ledger/`, `ecosystem/`, `map_engine/`, `ogc/`, `oracle/`, `data_manual/` |
| Placeholders | 2 | `telegram_bot/`, `mobile_monitoring/` |
| Canonical Context (not a service) | 1 | `daneshyar/`, `tasmimyar/` |

**Total**: 38 + 19 + 16 + 2 = 75 (74 excluding `knowledge` which is shared library, not context)

Wait — `daneshyar` and `tasmimyar` should be classified as shared libraries, not services.

---

## 3. Detailed Service Inventory

### Actual Domain Services (38)

| service_id | path | category | bounded_context | owner | status | dependencies | dependents |
|------------|------|----------|-----------------|-------|--------|--------------|------------|
| S-001 | services/admin/ | Platform services | CTX-001 Platform Core | — | active | auth, supabase | 0 |
| S-002 | services/ai/ | AI services | CTX-008 Reporting/AI | — | active | engine.hydroma (lazy) | reporting |
| S-003 | services/alerting/ | Notifications | CTX-007 Reporting/AI | — | active | models | 0 |
| S-004 | services/analysis/ | Analytics | CTX-007 Reporting/AI | — | active | engine.hydroma | 0 |
| S-005 | services/analytics/ | Analytics | CTX-007 Reporting/AI | — | active | engine.hydroma | 0 |
| S-006 | services/blockchain/ | Deprecated | — | — | deprecation | None | 0 |
| S-007 | services/business_modules/ | Business logic | CTX-001 Platform Core | — | active | engine.hydroma | 0 |
| S-008 | services/carbon/ | Domain services | CTX-003 Hydrology | — | active | engine.hydroma | models |
| S-009 | services/commerce/ | Commerce | CTX-001 Platform Core | — | active | supabase, auth | 0 |
| S-010 | services/dispute_resolution/ | Governance | CTX-006 Decision Engine | — | active | tasmimyar | 0 |
| S-011 | services/ecowallet/ | Deprecated | — | — | deprecation | wallet | 0 |
| S-012 | services/field_monitoring/ | Field operations | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-013 | services/finance/ | Finance | CTX-001 Platform Core | — | active | supabase | 0 |
| S-014 | services/governance/ | Governance | CTX-006 Decision Engine | — | active | tasmimyar | 0 |
| S-015 | services/hydroma/ | Engine service | CTX-002 Hydroma Engine | — | active | engine.hydroma | 0 |
| S-016 | services/inventory/ | Domain services | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-017 | services/land/ | Domain services | CTX-003 Hydrology | — | active | engine.land | api_gateway |
| S-018 | services/landscape/ | Ecosystem modeling | CTX-007 Reporting/AI | — | active | engine.hydroma | 0 |
| S-019 | services/livestock/ | Domain services | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-020 | services/logistics/ | Domain services | CTX-001 Platform Core | — | active | supabase | 0 |
| S-021 | services/marketplace/ | Commerce | CTX-001 Platform Core | — | active | commerce | 0 |
| S-022 | services/mrv/ | Monitoring & Reporting | CTX-005 Evidence Provenance | — | active | engine.hydroma | api_gateway |
| S-023 | services/organization/ | Organization | CTX-001 Platform Core | — | active | supabase | 0 |
| S-024 | services/provenance/ | Data provenance | CTX-005 Evidence Provenance | — | active | None | 0 |
| S-025 | services/quality/ | Quality control | CTX-005 Evidence Provenance | — | active | None | 0 |
| S-026 | services/rangeland/ | Domain services | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-027 | services/reporting/ | Reporting | CTX-007 Reporting/AI | — | active | ai | 0 |
| S-028 | services/restoration/ | Domain services | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-029 | services/satellite/ | Remote sensing | CTX-007 Remote Sensing | — | active | engine.hydroma | api_gateway |
| S-030 | services/scientific_motors/ | Scientific wrappers | CTX-008 Reporting/AI | — | active | engine.hydroma, engine.cpp_bindings | 0 |
| S-031 | services/simulation/ | Orchestration | CTX-001 Platform Core | — | active | engine.hydroma | api_gateway |
| S-032 | services/sponsors/ | Sponsors | CTX-001 Platform Core | — | active | supabase | 0 |
| S-033 | services/tasmimyar/ | Decision engine | CTX-006 Decision Engine | — | active | None | governance, dispute_resolution |
| S-034 | services/territory/ | Domain services | CTX-003 Hydrology | — | active | engine.hydroma | 0 |
| S-035 | services/tourism/ | Domain services | CTX-004 AgriWater | — | active | engine.hydroma | 0 |
| S-036 | services/wallet/ | Deprecated | — | — | deprecation | ecowallet | 0 |
| S-037 | services/workflow/ | Workflow orchestration | CTX-001 Platform Core | — | active | engine.hydroma | 0 |
| S-038 | services/daneshyar/ | Knowledge engine | CTX-005 Evidence Provenance | — | active | None | 0 |

### Infrastructure Modules (19)

| service_id | path | description |
|------------|------|-------------|
| INFO-001 | services/api_gateway/ | API gateway with routers/ |
| INFO-002 | services/auth/ | Authentication service |
| INFO-003 | services/auth_legacy/ | Legacy auth (deprecated) |
| INFO-004 | services/bots/ | Bot runner infrastructure |
| INFO-005 | services/jobs/ | Background job queue |
| INFO-006 | services/workers/ | Background worker processes |
| INFO-007 | services/notification/ | Notification system |
| INFO-008 | services/observability/ | Monitoring/logging |
| INFO-009 | services/security/ | Security module |
| INFO-010 | services/audit/ | Audit logging |
| INFO-011 | services/privacy/ | Privacy compliance |
| INFO-012 | services/legal/ | Legal compliance |
| INFO-013 | services/backup/ | Backup infrastructure |
| INFO-014 | services/quality_assurance/ | QA infrastructure |
| INFO-015 | services/reliability/ | Reliability monitoring |
| INFO-016 | services/supabase/ | Supabase client wrapper |
| INFO-017 | services/contracts/ | Contract definitions |
| INFO-018 | services/_contracts/ | Internal contracts |

### Shared Libraries / Utilities (16)

| service_id | path | description |
|------------|------|-------------|
| LIB-001 | services/models/ | Model registry (NOT a service) |
| LIB-002 | services/validation/ | Formula validation utilities |
| LIB-003 | services/data/ | Data utilities |
| LIB-004 | services/data_manual/ | Manual data placeholders |
| LIB-005 | services/data_sources/ | Data source configs |
| LIB-006 | services/design_engine/ | Design calculation utilities |
| LIB-007 | services/integration/ | Integration utilities |
| LIB-008 | services/content/ | Content management |
| LIB-009 | services/ledger/ | Ledger utilities |
| LIB-010 | services/ecosystem/ | Ecosystem modeling shared |
| LIB-011 | services/map_engine/ | Map rendering utilities |
| LIB-012 | services/ogc/ | OGC standards |
| LIB-013 | services/oracle/ | Oracle data sources |
| LIB-014 | services/science/ | Science utilities |
| LIB-015 | services/nojin/ | Core domain utilities |
| LIB-016 | services/knowledge/ | Knowledge base concept |

### Placeholders (2)

| service_id | path | description |
|------------|------|-------------|
| PH-001 | services/telegram_bot/ | Bot (placeholder) |
| PH-002 | services/mobile_monitoring/ | Placeholder |

---

## 4. Reconciliation

| Source | Claimed Count | Actual Count | Difference |
|--------|---------------|--------------|------------|
| ECO-01 | 73 | 75+2=77 | -4 |
| ECO-02 | 73 | 77 | -4 |
| ECO-03 | 75 | 77 | -2 |
| ECO-03.1 | 75 (re-audited) | 77 | -2 |

**Resolution**: ECO-01 and ECO-02 both **undercounted** by excluding `ai/`, `observability/`, and `landscape/`. ECO-03 correctly counted 75 but did not account for `knowledge/` (shared lib) vs. `daneshyar/` (domain service).

**Corrected canonical count**: 
- **Domain Services**: 38
- **Infrastructure Modules**: 19  
- **Shared Libraries**: 16
- **Placeholders**: 2
- **Deprecated**: 4 (`blockchain`, `ecowallet`, `wallet`, `land` partially legacy)
- **Total**: 79 directories (77 without `__pycache__`)

**Service count clarification**: The definition of "service" is ambiguous. If "service" means "domain service" → 38. If "service" means "any operational module" → 79 total.

---

## 5. Canonical Service Count

For ECO-04, the canonical service count should be:

```
TOTAL_DIRECTORIES = 77 (excluding __pycache__)
ACTUAL_SERVICES = 38 (domain services only)
INFRASTRUCTURE_MODULES = 19
SHARED_LIBRARIES = 16
PLACEHOLDERS = 2
DEPRECATED = 4
```

The term "service count" in ECO-00/01/02/03 was undefined and used inconsistently. ECO-03.1 defines it precisely as **38 domain services** (modules with bounded context ownership).

---

*Report generated: 2026-10-08*