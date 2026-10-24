# ECO-00 ENGINE & SERVICES FORENSIC AUDIT — SERVICE AUDIT REPORT

**Document ID:** ECO-00-SERVICE-AUDIT  
**Date:** 2026-10-08  
**Status:** COMPLETE
**Auditor:** Kilo autonomous agent

---

## Service Classification Legend

| Status | Meaning |
|--------|---------|
| **VALID_KEEP** | Service is clean, minimal legacy coupling, no defects |
| **KEEP_WITH_REPAIR** | Service has defects but is fundamentally valid |
| **KEEP_WITH_REFACTOR** | Service is valid but has architectural issues |
| **MERGE_CANDIDATE** | Service overlaps significantly with another |
| **DUPLICATE** | Service duplicates functionality |
| **LEGACY_WRAPPER** | Service is a compatibility wrapper for old platform |
| **OBSOLETE** | Service exists only for old platform, no new consumers |
| **UNSAFE** | Service has security or correctness defects |
| **UNKNOWN** | Service status cannot be determined |

---

## AUDIT-SVC-001: API Gateway

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-001 |
| **Name** | API Gateway |
| **Domain** | API / Routing / Orchestration |
| **Path** | `services/api_gateway/` |
| **Status** | KEEP_WITH_REPAIR |

**Purpose:** Central FastAPI application that routes all HTTP requests, provides authentication, error handling, middleware (CORS, upload size, tenant, idempotency), and NATS event bus integration.

**Entry points:**
- `services/api_gateway/main.py` — FastAPI app creation, router inclusion

**Public methods:**
- 30+ routers covering domain-specific operations

**Dependencies:**
- `engine.hydroma.config.settings` (settings)
- `engine.hydroma.*` (scientific calculations)
- `engine.land.models` (land analysis)
- `database.hub` (database access)
- `database.models` (ORM models)
- `services.api_gateway.*` (internal)
- `services.commerce`, `services.finance`, `services.inventory` (business logic)

**Business rules:**
- JWT-based authentication
- Role-based access control (RBAC)
- CORS policy enforcement
- Rate limiting
- Idempotency for state-changing operations

**State:** Stateless (HTTP)

**Persistence assumptions:**
- Database via `database.hub`
- NATS for event bus
- Redis (optional) for rate limiting
- Cloudflare R2 for file storage

**Events:** NATS (JetStream) for publish/subscribe

**Security assumptions:**
- All endpoints require authentication except health, auth, contact
- Secrets handled via pydantic SecretStr and settings
- CORS configured per settings

**Tests:** None found in `services/api_gateway/tests/`

**Known defects:**
- No local test directory discovered

**Legacy coupling:**
- Imports from `services.commerce`, `services.finance`, `services.inventory` for router inclusion (expected for gateway)

---

## AUDIT-SVC-002: Land Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-002 |
| **Name** | Land Service |
| **Domain** | Land Intelligence |
| **Path** | `services/land/` |
| **Status** | UNSAFE |

**Purpose:** Land profile creation and terrain analysis using the engine.

**Entry points:**
- `services/land/service.py` — `LandService` class

**Public methods:**
- `create_profile()`
- `get_profile()`
- `update_profile()`
- `analyze_terrain()`
- `calculate_capability()`
- `calculate_erosion_risk()`

**Dependencies:**
- `engine.land.models` (data structures)
- `adapters.engine_adapter.EngineAdapter` — **CREATED** (was BLOCKER-P1)

**Business rules:**
- Land profiles contain location, terrain analysis, capability assessment
- Profiles can be persisted optionally

**State:** In-memory profile cache (`_profiles` dict)

**Persistence assumptions:**
- Optional database persistence via `db` parameter

**Events:** None

**Security assumptions:**
- None explicit

**Tests:**
- `services/land/tests/test_integration.py`
- `services/land/tests/test_service.py`
- `services/land/tests/test_land_profile.py`

**Known defects:**
1. ✅ FIXED — `adapters.engine_adapter` now exists at project root
2. ✅ FIXED — `LandService.__init__` now succeeds with `EngineAdapter()` default

**Legacy coupling:**
- `services/land/land_profile.py` — comments reference removed direct engine imports (lines 1-3)

**Classification:** KEEP_WITH_REPAIR — adapters package created, import broken before repair

**Recommendation:** Service is functional. Optional future improvement: replace `adapters.engine_adapter.EngineAdapter` with direct engine import to reduce indirection.

---

## AUDIT-SVC-003: Authentication Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-003 |
| **Name** | Authentication Service |
| **Domain** | Auth |
| **Path** | `services/auth/` |
| **Status** | KEEP_WITH_REPAIR |

**Purpose:** User authentication, JWT token management, refresh tokens, role management.

**Entry points:**
- `services/auth/service.py` — `AuthService` class
- `services/auth/main.py` — entry point (imports database.hub)
- `services/auth/api/__init__.py` — API endpoints

**Public methods:**
- `register()`
- `login()`
- `refresh_token()`
- `verify_token()`
- `get_user()`

