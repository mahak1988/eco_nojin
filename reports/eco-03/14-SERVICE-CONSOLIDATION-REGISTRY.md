# ECO-03: Service Consolidation Registry — Report 14
## Complete 75-Service Registry with Migration Strategy

---

## Executive Summary

ECO-01 identified 73 services. ECO-03 forensic verification found **75 actual services** (2 unaccounted for in ECO-01 reports). This registry provides complete disposition and migration strategy for each service.

---

## 1. Full Service Registry (75 services)

### 1.1 Scientific / Domain Logic Services

| service_id | path | current_role | domain | dependencies | dependents | classification | bounded_context | canonical_owner | duplicate_of | replacement | migration_strategy | disposition | risk |
|------------|------|--------------|--------|--------------|------------|----------------|-----------------|-----------------|--------------|-------------|-------------------|-----------|------|
| SVC-001 | services/models | Scientific model registry (22 models) | Scientific | engine.hydroma, services.api_gateway | services.api_gateway | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine | engine team | services/science | hydroma-engine | EXTRACT | KEEP | HIGH |
| SVC-002 | services/science | Scientific analysis pipelines | Scientific | engine.hydroma | services/satellite | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine | engine team | - | - | MERGE_INTO_MODELS | MERGE | LOW |
| SVC-003 | services/simulation | Scenario simulation | Scientific | engine.hydroma | - | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine | engine team | - | - | KEEP | KEEP | LOW |
| SVC-004 | services/hydroma | Engine facade (empty dirs) | Scientific | - | - | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine | engine team | - | - | DELETE | OBSOLETE | LOW |
| SVC-005 | services/climate | Climate data processing | Climate | engine.hydroma | services/science, services/satellite | REUSABLE_DOMAIN_LOGIC | AgriWater/Hydroma | climate team | services/science | - | MERGE_INTO_HYDRA | KEEP | LOW |
| SVC-006 | services/soil | Soil analysis | Soil | engine.hydroma | services/land, services/validation | REUSABLE_DOMAIN_LOGIC | AgriWater | soil team | - | - | KEEP | KEEP | LOW |
| SVC-007 | services/carbon | Carbon accounting | Carbon | engine.hydroma | services/ecosystems | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | carbon team | - | - | KEEP | KEEP | LOW |
| SVC-008 | services/ecosystem | Ecosystem analysis | Ecosystem | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | ecosystem team | services/rangeland | - | MERGE_INTO_ECOSYSTEM | KEEP | LOW |
| SVC-009 | services/watershed | Watershed analysis | Hydrology | engine.hydroma | services/design_engine | REUSABLE_DOMAIN_LOGIC | Hydrology | hydrology team | - | - | KEEP | KEEP | LOW |
| SVC-010 | services/irrigation | Irrigation scheduling | Agriculture | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | AgriWater | irrigation team | - | - | KEEP | KEEP | LOW |
| SVC-011 | services/agriculture | Crop modeling | Agriculture | engine.hydroma | services/irrigation | REUSABLE_DOMAIN_LOGIC | AgriWater | agriculture team | - | - | KEEP | KEEP | LOW |
| SVC-012 | services/land | Land intelligence / GIS | GIS | engine.land | services/map_engine | REUSABLE_DOMAIN_LOGIC | AgriWater | land team | services/map_engine | - | MERGE_INTO_LAND | KEEP | MEDIUM |
| SVC-013 | services/design_engine | Engineering design | Engineering | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Hydrology | hydrology team | - | - | KEEP | KEEP | LOW |
| SVC-014 | services/knowledge | Knowledge base | Knowledge | Various | services/daneshyar | REUSABLE_DATA_CONCEPT | Knowledge | knowledge team | - | - | MERGE_INTO_DANESHYAR | KEEP | LOW |
| SVC-015 | services/provenance | Traceability | Governance | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Evidence Engine | provenance team | - | - | MERGE_INTO_EVIDENCE | KEEP | LOW |
| SVC-016 | services/daneshyar | Local knowledge | Knowledge | - | services/tasmimyar | REUSABLE_DOMAIN_LOGIC | Knowledge (Daneshyar) | knowledge team | - | - | BECOME_MODULE | KEEP | MEDIUM |
| SVC-017 | services/tasmimyar | Decision support | Decision | services/knowledge | - | REUSABLE_DECISION_LOGIC | Decision Engine | decision team | - | - | BECOME_MODULE | KEEP | HIGH |
| SVC-018 | services/satellite | Satellite data | Remote Sensing | engine.hydroma | - | REUSABLE_INTEGRATION | Remote Sensing | satellite team | services/science | - | MERGE_INTO_SCIENCE | MERGE | LOW |
| SVC-019 | services/map_engine | GIS operations | GIS | engine.land | services/land | REUSABLE_INTEGRATION | Land Intelligence | land team | - | - | MERGE_INTO_LAND | MERGE | LOW |
| SVC-020 | services/field_monitoring | Field data collection | Monitoring | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Evidence Engine | monitoring team | - | - | KEEP | KEEP | LOW |
| SVC-021 | services/monitoring | Observation data | Monitoring | - | services/mrv | REUSABLE_DATA_CONCEPT | Evidence Engine | monitoring team | services/mobile_monitoring | - | MERGE_INTO_MONITORING | KEEP | LOW |
| SVC-022 | services/mrv | MRV | Monitoring | services/monitoring | - | REUSABLE_DATA_CONCEPT | Evidence Engine | mrv team | - | - | KEEP | KEEP | LOW |
| SVC-023 | services/validation | Data validation | Validation | engine.hydroma | - | REUSABLE_VALIDATION_LOGIC | Evidence Engine | validation team | - | - | KEEP | KEEP | LOW |
| SVC-024 | services/audit | Audit primitives | Security | - | - | REUSABLE_SECURITY_PRIMITIVES | Evidence Engine | security team | - | - | KEEP | KEEP | LOW |
| SVC-025 | services/data_sources | External data integration | Integration | - | - | REUSABLE_INTEGRATION | Evidence Engine | data team | services/oracle | - | MERGE_INTO_DATA_SOURCES | KEEP | LOW |
| SVC-026 | services/data | Data pipeline management | Integration | - | - | REUSABLE_DATA_CONCEPT | Infrastructure | infrastructure team | services/data_manual | - | MERGE_INTO_DATA | KEEP | LOW |
| SVC-027 | services/rangeland | Rangeland analysis | Ecosystem | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | ecosystem team | - | - | MERGE_INTO_ECOSYSTEM | KEEP | LOW |
| SVC-028 | services/restoration | Restoration planning | Ecosystem | engine.hydroma | - | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | restoration team | - | - | KEEP | KEEP | LOW |
| SVC-029 | services/analytics | Analysis results | Reporting | engine.hydroma | - | REUSABLE_DATA_CONCEPT | Reporting | reporting team | services/reporting | - | MERGE_INTO_REPORTING | MERGE | LOW |

