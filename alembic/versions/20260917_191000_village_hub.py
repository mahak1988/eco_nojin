"""Village Development Hub models — capabilities, opportunities, projects, entrepreneurs, investments, tourism, events, needs, brand

Revision ID: 20260917_191000_village_hub
Revises: d4e5f6a7b8c9
Create Date: 2026-09-17T19:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260917_191000_village_hub"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # village_capabilities
    # -------------------------------------------------------------------------
    op.create_table(
        "village_capabilities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("capacity_value", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("confidence", sa.String(length=20), server_default="medium"),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_cap_village", "village_capabilities", ["village_id"])
    op.create_index("idx_cap_category", "village_capabilities", ["category"])
    op.create_index("idx_cap_active", "village_capabilities", ["is_active"])

    # -------------------------------------------------------------------------
    # village_opportunities
    # -------------------------------------------------------------------------
    op.create_table(
        "village_opportunities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("capability_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_model", sa.Text(), nullable=True),
        sa.Column("required_investment", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("target_markets", sa.JSON(), nullable=True),
        sa.Column("expected_revenue", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("maturity", sa.String(length=30), server_default="idea"),
        sa.Column("status", sa.String(length=20), server_default="draft"),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_opp_village", "village_opportunities", ["village_id"])
    op.create_index("idx_opp_category", "village_opportunities", ["category"])
    op.create_index("idx_opp_status", "village_opportunities", ["status"])
    op.create_index("idx_opp_capability", "village_opportunities", ["capability_id"])
    op.create_foreign_key(
        "fk_opp_capability",
        "village_opportunities",
        "village_capabilities",
        ["capability_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # village_projects
    # -------------------------------------------------------------------------
    op.create_table(
        "village_projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="planned"),
        sa.Column("progress_pct", sa.Integer(), server_default=sa.text("0")),
        sa.Column("investment_needed", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column(
            "investment_secured", sa.Numeric(precision=18, scale=2), server_default=sa.text("0")
        ),
        sa.Column("investors_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("expected_completion", sa.Date(), nullable=True),
        sa.Column("actual_completion", sa.Date(), nullable=True),
        sa.Column("team_size", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_proj_village", "village_projects", ["village_id"])
    op.create_index("idx_proj_status", "village_projects", ["status"])
    op.create_index("idx_proj_opportunity", "village_projects", ["opportunity_id"])
    op.create_foreign_key(
        "fk_proj_opportunity",
        "village_projects",
        "village_opportunities",
        ["opportunity_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # entrepreneur_profiles
    # -------------------------------------------------------------------------
    op.create_table(
        "entrepreneur_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("village_id", sa.String(length=100), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column("capacity_description", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_entrepreneur_user", "entrepreneur_profiles", ["user_id"])
    op.create_index("idx_entrepreneur_village", "entrepreneur_profiles", ["village_id"])

    # -------------------------------------------------------------------------
    # village_investments
    # -------------------------------------------------------------------------
    op.create_table(
        "village_investments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("investor_user_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="IRR"),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("confirmed_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_inv_project", "village_investments", ["project_id"])
    op.create_index("idx_inv_investor", "village_investments", ["investor_user_id"])
    op.create_foreign_key(
        "fk_inv_project",
        "village_investments",
        "village_projects",
        ["project_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # village_tourism_services
    # -------------------------------------------------------------------------
    op.create_table(
        "village_tourism_services",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), nullable=False),
        sa.Column("service_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("coordinates", sa.JSON(), nullable=True),
        sa.Column("price_per_unit", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("is_organic", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("is_regenerative", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_tour_svc_village", "village_tourism_services", ["village_id"])
    op.create_index("idx_tour_svc_type", "village_tourism_services", ["service_type"])
    op.create_index("idx_tour_svc_owner", "village_tourism_services", ["owner_user_id"])

    # -------------------------------------------------------------------------
    # village_events
    # -------------------------------------------------------------------------
    op.create_table(
        "village_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("title_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("coordinates", sa.JSON(), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column(
            "registration_fee", sa.Numeric(precision=12, scale=2), server_default=sa.text("0")
        ),
        sa.Column("status", sa.String(length=20), server_default="draft"),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_event_village", "village_events", ["village_id"])
    op.create_index("idx_event_start", "village_events", ["start_date"])
    op.create_index("idx_event_status", "village_events", ["status"])

    # -------------------------------------------------------------------------
    # village_event_registrations
    # -------------------------------------------------------------------------
    op.create_table(
        "village_event_registrations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="registered"),
        sa.Column(
            "registration_fee", sa.Numeric(precision=12, scale=2), server_default=sa.text("0")
        ),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_event_reg_event", "village_event_registrations", ["event_id"])
    op.create_index("idx_event_reg_user", "village_event_registrations", ["user_id"])
    op.create_index("idx_event_reg_status", "village_event_registrations", ["status"])
    op.create_foreign_key(
        "fk_event_reg",
        "village_event_registrations",
        "village_events",
        ["event_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # village_needs
    # -------------------------------------------------------------------------
    op.create_table(
        "village_needs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), server_default="medium"),
        sa.Column("estimated_investment", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("resolved_by", sa.String(length=36), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_need_village", "village_needs", ["village_id"])
    op.create_index("idx_need_priority", "village_needs", ["priority"])
    op.create_index("idx_need_category", "village_needs", ["category"])

    # -------------------------------------------------------------------------
    # village_brands
    # -------------------------------------------------------------------------
    op.create_table(
        "village_brands",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("village_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("story", sa.Text(), nullable=True),
        sa.Column("vision", sa.Text(), nullable=True),
        sa.Column("values", sa.JSON(), nullable=True),
        sa.Column("heritage", sa.Text(), nullable=True),
        sa.Column("certifications", sa.JSON(), nullable=True),
        sa.Column("media_kit_url", sa.String(length=500), nullable=True),
        sa.Column("brand_guidelines_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_brand_village", "village_brands", ["village_id"])

    # -------------------------------------------------------------------------
    # village_opportunity_interests (junction table)
    # -------------------------------------------------------------------------
    op.create_table(
        "village_opportunity_interests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("entrepreneur_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="interested"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("expressed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_interest_opp", "village_opportunity_interests", ["opportunity_id"])
    op.create_index(
        "idx_interest_entrepreneur", "village_opportunity_interests", ["entrepreneur_id"]
    )
    op.create_index("idx_interest_status", "village_opportunity_interests", ["status"])
    op.create_foreign_key(
        "fk_interest_opportunity",
        "village_opportunity_interests",
        "village_opportunities",
        ["opportunity_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_interest_entrepreneur",
        "village_opportunity_interests",
        "entrepreneur_profiles",
        ["entrepreneur_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_table("village_opportunity_interests")
    op.drop_table("village_brands")
    op.drop_table("village_needs")
    op.drop_table("village_event_registrations")
    op.drop_table("village_events")
    op.drop_table("village_tourism_services")
    op.drop_table("village_investments")
    op.drop_table("entrepreneur_profiles")
    op.drop_table("village_projects")
    op.drop_table("village_opportunities")
    op.drop_table("village_capabilities")
