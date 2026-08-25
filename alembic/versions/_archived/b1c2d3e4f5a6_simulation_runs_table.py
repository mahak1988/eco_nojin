"""simulation_runs table (Phase 3 simulation chain persistence)

Revision ID: b1c2d3e4f5a6
Revises: a9f8e7d6c5b4
Create Date: 2026-08-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a9f8e7d6c5b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.String(length=200), nullable=False),
        sa.Column("scenario", sa.String(length=20), nullable=False),
        sa.Column("area_ha", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_simulation_runs_site_id", "simulation_runs", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_simulation_runs_site_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")
