"""P6: sensitive_field_consent column on gov_community_spaces.

Adds a JSON consent log so the platform can demonstrate who authorized
publication of each sensitivity-classified field and how. Guarded and
re-run-safe.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_083000_p6_village_consent"
down_revision: str | None = "20261017_080000_p8_village_multilanguage"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "gov_community_spaces"
_COLUMN = "sensitive_field_consent"


def upgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE) and not any(
        c["name"] == _COLUMN for c in inspector.get_columns(_TABLE)
    ):
        op.add_column(
            _TABLE,
            sa.Column(_COLUMN, sa.JSON(), nullable=True, default=dict),
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
