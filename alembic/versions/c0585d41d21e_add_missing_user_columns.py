"""add_platform_id_to_users

Revision ID: c0585d41d21e
Revises: 84c70878671c
Create Date: 2026-09-15 05:39:02.474495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0585d41d21e'
down_revision: Union[str, None] = '84c70878671c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "platform_id" not in columns:
        op.add_column("users", sa.Column("platform_id", sa.String(), nullable=True, index=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "platform_id" in columns:
        op.drop_column("users", "platform_id")