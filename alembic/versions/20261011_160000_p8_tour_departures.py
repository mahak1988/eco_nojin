"""P8: the tour-departure table (the additive entity-model step).

One dated instance of a tour, with its own capacity — the smaller of the
departure's capacity and the tour's ecological capacity, enforced by the
service, not by the database. P7's guarded pattern: registry definitions,
create-when-missing, offline render, drop-on-downgrade.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401
import services.tourism.departures  # noqa: F401  (registers tourism_departures on the shared Base)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261011_160000_p8_tour_departures"
down_revision: str | None = "20261011_150000_p5_shared_user_key"
branch_labels: str | None = None
depends_on: str | None = None

_TABLES: tuple[str, ...] = ("tourism_departures",)


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _create_table(name: str) -> None:
    """Create the table from the registry definition.

    Matches the P7/P9 revisions exactly: columns plus every table-level
    constraint — primary key, foreign key, and the composite unique
    (``uq_departure_tour_date``) — with the column-level indexes riding along.
    Constraints pass through ``create_table`` itself (no ``ALTER TABLE`` is
    involved), so a migrated database no longer diverges from ``create_all``:
    the service guard stays, but the database enforces it too.
    """
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
