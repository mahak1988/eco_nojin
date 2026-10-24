"""P5: user_id column on inv_stock_movements for cross-ledger user attribution.

Per-user attribution across money/inventory ledgers was impossible because
``inv_stock_movements`` carried no user key. Adds ``user_id`` (nullable, indexed)
so every stock movement can be traced to the actor who caused it.

Guarded and re-run-safe.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_073000_p5_inventory_user_id"
down_revision: str | None = "20261017_070000_p9_inventory_signed_qty"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "inv_stock_movements"
_COLUMN = "user_id"


def upgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE) and not any(
        c["name"] == _COLUMN for c in inspector.get_columns(_TABLE)
    ):
        op.add_column(
            _TABLE,
            sa.Column(_COLUMN, sa.String(36), nullable=True, index=True),
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
