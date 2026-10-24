# ARCHITECTURE, MODELS & SERVICES REFERENCE — ECO Nojin / HyDroMA

**Date:** 2026-10-11 · **Audience:** planning, consulting and the frontend workstream
**Extracted from the live tree** (not from specs): 150 ORM tables / 1,847 columns,
630 documented API paths, 113 registered gateway routes, ~79 service domains,
47 scientific sub-domains in `engine/hydroma`, 8 architecture rules.

---

## 1. System shape

```
                        ┌─────────────────────────────────────────────┐
   clients (future SPA)  │  services/api_gateway  (FastAPI monolith)   │
                        │  630 paths · 113 routes · ~8 middleware     │
                        └───────┬───────────┬───────────┬─────────────┘
                                │           │           │
                 ┌──────────────▼──┐  ┌─────▼─────┐  ┌──▼───────────────┐
                 │ services/ (~79  │  │ database/ │  │ engine/ (via     │
                 │ domains)        │  │ 150 tables│  │ EngineGateway)   │
                 │ marketplace,    │  │ 1847 cols │  │ land, hydroma(47)│
                 │ finance,        │  │ 1 Base    │  │ cpp bridge       │
                 │ inventory, …    │  └───────────┘  └──────────────────┘
                 └──────┬──────────┘
                        │ NATS eventbus (20+ domain events) + notifications
```

**Three hard rules (enforced by `tools/detect_imports.py`, 8 rules, 0 violations):**
1. `engine/` must not import `services/`, `api_gateway/`, or anything but the sanctioned
   `database.config` / `database.base` persistence bridge.
2. `services/` reach the engine **only** through the gateway facade
   (`engine/gateway/`, `_gateway_facade.py`).
3. `services/ai` is isolated by its own rule.

**Cross-cutting services:** `services/api_gateway/eventbus/*` (NATS publisher with
`publish_marketplace_event` / `publish_event`); `services/notification/db_service.py`
(AppNotification, owner-scoped); `services/security/pqcrypto.py` (ML-DSA/ML-KEM);
`tools/detect_imports.py` (architecture guard); `tools/cleanup.py` (workspace hygiene).

---

## 2. Engine (`engine/`) — the scientific core

Isolated, deterministic, offline-testable (~2,700 tests). Sub-systems:

| Module | Role | Frontend relevance |
|---|---|---|
| `engine/gateway/` | `EngineGateway` — the only legal entry from services; model dispatch, input validation | indirect |
| `engine/land/` | terrain science: D8 hydrology, flow accumulation, Strahler, TPI/TWI, RUSLE erosion, capability (USDA IâVIII), DEM processing — **Numba-accelerated (measured 2026-10-11, 150x150 DEM, best-of-2: flow_accumulation 54x, strahler_order 247x, calculate_tpi 71x, combined 218x; optional import with pure-Python fallback, bit-identical parity)** | map layers, analysis results |
| `engine/hydroma/` (47 domains) | soil, climate/ET, crop, groundwater, carbon, MRV, soil-neuro, biofertilizer, calibration, assimilation, simulation, data pipeline | science tools, run results |
| `engine/cpp_core` + `cpp_bridge` | native extension (`hydroma_core.cp311/cp312.pyd`) with parity tests vs Python | performance; transparent to UI |
| `engine/data/` | soil parameter tables (van Genuchten), meta-contract, physics guards | reference data |
| `engine/indicators`, `engine/decision`, `engine/scenario`, `engine/numerical`, `engine/tasmimyar`, `engine/evidence`, `engine/honesty`, `engine/scientific_verification` | indicator registry, decision weights, scenario engine, numerical safety, verification harnesses, provenance/honesty labels | indicators shown with provenance |
| `engine/strict_tests/` | 1,323-test strict gate (S01–S18 architecture/science rules) | CI gate |

**Provenance contract:** engine results carry a `data_source` and an L0–L5 level label
(assumption → measured). The UI must display these — they are a core product differentiator.

---

## 3. Database (`database/`) — one Base, 150 tables

`database/models.py` aggregates every `services/*/models` module onto a single `Base`.
Tables are created at runtime by `create_all` **and** by the Alembic chain
(head `20261011_090000_remaining_legacy_tables`, guarded/idempotent ops).
Runtime DB: SQLite (`database/hub.py`, WAL-capable, `sqlite_wal_deployment_safe()`
gate) — a Postgres target needs an Enum pre-pass.

### 3.1 Data-model catalog by domain (key entities; full list from `Base.metadata`)

