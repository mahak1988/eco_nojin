"""add content escrow models

Revision ID: 20260924_000000
Revises: 152cf86214af
Create Date: 2026-09-24 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260924_000000'
down_revision = '152cf86214af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('language', sa.String(length=8), nullable=False, server_default='fa'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('generated_by_ai', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rag_synced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_item_status_language', 'content_items', ['status', 'language'])
    op.create_index('ix_content_item_category_status', 'content_items', ['category', 'status'])

    # Create content_versions table
    op.create_table(
        'content_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id', 'version', name='uq_content_version'),
    )
    op.create_index('ix_content_version_content_id_version', 'content_versions', ['content_id', 'version'])

    # Create content_translations table
    op.create_table(
        'content_translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('locale', sa.String(length=8), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=True, server_default='manual'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id', 'locale', name='uq_content_translation_locale'),
    )
    op.create_index('ix_content_translation_content_locale', 'content_translations', ['content_id', 'locale'])

    # Rename escrow_record to escrow_records
    # SQLite doesn't support RENAME INDEX, so we create new indexes after rename
    op.rename_table('escrow_record', 'escrow_records')
    
    # Create new indexes for renamed table (old indexes didn't exist in SQLite)
    op.create_index('ix_escrow_records_state', 'escrow_records', ['state'])
    op.create_index('ix_escrow_records_buyer', 'escrow_records', ['buyer_id'])
    op.create_index('ix_escrow_records_seller', 'escrow_records', ['seller_id'])

    # Add EscrowState enum values as check constraint (for SQLite/PostgreSQL compatibility)
    # The state column already has the right values, just ensure the check constraint exists
    # Note: This is handled by the application layer EscrowState enum


def downgrade() -> None:
    # Drop indexes for escrow_records
    op.drop_index('ix_escrow_records_state', table_name='escrow_records')
    op.drop_index('ix_escrow_records_buyer', table_name='escrow_records')
    op.drop_index('ix_escrow_records_seller', table_name='escrow_records')
    
    # Rename back escrow_records to escrow_record
    op.rename_table('escrow_records', 'escrow_record')
    
    # Drop content tables
    op.drop_index('ix_content_translation_content_locale', table_name='content_translations')
    op.drop_table('content_translations')
    op.drop_index('ix_content_version_content_id_version', table_name='content_versions')
    op.drop_table('content_versions')
    op.drop_index('ix_content_item_status_language', table_name='content_items')
    op.drop_index('ix_content_item_category_status', table_name='content_items')
    op.drop_table('content_items')