"""admin_modules_tables

Revision ID: d4e9f0a3b2c5
Revises: c3d8e0f2a1b4
Create Date: 2026-08-16 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e9f0a3b2c5'
down_revision: Union[str, Sequence[str], None] = 'c3d8e0f2a1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create settings, error_logs and content_items tables."""
    op.create_table(
        'settings',
        sa.Column('key', sa.String(length=100), primary_key=True),
        sa.Column('value', sa.String(length=1000), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'error_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('status', sa.Integer(), nullable=True),
        sa.Column('message', sa.String(length=1000), nullable=True),
        sa.Column('detail', sa.String(length=3000), nullable=True),
        sa.Column('acked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_error_logs_id', 'error_logs', ['id'])
    op.create_index('ix_error_logs_created_at', 'error_logs', ['created_at'])
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_content_items_id', 'content_items', ['id'])


def downgrade() -> None:
    """Drop the three tables."""
    op.drop_index('ix_content_items_id', table_name='content_items')
    op.drop_table('content_items')
    op.drop_index('ix_error_logs_created_at', table_name='error_logs')
    op.drop_index('ix_error_logs_id', table_name='error_logs')
    op.drop_table('error_logs')
    op.drop_table('settings')
