"""P2b: governance_space_id column on rangelands.

Links a rangeland to its governing CommunitySpace (pastoral_rangeland subtype).
Guarded and idempotent: column added only when absent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_120000_p2b_rangeland_governance_link"
down_revision: str | None = "20261017_110000_p10_tourism_festivals_unesco"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "rangelands"
_COLUMN = "governance_space_id"


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
