# CAPABILITY MATRIX — ECO Nojin / HyDroMA

* **Status:** Active · **Recorded:** 2026-10-11 · **Rule (eco.md P-01):** a file or endpoint is not a
  capability. Levels: `planned` → `stub` → `implemented` → `tested` → `validated`, plus
  `partial` (some steps missing) and `deprecated`.

## Platform core

| Capability | Status | Evidence | Gap / next |
|---|---|---|---|
| API gateway (routes, middleware stack: HTTPS, rate-limit, security headers, request-ID, CSRF, Idempotency) | **tested** | 113 routes / 630 paths / 710 ops boot clean | keep 113-route pin suite green |
| Auth & identity (login, refresh tokens, password reset, OAuth connections, login history) | **tested** | `services/auth`, `users`, `refresh_tokens`, `password_reset_tokens` | cross-tenant matrix (P3) |
| RBAC / authorization | **partial** | `services/auth/permissions.py`; rangeland RBAC only on delete/update | scope-complete authorization tests (P3), sponsors placeholder (KN-13) |
| Multi-tenancy data scoping | **partial** | buyer-scoped idempotency lookup; village-scoped indexes | negative tests shop↔shop, village↔village (P3) |
| Audit trail | **tested** | `audit_events`, `audit_logs`, `credit_audit_logs` | extend audit to governance actions (P7) |
| i18n / RTL | **partial** | locale middleware, EN/FA notification templates | real UI + translation workflow (P12) |

## Economic domains

| Capability | Status | Evidence | Gap / next |
|---|---|---|---|
| Accounting core (accounts, balanced journals, batches, idempotency) | **tested** | `fin_*`; 73 property-based money tests | single-truth model D-09/D-10 (P5) |
| Wallet | **implemented** | `eco_wallets`, `daily_earnings` | converge on journal (P5) |
| Commerce (catalog→cart→order→payment intent→settlement) | **tested** | `com_*`; cross-tenant idempotency, penny-order settlement fixes | E2E proof incl. payment success path (P6) |
| Marketplace bank payment and escrow | **partial / API-tested** | Persisted checkout, buyer tracking claims, admin pending-transfer queue and verification/escrow hold; focused API flow tested | Add settlement workflow and end-to-end browser coverage; resolve D-07 |
| Marketplace hierarchy (marketplace→bazaar→shop→product) | **partial** | `services/marketplace` + `services/commerce` order tables; **no `bazaar` level exists in code yet** | P6 defines the hierarchy contract (incl. the bazaar level from `eco.md`) and separates seller verification vs brand usage vs legal trademark vs product certification |
| Inventory (SKU, warehouse, lot, balance, movements, reservation, stocktake, FEFO paths) | **validated** | `services/inventory/tests`: 164 passed / 0 failed | fix `abs(qty)` adjust blindness (KN-07, P5) |
| Bank transfer webhook | **tested** | fail-closed `BANK_WEBHOOK_SECRET` (503 unset) | keep |
| Eco Coin | **implemented-but-policy-frozen** | `services/blockchain/service.py` + `ecocoin.transfer` permission; no migration, no registry | **freeze writes until D-04**; then governed ledger or removal (P1→P5) |
| Per-user financial attribution | **stub/absent** | five ledgers, no shared key (KN-08) | D-10 migration (P5) |

## Community / land / tourism

| Capability | Status | Evidence | Gap / next |
|---|---|---|---|
| Village space (profile, marketplace-of-village) | **partial** | Village Hub beta; ~18 tables, no migration; 4 dead routes fixed | migration + access tiers (P7) |
| Rangeland / pasture | **partial** | `services/rangeland/models.py:34` physical land row only | legal/social differentiation + carrying capacity ops (P7) |
| Local governance (working group, charter, approval workflow, member history) | **planned** | zero matches for `charter`/`working_group`/`community_space` | build per eco.md Phase 7 (P7) |
| Sensitive-data protection (migration routes, water sources, sacred sites, ownership) | **planned** | — | access tiers + publication rules (P7) |
| Tourism (tour, guide, booking, fee split, settlement) | **partial/stub-gate** | models+service tested (fee conservation suite) but router returns `requires_setup` (KN-01) | un-stub + 9-entity model decision + capacity/refund tests (P8) |
| Events (festival, expo, competition, seasonal market) | **planned** | — | P8 |
| Compliance registry (RegulatorySource→Jurisdiction→Requirement→Credential→Assessment) | **planned** | `services/legal` = 8 static texts only | registry + workflow, pilot jurisdiction (P9) |
| Restoration / development projects | **partial** | carbon/MRV/oracle modules exist | MVP-5 project lifecycle (P11) |

## Science & decision support

| Capability | Status | Evidence | Gap / next |
|---|---|---|---|
| HyDroMA engine (scenario runner, EngineGateway, cpp/numba bridge) | **tested** | engine suite 2698/0 fail; strict suite green | publish only validated models (D-13) |
| Model registry & maturity | **tested** | `engine/models/registry.py`: 70 models, 13 validated / 57 unvalidated, card-based honesty folding | triage 57 (P10) |
| Provenance & uncertainty on outputs | **partial** | provenance service + RAG provenance tests | wire into every scientific payload (P10) |
| Numba/C++ acceleration claim (124–244×) | **reported, not independently reproduced here** | program record in `reports/` | reproducibility note: hardware, data, versions (P10 gate) |
| Daneshyar / knowledge layer (entries, review queue, collections, attachments, RAG) | **partial** | owner-scoped submissions; content-admin review queue; approval records reviewer/time and alone enables public visibility; public collection list only exposes verified sources; API tests cover access boundaries | add review rationale/history; shard heavy tests (P13) |
| Tasmimyar (decision support) | **partial** | `services/tasmimyar` + `engine/tasmimyar` | explainability contract (P11) |
| Real-time events | **partial** | SSE/realtime router; NATS optional | D-06 (P2) |

## Frontend & operations

| Capability | Status | Evidence | Gap / next |
|---|---|---|---|
| Web frontend | **removed 2026-10-13** | the SPA tree, its design/audit/plan docs, its tooling and the CI job were deleted by owner decision (D-01 closed) | none — backend-only; any future frontend needs a new decision row |
| Observability | **tested** | Prometheus HTTP + 58 custom series; OTel disabled by config | enable tracing with D-15 |
| Backups | **tested** | `runtime/backup.py`, sha256 manifests | restore drill proof (P4/P15) |
| DB migrations | **tested** | single guarded head, renders clean | deferred FKs + Enum pre-pass + registry feed (P4) |
| Offline | **planned** | — | 3 tiers per D-12 (P13) |
| Staged release / rollback | **planned** | — | P15 |
