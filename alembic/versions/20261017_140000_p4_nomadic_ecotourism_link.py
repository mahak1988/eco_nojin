"""P4: nomadic community → ecotourism link.

Adds ``nomadic_community_id`` to ``village_tourism_services`` and
``tourism_tours`` so nomadic communities can register tourism services and
lead ecotourism tours. Guarded and idempotent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_140000_p4_nomadic_ecotourism_link"
down_revision: str | None = "20261017_130000_p3_territory_investment_link"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE_SVC = "village_tourism_services"
_TABLE_TOUR = "tourism_tours"


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

    # village_tourism_services.nomadic_community_id
    if not _column_exists(_TABLE_SVC, "nomadic_community_id"):
        op.add_column(
            _TABLE_SVC,
            sa.Column("nomadic_community_id", sa.String(36), nullable=True, index=True),
        )
        op.create_index(
            "idx_tour_svc_nomadic", _TABLE_SVC, ["nomadic_community_id"]
        )

    # tourism_tours.nomadic_community_id
    if not _column_exists(_TABLE_TOUR, "nomadic_community_id"):
        op.add_column(
            _TABLE_TOUR,
            sa.Column("nomadic_community_id", sa.String(36), nullable=True, index=True),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    for table, column in [
        (_TABLE_TOUR, "nomadic_community_id"),
        (_TABLE_SVC, "nomadic_community_id"),
    ]:
        if inspector.has_table(table) and any(
            c["name"] == column for c in inspector.get_columns(table)
        ):
            try:
                op.drop_column(table, column)
            except Exception:
                pass
