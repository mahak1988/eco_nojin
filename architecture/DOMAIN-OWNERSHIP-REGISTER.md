# Domain Ownership Register — Eco Nojin / HyDroMA

* **Status:** Active · **Opened:** 2026-10-11 (P2, A02, task 3 of `docs/project/PHASE_PLAN.md`)
* **Rule:** a row is the single answer to "who may change this data and who may read it". A new
  package that writes rows of a registered domain must be added to that domain's *allowed
  consumers/writers* in the same change, and the boundary check
  (`tools/check_service_boundaries.py`) stays green. `delete policy` follows the data-protection
  rules: no hard delete of decision/financial history (see `services/rangeland` governance rules).
* **Sensitivity:** `public` < `internal` < `sensitive` (migration routes, water sources, sacred
  sites, ownership, exact eco-locations — default private) < `regulated` (money, identity, legal).

| # | Logical domain | Data owner (package/tables) | Change reference | Allowed consumers | Delete policy | Sensitivity | Audit needs |
|---|---|---|---|---|---|---|---|
| 1 | Auth & identity | `services/auth` + `users`, `refresh_tokens`, `password_reset_tokens`, `login_history` | auth spec | gateway middleware, every service (read identity) | soft-delete users; never delete `login_history` | regulated | who/when/IP on every auth event |
| 2 | RBAC & roles | `services/auth/permissions.py`, `roles` | auth spec | gateway (enforcement only) | append-only | regulated | grant/revoke actor + timestamp |
| 3 | Marketplace | `com_orders`, `com_order_items`, `com_payment_intents`, `com_settlements`, `marketplace_order_items` | money contract D-09 | seller console, finance (read), notifications | no hard delete of orders | regulated | order state transitions with idempotency key |
| 4 | Seller console | `sellers`, `commission_rules` | marketplace spec | marketplace, admin | soft | internal | approval actor |
| 5 | Finance | `fin_accounts`, `fin_journal_batches`, `fin_journal_entries`, `fin_idempotency_keys` | money contract D-09 (source of truth) | wallet/ledger/commerce (read), consolidation (read) | **never delete** journal rows; corrections are new entries | regulated | every batch: poster, balanced proof |
| 6 | Wallet | `eco_wallets`, `daily_earnings` | money contract D-09 | finance (owner post-D-09), UI read | never delete balances | regulated | earn/redeem with correlation id |
| 7 | Ledger | `ledger_entries`, `escrow_records` | money contract D-09 | finance, marketplace | append-only | regulated | entry hash chain |
| 8 | Ecosystem balance | `eco_balance_accounts`, `eco_balance_entries` | money contract D-09 | finance, restoration (P11) | append-only | regulated | distribution snapshot per batch |
| 9 | EcoCoin | `ecocoin_balances`, `ecocoin_transactions` (**raw SQL, no migration — KN-02**) | **D-04 decision pending; writes frozen** | none until D-04 | n/a while frozen | regulated | full ledger + approval chain (P5) |
| 10 | Inventory | `inv_*` (9 tables) | inventory spec | marketplace (reserve/consume), landed stock | movements append-only; `abs(qty)` fix tracked as KN-07 | internal | movement reason + actor |
| 11 | Village hub | `village_*` (15 tables, several without migration — KN-12) | hub spec | village UI, admin queue | soft-delete; membership/history never deleted | sensitive | governance actions with approver |
| 12 | Nomads / pastoral communities | `nomadic_communities`, `tenure_rights` | land spec | village UI, land | never delete tenure rights | sensitive | approval + objection trail |
| 13 | Land & cadastre | `land_profiles`, `land_parcels`, `land_ownerships`, `land_tenure_rights`, `rangelands` | land spec | village, territory, map engine | never delete ownership history | sensitive | transfer chain |
| 14 | Tourism | `tourism_guides`, `tourism_tours`, `tourism_bookings` | tourism spec (P8) | marketplace checkout, finance (fee split) | bookings append-only | internal | approval + payment trail |
| 15 | Science runs & provenance | `engine/*`, run result tables | science spec D-13 | every domain (read), UI | runs are immutable once stored | internal | model/data versions + assumptions |
| 16 | Knowledge (Daneshyar) | `knowledge_*` | knowledge spec | tasmimyar, UI | soft | internal | publication rights |
| 17 | Decision support (Tasmimyar) | `tasmimyar/*`, decision records | decision spec | UI | advice records append-only | internal | criteria + accountable decision-maker |
| 18 | Notifications | `notification_*` | notification spec | every domain (enqueue only) | retention policy, 90 d | internal | delivery status |
| 19 | Realtime / events | `services/api_gateway/eventbus`, outbox | event policy (§below) | every domain (publish/subscribe) | outbox retained 7 d then pruned | internal | correlation id on every event |
| 20 | Audit & security | `audit_events`, `audit_logs`, `credit_audit_logs`, `admin_audit_logs` | security spec | admin UI | **never delete** | regulated | the audit trail itself |
| 21 | Content & compliance | `services/legal` static texts; compliance registry = **planned (P9)** | compliance spec D-03 | UI read | versions retained | regulated | assessment evidence per requirement |
| 22 | Admin settings | `settings` | admin spec | admin UI | append-only config history | regulated | setting change actor |

**Gaps the register makes explicit** (tracked in `docs/project/KNOWN_ISSUES.md`): rows 9, 11 and 21
are the D-04 / KN-12 / P9 debts — a registered owner with an unmanaged implementation is exactly
what this register exists to surface.
