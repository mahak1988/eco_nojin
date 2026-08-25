"""Phase 1-3: Complete Land, Soil, Climate, Water Tables

Revision ID: phase1_2_3_complete_v2
Revises: f6a2b3c4d5e6
Create Date: 2026-08-23 14:55:53

This migration creates all missing tables for Phase 1-3:
- Phase 1: land_capability_assessments
- Phase 2: soil_profiles, climate_data
- Phase 3: surface_water_sources, groundwater_data, watershed_data

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase1_2_3_complete_v2'
down_revision = 'f6a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # Phase 1: Land Capability Assessments
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'land_capability_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('capability_class', sa.String(10), nullable=False),
        sa.Column('subclass', sa.String(10), nullable=True),
        sa.Column('limiting_factors', postgresql.JSONB(), nullable=True),
        sa.Column('suitable_land_uses', postgresql.JSONB(), nullable=True),
        sa.Column('assessment_method', sa.String(50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('assessed_by', sa.String(100), nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_capability_land_id', 'land_capability_assessments', ['land_profile_id'])
    
    # ═══════════════════════════════════════════════════════════════════
    # Phase 2: Soil Profiles & Climate Data
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'soil_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('depth_min', sa.Float(), nullable=False),
        sa.Column('depth_max', sa.Float(), nullable=False),
        sa.Column('texture_class', sa.String(30), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('ec_dsm', sa.Float(), nullable=True),
        sa.Column('cec_mmolc_kg', sa.Float(), nullable=True),
        sa.Column('organic_carbon_g_kg', sa.Float(), nullable=True),
        sa.Column('nitrogen_g_kg', sa.Float(), nullable=True),
        sa.Column('phosphorus_g_kg', sa.Float(), nullable=True),
        sa.Column('potassium_g_kg', sa.Float(), nullable=True),
        sa.Column('salinity_class', sa.String(30), nullable=True),
        sa.Column('sodicity_class', sa.String(30), nullable=True),
        sa.Column('water_holding_capacity', sa.Float(), nullable=True),
        sa.Column('drainage_class', sa.String(30), nullable=True),
        sa.Column('biological_condition', sa.String(30), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_soil_profiles_land_id', 'soil_profiles', ['land_profile_id'])
    
    op.create_table(
        'climate_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('data_date', sa.Date(), nullable=False),
        sa.Column('temp_max_c', sa.Float(), nullable=True),
        sa.Column('temp_min_c', sa.Float(), nullable=True),
        sa.Column('temp_mean_c', sa.Float(), nullable=True),
        sa.Column('rainfall_mm', sa.Float(), nullable=True),
        sa.Column('humidity_percent', sa.Float(), nullable=True),
        sa.Column('wind_speed_m_s', sa.Float(), nullable=True),
        sa.Column('radiation_mj_m2', sa.Float(), nullable=True),
        sa.Column('et0_mm', sa.Float(), nullable=True),
        sa.Column('drought_index', sa.Float(), nullable=True),
        sa.Column('heat_stress_index', sa.Float(), nullable=True),
        sa.Column('frost_risk', sa.Float(), nullable=True),
        sa.Column('koppen_class', sa.String(10), nullable=True),
        sa.Column('aridity_index', sa.Float(), nullable=True),
        sa.Column('climate_scenario', sa.String(50), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_climate_data_land_date', 'climate_data', ['land_profile_id', 'data_date'])
    
    # ═══════════════════════════════════════════════════════════════════
    # Phase 3: Water, Watershed, Groundwater
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'surface_water_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('location', postgresql.JSONB(), nullable=True),
        sa.Column('flow_rate_m3_s', sa.Float(), nullable=True),
        sa.Column('seasonal_variation', postgresql.JSONB(), nullable=True),
        sa.Column('quality_class', sa.String(30), nullable=True),
        sa.Column('accessibility', sa.String(50), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_surface_water_land_id', 'surface_water_sources', ['land_profile_id'])
    
    op.create_table(
        'groundwater_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('well_depth_m', sa.Float(), nullable=True),
        sa.Column('water_table_depth_m', sa.Float(), nullable=True),
        sa.Column('hydraulic_conductivity_m_s', sa.Float(), nullable=True),
        sa.Column('recharge_rate_mm_yr', sa.Float(), nullable=True),
        sa.Column('water_quality_class', sa.String(30), nullable=True),
        sa.Column('abstraction_rate_m3_yr', sa.Float(), nullable=True),
        sa.Column('sustainability_index', sa.Float(), nullable=True),
        sa.Column('aquifer_type', sa.String(30), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_groundwater_land_id', 'groundwater_data', ['land_profile_id'])
    
    op.create_table(
        'watershed_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('land_profile_id', sa.Integer(), nullable=False),
        sa.Column('watershed_name', sa.String(200), nullable=True),
        sa.Column('watershed_boundary', postgresql.JSONB(), nullable=True),
        sa.Column('drainage_network', postgresql.JSONB(), nullable=True),
        sa.Column('runoff_coefficient', sa.Float(), nullable=True),
        sa.Column('flood_risk_level', sa.String(30), nullable=True),
        sa.Column('sediment_yield_t_yr', sa.Float(), nullable=True),
        sa.Column('erosion_rate_t_ha_yr', sa.Float(), nullable=True),
        sa.Column('recharge_rate_mm_yr', sa.Float(), nullable=True),
        sa.Column('groundwater_contribution', sa.Float(), nullable=True),
        sa.Column('interventions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['land_profile_id'], ['land_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_watershed_land_id', 'watershed_data', ['land_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_watershed_land_id', table_name='watershed_data')
    op.drop_table('watershed_data')
    op.drop_index('ix_groundwater_land_id', table_name='groundwater_data')
    op.drop_table('groundwater_data')
    op.drop_index('ix_surface_water_land_id', table_name='surface_water_sources')
    op.drop_table('surface_water_sources')
    op.drop_index('ix_climate_data_land_date', table_name='climate_data')
    op.drop_table('climate_data')
    op.drop_index('ix_soil_profiles_land_id', table_name='soil_profiles')
    op.drop_table('soil_profiles')
    op.drop_index('ix_capability_land_id', table_name='land_capability_assessments')
    op.drop_table('land_capability_assessments')
