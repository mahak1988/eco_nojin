"""P9: signed_qty column on inv_stock_movements.

``adjust`` movements stored ``abs(qty)`` with the signed delta only in a
free-text note, so the reconciliation CTE could not fold them into the
signed movement sum deterministically. This column carries the signed
delta for adjustment movements (and is ``NULL`` for every other type),
allowing ``reconcile_inventory`` to include them without ambiguity.

Guarded and re-run-safe: the column is added only when absent, so the
revision coexists with ``create_all`` and can be re-run on migrated
databases.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_070000_p9_inventory_signed_qty"
down_revision: str | None = "20261013_120000_p8_departure_cancel_reason"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "inv_stock_movements"
_COLUMN = "signed_qty"


def upgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE) and not any(
        c["name"] == _COLUMN for c in inspector.get_columns(_TABLE)
    ):
        op.add_column(
            _TABLE,
            sa.Column(_COLUMN, sa.Numeric(18, 8), nullable=True),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE) and any(
        c["name"] == _COLUMN for c in inspector.get_columns(_TABLE)
    ):
        try:
            op.drop_column(_TABLE, _COLUMN)
        except Exception:
            pass
