"""P5: nested project workflow on village_projects.

Adds ``parent_project_id`` (self-referential FK) and ``sub_tasks`` (JSON)
so village development projects can be organized into a tree with cascading
progress. Guarded and re-run-safe.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_090000_p5_project_nesting"
down_revision: str | None = "20261017_083000_p6_village_consent"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "village_projects"


def _column_exists(column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(_TABLE):
        return False
    return any(c["name"] == column for c in inspector.get_columns(_TABLE))


def upgrade() -> None:
    if context.is_offline_mode():
        return
    if not _column_exists("parent_project_id"):
        op.add_column(
            _TABLE,
            sa.Column(
                "parent_project_id",
                sa.String(36),
                sa.ForeignKey("village_projects.id"),
                nullable=True,
                index=True,
            ),
        )
    if not _column_exists("sub_tasks"):
        op.add_column(
            _TABLE, sa.Column("sub_tasks", sa.JSON(), nullable=True, default=list)
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE):
        for column in ("sub_tasks", "parent_project_id"):
            if any(c["name"] == column for c in inspector.get_columns(_TABLE)):
                try:
                    op.drop_column(_TABLE, column)
                except Exception:
                    pass