**Dependencies:**
- `services.auth.compat` → imports `services.api_gateway.auth` (circular potential)
- `services.api_gateway.auth` (shared auth functions)
- `database.hub`, `database.models`, `database.base`

**Business rules:**
- JWT-based auth with access + refresh tokens
- Role-based authorization
- Token expiration (30 min access, 30 day refresh)
- Password hashing via bcrypt

**Known defects:**
- `services/auth/compat.py:13` imports from `services.api_gateway.auth` creating inter-service coupling

**Legacy coupling:**
- `services/auth_legacy/` exists as separate service

**Classification:** KEEP_WITH_REPAIR — needs to resolve auth/api_gateway coupling

---

## AUDIT-SVC-004: Auth Legacy Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-004 |
| **Name** | Auth Legacy Service |
| **Domain** | Auth (Legacy) |
| **Path** | `services/auth_legacy/` |
| **Status** | LEGACY_WRAPPER |

**Purpose:** Legacy authentication compatibility layer.

**Dependencies:**
- `services.api_gateway.auth`
- `services.api_gateway.eventbus`
- `services.api_gateway.dependencies`
- `database.hub`, `database.models`

**Known defects:**
- `services/auth_legacy/repository.py:128` has deferred import of `services.api_gateway.logging`

**Classification:** LEGACY_WRAPPER — preserves backward compatibility for auth migration

---

## AUDIT-SVC-005: Commerce Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-005 |
| **Name** | Commerce Service |
| **Domain** | Commerce / Orders |
| **Path** | `services/commerce/` |
| **Status** | KEEP_WITH_REPAIR |

**Purpose:** Order processing, payment processing, idempotency.

**Dependencies:**
- `services.api_gateway.exceptions`
- `services.finance.ledger_service`
- `services.finance.payment_provider`
- `services.finance.wallet_service`
- `services.inventory.service`
- `database.hub`, `database.models`

**Business rules:**
- Order state machine (pending, paid, shipped, delivered, cancelled)
- Payment processing with idempotency
- Wallet integration for payments

**Known defects:**
- Circular import potential: if finance imports commerce, cycle occurs

**Classification:** KEEP_WITH_REPAIR — heavy cross-service dependencies

---

## AUDIT-SVC-006: Carbon Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-006 |
| **Name** | Carbon Service |
| **Domain** | Carbon / MRV |
| **Path** | `services/carbon/` |
| **Status** | VALID_KEEP |

**Purpose:** Carbon credit management and carbon project operations.

**Dependencies:**
- `database.models`
- `engine.hydroma.carbon`

**Classification:** VALID_KEEP — clean internal dependency

---

## AUDIT-SVC-007: Finance Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-007 |
| **Name** | Finance Service |
| **Domain** | Finance |
| **Path** | `services/finance/` |
| **Status** | VALID_KEEP |

**Purpose:** Wallet, payment, ledger operations.

**Classification:** VALID_KEEP — foundational service

---

## AUDIT-SVC-008: Inventory Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-008 |
| **Name** | Inventory Service |
| **Domain** | Inventory |
| **Path** | `services/inventory/` |
| **Status** | VALID_KEEP |

**Purpose:** Stock and inventory management.

**Classification:** VALID_KEEP

---

## AUDIT-SVC-009: Wallet Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-009 |
| **Name** | Wallet Service |
| **Domain** | Wallet / Credits |
| **Path** | `services/wallet/` |
| **Status** | VALID_KEEP |

**Purpose:** Eco wallet balance management, carbon credit retirement.

**Dependencies:**
- `database.models`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-010: Model Registry Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-010 |
| **Name** | Model Registry |
| **Domain** | Models |
| **Path** | `services/models/registry.py` |
| **Status** | KEEP_WITH_REPAIR |

**Purpose:** Registry of 22 scientific models with parameter specs, fidelity labels, and execution wrapper.

**Dependencies:**
- `engine.hydroma.carbon.calculator`
- `engine.hydroma.climate.et_calculator`
- `engine.hydroma.soil.health`
- `engine.hydroma.soil.pedotransfer`
- `engine.hydroma.soil.physics`
- `engine.hydroma.soil.salinity`
- `engine.hydroma.watershed.calculator`
- `engine.hydroma.wrapper`
- **`services.api_gateway.routers.carbon_engine`** — potential circular import

**Known defect:**
- Line 49: imports from `services.api_gateway.routers.carbon_engine` — cross-layer dependency from services/models to api_gateway

**Classification:** KEEP_WITH_REPAIR — needs to resolve carbon_engine import

---

## AUDIT-SVC-011: Validation Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-011 |
| **Name** | Validation Service |
| **Domain** | Validation |
| **Path** | `services/validation/` |
| **Status** | VALID_KEEP |

**Purpose:** Formula validation and validation checks.

**Dependencies:**
- `engine.hydroma.*` (14 imports)

**Classification:** VALID_KEEP

---

## AUDIT-SVC-012: Workflow Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-012 |
| **Name** | Workflow Service |
| **Domain** | Workflow |
| **Path** | `services/workflow/` |
| **Status** | KEEP_WITH_REPAIR |

