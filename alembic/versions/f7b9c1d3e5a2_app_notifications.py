"""In-app notifications table (plan v2.2)

Revision ID: f7b9c1d3e5a2
Revises: 718969b7e01d
Create Date: 2026-09-15 10:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f7b9c1d3e5a2"
down_revision: Union[str, Sequence[str], None] = "718969b7e01d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False, server_default="info"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link", sa.String(length=300), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notif_user_read", "app_notifications", ["user_id", "is_read"])
    op.create_index("ix_app_notifications_user_id", "app_notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("app_notifications")
