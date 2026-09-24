"""satellite_provenance_columns

Revision ID: b7c9d2e4f1a3
Revises: ed7a1747d8db
Create Date: 2026-08-16 05:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c9d2e4f1a3"
down_revision: str | Sequence[str] | None = "ed7a1747d8db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add real-data provenance columns to satellite_analyses."""
    op.add_column(
        "satellite_analyses",
        sa.Column("data_source", sa.String(length=20), server_default="simulated", nullable=False),
    )
    op.add_column("satellite_analyses", sa.Column("scene_id", sa.String(length=200), nullable=True))
    op.add_column("satellite_analyses", sa.Column("cloud_cover", sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove provenance columns."""
    op.drop_column("satellite_analyses", "cloud_cover")
    op.drop_column("satellite_analyses", "scene_id")
    op.drop_column("satellite_analyses", "data_source")
