"""add supabase sync fields to outbox event

Revision ID: 20260920_000000_add_supabase_sync_fields
Revises: b2c3d4e5_phase0_commerce_models
Create Date: 2026-09-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260920_000000_add_supabase_sync_fields"
down_revision: str | None = "b2c3d4e5_phase0_commerce_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add supabase_synced and last_error columns to int_outbox_event
    op.add_column(
        "int_outbox_event",
        sa.Column("supabase_synced", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "int_outbox_event",
        sa.Column("last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("int_outbox_event", "supabase_synced")
    op.drop_column("int_outbox_event", "last_error")