**Identity & access** — `users`, `refresh_tokens`, `oauth_connections`,
`password_reset_tokens`, `login_history`, `api_keys`, `organization_memberships`,
`organizations`, `audit_events`, `audit_logs`, `admin_audit_logs`.

**Marketplace / commerce (37 tables)** — `marketplaces`, `marketplace_sellers`,
`marketplace_products`, `marketplace_members`, `marketplace_orders`,
`marketplace_order_items` (line-level basket), `marketplace_commission_rules`,
`marketplace_founders`, `marketplace_reviews`, `marketplace_review_helpful`,
`marketplace_wishlist`, `marketplace_payments`, `marketplace_escrow_entries`;
`com_orders`, `com_order_items`, `com_payment_intents`, `com_settlements`;
`products`, `shipments`, `shipment_events`, `disputes`, `dispute_events`,
`b2b_demands`.

**Village hub & nomads (16)** — `village_capabilities`, `village_opportunities`,
`village_opportunity_interests`, `village_projects`, `village_investments`,
`village_events`, `village_event_registrations`, `village_needs`, `village_experiences`,
`village_destinations`, `village_brands`, `village_development_gaps`,
`village_engagements`, `village_festivals`, `village_tourism_services`,
`nomadic_communities` (14 base + 8 tribal columns: owner, village link, pasture area,
migration route, herd size, approver/at), `entrepreneur_profiles`.

**Land & territory (13)** — `land_profiles`, `land_parcels`, `land_ownerships`
(effective-dated, share_pct), `land_tenure_rights` (grazing + seasonal corridors),
`landscape_villages`, `landscape_governance`, `landscape_funds`, `landscape_fund_distributions`,
`landscape_fund_credits`, `territories`, `territory_governance`, `territory_funds`,
`territory_fund_distributions`, `territory_brands`, `rangelands`.

**Accounting & money (14)** — `fin_accounts` (chart of accounts, parent/is_active),
`fin_journal_batches`, `fin_journal_entries` (double-entry, posted at call sites),
`fin_idempotency_keys`, `ledger_entries`, `escrow_records`, `eco_wallets`,
`eco_transactions`, `eco_balance_accounts`, `eco_balance_entries`, `daily_earnings`,
`provenance_records`. **Five parallel money stores** exist; `GET /finance/consolidated/position`
reports them side by side without merging.

**Inventory (9)** — `inv_skus`, `inv_warehouses`, `inv_locations`,
`inv_inventory_balances` (unique per sku+warehouse+location+lot),
`inv_stock_movements` (append-only ledger, 9 movement types),
`inv_reservations` (expire + sweep), `inv_stocktakes`, `inv_stocktake_lines`,
`inv_lots` (lot number, expiry, unit cost, FEFO).

**Tourism (3)** — `tourism_guides`, `tourism_tours`, `tourism_bookings`
(ecological capacity enforcement; 800/200/200 bps fee split).

**Carbon / MRV / satellite / soil / science (12)** — `carbon_projects`,
`carbon_credits`, `carbon_events`, `carbon_credit_records`, `carbon_retirements`,
`mrv_observations`, `satellite_analyses`, `soil_analyses`, `crop_water_req_results`,
`runoff_calculation_results`, `structure_design_results`, `simulation_runs`,
`scenario_runs`, `model_versions`, `model_runs`, `data_lineage`, `compute_jobs`.

**Knowledge / content / engagement (10)** — `knowledge_entries`,
`knowledge_attachments`, `knowledge_collections`, `knowledge_collection_entries`,
`content_items`, `content_versions`, `content_translations`, `newsletter_subscribers`,
`contact_messages`, `ai_conversations`, `pilot_applications`, `sponsorships`,
`quality_inspections`, `quality_certificates`, `legal_texts`, `tool_registry_entries`,
`monitoring_data`, `alerts`, `alert_rules`, `alert_notifications`, `iot_devices`,
`oracle_*` (3), `disputes`, `notifications`, `settings`, `backup_configs`,
`backup_jobs`, `restore_jobs`, `workflow_runs`, `job_events`, `int_outbox_events`.

### 3.2 Relationship highlights the UI must respect
- `marketplace_order_items.order_id → marketplace_orders`; `com_order_items.order_id → com_orders`
  (FK deferred, business-key convention — always fetch by parent id, never assume a join).
- Village entities: `village_id` is a String business key with **no FK** to
  `landscape_villages`; ownership/governance is enforced in the service layer.
- `nomadic_communities.village_id` links a tribe to a village by business key;
  `land_tenure_rights` links a tribe/community to parcels with a seasonal window.
