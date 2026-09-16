"""Bazargah plan-v2.0: founders, disputes, shipments, quality tables

Adds the tables required by the marketplace plan v2.0 services:
- marketplace_founders  (services/marketplace/models/marketplace_founder.py)
- disputes / dispute_events  (services/dispute_resolution/models.py)
- shipments / shipment_events  (services/logistics/models.py)
- quality_inspections / quality_certificates  (services/quality_assurance/models.py)

Revision ID: b2f8a4c61e90
Revises: 425ba660dd2d
Create Date: 2026-09-15 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2f8a4c61e90'
down_revision: Union[str, Sequence[str], None] = '425ba660dd2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create plan-v2.0 marketplace tables."""
    op.create_table(
        'marketplace_founders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('marketplace_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='founder'),
        sa.Column('equity_share', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('contribution_type', sa.String(length=20), nullable=True),
        sa.Column('contribution_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('identity_verified', sa.Boolean(), nullable=True),
        sa.Column('identity_verification_date', sa.DateTime(), nullable=True),
        sa.Column('verification_method', sa.String(length=40), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('wallet_address', sa.String(length=42), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('marketplace_id', 'user_id', name='uq_marketplace_user'),
        sa.CheckConstraint('equity_share >= 0 AND equity_share <= 100', name='ck_equity_share'),
    )
    op.create_index('idx_founder_marketplace', 'marketplace_founders', ['marketplace_id'])
    op.create_index('idx_founder_user', 'marketplace_founders', ['user_id'])

    op.create_table(
        'disputes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('marketplace_id', sa.String(length=36), nullable=True),
        sa.Column('complainant_id', sa.String(length=36), nullable=False),
        sa.Column('respondent_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(length=36), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_dispute_order', 'disputes', ['order_id'])
    op.create_index('idx_dispute_status', 'disputes', ['status'])
    op.create_index('ix_disputes_marketplace_id', 'disputes', ['marketplace_id'])

    op.create_table(
        'dispute_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispute_id', sa.String(length=36), nullable=False),
        sa.Column('event', sa.String(length=40), nullable=False),
        sa.Column('actor', sa.String(length=36), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_dispute_event_dispute', 'dispute_events', ['dispute_id'])

    op.create_table(
        'shipments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('carrier', sa.String(length=60), nullable=True),
        sa.Column('tracking_code', sa.String(length=60), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('origin', sa.String(length=200), nullable=True),
        sa.Column('destination', sa.String(length=200), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_shipment_order', 'shipments', ['order_id'])
    op.create_index('ix_shipments_tracking_code', 'shipments', ['tracking_code'])

    op.create_table(
        'shipment_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('shipment_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('actor', sa.String(length=36), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_shipment_event_shipment', 'shipment_events', ['shipment_id'])

    op.create_table(
        'quality_inspections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('marketplace_id', sa.String(length=36), nullable=True),
        sa.Column('inspector_id', sa.String(length=36), nullable=True),
        sa.Column('inspection_type', sa.String(length=30), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_qi_product', 'quality_inspections', ['product_id'])
    op.create_index('ix_quality_inspections_marketplace_id', 'quality_inspections', ['marketplace_id'])

    op.create_table(
        'quality_certificates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('inspection_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('standard', sa.String(length=60), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('issued_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_qc_inspection', 'quality_certificates', ['inspection_id'])
    op.create_index('idx_qc_product', 'quality_certificates', ['product_id'])


def downgrade() -> None:
    """Drop plan-v2.0 marketplace tables (reverse creation order)."""
    op.drop_index('idx_qc_product', table_name='quality_certificates')
    op.drop_index('idx_qc_inspection', table_name='quality_certificates')
    op.drop_table('quality_certificates')
    op.drop_index('ix_quality_inspections_marketplace_id', table_name='quality_inspections')
    op.drop_index('idx_qi_product', table_name='quality_inspections')
    op.drop_table('quality_inspections')
    op.drop_index('idx_shipment_event_shipment', table_name='shipment_events')
    op.drop_table('shipment_events')
    op.drop_index('ix_shipments_tracking_code', table_name='shipments')
    op.drop_index('idx_shipment_order', table_name='shipments')
    op.drop_table('shipments')
    op.drop_index('idx_dispute_event_dispute', table_name='dispute_events')
    op.drop_table('dispute_events')
    op.drop_index('ix_disputes_marketplace_id', table_name='disputes')
    op.drop_index('idx_dispute_status', table_name='disputes')
    op.drop_index('idx_dispute_order', table_name='disputes')
    op.drop_table('disputes')
    op.drop_index('idx_founder_user', table_name='marketplace_founders')
    op.drop_index('idx_founder_marketplace', table_name='marketplace_founders')
    op.drop_table('marketplace_founders')

