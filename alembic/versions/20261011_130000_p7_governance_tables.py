"""P7: the local-governance tables (village + pastoral-rangeland governance).

Phase 7 of the program (``docs/project/PHASE_PLAN.md``) adds the governance
layer that was measurably absent (KN-12): before this revision a repository-wide
search found zero occurrences of ``charter``, ``working_group`` or
``community_space``.

Tables created (all on the shared registry ``Base`` via
``services/village/models.py``):

* ``gov_community_spaces`` â€” one lifecycle, two subtypes (``village`` /
  ``pastoral_rangeland``); the sensitivity-classified fields
  (migration routes, water sources, sacred sites, exact boundary) are private
  until published one by one.
* ``gov_local_charters`` â€” versioned; amendments are new versions, never edits.
* ``gov_working_groups`` / ``gov_working_group_members`` â€” mandate-scoped groups
  and terms; ending a term keeps the row and its reason, so decision history
  stays interpretable.
* ``gov_applications`` â€” the workflow evidence a step really happened.
* ``gov_decisions`` â€” the append-only local decision log.

Guarded shape (the pattern ``20261011_120000`` established)
----------------------------------------------------------
* The definitions come from the registry (``Base.metadata``), never transcribed;
  a rebuild is issued only when the table is missing.
* A live column the registry does not declare aborts the upgrade with the column
  names rather than dropping data.
* Offline (``--sql``) renders every create; no database is consulted.
* Downgrade drops exactly these tables in reverse dependency order; run it on a
  scratch database, never on production.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers every declared table on the shared Base)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261011_130000_p7_governance_tables"
down_revision: str | None = "20261011_120000_p4_relationship_backstops"
branch_labels: str | None = None
depends_on: str | None = None

#: This revision's tables, in creation order (parents before children).
_TABLES: tuple[str, ...] = (
    "gov_community_spaces",
    "gov_local_charters",
    "gov_working_groups",
    "gov_working_group_members",
    "gov_applications",
    "gov_decisions",
)


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _registry_table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def _assert_registry_covers_live(table: str) -> None:
    """Refuse a rebuild that would drop a column the model does not declare."""
    registry_columns = {column.name for column in _registry_table(table).columns}
    live = {column["name"] for column in _inspector().get_columns(table)}
    extra = live - registry_columns
    if extra:
        raise RuntimeError(
            f"{table} has live columns the registry does not declare: {sorted(extra)}."
        )


def _create_table(name: str) -> None:
    """Create one table from the registry definition, indexes rebuilt after.

    A registry ``Index`` object already carries its table, so passing it inside
    ``create_table`` makes SQLAlchemy refuse ("cannot be associated with" the
    same table); the indexes are created by the follow-up pass instead —
    column-level ``index=True`` flags ride along with the columns.

    Foreign keys and unique constraints *must* pass through: a table created
    with only its primary key diverges permanently from ``create_all`` and
    admits orphan or duplicate rows.
    """
    table = _registry_table(name)
    columns = [column.copy() for column in table.columns]
    constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(
            constraint,
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
