"""add land tables

Revision ID: land_001
Revises: <previous_revision>
Create Date: 2026-08-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'land_001'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """ارتقاء دیتابیس"""
    
    # Create land_profiles table
    op.create_table(
        'land_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('location_lat', sa.Float, nullable=False),
        sa.Column('location_lon', sa.Float, nullable=False),
        sa.Column('area_hectares', sa.Float, nullable=True),
        sa.Column('boundary_geojson', postgresql.JSONB, nullable=True),
        sa.Column('dem_source', sa.String(100), nullable=True),
        sa.Column('dem_resolution_m', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('created_by', sa.String(100), nullable=True),
    )
    
    # Create terrain_analyses table
    op.create_table(
        'terrain_analyses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('land_profiles.id'), nullable=False),
        sa.Column('terrain_type', sa.String(50), nullable=False),
        sa.Column('elevation_min', sa.Float, nullable=False),
        sa.Column('elevation_max', sa.Float, nullable=False),
        sa.Column('elevation_mean', sa.Float, nullable=False),
        sa.Column('slope_mean', sa.Float, nullable=False),
        sa.Column('slope_max', sa.Float, nullable=False),
        sa.Column('aspect_dominant', sa.String(10), nullable=False),
        sa.Column('roughness_index', sa.Float, nullable=False),
        sa.Column('curvature_mean', sa.Float, nullable=False),
        sa.Column('analyzed_at', sa.DateTime, server_default=sa.text('now()')),
    )
    
    # Create drainage_analyses table
    op.create_table(
        'drainage_analyses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('land_profiles.id'), nullable=False),
        sa.Column('drainage_pattern', sa.String(50), nullable=True),
        sa.Column('drainage_density', sa.Float, nullable=True),
        sa.Column('stream_order', sa.Integer, nullable=True),
        sa.Column('flow_accumulation', postgresql.JSONB, nullable=True),
        sa.Column('watershed_area_km2', sa.Float, nullable=True),
        sa.Column('time_of_concentration_hours', sa.Float, nullable=True),
        sa.Column('analyzed_at', sa.DateTime, server_default=sa.text('now()')),
    )
    
    # Create capability_assessments table
    op.create_table(
        'capability_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('land_profiles.id'), nullable=False),
        sa.Column('capability_class', sa.String(10), nullable=False),
        sa.Column('subclass', sa.String(10), nullable=True),
        sa.Column('limiting_factors', postgresql.JSONB, nullable=False),
        sa.Column('suitable_uses', postgresql.JSONB, nullable=False),
        sa.Column('constraints', postgresql.JSONB, nullable=False),
        sa.Column('recommendations', postgresql.JSONB, nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('assessed_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('assessed_by', sa.String(100), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_land_profiles_location', 'land_profiles', ['location_lat', 'location_lon'])
    op.create_index('ix_terrain_analyses_profile', 'terrain_analyses', ['profile_id'])
    op.create_index('ix_drainage_analyses_profile', 'drainage_analyses', ['profile_id'])
    op.create_index('ix_capability_assessments_profile', 'capability_assessments', ['profile_id'])


def downgrade():
    """بازگشت دیتابیس"""
    op.drop_table('capability_assessments')
    op.drop_table('drainage_analyses')
    op.drop_table('terrain_analyses')
    op.drop_table('land_profiles')