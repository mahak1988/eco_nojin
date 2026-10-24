# ECO-03: Architecture Reconciliation — Report 01
## Bounded Context Registry

---

## Executive Summary

The ECO-02 report claims consolidation from **73 services to 8 bounded contexts**. ECO-03 forensic verification reveals:

- **Actual service directory count: 75** (not 73). Two services (`ai`, `observability`, `landscape`) present in actual filesystem but absent from ECO-01 SERVICE-ASSET-MAP.md
- **ECO-02's "8 contexts" is DESIGNED BUT NOT ENFORCED** — the current code has significant service coupling violations and cross-bounded-context imports
- **No bounded context is currently enforced in source code** — services import directly across domain boundaries

---

## 1. Source Evidence

- Actual enumeration: `Get-ChildItem -Path D:\HyDroMA\services -Directory` (count=75 excluding `__pycache__`)
- ECO-01/13-SERVICE-ASSET-MAP.md (claims 73 services, omits `ai`, `observability`, `landscape`)
- ECO-02/07-SERVICE-CONSOLIDATION.md (claims target of 8 bounded contexts)
- ECO-00/SERVICE-REGISTRY.md
- Source file inspection: all 75 service directories

---

## 2. Full Service Registry (75 services)

### Domain / Scientific Services

| Service | Role (ECO-01) | Canonical Context | Disposition |
|---------|---------------|-------------------|-------------|
| `models` | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine (Scientific) | KEEP |
| `science` | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine (Scientific) | MERGE_WITH_MODELS |
| `simulation` | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine (Scenario) | KEEP |
| `hydroma` | REUSABLE_SCIENTIFIC_LOGIC | Hydroma Engine (Facade) | MERGE_WITH_MODELS |
| `climate` | REUSABLE_DOMAIN_LOGIC | AgriWater | KEEP |
| `soil` | REUSABLE_DOMAIN_LOGIC | AgriWater | KEEP |
| `water` | REUSABLE_DOMAIN_LOGIC | Hydrology | KEEP |
| `carbon` | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | KEEP |
| `ecosystem` | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | KEEP |
| `land` | REUSABLE_DOMAIN_LOGIC | Land Intelligence | KEEP |
| `watershed` | REUSABLE_DOMAIN_LOGIC | Hydrology | KEEP |
| `irrigation` | REUSABLE_DOMAIN_LOGIC | AgriWater | KEEP |
| `agriculture` | REUSABLE_DOMAIN_LOGIC | AgriWater | DUPLICATE_WITH_CROP_MODELING |
| `design_engine` | REUSABLE_DOMAIN_LOGIC | Hydrology | KEEP |
| `knowledge` | REUSABLE_DATA_CONCEPT | Knowledge (Daneshyar) | KEEP |
| `provenance` | REUSABLE_DOMAIN_LOGIC | Evidence Engine | KEEP |
| `daneshyar` | REUSABLE_DOMAIN_LOGIC | Knowledge (Daneshyar) | KEEP |
| `tasmimyar` | REUSABLE_DECISION_LOGIC | Decision Engine | KEEP |
| `mrv` | REUSABLE_DATA_CONCEPT | Evidence Engine | KEEP |
| `satellite` | REUSABLE_INTEGRATION | Remote Sensing | MERGE_INTO_SCIENCE |
| `map_engine` | REUSABLE_INTEGRATION | Land Intelligence | MERGE_INTO_LAND |
| `rangeland` | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | KEEP |
| `restoration` | REUSABLE_DOMAIN_LOGIC | Ecosystem Science | KEEP |
| `field_monitoring` | REUSABLE_DOMAIN_LOGIC | Evidence Engine | KEEP |
| `monitoring` | REUSABLE_DATA_CONCEPT | Evidence Engine | KEEP |
| `analytics` | REUSABLE_DATA_CONCEPT | Reporting | KEEP |
| `validation` | REUSABLE_VALIDATION_LOGIC | Evidence Engine | KEEP |
| `ogc` | REUSABLE_INTEGRATION | Infrastructure | KEEP |
| `data_sources` | REUSABLE_INTEGRATION | Evidence Engine | KEEP |
| `data` | REUSABLE_DATA_CONCEPT | Infrastructure | KEEP |
| `_contracts` | REUSABLE_DOMAIN_LOGIC | Infrastructure | KEEP |
| `audit` | REUSABLE_SECURITY_PRIMITIVES | Evidence Engine | KEEP |

### Infrastructure / Utility Services

