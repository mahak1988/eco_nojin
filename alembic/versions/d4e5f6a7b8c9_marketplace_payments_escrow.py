"""Marketplace payments + escrow ledger (plan v2.1)

Revision ID: d4e5f6a7b8c9
Revises: b2f8a4c61e90
Create Date: 2026-09-15 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'b2f8a4c61e90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'marketplace_payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('gateway', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='IRR'),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='initiated'),
        sa.Column('escrow_status', sa.String(length=24), nullable=False, server_default='none'),
        sa.Column('authority', sa.String(length=100), nullable=True),
        sa.Column('ref_id', sa.String(length=60), nullable=True),
        sa.Column('card_pan_masked', sa.String(length=30), nullable=True),
        sa.Column('tracking_code', sa.String(length=60), nullable=True),
        sa.Column('redirect_url', sa.Text(), nullable=True),
        sa.Column('gateway_meta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_mpay_order', 'marketplace_payments', ['order_id'])
    op.create_index('idx_mpay_status', 'marketplace_payments', ['status'])
    op.create_index('ix_marketplace_payments_user_id', 'marketplace_payments', ['user_id'])
    op.create_index('ix_marketplace_payments_authority', 'marketplace_payments', ['authority'])

    op.create_table(
        'marketplace_escrow_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payment_id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('seller_id', sa.String(length=36), nullable=True),
        sa.Column('marketplace_id', sa.String(length=36), nullable=True),
        sa.Column('entry_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='IRR'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_escrow_payment', 'marketplace_escrow_entries', ['payment_id'])
    op.create_index('idx_escrow_order', 'marketplace_escrow_entries', ['order_id'])
    op.create_index('ix_marketplace_escrow_entries_seller_id', 'marketplace_escrow_entries', ['seller_id'])
    op.create_index('ix_marketplace_escrow_entries_marketplace_id', 'marketplace_escrow_entries', ['marketplace_id'])


def downgrade() -> None:
    op.drop_table('marketplace_escrow_entries')
    op.drop_table('marketplace_payments')
