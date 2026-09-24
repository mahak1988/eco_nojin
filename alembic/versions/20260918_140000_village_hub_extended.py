"""Extend Village Development Hub with experiences, destinations, B2B, engagements, gaps, festivals, nomadic communities

Revision ID: 20260918_140000_village_hub_extended
Revises: 20260917_191000_village_hub
Create Date: 2026-09-18T14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260918_140000_village_hub_extended"
down_revision: str | Sequence[str] | None = "20260917_191000_village_hub"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # village_experiences
    # -------------------------------------------------------------------------
    op.create_table(
        "village_experiences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("experience_type", sa.String(length=50), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("price_range_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("price_range_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("guide_required", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_exp_village", "village_experiences", ["village_id"])
    op.create_index("idx_exp_type", "village_experiences", ["experience_type"])

    # -------------------------------------------------------------------------
    # village_destinations
    # -------------------------------------------------------------------------
    op.create_table(
        "village_destinations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("natural_attractions", sa.JSON(), nullable=True),
        sa.Column("cultural_attractions", sa.JSON(), nullable=True),
        sa.Column("experiences", sa.JSON(), nullable=True),
        sa.Column("accommodations", sa.JSON(), nullable=True),
        sa.Column("tagline", sa.String(length=500), nullable=True),
        sa.Column("hero_image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_dest_village", "village_destinations", ["village_id"])

    # -------------------------------------------------------------------------
    # b2b_demands
    # -------------------------------------------------------------------------
    op.create_table(
        "b2b_demands",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("buyer_id", sa.String(length=36), nullable=False),
        sa.Column("buyer_name", sa.String(length=200), nullable=True),
        sa.Column("commodity", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("quantity_required", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=30), server_default="monthly"),
        sa.Column("target_regions", sa.JSON(), nullable=True),
        sa.Column("min_quality_cert", sa.String(length=200), nullable=True),
        sa.Column("price_range", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open"),
        sa.Column("matched_villages", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_b2b_buyer", "b2b_demands", ["buyer_id"])
    op.create_index("idx_b2b_commodity", "b2b_demands", ["commodity"])
    op.create_index("idx_b2b_status", "b2b_demands", ["status"])

    # -------------------------------------------------------------------------
    # village_engagements
    # -------------------------------------------------------------------------
    op.create_table(
        "village_engagements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_eng_user", "village_engagements", ["user_id"])
    op.create_index("idx_eng_opportunity", "village_engagements", ["opportunity_id"])
    op.create_index("idx_eng_project", "village_engagements", ["project_id"])
    op.create_index("idx_eng_role", "village_engagements", ["role"])
    op.create_foreign_key(
        "fk_eng_opportunity",
        "village_engagements",
        "village_opportunities",
        ["opportunity_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eng_project",
        "village_engagements",
        "village_projects",
        ["project_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # village_development_gaps
    # -------------------------------------------------------------------------
    op.create_table(
        "village_development_gaps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("gap_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("proposed_solution", sa.Text(), nullable=True),
        sa.Column("suggested_opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_gap_village", "village_development_gaps", ["village_id"])
    op.create_index("idx_gap_type", "village_development_gaps", ["gap_type"])
    op.create_foreign_key(
        "fk_gap_opportunity",
        "village_development_gaps",
        "village_opportunities",
        ["suggested_opportunity_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # village_festivals
    # -------------------------------------------------------------------------
    op.create_table(
        "village_festivals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(length=30), server_default="local"),
        sa.Column("mode", sa.String(length=20), server_default="both"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("participating_villages", sa.JSON(), nullable=True),
        sa.Column("registration_link", sa.String(length=500), nullable=True),
        sa.Column("featured_products", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="planning"),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_fest_scope", "village_festivals", ["scope"])

    # -------------------------------------------------------------------------
    # nomadic_communities
    # -------------------------------------------------------------------------
    op.create_table(
        "nomadic_communities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("region", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=10), server_default="IR"),
        sa.Column("capacities", sa.JSON(), nullable=True),
        sa.Column("tourism_experience", sa.Text(), nullable=True),
        sa.Column("has_tented_accommodation", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("contact_person", sa.String(length=200), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_nomadic_region", "nomadic_communities", ["region"])


def downgrade() -> None:
    op.drop_table("nomadic_communities")
    op.drop_table("village_festivals")
    op.drop_table("village_development_gaps")
    op.drop_table("village_engagements")
    op.drop_table("b2b_demands")
    op.drop_table("village_destinations")
    op.drop_table("village_experiences")