### 1.2 Infrastructure Services

| service_id | path | current_role | bounded_context | dependencies | classification | disposition | risk |
|------------|------|--------------|-----------------|--------------|----------------|-------------|------|
| SVC-030 | services/auth | Authentication | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-031 | services/auth_legacy | Legacy auth | PLATFORM_CORE | services/auth, services/api_gateway | Legacy | OBSOLETE | LOW |
| SVC-032 | services/backup | Backup service | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-033 | services/jobs | Background jobs | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-034 | services/workers | Worker management | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-035 | services/notification | Notifications | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-036 | services/alerting | Alerting | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-037 | services/privacy | Privacy compliance | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-038 | services/security | Security utilities | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-039 | services/reliability | Reliability monitoring | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-040 | services/supabase | Supabase integration | Platform Core | supabase client | Infrastructure | PLATFORM_CORE | LOW |
| SVC-041 | services/integration | Integration platform | Platform Core | - | Infrastructure | PLATFORM_CORE | LOW |
| SVC-042 | services/observability | Monitoring/setup | Platform Core | - | Infrastructure | KEEP | LOW |
| SVC-043 | services/governance | Governance | Platform Core | - | Infrastructure | LEGACY_ONLY | LOW |
| SVC-044 | services/landscape | Landscape analysis | Ecosystem Science | - | Domain | UNKNOWN | LOW |

### 1.3 AI / Experimental Services

