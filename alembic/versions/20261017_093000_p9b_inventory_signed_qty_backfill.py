"""P9b: backfill signed_qty on historical adjustment movements.

``adjust`` movements stored ``abs(qty)`` in ``qty`` with the signed delta only
in ``notes`` (``Adjustment: {signed_qty} - {reason}``). This migration parses
that note and backfills ``signed_qty`` so the reconciliation CTE can fold
adjustments into the signed movement sum deterministically.

Guard: rows already carrying ``signed_qty`` are skipped; rows whose notes do
not match the expected pattern are left NULL (reconciliation treats NULL as
"not an adjustment" and excludes them, matching pre-migration behaviour).
"""

from __future__ import annotations

import re
from typing import Any

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_093000_p9b_inventory_signed_qty_backfill"
down_revision: str | None = "20261017_090000_p5_project_nesting"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "inv_stock_movements"
_COLUMN = "signed_qty"

# Matches "Adjustment: -3.5 - reason" or "Adjustment: 10 - reason"
_SIGNED_QTY_RE = re.compile(r"Adjustment:\s*(-?\d+(?:\.\d+)?)")


def _column_exists() -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(_TABLE):
        return False
    return any(c["name"] == _COLUMN for c in inspector.get_columns(_TABLE))


def upgrade() -> None:
    if context.is_offline_mode():
        return
    if not _column_exists():
        return

    bind = op.get_bind()
    stmt = sa.text(
        f"SELECT id, qty, notes FROM {_TABLE} "
        f"WHERE movement_type = 'adjustment' AND {_COLUMN} IS NULL"
    )
    result = bind.execute(stmt)
    to_update: list[dict[str, Any]] = []
    for row in result:
        notes = row.notes or ""
        m = _SIGNED_QTY_RE.search(notes)
        if not m:
            continue
        to_update.append({"id": row.id, "signed_qty": m.group(1)})

    if to_update:
        bind.execute(
            sa.text(
                f"UPDATE {_TABLE} SET {_COLUMN} = :signed_qty WHERE id = :id"
            ),
            to_update,
        )


def downgrade() -> None:
    # Backfill is not reversible: signed_qty was derived from notes, which are
    # preserved. No-op on purpose.
    pass
