"""PostGIS geography columns for tribal migration routes (plan v2.1, pg-only)

Adds marketplaces.static_location (POINT), migration_route (LINESTRING),
current_position (POINT) + coverage_radius_km with GIST indexes.
Runs ONLY on PostgreSQL (no-ops on SQLite dev databases); requires the
PostGIS extension on the target database.

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-09-15 09:47:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.add_column("marketplaces", sa.Column("postal_code", sa.String(length=20), nullable=True))
    op.add_column("marketplaces", sa.Column("province", sa.String(length=100), nullable=True))
    op.add_column("marketplaces", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("marketplaces", sa.Column("village_code", sa.String(length=50), nullable=True))
    op.add_column(
        "marketplaces",
        sa.Column("coverage_radius_km", sa.Integer(), nullable=True, server_default="50"),
    )
    op.add_column(
        "marketplaces",
        sa.Column(
            "accountability_score",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            server_default="100",
        ),
    )
    op.execute(
        "ALTER TABLE marketplaces ADD COLUMN IF NOT EXISTS static_location geography(POINT, 4326)"
    )
    op.execute(
        "ALTER TABLE marketplaces ADD COLUMN IF NOT EXISTS migration_route geography(LINESTRING, 4326)"
    )
    op.execute(
        "ALTER TABLE marketplaces ADD COLUMN IF NOT EXISTS current_position geography(POINT, 4326)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_marketplace_location ON marketplaces USING GIST (static_location)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_marketplace_route ON marketplaces USING GIST (migration_route)"
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute("DROP INDEX IF EXISTS idx_marketplace_route")
    op.execute("DROP INDEX IF EXISTS idx_marketplace_location")
    op.execute("ALTER TABLE marketplaces DROP COLUMN IF EXISTS current_position")
    op.execute("ALTER TABLE marketplaces DROP COLUMN IF EXISTS migration_route")
    op.execute("ALTER TABLE marketplaces DROP COLUMN IF EXISTS static_location")
    for col in (
        "accountability_score",
        "coverage_radius_km",
        "village_code",
        "city",
        "province",
        "postal_code",
    ):
        op.execute("ALTER TABLE marketplaces DROP COLUMN IF EXISTS {}".format(col))
