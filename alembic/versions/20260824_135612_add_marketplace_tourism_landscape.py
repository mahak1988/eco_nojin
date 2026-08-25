"""Add marketplace, tourism, and landscape models (stand-alone)

Revision ID: 20260824_135612_marketplace_tourism_landscape
Revises: None
Create Date: 2026-08-24T13:56:12.322348+00:00

Note: This migration is stand-alone and does not depend on previous migrations.
"""
from alembic import op
import sqlalchemy as sa

revision = '20260824_135612_marketplace_tourism_landscape'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Marketplace Tables
    op.create_table(
        'marketplace_sellers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('shop_name', sa.String(200), nullable=False),
        sa.Column('shop_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('certifications', sa.JSON(), nullable=True),
        sa.Column('total_sales', sa.Integer(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_seller_user', 'marketplace_sellers', ['user_id'])
    op.create_index('idx_seller_village', 'marketplace_sellers', ['village_id'])
    op.create_index('idx_seller_status', 'marketplace_sellers', ['status'])

    op.create_table(
        'marketplace_products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('seller_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(300), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('stock', sa.Integer(), server_default=sa.text('0')),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('pgs_certified', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('organic', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('story', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('sales_count', sa.Integer(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['seller_id'], ['marketplace_sellers.id'], ),
    )
    op.create_index('idx_product_seller', 'marketplace_products', ['seller_id'])
    op.create_index('idx_product_village', 'marketplace_products', ['village_id'])

    op.create_table(
        'marketplace_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True),
        sa.Column('buyer_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(15, 2), server_default=sa.text('0')),
        sa.Column('landscape_fee', sa.Numeric(15, 2), server_default=sa.text('0')),
        sa.Column('total', sa.Numeric(15, 2), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('payment_status', sa.String(20), server_default='pending'),
        sa.Column('shipping_address', sa.JSON(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_order_buyer', 'marketplace_orders', ['buyer_id'])
    op.create_index('idx_order_status', 'marketplace_orders', ['status'])

    op.create_table(
        'marketplace_commission_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('village_id', sa.String(100), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('platform_fee_bps', sa.Integer(), server_default=sa.text('300')),
        sa.Column('landscape_fee_bps', sa.Integer(), server_default=sa.text('100')),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Tourism Tables
    op.create_table(
        'tourism_guides',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('languages', sa.JSON(), nullable=True),
        sa.Column('specialties', sa.JSON(), nullable=True),
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('total_tours', sa.Integer(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_guide_user', 'tourism_guides', ['user_id'])
    op.create_index('idx_guide_village', 'tourism_guides', ['village_id'])

    op.create_table(
        'tourism_tours',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('guide_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(300), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tour_type', sa.String(50), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=False),
        sa.Column('max_participants', sa.Integer(), server_default=sa.text('10')),
        sa.Column('min_participants', sa.Integer(), server_default=sa.text('2')),
        sa.Column('difficulty', sa.String(20), server_default='moderate'),
        sa.Column('price_per_person', sa.Numeric(12, 2), nullable=False),
        sa.Column('ecological_capacity', sa.Integer(), nullable=True),
        sa.Column('current_bookings', sa.Integer(), server_default=sa.text('0')),
        sa.Column('status', sa.String(20), server_default='pending_approval'),
        sa.Column('is_regenerative', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('regenerative_activity', sa.Text(), nullable=True),
        sa.Column('total_bookings', sa.Integer(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['guide_id'], ['tourism_guides.id'], ),
    )
    op.create_index('idx_tour_guide', 'tourism_tours', ['guide_id'])
    op.create_index('idx_tour_village', 'tourism_tours', ['village_id'])
    op.create_index('idx_tour_status', 'tourism_tours', ['status'])

    op.create_table(
        'tourism_bookings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('booking_number', sa.String(50), nullable=False, unique=True),
        sa.Column('tour_id', sa.String(36), nullable=False),
        sa.Column('guest_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('participants_count', sa.Integer(), nullable=False),
        sa.Column('tour_date', sa.DateTime(), nullable=False),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(15, 2), server_default=sa.text('0')),
        sa.Column('landscape_fee', sa.Numeric(15, 2), server_default=sa.text('0')),
        sa.Column('insurance_fee', sa.Numeric(15, 2), server_default=sa.text('0')),
        sa.Column('total', sa.Numeric(15, 2), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('payment_status', sa.String(20), server_default='pending'),
        sa.Column('blockchain_tx_hash', sa.String(100), nullable=True),
        sa.Column('regenerative_completed', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tour_id'], ['tourism_tours.id'], ),
    )
    op.create_index('idx_booking_tour', 'tourism_bookings', ['tour_id'])
    op.create_index('idx_booking_guest', 'tourism_bookings', ['guest_id'])
    op.create_index('idx_booking_status', 'tourism_bookings', ['status'])

    # Landscape Tables
    op.create_table(
        'landscape_villages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('village_id', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), server_default='IR'),
        sa.Column('coordinates', sa.JSON(), nullable=True),
        sa.Column('geo_boundary', sa.JSON(), nullable=True),
        sa.Column('brand_name', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('active_modules', sa.JSON(), nullable=True),
        sa.Column('total_members', sa.Integer(), server_default=sa.text('0')),
        sa.Column('active_sellers', sa.Integer(), server_default=sa.text('0')),
        sa.Column('active_tour_guides', sa.Integer(), server_default=sa.text('0')),
        sa.Column('monthly_gmv', sa.Numeric(18, 2), server_default=sa.text('0')),
        sa.Column('ecological_metrics_data', sa.JSON(), nullable=True),
        sa.Column('smart_contract_address', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'landscape_governance',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('term_start', sa.Date(), nullable=True),
        sa.Column('term_end', sa.Date(), nullable=True),
        sa.Column('elected_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
    )
    op.create_index('idx_gov_village', 'landscape_governance', ['village_id'])
    op.create_index('idx_gov_user', 'landscape_governance', ['user_id'])
    op.create_index('idx_gov_role', 'landscape_governance', ['role'])

    op.create_table(
        'landscape_funds',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('village_id', sa.String(100), nullable=False, unique=True),
        sa.Column('contract_address', sa.String(100), nullable=True),
        sa.Column('fee_bps', sa.Integer(), server_default=sa.text('100')),
        sa.Column('total_collected', sa.Numeric(18, 2), server_default=sa.text('0')),
        sa.Column('total_distributed', sa.Numeric(18, 2), server_default=sa.text('0')),
        sa.Column('pending_balance', sa.Numeric(18, 2), server_default=sa.text('0')),
        sa.Column('currency', sa.String(3), server_default='IRR'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'landscape_fund_distributions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fund_id', sa.String(36), nullable=False),
        sa.Column('village_id', sa.String(100), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('purpose', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recipient_user_id', sa.String(36), nullable=True),
        sa.Column('recipient_organization', sa.String(200), nullable=True),
        sa.Column('proposed_by', sa.String(36), nullable=False),
        sa.Column('approved_by', sa.String(36), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('blockchain_tx_hash', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['fund_id'], ['landscape_funds.id'], ),
    )
    op.create_index('idx_dist_fund', 'landscape_fund_distributions', ['fund_id'])
    op.create_index('idx_dist_village', 'landscape_fund_distributions', ['village_id'])
    op.create_index('idx_dist_status', 'landscape_fund_distributions', ['status'])


def downgrade() -> None:
    op.drop_table('landscape_fund_distributions')
    op.drop_table('landscape_funds')
    op.drop_table('landscape_governance')
    op.drop_table('landscape_villages')
    op.drop_table('tourism_bookings')
    op.drop_table('tourism_tours')
    op.drop_table('tourism_guides')
    op.drop_table('marketplace_commission_rules')
    op.drop_table('marketplace_orders')
    op.drop_table('marketplace_products')
    op.drop_table('marketplace_sellers')