- Journal chain: batch → entries → account (join by **code first, id second** —
  `finance/account_ref.py`); reports read **posted batches only**.
- Inventory FIFO/FEFO: movements carry `lot_uuid` (nullable) beside the legacy `lot_id`
  sentinel; non-lot stock uses weighted-average costing.

---

## 4. Services & API catalog (by frontend priority)

### 4.1 Marketplace & commerce — 115 ops
Write: `POST /products`, `/products/{id}/images`, `/products/{id}/tokenize`, `/orders`,
`/orders/{id}/confirm`, `/cart`, `/payments` (bank transfer live; Stripe stub — hide),
`/orders/{id}/dispute|settle|complete`, escrow release/refund, admin approve/reject
(vendors, products, marketplaces). Reads: catalogue, vendors, my orders, admin stats,
**`/orders/{id}/items`** (persisted basket). Commerce parallel flow:
`POST /commerce/orders` → `/pay` → `/confirm-payment` → `/ship` → `/mark-delivered`
→ `/settle`; `GET /orders/{id}` returns truthful per-line `fulfilled_qty`.

### 4.2 Auth — 49 ops
`/auth/register|login|refresh|logout`, forgot/reset/change password, profile, sessions,
**passkeys (WebAuthn)**, admin user management (block/unblock/bulk-action, 46 admin ops
under `/admin/*`). Rate-limited (env-configurable, 429 + `Retry-After`).

### 4.3 Inventory — 27 ops
SKUs (`is_active`, `is_trackable`), warehouses, locations, movement verbs
(`receipt`, `issue`, `transfer`, `adjust`, `scrap`, `return`, `unblock`), reservations
(reserve/consume/release, `expires_at` 422-validated), lots (`POST /lots`, `/expire-due`,
`/{id}/close`, list), stocktakes, **`/valuation/report` + `/valuation/{sku_code}`**.

### 4.4 Finance — 18 ops
`/accounts` (chart of accounts), `/ledger/batch` (+`/post`), `/ledger/trial-balance`,
`/ledger/profit-and-loss` (admin), `/wallet` (earn/redeem/stats), `/payments/intent`,
`/payments/webhook/{provider}` (**HMAC-SHA256, fail-closed**), `/reconciliation/*`,
`/idempotency/keys`, **`/consolidated/position`** (five ledgers, admin).

### 4.5 Village hub — 53 routes
Reads: village profile/dashboard/dossier, capabilities, opportunities (+interest/team),
projects (+progress/investors), investments, experiences, destinations, events
(+register), needs, brands, development gaps, festivals, engagements, B2B demands,
**nomadic communities** (list/get). Writes: create for each (governance-guarded) +
owner/admin update/delete + **approve** for nomads. `POST /ai-recommendations`.

### 4.6 Land & territory — 21 ops
`/land/profiles` CRUD + `terrain-analysis`, `drainage-analysis`, `capability-assessment`;
`/landscape/villages` + governance members (role-guarded);
`/territories/{village_id}/submit|verify|review|resubmit|archive`;
cadastral registry service (parcels/ownership/tenure) — **no HTTP routes yet** (planned:
`/api/v1/land/parcels…`).

### 4.7 Tourism — 14 ops
Guides (register/verify by admin or landscape_manager), tours (create/approve),
bookings (create/confirm-payment/complete), public catalogue with capacity enforcement.

### 4.8 Remaining platform (≈380 ops)
`/ecowallet` (12), `/blockchain` (23), `/compliance` (17), `/carbon` (10),
`/ecosystem` (10), `/satellite` (11), `/mrv` (11), `/hydroma` (34 — the engine tools),
`/ai` (13), `/analytics` (7), `/science` (7), `/security` (13), `/knowledge` (9),
`/iot` (6), `/legal-texts` (6), `/tool-registry` (6), `/realtime`, `/sync`,
`/voice`, `/ussd`, `/passkeys`, `/lms`, `/pilot`, `/sponsors`, `/quality`,
`/logistics`, `/livestock`, `/manual`, `/models`, `/nature`, `/water-signature`…

---

## 5. Contracts the frontend must implement

1. **Idempotency**: mutation routes read the `Idempotency-Key` header via middleware;
   the client must mint one key per user intent and reuse it across retries (finance table
   `fin_idempotency_keys`, commerce orders, payments).
2. **Errors**: `EcoNojinException` with `ECO-*` codes and a status code; the gateway has a
   catch-all in dev — map codes to human messages, never show raw text.
