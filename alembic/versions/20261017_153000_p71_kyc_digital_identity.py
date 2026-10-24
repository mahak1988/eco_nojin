"""P7.1: KYC / Digital Identity fields on landscape_villages.

Adds digital identity (eIDAS / National ID) verification fields so that a
village can only reach ``verification_status="approved"`` after its
representative has passed KYC. This is the gate that connects the
governance onboarding workflow to the marketplace: unverified villages
stay invisible in marketplace listings.

Guarded and idempotent: every column is added only when absent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_153000_p71_kyc_digital_identity"
down_revision: str | None = "20261017_150000_p5_b2b_demand_opportunity_match"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "landscape_villages"


def _column_exists(column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(_TABLE):
        return False
    return any(c["name"] == column for c in inspector.get_columns(_TABLE))


def upgrade() -> None:
    if context.is_offline_mode():
        return

    for column_def in [
        ("kyc_status", sa.String(20), "pending", False),
        ("kyc_submitted_at", sa.DateTime(), None, True),
        ("kyc_approved_at", sa.DateTime(), None, True),
        ("kyc_evidence_ref", sa.String(300), None, True),
        ("kyc_rejected_reason", sa.Text(), None, True),
        ("representative_identity_verified", sa.Boolean(), False, False),
        ("national_id_hash", sa.String(128), None, True),
        ("eidas_level", sa.String(20), None, True),
    ]:
        name, col_type, server_default, nullable = column_def
        if not _column_exists(name):
            op.add_column(
                _TABLE,
                sa.Column(name, col_type, nullable=nullable, server_default=str(server_default) if server_default is not None else None),
            )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE):
        for column in [
            "eidas_level",
            "national_id_hash",
            "representative_identity_verified",
            "kyc_rejected_reason",
            "kyc_evidence_ref",
            "kyc_approved_at",
            "kyc_submitted_at",
            "kyc_status",
        ]:
            if any(c["name"] == column for c in inspector.get_columns(_TABLE)):
                try:
                    op.drop_column(_TABLE, column)
                except Exception:
                    pass
