"""Canonical chart of accounts for the ECO platform.

``services/commerce/service.py::settle_order`` and
``services/finance/wallet_service.py`` both write their journal batches with
``FinJournalEntry.account_id`` holding the account **code** (see
``services/finance/account_ref.py``), but nothing ever created the
``FinAccount`` rows those codes name. Every settlement and wallet batch
therefore referenced accounts that did not exist, and
``LedgerService.profit_and_loss`` had to report the whole settlement under
``unclassified`` with ``reason="account_not_found"`` instead of classifying
``ECO_PLATFORM_REVENUE`` as income.

This module is the single, idempotent seeder for that chart:

* :data:`ECO_CHART_OF_ACCOUNTS` — the declarative table of the platform's
  accounts, including the codes the wallet and commerce flows journal against.
* :func:`ensure_account` — get-or-create by ``code``, safe under concurrent
  calls (an ``IntegrityError`` on a racing INSERT is re-read, not raised).
* :func:`seed_chart_of_accounts` — ensure every chart row exists.

The per-user wallet accounts (``ECO_USER_<user_id>``) are **not** seeded: they
are created lazily by :func:`wallet_account_spec` the first time a user's
wallet has a ledger entry, exactly as the wallet path did before. This module
only fixes *which* row that is and *where* it hangs in the hierarchy.

Inventory valuation (``ECO_INVENTORY`` / ``ECO_COGS``) is seeded here because
``services/inventory/service.py`` now prices its stock ledger and journals
against those codes: a goods receipt debits ``ECO_INVENTORY`` against
``ECO_ACCOUNTS_PAYABLE`` (or ``ECO_CASH`` for a cash purchase), an issue debits
``ECO_COGS`` against ``ECO_INVENTORY``, and adjustments, stocktake variances and
scraps are booked against ``ECO_INVENTORY_VARIANCE``. ``ECO_INVENTORY`` is
currency-neutral: it carries the *value* of goods on hand in the reporting
currency, while the quantities themselves stay in the ``inv_*`` tables.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FinAccount

logger = logging.getLogger(__name__)


class UnknownAccountCode(LookupError):
    """An account code was referenced that is neither a row nor in the chart."""


# ---------------------------------------------------------------------------
# Canonical account codes
# ---------------------------------------------------------------------------

#: ECO token inventory — the debit leg of every earning batch.
ECO_ASSET = "ECO_ASSET"
#: Cash released by a marketplace settlement — the debit leg of ``settle_order``.
ECO_CASH = "ECO_CASH"
#: Value of goods on hand — the debit leg of a goods receipt.
ECO_INVENTORY = "ECO_INVENTORY"
#: What the platform owes its sellers — the credit leg of ``settle_order``.
ECO_SELLER_PAYABLE = "ECO_SELLER_PAYABLE"
#: What the platform owes its suppliers — the credit leg of a goods receipt.
ECO_ACCOUNTS_PAYABLE = "ECO_ACCOUNTS_PAYABLE"
#: Platform commission plus landscape fee — the credit leg of ``settle_order``.
ECO_PLATFORM_REVENUE = "ECO_PLATFORM_REVENUE"
#: ECO the platform owes its users — the credit leg of an earning batch.
REWARD_LIABILITY = "REWARD_LIABILITY"
#: Platform equity in the reporting currency (IRR). No writer yet.
ECO_EQUITY = "ECO_EQUITY"
#: Platform operating expense (IRR). No writer yet.
ECO_OPERATING_EXPENSE = "ECO_OPERATING_EXPENSE"
#: Cost of goods issued or consumed — the debit leg of an ``issue`` movement.
ECO_COGS = "ECO_COGS"
#: Shrinkage and write-offs booked against inventory — adjustments, stocktake
#: variances and scraps.
ECO_INVENTORY_VARIANCE = "ECO_INVENTORY_VARIANCE"

#: Prefix of the per-user wallet accounts created lazily by the wallet flows.
WALLET_ACCOUNT_PREFIX = "ECO_USER_"

#: The codes a commerce settlement journals against; they must all exist as
#: rows before ``LedgerService.create_journal_batch`` runs.
SETTLEMENT_ACCOUNT_CODES = frozenset({ECO_CASH, ECO_PLATFORM_REVENUE, ECO_SELLER_PAYABLE})

#: The two chart accounts every wallet batch journals against.
WALLET_ACCOUNT_CODES = frozenset({ECO_ASSET, REWARD_LIABILITY})

#: The chart accounts the inventory valuation legs journal against; they must
#: all exist as rows before a stock movement posts its batch.
INVENTORY_ACCOUNT_CODES = frozenset(
    {ECO_INVENTORY, ECO_ACCOUNTS_PAYABLE, ECO_COGS, ECO_INVENTORY_VARIANCE}
)

#: Account types ``LedgerService.profit_and_loss`` classifies (``income`` and
#: ``expense`` are reported; the balance-sheet types are excluded from P&L).
ACCOUNT_TYPES = frozenset({"asset", "liability", "equity", "income", "expense"})

#: Assets ``LedgerService.create_journal_batch`` accepts on an entry.
ACCOUNT_ASSETS = frozenset({"IRR", "ECO", "CARBON_tCO2e", "USD"})


# ---------------------------------------------------------------------------
# Declarative chart
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AccountSpec:
    """One row of :data:`ECO_CHART_OF_ACCOUNTS`.

    ``parent_code`` is a code, not an id, so the table stays readable and
    portable: :func:`ensure_account` resolves it to ``FinAccount.parent_id``.
    ``description`` records intent for reviewers; it is not persisted because
    ``FinAccount`` carries no description column and adding one belongs to the
    schema/migration wave.
    """

    code: str
    name: str
    type: str
    asset: str
    currency: str
    parent_code: str | None = None
    description: str | None = None


#: Ordered so parents precede children. ``asset``/``currency`` describe the
#: account's own unit; journal entries carry the asset they were booked in.
ECO_CHART_OF_ACCOUNTS: tuple[AccountSpec, ...] = (
    AccountSpec(
        code=ECO_ASSET,
        name="ECO Token Asset",
        type="asset",
        asset="ECO",
        currency="ECO",
        description="ECO held by the platform: debit leg of an earning batch.",
    ),
    AccountSpec(
        code=ECO_CASH,
        name="Cash — Marketplace Settlements",
        type="asset",
        asset="IRR",
        currency="IRR",
        description="Order cash released at settlement: debit leg of settle_order.",
    ),
    AccountSpec(
        code=ECO_INVENTORY,
        name="Inventory — Goods on Hand",
        type="asset",
        asset="IRR",
        currency="IRR",
        description=(
            "Value of goods on hand: debit leg of a goods receipt, credit leg of "
            "an issue. Currency-neutral — the account carries goods *value* in "
            "the reporting currency while the quantities stay in the inv_* tables."
        ),
    ),
    AccountSpec(
        code=REWARD_LIABILITY,
        name="ECO Reward Liability",
        type="liability",
        asset="ECO",
        currency="ECO",
        parent_code=ECO_ASSET,
        description="ECO owed to users: credit leg of an earning batch, debit on redemption.",
    ),
    AccountSpec(
        code=ECO_SELLER_PAYABLE,
        name="Seller Payable",
        type="liability",
        asset="IRR",
        currency="IRR",
        parent_code=ECO_CASH,
        description="Seller proceeds held after settlement: credit leg of settle_order.",
    ),
    AccountSpec(
        code=ECO_ACCOUNTS_PAYABLE,
        name="Accounts Payable — Suppliers",
        type="liability",
        asset="IRR",
        currency="IRR",
        parent_code=ECO_CASH,
        description=(
            "Supplier invoices for goods received on account: credit leg of a "
            "goods receipt (ECO_CASH instead when the purchase is paid cash)."
        ),
    ),
    AccountSpec(
        code=ECO_PLATFORM_REVENUE,
        name="Platform Revenue",
        type="income",
        asset="IRR",
        currency="IRR",
        description="Platform commission plus landscape fee: credit leg of settle_order.",
    ),
    AccountSpec(
        code=ECO_EQUITY,
        name="Platform Equity",
        type="equity",
        asset="IRR",
        currency="IRR",
        description="Platform equity in the reporting currency. No writer yet.",
    ),
    AccountSpec(
        code=ECO_OPERATING_EXPENSE,
        name="Platform Operating Expense",
        type="expense",
        asset="IRR",
        currency="IRR",
        description="Platform operating costs. No writer yet.",
    ),
    AccountSpec(
        code=ECO_COGS,
        name="Cost of Goods Sold",
        type="expense",
        asset="IRR",
        currency="IRR",
        parent_code=ECO_OPERATING_EXPENSE,
        description=(
            "Cost of goods issued or consumed: debit leg of an issue movement, "
            "credit leg of a customer return."
        ),
    ),
    AccountSpec(
        code=ECO_INVENTORY_VARIANCE,
        name="Inventory Variance",
        type="expense",
        asset="IRR",
        currency="IRR",
        parent_code=ECO_OPERATING_EXPENSE,
        description=(
            "Shrinkage and write-offs booked against inventory: adjustments, "
            "stocktake variances and scraps."
        ),
    ),
)

_CHART_BY_CODE: dict[str, AccountSpec] = {spec.code: spec for spec in ECO_CHART_OF_ACCOUNTS}


def get_account_spec(code: str) -> AccountSpec | None:
    """The chart spec for ``code``, or ``None`` when it is not a chart code."""
    return _CHART_BY_CODE.get(code)


def wallet_account_code(user_id: str) -> str:
    """The account code carrying ``user_id``'s ECO holdings."""
    return f"{WALLET_ACCOUNT_PREFIX}{user_id}"


