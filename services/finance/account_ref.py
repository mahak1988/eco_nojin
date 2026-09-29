"""Resolving a ``FinJournalEntry.account_id`` against the chart of accounts.

``FinJournalEntry.account_id`` is a ``String`` column, but writers have used
two conventions for its contents:

* ``services/finance/wallet_service.py`` wrote ``FinAccount.id`` (an integer,
  stored by SQLAlchemy as its decimal string);
* ``services/commerce/service.py`` wrote the account **code** — for example
  ``"ECO_PLATFORM_REVENUE"``.

That made a single JOIN impossible. ``services/finance/reconciliation.py``
joined ``account_id == FinAccount.id``, comparing a string column to an integer
primary key, so the join could never match and every wallet was reported with
a ledger balance of zero — i.e. a discrepancy equal to its entire balance.

**Canonical convention going forward: the account code.** Codes are stable
across databases, readable in the journal, and already what the commerce
settlement path uses. ``account_join_condition`` matches the code first and the
stringified id second, so rows written under either convention keep reconciling
instead of silently dropping out of every report.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, cast, or_


def account_join_condition() -> Any:
    """JOIN condition matching the chart of accounts to a journal entry.

    Use as ``.join(FinAccount, account_join_condition())``. Matches on code
    first and on the stringified id second, so both historical conventions
    resolve. Without this, the naive ``account_id == FinAccount.id`` compares a
    string column to an integer primary key and never matches.
    """
    from database.models import FinAccount, FinJournalEntry

    return or_(
        FinJournalEntry.account_id == FinAccount.code,
        FinJournalEntry.account_id == cast(FinAccount.id, String),
    )


def matches_account(ref: Any) -> Any:
    """Column condition matching a journal entry to one specific account.

    Pair with ``account_join_condition()`` when the reference may be either a
    code or a numeric id: the exact-string arm catches the code convention, and
    the join already constrained rows to the right account for the id one.
    """
    from database.models import FinJournalEntry

    return FinJournalEntry.account_id == str(ref)
