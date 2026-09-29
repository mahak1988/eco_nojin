"""Add the sponsorships table.

Sponsorship is labelled funder recognition, not advertising. The schema
deliberately has no impression, view or click column: engagement must never be
collectable, so it can never be reported to a sponsor or optimised for one.
Reaching a slot is contextual, derived from the page, never from the reader.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260926_020000_sponsorships"
down_revision = "20260924_000000"  # was the file stem, not the revision id, so alembic
# raised KeyError on every command; the real id of
# 20260924_000000_add_content_escrow_models.py is 20260924_000000
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sponsorships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sponsor_name", sa.String(length=200), nullable=False),
        sa.Column("sponsor_name_fa", sa.String(length=200), nullable=True),
        sa.Column("sponsor_url", sa.String(length=500), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("tagline", sa.String(length=200), nullable=True),
        sa.Column("tagline_fa", sa.String(length=200), nullable=True),
        sa.Column("tier", sa.Enum(*_TIERS, name="sponsortier"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(*_STATUSES, name="sponsorshipstatus"),
            nullable=False,
        ),
        sa.Column(
            "placement",
            sa.Enum(*_PLACEMENTS, name="slotplacement"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("is_project_funder", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_revenue_source_funder", sa.Boolean(), nullable=False, server_default=sa.false()),
        # Not nullable: an unlabelled slot must be impossible at the row level,
        # not merely discouraged in the service layer.
        sa.Column(
            "disclosure_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("green_claims_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("green_claims_attested_by", sa.String(length=120), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # A sponsorship that never ends is a permanent advertisement.
        sa.CheckConstraint("ends_on > starts_on", name="ck_sponsorship_window"),
        # Zero-value sponsorship is a free placement, which is advertising.
        sa.CheckConstraint("amount > 0", name="ck_sponsorship_amount_positive"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_sponsorship_status", "sponsorships", ["status"])
    op.create_index("idx_sponsorship_placement", "sponsorships", ["placement"])
    op.create_index("idx_sponsorship_sponsor_name", "sponsorships", ["sponsor_name"])
    op.create_index(
        "idx_sponsorship_active_lookup",
        "sponsorships",
        ["status", "placement", "ends_on"],
    )
    op.create_index(
        "ix_sponsorships_sponsor_name", "sponsorships", ["sponsor_name"]
    )
    op.create_index(
        "ix_sponsorships_is_project_funder", "sponsorships", ["is_project_funder"]
    )
    op.create_index(
        "ix_sponsorships_disclosure_required", "sponsorships", ["disclosure_required"]
    )
    op.create_index("ix_sponsorships_created_at", "sponsorships", ["created_at"])


def downgrade() -> None:
    op.drop_table("sponsorships")
    for name in ("sponsorshipstatus", "sponsortier", "slotplacement"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)


# Enum values are duplicated rather than imported so that a future edit to the
# model cannot silently change a historical migration.
_TIERS = ["page", "section", "tool", "district", "founding"]
_STATUSES = [
    "prospect",
    "contracted",
    "active",
    "suspended",
    "ended",
    "terminated",
]
_PLACEMENTS = ["public_services", "public_audiences", "tool_footer"]

__all__ = ["down_revision", "downgrade", "revision", "upgrade"]