def is_wallet_account_code(code: str) -> bool:
    """Whether ``code`` is a lazily created per-user wallet account code."""
    return code.startswith(WALLET_ACCOUNT_PREFIX)


def wallet_account_spec(code: str) -> AccountSpec:
    """The chart spec of a wallet account, given its code or its bare user id.

    Accepting either spelling keeps the wallet call sites (which build the code
    as ``f"ECO_USER_{user_id}"``) from having to strip the prefix back off.
    """
    account_code = code if is_wallet_account_code(code) else wallet_account_code(code)
    user_id = account_code[len(WALLET_ACCOUNT_PREFIX) :]
    return AccountSpec(
        code=account_code,
        name=f"ECO Wallet — {user_id}",
        type="asset",
        asset="ECO",
        currency="ECO",
        parent_code=ECO_ASSET,
        description="Per-user ECO holding, created on the user's first ledger entry.",
    )


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


async def _find_account(db: AsyncSession, code: str) -> FinAccount | None:
    result = await db.execute(select(FinAccount).where(FinAccount.code == code))
    return result.scalar_one_or_none()


async def ensure_account(
    db: AsyncSession,
    *,
    code: str,
    name: str,
    type: str,
    asset: str,
    currency: str,
    parent_code: str | None = None,
    description: str | None = None,
) -> FinAccount:
    """Get-or-create the chart row for ``code`` and return it.

    Idempotent: an existing row is returned unchanged, so a re-seed never
    rewrites a name an operator has since edited, and a lost INSERT race is
    resolved by re-reading the winner instead of raising — which is what makes
    the function safe to call from a request path that may run concurrently.

    ``parent_code`` is resolved to ``FinAccount.parent_id``: a canonical parent
    is seeded on demand, an unknown one raises :class:`UnknownAccountCode`.
    """
    spec = AccountSpec(
        code=code,
        name=name,
        type=type,
        asset=asset,
        currency=currency,
        parent_code=parent_code,
        description=description,
    )
    return await _ensure_spec(db, spec, frozenset())


