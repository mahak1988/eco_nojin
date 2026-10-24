"""Add content escrow model tables.

Revision ID: 20260924_000000_add_content_escrow_models
Revises: 
Create Date: 2026-09-24 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "20260924_000000_add_content_escrow_models"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "land_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=True),
        sa.Column("area_ha", sa.Numeric(12, 2), nullable=True),
        sa.Column("elevation_min_m", sa.Float(), nullable=True),
        sa.Column("elevation_max_m", sa.Float(), nullable=True),
        sa.Column("slope_avg_pct", sa.Float(), nullable=True),
        sa.Column("aspect_deg", sa.Float(), nullable=True),
        sa.Column("soil_texture", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "escrow_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("claim_id", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("escrow_items")
    op.drop_table("land_profiles")
