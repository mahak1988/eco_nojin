"""Phase 3 — بازارچه نهاد: tenants + bazaars + trustees + signatures

Revision ID: 20260923_120000_phase3_bazaar_institution
Revises: 300c2f07b568
Create Date: 2026-09-23T12:00:00.000000

Multi-tenant bazaar institution schema:
- tenants: legal entities that own bazaars
- bazaars: bazaar institutions with PostGIS polygon geometry
- bazaar_trustees: 5-member founding board (§1.2)
- bazaar_signatures: PQ digital signatures (§6.2 T05 5-party)
- market_profiles: regional hub profiles (§5.3)

RLS: bazaars.trustee_id = tenant_id (multi-tenant isolation)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260923_120000_phase3_bazaar_institution"
down_revision: str | Sequence[str] | None = "300c2f07b568"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False, unique=True, index=True),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("legal_form", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"])

    # --- market_profiles (§5.3 کانون منطقه‌ای) ---
    op.create_table(
        "market_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region_type", sa.String(length=50), nullable=False, server_default="local"),
        sa.Column("center_lat", sa.Float(), nullable=True),
        sa.Column("center_lon", sa.Float(), nullable=True),
        sa.Column("coverage_radius_m", sa.Float(), nullable=True),
        sa.Column("bazaar_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("store_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("established_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_market_profile_tenant",
        "market_profiles",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_market_profile_tenant", "market_profiles", ["tenant_id"])

    # --- bazaars (§5.2 42 bazaars, PostGIS Polygon) ---
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "bazaars",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("market_profile_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False, unique=True, index=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bazaar_type", sa.String(length=50), nullable=False, server_default="rural"),
        sa.Column("geom", sa.String(length=50), nullable=True),
        sa.Column(
            "bounding_box",
            sa.JSON(),
            nullable=True,
        ),  # GeoJSON Polygon for PostGIS-less environments
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column("store_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("established_date", sa.Date(), nullable=True),
        sa.Column("regulator_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_bazaar_tenant",
        "bazaars",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_bazaar_market_profile",
        "bazaars",
        "market_profiles",
        ["market_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_bazaar_tenant", "bazaars", ["tenant_id"])
    op.create_index("idx_bazaar_status", "bazaars", ["status"])
    op.create_index("idx_bazaar_tenant_status", "bazaars", ["tenant_id", "status"])

    # RLS policy: tenants can only see their own bazaars
    op.execute("ALTER TABLE bazaars ENABLE ROW LEVEL SECURITY")
    op.execute(
        """CREATE POLICY bazaar_tenant_isolation ON bazaars
           FOR ALL TO authenticated
           USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)"""
    )
    op.execute(
        """CREATE POLICY bazaar_tenant_isolation_w ON bazaars
           FOR ALL TO authenticated
           USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
           WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID)"""
    )

    # --- bazaar_trustees (§1.2 هیئت مؤسس 5 نفره) ---
    op.create_table(
        "bazaar_trustees",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bazaar_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("national_id", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="trustee"),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_trustee_bazaar",
        "bazaar_trustees",
        "bazaars",
        ["bazaar_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_trustee_tenant",
        "bazaar_trustees",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_trustee_bazaar", "bazaar_trustees", ["bazaar_id"])
    op.create_unique_constraint(
        "uq_trustee_bazaar_position",
        "bazaar_trustees",
        ["bazaar_id", "position"],
    )

    # --- bazaar_signatures (§6.2 T05 5-party digital signature, PQ per test_pqcrypto.py) ---
    op.create_table(
        "bazaar_signatures",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bazaar_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("trustee_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column(
            "agreement_type", sa.String(length=50), nullable=False, server_default="establishment"
        ),
        sa.Column("signature_hex", sa.Text(), nullable=False),
        sa.Column("pq_public_hex", sa.Text(), nullable=False),
        sa.Column("ciphertext_hex", sa.Text(), nullable=True),
        sa.Column("shared_secret_hex", sa.Text(), nullable=True),
        sa.Column(
            "algorithm", sa.String(length=50), nullable=False, server_default="DILITHIUM2+ED25519"
        ),
        sa.Column(
            "kem_algorithm", sa.String(length=50), nullable=True, server_default="KYBER512+X25519"
        ),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_signature_bazaar",
        "bazaar_signatures",
        "bazaars",
        ["bazaar_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_signature_trustee",
        "bazaar_signatures",
        "bazaar_trustees",
        ["trustee_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_signature_tenant",
        "bazaar_signatures",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_signature_trustee_step",
        "bazaar_signatures",
        ["trustee_id", "step_number"],
    )
    op.create_index("idx_signature_bazaar", "bazaar_signatures", ["bazaar_id"])

    # --- downgrade ---
    # (order matters: drop dependent tables first)


def downgrade() -> None:
    op.drop_table("bazaar_signatures")
    op.drop_table("bazaar_trustees")
    op.execute("DROP POLICY IF EXISTS bazaar_tenant_isolation_w ON bazaars")
    op.execute("DROP POLICY IF EXISTS bazaar_tenant_isolation ON bazaars")
    op.execute("ALTER TABLE bazaars DISABLE ROW LEVEL SECURITY")
    op.drop_table("bazaars")
    op.drop_table("market_profiles")
    op.drop_table("tenants")