async def _ensure_spec(
    db: AsyncSession, spec: AccountSpec, ancestors: frozenset[str]
) -> FinAccount:
    existing = await _find_account(db, spec.code)
    if existing is not None:
        return existing

    if spec.code in ancestors or spec.parent_code == spec.code:
        raise UnknownAccountCode(f"Circular account parent chain at {spec.code!r}")

    parent_id: int | None = None
    if spec.parent_code is not None:
        parent_id = await _ensure_parent_id(db, spec.parent_code, ancestors | {spec.code})

    account = FinAccount(
        code=spec.code,
        name=spec.name,
        type=spec.type,
        asset=spec.asset,
        currency=spec.currency,
        # ``parent_id`` is a String column holding the parent's decimalised
        # Integer key — the column is text because a foreign key between it and
        # the Integer ``fin_accounts.id`` primary key is rejected by PostgreSQL
        # DDL, so the hierarchy stays a business key. ``str()`` keeps the
        # Decimal-or-int shape of ``_ensure_parent_id`` out of the column.
        parent_id=str(parent_id) if parent_id is not None else None,
        is_active=True,
    )
    # The INSERT runs inside a SAVEPOINT so that losing a race to a concurrent
    # seeder rolls back only this row and leaves the caller's surrounding
    # transaction (an order status change, a wallet balance) intact.
    try:
        async with db.begin_nested():
            db.add(account)
            await db.flush()
    except IntegrityError:
        if account in db:
            db.expunge(account)
        winner = await _find_account(db, spec.code)
        if winner is not None:
            return winner
        raise
    return account