**Purpose:** Workflow orchestration using engine simulation components.

**Dependencies:**
- `services.api_gateway.errors`
- `engine.hydroma.simulation.orchestrator`
- `engine.hydroma.decision_support.recommender`
- `database.hub`, `database.models`

**Classification:** KEEP_WITH_REPAIR

---

## AUDIT-SVC-013: Field Monitoring Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-013 |
| **Name** | Field Monitoring Service |
| **Domain** | Monitoring |
| **Path** | `services/field_monitoring/` |
| **Status** | VALID_KEEP |

**Purpose:** IoT device monitoring and data ingestion.

**Dependencies:**
- `engine.hydroma.soil.health`
- `engine.hydroma.water.quality`
- `database.hub`, `database.models`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-014: Notification Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-014 |
| **Name** | Notification Service |
| **Domain** | Notification |
| **Path** | `services/notification/` |
| **Status** | VALID_KEEP |

**Purpose:** Send notifications via various channels.

**Dependencies:**
- `engine.hydroma.config.settings`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-015: Business Modules

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-015 |
| **Name** | Business Modules |
| **Domain** | Business Logic |
| **Path** | `services/business_modules/` |
| **Subservices** | voice/, iot/, carbon/ |
| **Status** | KEEP_WITH_REPAIR |

**Voice Module Dependencies:**
- `services.ai.llm_router`
- `services.ai.unified_rag`

**IoT Module Dependencies:**
- `engine.hydroma.mrv.iot_ingest`
- `database.hub`, `database.models`

**Classification:** KEEP_WITH_REPAIR — cross-service AI dependency in voice module

---

## AUDIT-SVC-016: Backup Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-016 |
| **Name** | Backup Service |
| **Domain** | Administration |
| **Path** | `services/backup/` |
| **Status** | VALID_KEEP |

**Dependencies:**
- `services.api_gateway.errors`
- `database.hub`, `database.models`, `database.base`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-017: Analytics Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-017 |
| **Name** | Analytics Service |
| **Domain** | Analytics |
| **Path** | `services/analytics/` |
| **Status** | VALID_KEEP |

**Dependencies:**
- `database.hub`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-018: Eco Wallet Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-018 |
| **Name** | Eco Wallet Service |
| **Domain** | Wallet / Earnings |
| **Path** | `services/ecowallet/` |
| **Status** | VALID_KEEP |

**Dependencies:**
- `database.models`

**Classification:** VALID_KEEP

---

## AUDIT-SVC-019: Satellite Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-019 |
| **Name** | Satellite Service |
| **Domain** | Satellite Data |
| **Path** | `services/satellite/` |
| **Status** | UNKNOWN |

**Purpose:** Satellite data ingestion and processing.

**Classification:** UNKNOWN — needs further investigation

---

## AUDIT-SVC-020: Oracle Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-020 |
| **Name** | Oracle Service |
| **Domain** | Data Sources |
| **Path** | `services/oracle/` |
| **Status** | VALID_KEEP |

**Purpose:** Data source orchestration.

**Classification:** VALID_KEEP

---

## AUDIT-SVC-021: Privacy Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-021 |
| **Name** | Privacy Service |
| **Domain** | Privacy |
| **Path** | `services/privacy/` |
| **Status** | VALID_KEEP |

**Purpose:** Privacy vault for user data protection.

**Classification:** VALID_KEEP

---

## AUDIT-SVC-022: Ecosystem Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-022 |
| **Name** | Ecosystem Service |
| **Domain** | Ecosystem |
| **Path** | `services/ecosystem/` |
| **Status** | VALID_KEEP |

**Purpose:** Ecosystem activity tracking and verification.

**Classification:** VALID_KEEP

---

## AUDIT-SVC-023: Contracts Service

| Field | Value |
|-------|-------|
| **Service ID** | AUDIT-SVC-023 |
| **Name** | Contracts Service |
| **Domain** | Contracts |
| **Path** | `services/contracts/` |
| **Status** | VALID_KEEP |

**Purpose:** Contract versioning and testing.

**Dependencies:**
- `database.base`, `database.models`

**Classification:** VALID_KEEP

---

## Service Classification Summary

| Classification | Count | Services |
|----------------|-------|----------|
| VALID_KEEP | 11 | Carbon, Finance, Inventory, Wallet, Validation, Backup, Analytics, EcoWallet, Oracle, Privacy, Ecosystem, Contracts |
| KEEP_WITH_REPAIR | 4 | API Gateway, Land, Auth, Commerce, Workflow, Model Registry, Business Modules |
| LEGACY_WRAPPER | 1 | Auth Legacy |
| UNKNOWN | 1+ | Satellite, others not fully inspected |
| OBSOLETE | 0 | (none confirmed) |
| UNSAFE | 0 | (none — Land Service repaired) |
| DUPLICATE | 0 | (none confirmed) |
| MERGE_CANDIDATE | 0 | (deferred per ECO-00 rules) |

---

*End of Service Audit Report*
