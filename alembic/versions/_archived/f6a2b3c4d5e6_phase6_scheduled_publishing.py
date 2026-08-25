"""phase6 scheduled publishing

Revision ID: f6a2b3c4d5e6
Revises: e5f1a2b3c4d5
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa

revision = "f6a2b3c4d5e6"
down_revision = "e5f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_items", sa.Column("scheduled_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_items", "scheduled_at")
