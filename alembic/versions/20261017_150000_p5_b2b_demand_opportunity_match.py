"""P5: B2B Demand → Opportunity matching.

Adds cross-reference columns between ``b2b_demands`` and
``village_opportunities`` so a buyer's purchase demand can be converted
into a village development opportunity, and vice-versa. Guarded and
idempotent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_150000_p5_b2b_demand_opportunity_match"
down_revision: str | None = "20261017_140000_p4_nomadic_ecotourism_link"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE_DEMAND = "b2b_demands"
_TABLE_OPPORTUNITY = "village_opportunities"


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

    # b2b_demands.matched_opportunity_id
    if not _column_exists(_TABLE_DEMAND, "matched_opportunity_id"):
        op.add_column(
            _TABLE_DEMAND,
            sa.Column(
                "matched_opportunity_id",
                sa.String(36),
                sa.ForeignKey("village_opportunities.id"),
                nullable=True,
                index=True,
            ),
        )

    # village_opportunities.matched_demand_id
    if not _column_exists(_TABLE_OPPORTUNITY, "matched_demand_id"):
        op.add_column(
            _TABLE_OPPORTUNITY,
            sa.Column(
                "matched_demand_id",
                sa.String(36),
                sa.ForeignKey("b2b_demands.id"),
                nullable=True,
                index=True,
            ),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    for table, column in [
        (_TABLE_DEMAND, "matched_opportunity_id"),
        (_TABLE_OPPORTUNITY, "matched_demand_id"),
    ]:
        if inspector.has_table(table) and any(
            c["name"] == column for c in inspector.get_columns(table)
        ):
            try:
                op.drop_column(table, column)
            except Exception:
                pass
