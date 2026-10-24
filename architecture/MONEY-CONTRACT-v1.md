# Money Contract v1 — RATIFIED

* **Status:** **RATIFIED** · **Ratified:** 2026-10-11 by the user's execution instruction
  (the approver rows D-09/D-10/D-11 in `docs/project/OPEN_DECISIONS.md` are closed with this
  document as their record). Supersedes `MONEY-CONTRACT-v1-PROPOSED.md`.
* **Enforced by:** `services/finance/tests/test_p5_money_invariants.py` (the write-boundary
  scan), `services/finance/tests/test_cross_ledger_report.py` (the attribution report), the
  property-based money suites, and `tests/test_p14_guard_sweep.py`.

## 1. Source of truth (D-09)

`fin_journal_entries` is **the** source of truth for value. Every value change in any domain
posts a balanced batch (debits == credits) through the finance contract in the **same
transaction** as the domain change it pays for. Wallets, the ecosystem balance, the commerce
settlements and the EcoCoin ledger (when it returns) are **read models** derived from the
journal — never independent ledgers.

Consequences:
* A domain that changes value without posting a balanced batch is a contract violation.
* A batch that does not balance is rejected, never rounded into agreement.
* Money is `Decimal` end to end; the API wire format is JSON numbers (contract v1 §3), and the
  string-amount option stays a v2 decision with the frontend contract (D-01).

## 2. The shared user key (D-10)

`users.id` is the single attribution key, carried by every ledger row that names a party:

| Table | Column | State |
|---|---|---|
| `eco_wallets` | `user_id` | always had it |
| `eco_balance_accounts` / `eco_balance_entries` | `user_id` | always had it (measured in P5) |
| `com_orders` | `buyer_id` | order identity |
| `ledger_entries` | `user_id` | **added by `20261011_150000_p5_shared_user_key`** (nullable; historical rows stay NULL and are not edited retroactively) |
| `ecocoin_balances` / `ecocoin_transactions` | (raw SQL) | frozen (D-04); the registry move brings them under this table when it lands |

The cross-ledger report (`services/finance/cross_ledger_report.py`) is the sanctioned way to
answer "what does this user hold" — side by side, source-named, empty ≠ zero, never merged.

## 3. Who may write balances (D-11)

**Only `services/finance`.** Wallets, the ecosystem ledger and commerce post *through* finance;
they do not write balance rows themselves. This is already true statically — the boundary test
in `test_p5_money_invariants.py` scans for unauthorized writers of
`EcoWallet` / `FinJournalEntry` / `FinJournalBatch` / `LedgerEntry` / `EcoBalanceAccount` /
`EcoBalanceEntry` — so the ratification makes the rule explicit rather than creating new work.

## 4. Compensation, not deletion (all decisions)

A wrong or unknown money movement is corrected by a **new** balanced batch that reverses it;
rows are never edited or deleted. Escrow release requires a verified payment; a refund posts a
reversing batch against the same evidence chain.

## 5. Change control

Changing this document requires: a new version (v2), the named approvers of D-09/D-10/D-11,
and the tests above updated in the same change. A change that alters the source of truth, the
attribution key, or the write owners is **never** "compatible" (API contract v1 §6).
