"""Merge multiple heads

Revision ID: merge_heads_phase123
Revises: phase1_2_3_complete_v2, yyy_new_analysis_fixed
Create Date: 2026-08-23 14:59:44

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'merge_heads_phase123'
down_revision = ['phase1_2_3_complete_v2', 'yyy_new_analysis_fixed']
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No schema changes - just merge
    pass


def downgrade() -> None:
    # No schema changes - just split
    pass
