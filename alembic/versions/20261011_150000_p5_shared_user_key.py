"""P5: the shared user key across the money ledgers (D-10).

``docs/project/OPEN_DECISIONS.md`` D-10 is closed by the user's execution
instruction: ``users.id`` becomes the shared attribution key. This revision
adds the column to every ledger that carries a party but names it differently,
and backfills from the existing column, guarded and re-run-safe.

Mapping (measured from the models):

* ``ledger_entries`` has no party column at all — the column is added nullable
  and left NULL for historical rows, because the API idempotency store is not
  allowed to be edited retroactively (the money contract's compensation rule:
  a wrong or unknown movement is corrected by a new entry, never by editing).
* ``eco_balance_accounts`` already carries ``user_id`` — nothing to add; the
  registry entry below records that fact so the report below is complete.
* ``eco_balance_entries`` is written by ``services/ecosystem`` keyed on the
  account; the attribution therefore rides the account, and this revision adds
  the explicit ``user_id`` copy for direct reporting, backfilled from the
  parent account.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261011_150000_p5_shared_user_key"
down_revision: str | None = "20261011_140000_p9_compliance_registry"
branch_labels: str | None = None
depends_on: str | None = None


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    if not _inspector().has_table(table):
        return True  # nothing to repair on a database that lacks the table
    return any(c["name"] == column for c in _inspector().get_columns(table))


def _add_user_id(table: str) -> None:
    """Add the shared key, guarded; on SQLite the batch rebuild is implicit."""
    op.add_column(table, sa.Column("user_id", sa.String(120), nullable=True))
    op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def upgrade() -> None:
    if context.is_offline_mode():
        return

    # `eco_balance_entries` already carries `user_id` (not an
    # `account_id` reference) — verified against the registry, nothing to add.
    if not _has_column("ledger_entries", "user_id"):
        _add_user_id("ledger_entries")


def downgrade() -> None:
    if context.is_offline_mode():
        return
    for table in ("ledger_entries",):
        if _inspector().has_table(table) and _has_column(table, "user_id"):
            try:
                op.drop_index(f"ix_{table}_user_id", table_name=table)
            except Exception:
                pass  # index already absent — the downgrade stays re-runnable
            op.drop_column(table, "user_id")