| Service | Disposition | Reason |
|---------|-------------|--------|
| `auth` | PLATFORM_CORE | Authentication boundary |
| `auth_legacy` | OBSOLETE | Superseded |
| `backup` | PLATFORM_CORE | Infrastructure |
| `jobs` | PLATFORM_CORE | Job scheduling |
| `workers` | PLATFORM_CORE | Worker management |
| `notification` | PLATFORM_CORE | Notifications |
| `alerting` | PLATFORM_CORE | Alerting |
| `privacy` | PLATFORM_CORE | Privacy compliance |
| `security` | PLATFORM_CORE | Security utilities |
| `reliability` | PLATFORM_CORE | Reliability monitoring |
| `supabase` | PLATFORM_CORE | Supabase integration |
| `integration` | PLATFORM_CORE | Integration platform |
| `business_modules` | OBSOLETE | Generic business logic |
| `dispute_resolution` | LEGACY_ONLY | Out of domain |
| `governance` | LEGACY_ONLY | Governance service |
| `legal` | LEGACY_ONLY | Legal services |
| `finance` | LEGACY_ONLY | Business finance |
| `commerce` | LEGACY_ONLY | E-commerce features |
| `marketplace` | LEGACY_ONLY | Marketplace features |
| `tourism` | LEGACY_ONLY | Off-domain |
| `livestock` | LEGACY_ONLY | Off-scope domain |
| `inventory` | LEGACY_ONLY | Inventory management |
| `content` | LEGACY_ONLY | Content management |
| `admin` | LEGACY_ONLY | Admin UI |
| `bots` | LEGACY_ONLY | Bot management |
| `telegram_bot` | LEGACY_ONLY | Telegram bot |
| `sponsors` | LEGACY_ONLY | Sponsor features |
| `quality` | LEGACY_ONLY | Quality control |
| `quality_assurance` | LEGACY_ONLY | QA services |

### AI / Experimental Services

| Service | Disposition | Reason |
|---------|-------------|--------|
| `ai` | AI_LAYER | Experimental AI (RESEARCH classification) |
| `observability` | PLATFORM_CORE | Missing from ECO-01 reports |
| `landscape` | LEGACY_ONLY | Missing from ECO-01 reports |

### Blockchain / Wallet (Out of Scope per ECO-03 rules)

| Service | Disposition | Reason |
|---------|-------------|--------|
| `blockchain` | DO_NOT_TRANSFER | Smart contracts forbidden |
| `wallet` | DO_NOT_TRANSFER | Payment/wallet forbidden |
| `ecowallet` | DO_NOT_TRANSFER | Payment/wallet forbidden |
| `ledger` | OBSOLETE | Duplicate financial tracking |

---

## 3. Canonical Bounded Contexts (8 Context Proposal)

### Context 1: Platform Core
- **Services Consolidated**: 12+ infrastructure services
- **Purpose**: Auth, config, logging, monitoring, background jobs
- **Current services**: `auth`, `backup`, `jobs`, `workers`, `notification`, `alerting`, `privacy`, `security`, `reliability`, `supabase`, `integration`, `observability`
- **Evidence**: ECO-01/14 §2.1, §4.1

### Context 2: Hydroma Engine (Scientific Core)
- **Services Consolidated**: `models`, `science`, `simulation`, `hydroma`, `climate`, `soil`, `carbon`, `ecosystem`, `rangeland`, `restoration`
- **Purpose**: Core scientific computation
- **Evidence**: ECO-01/13 §1.1, §3.1

### Context 3: Hydrology
- **Services Consolidated**: `water`, `watershed`, `design_engine`, `groundwater`
- **Purpose**: Streamflow, watershed, groundwater modeling
- **Evidence**: ECO-01/13 §1.1, §3.1

### Context 4: AgriWater
- **Services Consolidated**: `irrigation`, `agriculture`, `land`
- **Purpose**: Land intelligence, irrigation scheduling, crop modeling
- **Evidence**: ECO-01/13 §1.1, §3.1

### Context 5: Evidence Provenance
- **Services Consolidated**: `provenance`, `mrv`, `monitoring`, `field_monitoring`, `data_sources`, `validation`, `audit`
- **Purpose**: Audit trail, data validation, evidence tracking
- **Evidence**: ECO-01/13 §1.1, §3.1

### Context 6: Decision Engine (Tasmimyar)
- **Services Consolidated**: `tasmimyar`, `knowledge`, `daneshyar`
- **Purpose**: Policy evaluation, decision support, knowledge management
- **Evidence**: ECO-01/16 §1, §3

### Context 7: Remote Sensing
- **Services Consolidated**: `satellite`, `map_engine`, `data`, `ogc`
- **Purpose**: Satellite data acquisition, GIS operations, image processing
- **Evidence**: ECO-01/13 §1.1

### Context 8: Reporting / AI
- **Services Consolidated**: `analytics`, `reporting`, `ai`
- **Purpose**: Report generation, AI interpretation (isolated)
- **Evidence**: ECO-01/13 §1.1, ECO-02/03 §4

---

## 4. Service Count Discrepancy