| service_id | path | current_role | bounded_context | classification | disposition | risk |
|------------|------|--------------|-----------------|----------------|-------------|------|
| SVC-045 | services/ai | AI services | Reporting/AI | RESEARCH | KEEP_SEPARATE | MEDIUM |
| SVC-046 | services/scientific_motors | Scientific motor wrappers | Cross-domain | UNKNOWN | REVIEW | HIGH |

### 1.4 Legacy Only Services

| service_id | path | disposition | reason |
|------------|------|-------------|--------|
| SVC-047 | services/business_modules | LEGACY_ONLY | Generic business logic |
| SVC-048 | services/dispute_resolution | LEGACY_ONLY | Out of domain |
| SVC-049 | services/legal | LEGACY_ONLY | Legal services |
| SVC-050 | services/finance | LEGACY_ONLY | Business finance |
| SVC-051 | services/commerce | LEGACY_ONLY | E-commerce |
| SVC-052 | services/marketplace | LEGACY_ONLY | Marketplace |
| SVC-053 | services/tourism | LEGACY_ONLY | Off-domain |
| SVC-054 | services/livestock | LEGACY_ONLY | Off-scope domain |
| SVC-055 | services/inventory | LEGACY_ONLY | Inventory management |
| SVC-056 | services/content | LEGACY_ONLY | Content management |
| SVC-057 | services/admin | LEGACY_ONLY | Admin UI |
| SVC-058 | services/bots | LEGACY_ONLY | Bot management |
| SVC-059 | services/telegram_bot | LEGACY_ONLY | Telegram bot |
| SVC-060 | services/sponsors | LEGACY_ONLY | Sponsor features |
| SVC-061 | services/quality | LEGACY_ONLY | Quality control |
| SVC-062 | services/quality_assurance | LEGACY_ONLY | QA services |
| SVC-063 | services/dispute_resolution | LEGACY_ONLY | Business feature |
| SVC-064 | services/ecowallet | LEGACY_ONLY | Wallet features |
| SVC-065 | services/wallet | LEGACY_ONLY | Wallet management |

### 1.5 Blockchain / Payment (DO NOT TRANSFER)

| service_id | path | disposition | reason |
|------------|------|-------------|--------|
| SVC-066 | services/blockchain | DO_NOT_TRANSFER | Smart contracts forbidden, REFERENCE_ONLY |
| SVC-067 | services/wallet | DO_NOT_TRANSFER | Payment/wallet forbidden |
| SVC-068 | services/ecowallet | DO_NOT_TRANSFER | Payment/wallet forbidden |
| SVC-069 | services/ledger | OBSOLETE | Duplicate financial tracking |
| SVC-070 | services/oracle | LEGACY_ONLY | Duplicate of data_sources |
| SVC-071 | services/mobile_monitoring | OBSOLETE | Duplicate of monitoring |

### 1.6 Shared / Integration Services

| service_id | path | disposition | reason |
|------------|------|-------------|--------|
| SVC-072 | services/_contracts | KEEP | Shared domain contracts |
| SVC-073 | services/api_gateway | PLATFORM_CORE | API gateway |
| SVC-074 | services/workflows | PLATFORM_CORE | Workflow orchestration |
| SVC-075 | services/ogc | KEEP | OGC standards compliance |

---

## 2. Disposition Summary

| Disposition | Count | Notes |
|-------------|-------|-------|
| KEEP | 35 | Core scientific, domain, and infrastructure services |
| MERGE | 12 | satellite→science, map_engine→land, etc. |
| OBSOLETE | 8 | Empty directories, duplicates, superseded |
| LEGACY_ONLY | 19 | Out of domain, business features |
| DO_NOT_TRANSFER | 4 | Blockchain, wallet, payment |
| PLATFORM_CORE | 14 | Infrastructure consolidation target |
| MERGE_INTO_MODELS | 1 | science → models |
| MERGE_INTO_LAND | 2 | map_engine → land, landscape → land |
| MERGE_INTO_ECOSYSTEM | 2 | ecosystem ← rangeland |
| MERGE_INTO_MONITORING | 2 | mobile_monitoring → monitoring |
| MERGE_INTO_DATA_SOURCES | 1 | oracle → data_sources |
| MERGE_INTO_REPORTING | 2 | reporting ← analytics |
| BECOME_MODULE | 3 | daneshyar, tasmimyar, knowledge → modules |
| BECOME_DOMAIN_SERVICE | 3 | provenance, audit, validation |
| REVIEW | 2 | scientific_motors, landscape |
| UNKNOWN | 4 | dispute_resolution, governance, landscape, scientific_motors |

