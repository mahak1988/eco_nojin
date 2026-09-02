"""Phase 5: Add audit log fields for RBAC + Audit

Revision ID: phase5_audit_complete
Revises: 20260824_135612
Create Date: 2026-08-28

"""
import structlog

logger = structlog.get_logger()
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'phase5_audit_complete'
down_revision = '20260824_135612'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'auditlog' not in inspector.get_table_names():
        logger.info('Table auditlog does not exist, creating it...')
        op.create_table(
            'auditlog',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('actor_id', sa.String(100), nullable=False),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('resource_type', sa.String(50), nullable=True),
            sa.Column('resource_id', sa.String(100), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_auditlog_actor_time', 'auditlog', ['actor_id', 'created_at'])
        return
    
    # Add new columns to existing table
    op.add_column('auditlog', sa.Column('resource_type', sa.String(50), nullable=True))
    op.add_column('auditlog', sa.Column('resource_id', sa.String(100), nullable=True))
    op.add_column('auditlog', sa.Column('ip_address', sa.String(45), nullable=True))
    op.add_column('auditlog', sa.Column('user_agent', sa.String(500), nullable=True))
    
    # For SQLite, use Text instead of JSON
    if conn.dialect.name == 'sqlite':
        op.add_column('auditlog', sa.Column('details', sa.Text(), nullable=True))
    else:
        op.add_column('auditlog', sa.Column('details', sa.JSON(), nullable=True))
    
    # Add indexes for performance
    try:
        op.create_index('ix_auditlog_actor_time', 'auditlog', ['actor_id', 'created_at'])
        op.create_index('ix_auditlog_resource', 'auditlog', ['resource_type', 'resource_id'])
    except Exception:
        pass  # Indexes may already exist


def downgrade():
    op.drop_index('ix_auditlog_resource', table_name='auditlog')
    op.drop_index('ix_auditlog_actor_time', table_name='auditlog')
    op.drop_column('auditlog', 'details')
    op.drop_column('auditlog', 'user_agent')
    op.drop_column('auditlog', 'ip_address')
    op.drop_column('auditlog', 'resource_id')
    op.drop_column('auditlog', 'resource_type')