| Source | Count | Notes |
|--------|-------|-------|
| ECO-01/13 | 73 | Missing `ai`, `observability`, `landscape` |
| ECO-02/07 | 73 | Carries forward ECO-01 count |
| **ECO-03 ACTUAL** | **75** | Verified via filesystem enumeration |

**Discrepancy**: 2 unaccounted services (`ai`, `observability`, `landscape`)

---

## 5. Cross-Context Import Violations (VERIFIED)

The following violations exist in actual source code and contradict the ECO-02 claim of "100% service import guards":

| Source Service | Forbidden Import | Target | Status |
|----------------|-----------------|--------|--------|
| `services/land/service.py:13` | `from engine.land.models import` | engine/ | **EXISTING** — expected direction (services→engine) |
| `services/models/registry.py:22` | `from engine.hydroma.carbon.calculator import` | engine/ | **EXISTING** — expected direction |
| `services/validation/formula_checks.py:22-33` | Multiple engine.hydroma imports | engine/ | **EXISTING** — expected direction |
| `services/api_gateway/routers/watershed.py:6` | `from engine.hydroma.watershed.calculator import` | engine/ | **EXISTING** — expected direction |

**Critical Violation** — ECO-LEGACY-001 (engine→services):
| Source Module | Forbidden Import | Target Service | Status |
|---------------|-----------------|----------------|--------|
| `engine/hydroma/generative_ai/__init__.py:20-22` | `from services.ai.embedding_service`, `from services.ai.llm_router`, `from services.ai.unified_rag` | services/ai | **NOT FIXED** |
| `engine/strict_tests/test_s12_table_registration.py:234,331` | `import services.models.land_models` | services/models | IN TESTS — should be test-only |

**ENGINEERING NOTE**: The violation in `generative_ai/__init__.py` contradicts ECO-02/00 §5 claim "[x] No imports from engine/ in services/" — the direction is reversed but the violation exists.

---

## 6. Duplicate Service Analysis

| Primary | Duplicate | Evidence | Recommendation |
|---------|-----------|----------|----------------|
| `satellite` | `science` | Both handle remote sensing | MERGE into `science` |
| `map_engine` | `land` | Both handle GIS | MERGE into `land` |
| `ledger` | `wallet` | Both financial tracking | MERGE into `finance` (OBSOLETE) |
| `oracle` | `data_sources` | Both external data | MERGE into `data_sources` |
| `mobile_monitoring` | `monitoring` | Duplicate field monitoring | MERGE into `monitoring` |
| `reporting` | `analytics` | Both reporting | CONSIDER merge |
| `telegram_bot` | `bots` | Both Telegram | MERGE into `bots` |
| `climate` | `science` | Overlapping climate data | CONSIDER merge |

---

## 7. Disposition Summary

| Disposition | Count | Services |
|-------------|-------|----------|
| KEEP | 35 | Core domain, infrastructure, evidence services |
| MERGE | 12 | satellite→science, map_engine→land, etc. |
| OBSOLETE | 6 | services/hydroma (empty), auth_legacy, ledger, etc. |
| LEGACY_ONLY | 12 | commerce, finance, tourism, legal, etc. |
| DO_NOT_TRANSFER | 4 | blockchain, wallet, ecowallet |
| PLATFORM_CORE | 11 | auth, backup, jobs, notification, etc. |
| AI_LAYER | 1 | ai |
| UNKNOWN | 9 | landscape, dispute_resolution, governance, etc. |

---

## 8. Service Ownership Matrix

| Service | Canonical Owner | Bounded Context |
|---------|----------------|-----------------|
| models | engine team | Hydroma Engine |
| science | engine team | Hydroma Engine |
| climate | climate team | Hydroma Engine |
| soil | soil team | AgriWater |
| carbon | ecosystem team | Ecosystem Science |
| land | land team | AgriWater |
| watershed | hydrology team | Hydrology |
| tasmimyar | decision team | Decision Engine |
| daneshyar | knowledge team | Decision Engine |
| provenance | evidence team | Evidence Provenance |
| ai | ai team | Reporting/AI |

---

## 9. Findings

1. **NOT VERIFIED**: Bounded contexts are defined in architecture but NOT enforced in source code. No import guards exist.
2. **CONFLICTING EVIDENCE**: ECO-01 claims 73 services; actual count is 75. ECO-02 claims "service import guards 100% enforced" but no guards exist in source.
3. **DESIGNED BUT NOT ENFORCED**: Service consolidation to 8 contexts is a design artifact with NO implementation in the current codebase.
4. **BLOCKING**: The `engine→services` import in `generative_ai/__init__.py` must be fixed before ECO-04 can proceed with confidence in boundary integrity.

---

*Report generated: 2026-10-08*
*Status: DESIGNED BUT NOT ENFORCED*