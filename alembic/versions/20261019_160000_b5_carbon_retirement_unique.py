"""B5: double-retirement backstop on carbon credits.

``services/wallet/credits.py`` promised that "a second retirement of the same
unit is rejected by a unique constraint rather than by a code path", but the
``carbon_retirements`` table carried no such constraint. The same tonne could
therefore be retired twice and counted twice.

This revision adds the unique constraint on ``carbon_retirements.credit_id``.
It is guarded: it is skipped when the constraint is already present, and it is
skipped when the table holds duplicate credit_ids (a pre-existing double
retirement must be reported, not silently deleted).
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers the tables)
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261019_160000_b5_carbon_retirement_unique"
down_revision: str | None = "20261019_150000_b4_tourism_complaints"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "carbon_retirements"
_CONSTRAINT = "uq_carbon_retirement_credit"


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _has_constraint() -> bool:
    inspector = _inspector()
    if not inspector.has_table(_TABLE):
        return False
    for uc in inspector.get_unique_constraints(_TABLE):
        if uc.get("name") == _CONSTRAINT:
            return True
    # SQLite reports the constraint in the table DDL rather than in
    # get_unique_constraints() on some versions.
    for index in inspector.get_indexes(_TABLE):
        if index.get("unique") and index.get("column_names") == ["credit_id"]:
            return True
    return False


def _duplicate_credit_ids() -> list[int]:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            f"SELECT credit_id, COUNT(*) AS n FROM {_TABLE} "
            "GROUP BY credit_id HAVING COUNT(*) > 1"
        )
    ).all()
    return [int(r[0]) for r in rows]


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
        with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
            batch_op.create_unique_constraint(_CONSTRAINT, ["credit_id"])
        return

    inspector = _inspector()
    if not inspector.has_table(_TABLE):
        return
    if _has_constraint():
        return

    duplicates = _duplicate_credit_ids()
    if duplicates:
        # A duplicate is a real double retirement that already happened. The
        # constraint cannot be applied without deciding what to do with it, so
        # the migration refuses rather than deleting financial records.
        raise RuntimeError(
            f"cannot add {_CONSTRAINT}: {_TABLE} already holds duplicate "
            f"credit_ids {duplicates}. Resolve the double retirements first."
        )

    # SQLite has no ``ALTER TABLE ... ADD CONSTRAINT``; the batch mode
    # recreates the table with a copy-and-move strategy.
    with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
        batch_op.create_unique_constraint(_CONSTRAINT, ["credit_id"])


def downgrade() -> None:
    if context.is_offline_mode():
        with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
            batch_op.drop_constraint(_CONSTRAINT, type_="unique")
        return
    if not _has_constraint():
        return
    with op.batch_alter_table(_TABLE, copy_from=_batch_table()) as batch_op:
        batch_op.drop_constraint(_CONSTRAINT, type_="unique")
