"""B5: add the missing ``content_items.rag_synced`` column.

``services/content/rag_sync.py`` and ``services/content/bot_dispatch.py`` both
read and write ``ContentItem.rag_synced``, but the column was never added to
the model. Every ``sync_content_to_rag`` call raised
``AttributeError: type object 'ContentItem' has no attribute 'rag_synced'``,
and the publish path set a phantom attribute SQLAlchemy silently ignored.

The public keyword search (``GET /api/v1/content/search``) filters on
``status``, not on this column, which is why the *search* worked while the
*sync* did not.

Guarded and idempotent: the column is added only when it is missing.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers the table)
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261019_180000_b5_content_item_rag_synced"
down_revision: str | None = "20261019_160000_b5_carbon_retirement_unique"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "content_items"
_COLUMN = "rag_synced"


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _has_column() -> bool:
    inspector = _inspector()
    if not inspector.has_table(_TABLE):
        return False
    return any(c["name"] == _COLUMN for c in inspector.get_columns(_TABLE))


def _batch_table() -> Any:
    """The full Table object, so batch mode can skip reflection.

    Batch mode in offline (``--sql``) mode cannot reflect the table -- there
    is no live connection -- so it needs the complete ``Table`` handed to it.
    """
    import database.models  # noqa: F401  (registers the table)

    from database.base import Base

    return Base.metadata.tables[_TABLE]


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column(
            _TABLE,
            sa.Column(_COLUMN, sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        return

    if not _inspector().has_table(_TABLE):
        return
    if _has_column():
        return

    op.add_column(
        _TABLE,
        sa.Column(_COLUMN, sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    if context.is_offline_mode():
        with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
            batch_op.drop_column(_COLUMN)
        return
    if not _has_column():
        return
    with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
        batch_op.drop_column(_COLUMN)
