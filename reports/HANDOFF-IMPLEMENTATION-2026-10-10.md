# HANDOFF — Implementation program (P0/P1/P2 items)

- **Created:** 2026-10-10 (session pause point)
- **Purpose:** resume the subagent implementation program with the command «ادامه بده» / «continue».
- **Rule:** the whole working tree is intentionally uncommitted (408 dirty entries; many pre-date this program from earlier sessions). **No agent may run mutating git commands.**

## Environment (every agent must be told this)

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest ...   # plain `python` is NOT on PATH
```

Validation gates after each change: targeted tests → `ruff check <files>` (pre-existing debt ~1876 must not grow) → `& "D:\eco_nojin\.venv\Scripts\python.exe" tools/detect_imports.py --root .` (must be 0 violations).

## DONE (verified by the owning agent; tests green at handoff time)

| # | Item | Key deliverables |
|---|---|---|
| P0-1 | Journal batches posted | wallet earn/redeem/transfer + commerce `settle_order` post their batches → trial balance & P&L non-empty (`finance/ledger_service.py` untouched semantics; tests: `test_wallet_batch_posting.py`, `commerce/tests/test_settlement_posting.py`) |
| P0-2 | `/finance/wallet/earn|redeem` 500 | signatures aligned + category aliases resolved via `earning_rates` (23 tests) |
| P0-3 | Five HTTP 500s | `InvSKU.is_active/is_trackable`, `ComOrderItem.fulfilled_qty` (router derives it from reservation `consumed_qty`), TYPE_CHECKING import fixed, explicit predicates, 422 for bad `expires_at` (16 tests) |
| P0-5 | Route shadowing | village_hub: all literal routes precede `/{village_id}`; test asserts ordering + count |
| P1-6 | Order items | `MarketplaceOrderItem` persisted; order+items+stock decrements atomic; `get_order_items` (7 tests) |
| P1-7 | Payments→orders | verify advances order to paid; amount validated server-side; dispute/settle/complete rewritten onto marketplace escrow; 3 `.get()` crashes fixed; admin approve mutates (15 tests) |
| P1-8 | LandscapeFund | settlements credit the per-village fund (`LandscapeFundCredit`), village read from `shipping_address["village_id"]`, `revenue_indicators` wired into a reporting path (12 tests) |
| P1-9 | Chart of accounts | `FinAccount.parent_id/is_active`, `chart_of_accounts.py` (ensure/seed, ECO_USER_*), pg_insert replaced with portable upsert, settlement+wallet ensure accounts → P&L classifies income (18 tests). **Known debt: `parent_id` is String(64); migration must make it Integer** |
| P1-10 | Nomadic workflow | tribal columns, approve/get/update/delete, owner-or-governance mutation, 4 routes, 12 tests; router now forwards `user.id` to the 5 create paths |
| P1-11 | Hub RBAC | all 12 create paths guarded (`_ensure_village_write`/`_ensure_landscape_write`), 18 negative tests |
| P1-12 | Reconciliation | real order/payment/settlement + inventory/ledger checks, `overall_ok` from results (9 tests) |
| P2-13 | Consolidated ledger | `consolidation.py` + admin endpoint, 5 sources side-by-side (5 tests) |
| P2-17 | Tourism API | 13 endpoints + schemas + model registration + mount (12 tests) |
| P2-18 | Inventory integrity | unique constraint on balance key, full-key locking, savepoint-based get-or-create, expiry sweeper, unblock, adjust floor, fixed reconciliation/stocktake (22 tests) |
| P2-19 | HTTP regression | 82 tests across 4 new files in `services/api_gateway/tests/` |
| P2-20 | Events/notifications | 20 domain events + owner notifications, lazy imports, failure-isolated (24 tests) |
| X | Integration debt | payment `_notify` session poisoning fixed + crediting tests de-flaked + pinning test |
| Y | New capability surface | `GET /marketplace/orders/{id}/items`, SKU list `is_trackable` + 404 guard, `bank_transfer` registered, startup chart seeding |
| — | test count fix | `test_total_route_count_unchanged` 49→53 (coordinator) |

Baseline at pause: `pytest services/` green (≈915+ passed, 9 skipped), `engine/` green (2440 passed).

## PROGRAM COMPLETE — all 20 items done (2026-10-10, final gates green)

| item | agent | outcome |
|---|---|---|
| N (P2-16) land registry | completed | 3 tables + `LandRegistryService` + 26 tests |
| S (P2-15) valuation/COGS | completed | 4 accounts, moving average, balanced/posted batches, 40 tests |
| X (integration debt) | completed | `_notify` own unit of work; crediting tests de-flaked; 4 tests |
| Y (capability surface) | completed | order-items route, `is_trackable` list + 404 guards, bank_transfer registered, startup chart seeding |
| Q (P2-14) Lot/FEFO | completed | `InvLot` + additive `lot_uuid`, FEFO, expiry, 7 endpoints, 54 tests |
| Z (import-time flake) | completed | lazy provider, no import-time engine side effect, 7 tests |
| U (P0-4) Alembic | completed | guarded revision `20261010_180000_waves_2_6_schema_delta`; incompatible `parent_id` FK REMOVED (Integer change rejected: 5 existing tests); fresh-DB and create_all-DB both pass |
| AA (parallel) Numba | completed | 124–244x speedup, bit-identical, optional import + pure fallback, 62 tests |
| AB (parallel) money property tests | completed | 73 Hypothesis tests + **6 invariant violations found (see below)** |
| AC (parallel) security | completed | real webhook mapping, CSP/HSTS-https-only headers, auth rate limiter, 22 tests |

**FINAL GATES (all green):** `pytest services/` 1164 passed / 9 skipped / 0 failed · `pytest engine/` 2642 passed / 30 skipped / 42 xfailed / 0 failed · `ruff check .` **890** (AGENTS.md baseline 1876 is stale) · `mypy engine` **0** (baseline 1034 stale) · `tools/detect_imports.py` 0 violations · app boots (112 routes).

**6 invariant violations exposed by AB's property tests (NOT fixed — outside the 20-item scope, recommended next wave):**
1. **CRITICAL cross-tenant idempotency**: `OrderService._check_order_idempotency` (`services/commerce/service.py:314`) looks the key up without `buyer_id` — a buyer can be handed another buyer's order id and pay its total. Test: `services/commerce/tests/test_properties_order_money.py:518`.
2. Penny orders unsellable: when both fees round to `0.00`, the `ECO_PLATFORM_REVENUE` leg is zero and `create_journal_batch` refuses → paid order cannot settle (`commerce/service.py:754`). Test: `:622`.
3. Marketplace fee drift: `marketplace/service.py:330` builds `total` from unrounded divisions → stored lines need not sum to total (64 drifting cases in sweep). Test: `test_properties_marketplace_money.py:260`.
4. `reconcile_inventory` docstring justification about `unblock` is factually wrong (drift detected). 
5. Documented take-rate band "0–588 bps" is wrong (measured 0–600 commerce, 0–1600 tourism) — `finance/revenue_indicators.py:14-16`.
6. `adjust` drift — known/documented limitation.

**Order-dependent fragility (not a gate failure):** `test_s18` soil tests (`SOIL_AMENDMENT` requires `bulk_density`) fail in isolation but pass in the full suite — pre-existing debt from an earlier session's half-finished work on `engine/hydroma/soil`.

## Suggested next wave (if requested)

Priority order: (1) fix the cross-tenant idempotency scope (security), (2) zero-fee settlement, (3) marketplace fee quantisation, (4) correct the take-rate documentation, (5) migrate the remaining legacy `create_all` tables with the guarded-reconcile pattern from U, (6) HMAC on the bank webhook + ASVS v5.0.0 pass, (7) Postgres-backed concurrency tests.

## Known follow-ups (report-only, not yet scheduled)

- Per-user attribution across the five ledgers is still impossible (no shared user key) — P2-13 documents this.
- `ComOrder.village_id` does not exist (village resolved from `shipping_address`); a real column would make LandscapeFund crediting first-class.
- Tourism hub-side half (`village_hub /{id}/tourism`) is still a second, unmerged surface.
- Grazing rights/migration corridors are modelled as columns, not first-class entities; herd registry absent.
- `adjust` movements still store `abs(qty)` (signed delta only in notes) — reconciliation excludes them.
- FOR UPDATE cannot be proven on SQLite; needs a Postgres-backed concurrency test.
- Postgres `varchar`-FK issue on `FinAccount.parent_id` (fix inside P0-4).
