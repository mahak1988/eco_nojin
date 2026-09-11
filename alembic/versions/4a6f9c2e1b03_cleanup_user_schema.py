"""Remove duplicate password_hash column and add missing user profile columns.

Revision ID: 4a6f9c2e1b03
Revises: 300c2f07b568
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime


# revision identifiers, used by Alembic.
revision: str = "4a6f9c2e1b03"
down_revision: Union[str, None] = "300c2f07b568"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "password_hash" in columns:
        op.drop_column("users", "password_hash")

    if "date_of_birth" not in columns:
        op.add_column("users", sa.Column("date_of_birth", DateTime(), nullable=True))

    if "address" not in columns:
        op.add_column("users", sa.Column("address", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "address" in columns:
        op.drop_column("users", "address")

    if "date_of_birth" in columns:
        op.drop_column("users", "date_of_birth")

    if "password_hash" not in columns:
        op.add_column("users", sa.Column("password_hash", sa.String(), nullable=True))
