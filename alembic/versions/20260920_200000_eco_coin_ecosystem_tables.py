"""eco_coin_ecosystem_tables

Revision ID: eco_coin_ecosystem_001
Revises: a1b2c3d4_phase0_financial_schema
Create Date: 2026-09-20 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'eco_coin_ecosystem_001'
down_revision = 'a1b2c3d4_phase0_financial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ecosystem Activities
    op.create_table(
        'ecosystem_activity',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('activity_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.String(64), nullable=False, index=True),
        sa.Column('activity_type', sa.String(64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location_hash', sa.String(64), nullable=False),
        sa.Column('region', sa.String(120), nullable=False),
        sa.Column('estimated_impact', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('evidence_ids', postgresql.ARRAY(sa.String(64)), nullable=False, default=[]),
        sa.Column('status', sa.String(32), nullable=False, default='provisional'),
        sa.Column('confidence', sa.Integer(), nullable=False, default=0),
        sa.Column('trust_score', sa.Numeric(5, 4), nullable=False, default=0.5),
        sa.Column('impact_score', sa.Numeric(10, 4), nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('challenge_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 100', name='ck_activity_confidence'),
        sa.CheckConstraint('trust_score >= 0 AND trust_score <= 1', name='ck_activity_trust_score'),
    )
    op.create_index('ix_ecosystem_activity_user', 'ecosystem_activity', ['user_id'])
    op.create_index('ix_ecosystem_activity_status', 'ecosystem_activity', ['status'])
    op.create_index('ix_ecosystem_activity_region', 'ecosystem_activity', ['region'])

    # Activity Evidence
    op.create_table(
        'ecosystem_activity_evidence',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('evidence_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('activity_id', sa.String(64), nullable=False, index=True),
        sa.Column('user_id', sa.String(64), nullable=False, index=True),
        sa.Column('data_type', sa.String(32), nullable=False),
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),
        sa.Column('commitment_hash', sa.String(64), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('access_log', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=[]),
    )
    op.create_index('ix_ecosystem_evidence_activity', 'ecosystem_activity_evidence', ['activity_id'])
    op.create_index('ix_ecosystem_evidence_user', 'ecosystem_activity_evidence', ['user_id'])

    # Oracle Attestations
    op.create_table(
        'oracle_attestation',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('attestation_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('activity_id', sa.String(64), nullable=False, index=True),
        sa.Column('node_id', sa.String(64), nullable=False, index=True),
        sa.Column('data_type', sa.String(32), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('commitment', sa.String(64), nullable=False),
        sa.Column('signature', sa.Text(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
    )
    op.create_index('ix_oracle_attestation_activity', 'oracle_attestation', ['activity_id'])
    op.create_index('ix_oracle_attestation_node', 'oracle_attestation', ['node_id'])

    # Impact Reports
    op.create_table(
        'oracle_impact_report',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('report_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('activity_id', sa.String(64), nullable=False, index=True),
        sa.Column('reporter', sa.String(64), nullable=False),
        sa.Column('data_type', sa.String(32), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('impact_hash', sa.String(64), nullable=False),
        sa.Column('evidence_commitment', sa.String(64), nullable=False),
        sa.Column('methodology_version', sa.Integer(), nullable=False, default=1),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('challenged', sa.Boolean(), nullable=False, default=False),
        sa.Column('challenge_deadline', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_oracle_report_activity', 'oracle_impact_report', ['activity_id'])

    # Impact Metrics
    op.create_table(
        'oracle_impact_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('activity_id', sa.String(64), nullable=False, index=True),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('impact_score', sa.Integer(), nullable=False),
        sa.Column('trust_multiplier', sa.Integer(), nullable=False, default=10000),
        sa.Column('survival_factor', sa.Integer(), nullable=False, default=10000),
        sa.Column('scarcity_factor', sa.Integer(), nullable=False, default=10000),
        sa.Column('challenge_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
    )
    op.create_index('ix_oracle_metrics_activity', 'oracle_impact_metrics', ['activity_id'])

    # Challenges
    op.create_table(
        'oracle_challenge',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('challenge_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('activity_id', sa.String(64), nullable=False, index=True),
        sa.Column('challenger', sa.String(64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('upheld', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_oracle_challenge_activity', 'oracle_challenge', ['activity_id'])

    # Oracle Nodes
    op.create_table(
        'oracle_node',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('node_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('public_key', sa.String(130), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False, default=1),
        sa.Column('reputation', sa.Integer(), nullable=False, default=50),
        sa.Column('stake', sa.Numeric(19, 4), nullable=False, default=0),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
    )
    op.create_index('ix_oracle_node_active', 'oracle_node', ['active'])

    # Trust Score Events
    op.create_table(
        'trust_score_event',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.String(64), nullable=False, index=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('impact', sa.Numeric(5, 4), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )
    op.create_index('ix_trust_score_event_user', 'trust_score_event', ['user_id'])
    op.create_index('ix_trust_score_event_type', 'trust_score_event', ['event_type'])

    # Trust Score Cache
    op.create_table(
        'trust_score_cache',
        sa.Column('user_id', sa.String(64), primary_key=True),
        sa.Column('score', sa.Numeric(5, 4), nullable=False),
        sa.Column('level', sa.String(16), nullable=False),
        sa.Column('multiplier_bps', sa.Integer(), nullable=False, default=10000),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Privacy Vault
    op.create_table(
        'privacy_vault_entry',
        sa.Column('entry_id', sa.String(64), primary_key=True),
        sa.Column('owner_id', sa.String(64), nullable=False, index=True),
        sa.Column('ciphertext', sa.LargeBinary(), nullable=False),
        sa.Column('commitment_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('access_log', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=[]),
    )
    op.create_index('ix_privacy_vault_owner', 'privacy_vault_entry', ['owner_id'])

    # Trust Score Events for EcoWallet
    op.create_table(
        'eco_wallet_trust_event',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(64), nullable=False, index=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('impact', sa.Numeric(5, 4), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
    )
    op.create_index('ix_eco_wallet_trust_event_user', 'eco_wallet_trust_event', ['user_id'])

    # EcoWallet Phase Gates
    op.create_table(
        'eco_wallet_phase_gate',
        sa.Column('phase', sa.Integer(), primary_key=True),
        sa.Column('active', sa.Boolean(), nullable=False, default=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activities_count', sa.Integer(), nullable=False, default=0),
        sa.Column('verified_count', sa.Integer(), nullable=False, default=0),
        sa.Column('discrepancy_count', sa.Integer(), nullable=False, default=0),
        sa.Column('oracle_uptime_sum', sa.Integer(), nullable=False, default=0),
        sa.Column('oracle_checks', sa.Integer(), nullable=False, default=0),
        sa.Column('emission_cap', sa.Numeric(19, 4), nullable=False, default=0),
    )

    # Add columns to existing ecowallet table for phase-gated transfers
    op.add_column('ecowallet', sa.Column('phase', sa.Integer(), nullable=False, default=0))
    op.add_column('ecowallet', sa.Column('kyc_status', sa.String(32), nullable=False, default='pending'))
    op.add_column('ecowallet', sa.Column('self_custody_enabled', sa.Boolean(), nullable=False, default=False))
    op.add_column('ecowallet', sa.Column('external_wallet_address', sa.String(130), nullable=True))
    op.add_column('ecowallet', sa.Column('transfer_enabled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_table('ecosystem_activity')
    op.drop_table('ecosystem_activity_evidence')
    op.drop_table('oracle_attestation')
    op.drop_table('oracle_impact_report')
    op.drop_table('oracle_impact_metrics')
    op.drop_table('oracle_challenge')
    op.drop_table('oracle_node')
    op.drop_table('trust_score_event')
    op.drop_table('trust_score_cache')
    op.drop_table('privacy_vault_entry')
    op.drop_table('eco_wallet_trust_event')
    op.drop_table('eco_wallet_phase_gate')
    op.drop_column('ecowallet', 'phase')
    op.drop_column('ecowallet', 'kyc_status')
    op.drop_column('ecowallet', 'self_custody_enabled')
    op.drop_column('ecowallet', 'external_wallet_address')
    op.drop_column('ecowallet', 'transfer_enabled_at')