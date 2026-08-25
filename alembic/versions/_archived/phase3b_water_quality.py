"""Phase 3B: Water Quality, Aquifer, Stream Gauge Tables

Revision ID: phase3b_water_quality
Revises: phase1_2_3_complete_v2
Create Date: 2026-08-23

Adds missing Phase 3 tables:
- water_quality
- aquifer_data  
- stream_gauge_data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase3b_water_quality'
down_revision = 'merge_heads_phase123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════
    # Water Quality Measurements
    # ═══════════════════════════════════════════════════════════════
    
    op.create_table(
        'water_quality',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),  # "groundwater", "surface", "spring"
        sa.Column('sample_date', sa.Date(), nullable=False),
        sa.Column('tds_mg_l', sa.Float(), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('ec_dsm_cm', sa.Float(), nullable=True),
        sa.Column('chloride_mg_l', sa.Float(), nullable=True),
        sa.Column('sulfate_mg_l', sa.Float(), nullable=True),
        sa.Column('nitrate_mg_l', sa.Float(), nullable=True),
        sa.Column('fluoride_mg_l', sa.Float(), nullable=True),
        sa.Column('iron_mg_l', sa.Float(), nullable=True),
        sa.Column('hardness_mg_l', sa.Float(), nullable=True),
        sa.Column('coliform_cfu_100ml', sa.Integer(), nullable=True),
        sa.Column('quality_class', sa.String(30), nullable=True),
        sa.Column('suitable_for', postgresql.JSONB(), nullable=True),
        sa.Column('laboratory', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_water_quality_land_date', 'water_quality', ['land_profile_id', 'sample_date'])
    
    # ═══════════════════════════════════════════════════════════════
    # Aquifer Data
    # ═══════════════════════════════════════════════════════════════
    
    op.create_table(
        'aquifer_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('aquifer_name', sa.String(200), nullable=True),
        sa.Column('aquifer_type', sa.String(30), nullable=False),  # unconfined, confined, etc.
        sa.Column('thickness_m', sa.Float(), nullable=True),
        sa.Column('depth_to_top_m', sa.Float(), nullable=True),
        sa.Column('lithology', sa.String(200), nullable=True),
        sa.Column('hydraulic_conductivity_m_s', sa.Float(), nullable=True),
        sa.Column('transmissivity_m2_day', sa.Float(), nullable=True),
        sa.Column('storativity', sa.Float(), nullable=True),
        sa.Column('specific_yield', sa.Float(), nullable=True),
        sa.Column('porosity', sa.Float(), nullable=True),
        sa.Column('recharge_zone', postgresql.JSONB(), nullable=True),
        sa.Column('vulnerable_to_pollution', sa.Boolean(), default=False),
        sa.Column('assessment_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_aquifer_data_land_id', 'aquifer_data', ['land_profile_id'])
    
    # ═══════════════════════════════════════════════════════════════
    # Stream Gauge Data
    # ═══════════════════════════════════════════════════════════════
    
    op.create_table(
        'stream_gauge_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('station_name', sa.String(200), nullable=True),
        sa.Column('station_code', sa.String(50), nullable=True),
        sa.Column('river_name', sa.String(200), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('discharge_m3_s', sa.Float(), nullable=True),
        sa.Column('water_level_m', sa.Float(), nullable=True),
        sa.Column('velocity_m_s', sa.Float(), nullable=True),
        sa.Column('cross_section_m2', sa.Float(), nullable=True),
        sa.Column('sediment_load_kg_s', sa.Float(), nullable=True),
        sa.Column('water_temperature_c', sa.Float(), nullable=True),
        sa.Column('measurement_method', sa.String(100), nullable=True),
        sa.Column('data_source', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stream_gauge_land_date', 'stream_gauge_data', 
                    ['land_profile_id', 'measurement_date'])


def downgrade() -> None:
    op.drop_index('ix_stream_gauge_land_date', table_name='stream_gauge_data')
    op.drop_table('stream_gauge_data')
    op.drop_index('ix_aquifer_data_land_id', table_name='aquifer_data')
    op.drop_table('aquifer_data')
    op.drop_index('ix_water_quality_land_date', table_name='water_quality')
    op.drop_table('water_quality')
