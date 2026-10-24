# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — SERVICE REGISTRY

**Document ID:** ECO-00-SERVICE-REGISTRY  
**Date:** 2026-10-08  
**Status:** COMPLETE

---

## Service Registry

This registry catalogs every service identified in the `services/` directory.

| Service ID | Name | Domain | Status | Repair Status | Engine Dependencies | Data Dependencies | Consumers | Legacy Coupling | Future Destination |
|------------|------|--------|--------|---------------|---------------------|-------------------|-----------|-----------------|--------------------|
| AUDIT-SVC-001 | API Gateway | API / Routing | KEEP_WITH_REPAIR | Needs test coverage | `engine.hydroma.*`, `engine.land.models` | `database.hub`, `database.models` | All external clients | Imports business module routers | Central gateway in new platform |
| AUDIT-SVC-002 | Land Service | Land Intelligence | KEEP_WITH_REPAIR | **FIXED** — adapters/ created, import broken before repair | `engine.land.models` | None | API Gateway / api_gateway/routers/land.py | Fixed: `adapters.engine_adapter` now exists | Replace with direct engine import |
| AUDIT-SVC-003 | Auth Service | Auth | KEEP_WITH_REPAIR | Circular import risk with gateway | None direct | `database.hub`, `database.models` | API Gateway | `services.auth.compat` → `services.api_gateway.auth` | Resolve auth boundary |
| AUDIT-SVC-004 | Auth Legacy | Auth (Legacy) | LEGACY_WRAPPER | N/A — compatibility layer | None | `database.hub`, `database.models` | API Gateway / auth routers | Heavy coupling to api_gateway | Deprecate after auth migration |
| AUDIT-SVC-005 | Commerce | Orders | KEEP_WITH_REPAIR | Inter-service coupling | None | `database.models` | API Gateway | Imports finance, inventory | Keep, refactor boundaries |
| AUDIT-SVC-006 | Carbon | Carbon | VALID_KEEP | None | `engine.hydroma.carbon` | `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-007 | Finance | Finance | VALID_KEEP | None | None | `database.models` | Commerce service | None | Keep |
| AUDIT-SVC-008 | Inventory | Inventory | VALID_KEEP | None | None | `database.models` | Commerce | None | Keep |
| AUDIT-SVC-009 | Wallet | Wallet | VALID_KEEP | None | None | `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-010 | Model Registry | Models | KEEP_WITH_REPAIR | Carbon_engine import risk | 22 engine imports | None | API Gateway | None | Keep, resolve import |
| AUDIT-SVC-011 | Validation | Validation | VALID_KEEP | None | 14 engine.hydroma imports | None | API Gateway | None | Keep |
| AUDIT-SVC-012 | Workflow | Workflow | KEEP_WITH_REPAIR | Cross-service dependencies | `engine.hydroma.simulation.*` | `database.hub`, `database.models` | API Gateway | Imports api_gateway.errors | Keep, resolve boundaries |
| AUDIT-SVC-013 | Field Monitoring | Monitoring | VALID_KEEP | None | `engine.hydroma.soil.health`, `engine.hydroma.water.quality` | `database.hub`, `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-014 | Notification | Notification | VALID_KEEP | None | `engine.hydroma.config.settings` | None | API Gateway | None | Keep |
| AUDIT-SVC-015 | Business Modules | Business Logic | KEEP_WITH_REPAIR | Cross-service AI dependency | `engine.hydroma.mrv.iot_ingest` | `database.models` | API Gateway | Voice module imports services.ai | Keep, isolate AI layer |
| AUDIT-SVC-016 | Backup | Admin | VALID_KEEP | None | None | `database.hub`, `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-017 | Analytics | Analytics | VALID_KEEP | None | None | `database.hub` | API Gateway | None | Keep |
| AUDIT-SVC-018 | Eco Wallet | Wallet | VALID_KEEP | None | None | `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-019 | Satellite | Satellite | UNKNOWN | Not yet inspected | None | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-020 | Oracle | Data Sources | VALID_KEEP | None | None | Unknown | API Gateway | None | Keep |
| AUDIT-SVC-021 | Privacy | Privacy | VALID_KEEP | None | None | Unknown | API Gateway | None | Keep |
| AUDIT-SVC-022 | Ecosystem | Ecosystem | VALID_KEEP | None | None | Unknown | API Gateway | None | Keep |
| AUDIT-SVC-023 | Contracts | Contracts | VALID_KEEP | None | None | `database.base`, `database.models` | API Gateway | None | Keep |
| AUDIT-SVC-024 | Admin | Admin | KEEP_WITH_REPAIR | Conditional market imports | None | `database.hub`, `database.models` | API Gateway | Imports marketplace, tourism, landscape conditionally | Keep |
| AUDIT-SVC-025 | Alerting | Alerting | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-026 | Analysis | Analysis | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-027 | Bots | Bots | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Has adapters/ dir | Unknown |
| AUDIT-SVC-028 | Blockchain | Blockchain | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-029 | Content | Content | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-030 | Dispute Resolution | Legal | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-031 | Knowledge | Knowledge | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-032 | Landscape | Landscape | UNKNOWN | Not yet inspected | Unknown | Unknown | Admin, Auth | Unknown | Unknown |
| AUDIT-SVC-033 | Ledger | Financial | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-034 | Legal | Legal | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-035 | Livestock | Livestock | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-036 | Logistics | Logistics | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-037 | Map Engine | GIS | UNKNOWN | Not yet inspected; **engine forbidden-import resolved** | Unknown | Unknown | API Gateway | Previously referenced by engine/land/integration/water_adapter (now removed) | Unknown |
| AUDIT-SVC-038 | Marketplace | Marketplace | UNKNOWN | Not yet inspected | Unknown | Unknown | Admin | Referenced conditionally by admin | Unknown |
| AUDIT-SVC-039 | OGC | GIS | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-040 | Quality Assurance | QA | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-041 | Quality | Quality | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-042 | Rangeland | Rangeland | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-043 | Reliability | Reliability | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-044 | Reporting | Reporting | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-045 | Restoration | Restoration | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-046 | Science | Science | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-047 | Scientific Motors | Scientific | UNKNOWN | Referenced in models/registry.py docstring | Unknown | Unknown | API Gateway, engine | Referenced in engine code | Unknown |
| AUDIT-SVC-048 | Security | Security | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-049 | Simulation | Simulation | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-050 | Sponsors | Sponsorship | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-051 | Supabase | Integration | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-052 | Tourism | Tourism | UNKNOWN | Not yet inspected | Unknown | Unknown | Admin (conditional) | Referenced conditionally by admin | Unknown |
| AUDIT-SVC-053 | Workers | Background Jobs | UNKNOWN | Not yet inspected | Unknown | Unknown | API Gateway | Unknown | Unknown |
| AUDIT-SVC-054 | Hydroma (services/hydroma) | Obsolete | OBSOLETE | All subdirectories empty | None (empty) | None | None | None | Archive/remove |

**Note:** Services AUDIT-SVC-024 through AUDIT-SVC-054 were not fully inspected during this audit pass. Their status is based on import pattern evidence from dependency analysis. Full forensic details for these services require additional audit passes.

---

*End of Service Registry*