async def _ensure_parent_id(
    db: AsyncSession, parent_code: str, ancestors: frozenset[str]
) -> int | None:
    parent = await _find_account(db, parent_code)
    if parent is not None:
        return parent.id

    parent_spec = get_account_spec(parent_code)
    if parent_spec is None:
        raise UnknownAccountCode(f"Unknown parent account code: {parent_code!r}")

    parent = await _ensure_spec(db, parent_spec, ancestors)
    return parent.id


async def ensure_codes(db: AsyncSession, codes: Iterable[str]) -> list[FinAccount]:
    """Ensure every named chart code exists; return the rows in sorted order.

    Used by the flows that journal against a fixed set of codes so they never
    have to repeat the lookup themselves.
    """
    ensured: list[FinAccount] = []
    for code in sorted(codes):
        spec = get_account_spec(code)
        if spec is None:
            raise UnknownAccountCode(f"Unknown chart account code: {code!r}")
        ensured.append(await _ensure_spec(db, spec, frozenset()))
    return ensured


async def ensure_settlement_accounts(db: AsyncSession) -> list[FinAccount]:
    """Ensure the three accounts a commerce settlement journals against."""
    return await ensure_codes(db, SETTLEMENT_ACCOUNT_CODES)


async def ensure_wallet_accounts(db: AsyncSession) -> list[FinAccount]:
    """Ensure the accounts a wallet batch journals against (not the per-user ones)."""
    return await ensure_codes(db, WALLET_ACCOUNT_CODES)


async def ensure_inventory_accounts(db: AsyncSession) -> list[FinAccount]:
    """Ensure the accounts the inventory valuation legs journal against."""
    return await ensure_codes(db, INVENTORY_ACCOUNT_CODES)


async def seed_chart_of_accounts(db: AsyncSession) -> list[FinAccount]:
    """Ensure every :data:`ECO_CHART_OF_ACCOUNTS` row exists. Idempotent.

    Callers own the transaction: the rows are flushed, not committed, so the
    seeder can run inside a settlement or at application start-up.
    """
    return [await _ensure_spec(db, spec, frozenset()) for spec in ECO_CHART_OF_ACCOUNTS]
