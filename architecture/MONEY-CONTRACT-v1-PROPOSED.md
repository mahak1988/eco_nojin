# Money Contract v1 — PROPOSED (pending D-09/D-10/D-11 approver)

* **Status:** **PROPOSED — not ratified.** `docs/project/OPEN_DECISIONS.md` rows
  D-09 (source of truth), D-10 (shared user key) and D-11 (balance write
  ownership) name their approvers; an agent may not close them. This page is the
  analysis + recommended default the approver signs or amends. Nothing in the
  repository behaves differently because this page exists.
* **Authored:** 2026-10-11, P5 (A05) · **Measured baseline:** `docs/project/BASELINE.md` §3
  (five parallel money stores) and `services/api_gateway/routers/finance_consolidation.py`
  (the read-only consolidation view).

## 1. What the code says today (measured, not intended)

| Store | Tables | Writers observed | Role today |
|---|---|---|---|
| finance | `fin_accounts`, `fin_journal_batches`, `fin_journal_entries`, `fin_idempotency_keys` | `services/finance` | the only double-entry store with balanced-batch invariant + trial balance |
| wallet | `eco_wallets`, `daily_earnings` | `services/finance.wallet_service` (economics layer) | user-facing ECO balance, credited via balanced journal batches |
| ledger | `ledger_entries`, `escrow_records` | `services/ecosystem` | ecosystem ledger + escrow |
| ecosystem | `eco_balance_accounts`, `eco_balance_entries` | `services/ecosystem` | the 800/200/200 fee distribution |
| commerce | `com_payment_intents`, `com_orders`, `com_order_items`, `com_settlements` | `services/commerce` | order/payment/settlement records (money magnaritus live in `com_payment_intents`) |
| blockchain | `ecocoin_balances`, `ecocoin_transactions` | `services/blockchain` via **raw SQL, no migration** | frozen since P1 (KN-02) until D-04 closes |

## 2. The recommended model (D-09/D-10/D-11)

1. **`fin_journal_entries` is the source of truth for value.** Every value
   change in any domain posts a balanced batch through the finance contract in
   the same transaction as the domain change (wallets, orders, settlements and
   the ecosystem distribution are *read models* derived from it).
2. **`users.id` is the shared attribution key (D-10).** Every ledger row that
   carries a party gains a `user_id` column (additive, guarded, backfill-safe),
   so per-user attribution across all five stores becomes possible. Until the
   approver signs, reports place figures side by side and say attribution is
   pending — never aggregate into one "user balance".
3. **Exactly one domain may write balances (D-11): finance.** Wallets, the
   ecosystem ledger and commerce post *through* finance; they do not write
   balance rows themselves. Enforced by the static scan in
   `services/finance/tests/test_p5_money_invariants.py`.
4. **Every money write carries: balanced batch (debits == credits), an
   idempotency key at the API edge, a trace/correlation id, an audit row, and a
   post-at-call-site (no deferred flush that can half-apply).**
5. **Compensation, not deletion:** a wrong money movement is reversed by a new
   balanced batch; rows are never edited or deleted.

## 3. What P5 implemented while the decision is open

* KN-07: `reconcile_inventory` folds adjustment movements into the signed sum
  (signed delta recovered from the documented notes prefixes; an unknown format
  still surfaces as drift) — so inventory value is no longer blind to ledger
  mispostings.
* The money-write boundary scan (test above) — it passes on the current tree,
  which means the recommended D-11 ownership already holds statically; the test
  is the regression guard.
* D-04 (EcoCoin): writes remain frozen behind
  `HYDROMA_ECOCOIN_WRITES_ENABLED` (P1); the HTTP router still returns
  fabricated literals (KN-19). Resolution options for the approver:
  **(a) governed ledger** — model + migration + registry + tests, unfreeze;
  **(b) removal** — delete the service + router and the raw-SQL tables; **(c)
  keep frozen** — hard-disable the route honestly (an explicit
  `feature-disabled` error instead of a fake success).

## 4. Migration sketch for D-10 (only after approval)

1. Additive column `user_id VARCHAR(36)` (nullable) to
   `ledger_entries`, `eco_balance_accounts`, `eco_balance_entries`,
   `com_orders` (already `buyer_id`), `ecocoin_*` when they gain a registry —
   each a guarded `add_column` revision with a backfill from the existing
   party column, one table per revision.
2. A reconciliation report keyed by `users.id` across all five stores.
3. The static boundary scan extended with the new owners.

**Nothing in this section is executed until the named approver closes D-09/10/11.**