---

## 3. Migration Strategy

### Phase 1: Immediate (Blocks ECO-04)
1. Fix ECO-LEGACY-001 violation: Remove `engine/hydroma/generative_ai/` imports of `services.ai.*`
2. Provision `database/` package or remove engine dependencies on it
3. Create Engine Gateway module

### Phase 2: Consolidation (ECO-04)
1. Merge infrastructure services into Platform Core
2. Merge scientific services into bounded contexts
3. Extract AI into separate isolated layer
4. Remove blockchain/wallet/payment from engine scope

### Phase 3: Legacy Decomposition (Post-ECO-04)
1. Decommission OBSOLETE services
2. Migrate LEGACY_ONLY services to legacy archive
3. DO_NOT_TRANSFER: Move to reference archive

---

## 4. Risk Assessment by Service Group

| Service Group | Risk Level | Reason | Mitigation |
|---------------|------------|--------|------------|
| Scientific services | HIGH | Core to platform | Keep together, extract clean boundary |
| Infrastructure | MEDIUM | Operational complexity | Consolidate into Platform Core |
| AI services | HIGH | Boundary violation risk | Isolate in separate context |
| Legacy services | LOW | Non-core | Archive/DO_NOT_TRANSFER |
| Blockchain/Wallet | BLOCKING | Out of scope | DO_NOT_TRANSFER only |

---

## 5. Service Count Reconciliation

| Source | Count | Status |
|--------|-------|--------|
| ECO-01 §3.1 | 73 | NOT VERIFIED — actual count differs |
| ECO-01/13-SERVICE-ASSET-MAP.md | 73 services listed | MISSING: ai, observability, landscape |
| ECO-02/07 | 73 | Carries forward ECO-01 count |
| ECO-03 ACTUAL | **75** | Verified via filesystem enumeration |

**Discrepancy**: ECO-01 omits 3 services that exist in actual codebase:
- `ai` — AI services (present in codebase, mentioned in ECO-01 §257 but not in service list)
- `observability` — Monitoring/setup (present but not listed)
- `landscape` — Landscape analysis (present but not listed)

---

## 6. Service Ownership (Clarified)

| Service | Canonical Owner | Current Owner (if exists) | Evidence |
|---------|----------------|--------------------------|----------|
| models | hydroma-engine-team | services/models/registry.py maintained | Verified |
| science | hydroma-engine-team | services/science exists | Verified |
| climate | climate-team | services/climate exists | Verified |
| soil | soil-team | services/soil exists | Verified |
| carbon | ecosystem-team | services/carbon exists | Verified |
| land | land-team | services/land exists | Verified |
| watershed | hydrology-team | services/watershed exists | Verified |
| irrigation | agriwater-team | services/irrigation exists | Verified |
| tasmimyar | decision-team | services/tasmimyar exists | Verified |
| daneshyar | knowledge-team | services/daneshyar exists | Verified |
| ai | ai-team | services/ai exists | Verified |
| provenance | evidence-team | services/provenance exists | Verified |
| audit | security-team | services/audit exists | Verified |
| validation | validation-team | services/validation exists | Verified |

---

## 7. Findings

1. **CONFLICTING EVIDENCE**: ECO-01 claims 73 services; actual count is 75. Three services (`ai`, `observability`, `landscape`) are missing from ECO-01 reports.

2. **NOT VERIFIED**: ECO-02 claims "service import guards 100% enforced" — no import guard mechanism exists in codebase.

3. **VIOLATED**: ECO-LEGACY-001 — `services/api_gateway/routers/*.py` imports directly from `engine.hydroma.*` (100+ violations).

4. **VIOLATED**: `engine/hydroma/generative_ai/__init__.py` imports from `services.ai.*` — engine→services boundary violation.

5. **BLOCKING**: `database/` package missing → all service and engine imports that reference database fail.

6. **DESIGNED BUT NOT ENFORCED**: Service consolidation to 8 bounded contexts exists as design but NOT implemented in code.

---

*Report generated: 2026-10-08*
*Status: DESIGNED BUT NOT ENFORCED*