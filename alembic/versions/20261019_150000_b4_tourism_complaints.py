"""B4: tourism complaints table (capacity/refund/complaint E2E follow-up)."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401
import services.tourism.incidents  # noqa: F401  (registers tourism_complaints)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261019_150000_b4_tourism_complaints"
down_revision: str | None = "20261018_153000_b2_marketplace_persistent_cart"
branch_labels: str | None = None
depends_on: str | None = None

_TABLES: tuple[str, ...] = ("tourism_complaints",)


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _create_table(name: str) -> None:
    table = Base.metadata.tables[name]
    columns = [column.copy() for column in table.columns]
    constraints = [
        c
        for c in table.constraints
        if isinstance(
            c,
            (
                sa.PrimaryKeyConstraint,
                sa.ForeignKeyConstraint,
                sa.UniqueConstraint,
                sa.CheckConstraint,
            ),
        )
    ]
    op.create_table(name, *columns, *constraints)


def upgrade() -> None:
    if context.is_offline_mode():
        for name in _TABLES:
            _create_table(name)
        return
    for name in _TABLES:
        if not _inspector().has_table(name):
            _create_table(name)


def downgrade() -> None:
    if context.is_offline_mode():
        return
    for name in reversed(_TABLES):
        if _inspector().has_table(name):
            op.drop_table(name)