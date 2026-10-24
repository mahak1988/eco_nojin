"""P3: territory linkage on village_projects and village_investments.

Adds ``territory_id`` to ``village_projects`` (FK to territories) and
``territory_id``/``territory_fund_id`` to ``village_investments`` so a
territory fund can sponsor village projects. Guarded and idempotent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_130000_p3_territory_investment_link"
down_revision: str | None = "20261017_120000_p2b_rangeland_governance_link"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE_PROJECT = "village_projects"
_TABLE_INVESTMENT = "village_investments"


def _column_exists(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    if context.is_offline_mode():
        return

    # village_projects.territory_id
    if not _column_exists(_TABLE_PROJECT, "territory_id"):
        op.add_column(
            _TABLE_PROJECT,
            sa.Column(
                "territory_id",
                sa.String(36),
                sa.ForeignKey("territories.id"),
                nullable=True,
                index=True,
            ),
        )

    # village_investments.territory_id
    if not _column_exists(_TABLE_INVESTMENT, "territory_id"):
        op.add_column(
            _TABLE_INVESTMENT,
            sa.Column("territory_id", sa.String(36), nullable=True, index=True),
        )

    # village_investments.territory_fund_id
    if not _column_exists(_TABLE_INVESTMENT, "territory_fund_id"):
        op.add_column(
            _TABLE_INVESTMENT,
            sa.Column("territory_fund_id", sa.String(36), nullable=True, index=True),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    for table, columns in [
        (_TABLE_INVESTMENT, ["territory_fund_id", "territory_id"]),
        (_TABLE_PROJECT, ["territory_id"]),
    ]:
        if inspector.has_table(table):
            existing = {c["name"] for c in inspector.get_columns(table)}
            for column in columns:
                if column in existing:
                    try:
                        op.drop_column(table, column)
                    except Exception:
                        pass