3. **Auth**: bearer access token (memory), refresh rotation, WebAuthn for passkeys;
   CSRF middleware active for cookie flows; auth endpoints rate-limited (handle 429).
4. **RBAC vocabulary** (mirror it exactly in `permissions.ts`): platform roles
   `ROLE_ADMIN`, `ROLE_ADVISOR`, `ROLE_CONTENT_ADMIN`, `ROLE_FARMER`, `ROLE_SECURITY_ADMIN`,
   `ROLE_USER_ADMIN`; domain/governance roles `admin`, `landscape_manager`,
   `council_member`, `marketplace_rep`, `tourism_rep`, `agriculture_rep`.
   Guards seen in code: `require_user`, `require_admin`, `require_roles(...)`,
   `require_api_key`.
5. **Realtime**: SSE via `/api/v1/realtime` + NATS-backed domain events (20+ emitted for
   marketplace/commerce/hub: `order_placed`, `payment_completed`, `order_shipped`,
   `order_completed`, `order_cancelled`, `order_settled`, `shop_created`,
   `seller_verified`, `product_approved|rejected`, `marketplace_approved|rejected`,
   `settlement_posted`, `payment_refunded`, `nomadic_community_created|approved`,
   `event_registration_created`, `b2b_demand_created`) — use them to invalidate queries.
6. **Money**: all amounts are `Decimal` serialized as strings with scale
   (`Numeric(18,8)` in the ledger vs `Numeric(15,2)`/`(18,2)` in commerce/marketplace) —
   parse with a decimal library, never `parseFloat`, and render per-context precision.
7. **Provenance**: scientific results carry `data_source` + L0–L5 level; render as a badge.
8. **Pagination**: server-side (`limit`/`offset` on list endpoints) — assume tables of
   thousands of rows (movements, journal entries, audit logs).

---

## 6. Domain → frontend screen map (data + flows)

| Domain | Screens | Primary entities | Key flows |
|---|---|---|---|
| Auth | login (password/passkey), profile, sessions, admin users | users, roles | login → token → refresh |
| Marketplace | catalogue, search, product, storefront, cart, checkout, orders, reviews | products, sellers, orders, order_items | browse → cart → checkout (idempotency key) → bank transfer → order tracking → escrow/dispute |
| Seller console | my products, orders, commission, payouts | sellers, commission_rules | create product → admin approval → sell → commission |
| Village hub | village workspace (9 tabs), governance queue | village_* (15) | create project → invest → progress → complete |
| Nomads | community list/register, approval queue, pasture map | nomadic_communities, tenure_rights | register → approve → visible |
| Land | map workspace, parcel editor, ownership, tenure, analyses | land_profiles/parcels/ownerships/tenure_rights, rangelands | create profile → analysis → parcel → ownership/transfer → tenure rights |
| Inventory | SKU table, stock by location/lot, reservations, stocktake, valuation | inv_* (9) | receipt (+lot) → reserve → issue (FEFO) → stocktake → valuation |
| Finance | wallet, payments, settlements, journal, TB/P&L, reconciliation, consolidated | fin_* (4), eco_*, ledger | earn/redeem → payment intent → settlement → journal → TB/P&L → reconcile |
| Tourism | guides, tours, bookings, capacity | tourism_* (3) | guide → verify → tour → approve → book → pay → complete |
| Science | run tools, results, history | soil/carbon/mrv/satellite/scenario runs | parameters → run → result + provenance |
| Admin | users/roles, audit, settings, security status | admin_audit_logs, audit_events, settings | block/unblock, review audit |

---

## 7. What is solid vs. what is in flux (for planning)

**Solid (build on it):** auth + RBAC, double-entry ledger (posted, chart of accounts),
inventory CRUD/reservations/lots/valuation, marketplace order + escrow flows, village hub
CRUD + governance, tourism lifecycle, Alembic chain, eventbus emission, security headers +
rate limiting + webhook HMAC, import guard, cleanup tooling.

**Stubs to hide or plan around:** Stripe payment provider (raises), COD/Wallet confirm
paths, sponsors admin router (placeholder auth → 501), several `engine/ports` stubs,
`adjust` unsigned movements, per-user ledger attribution absent, WebAuthn requires
backend session support verification.

**In flux (re-check before committing UI):** cadastral registry has no HTTP routes yet;
five money ledgers are reported side-by-side, not merged; tourism exists as two surfaces
(API service + hub listing) pending consolidation; SQLite runtime (WAL needs ≥3.51.3).
