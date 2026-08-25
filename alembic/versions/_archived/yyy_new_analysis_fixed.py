"""Add new analysis and design result tables

Revision ID: yyy_new_analysis_fixed
Revises: b1c2d3e4f5a6
Create Date: 2026-08-23 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'yyy_new_analysis_fixed'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Topography ---
    op.create_table('topography_analysis_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('dem_path', sa.String(), nullable=True),
    sa.Column('analysis_types', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('slope_map_path', sa.String(), nullable=True),
    sa.Column('aspect_map_path', sa.String(), nullable=True),
    sa.Column('curvature_map_path', sa.String(), nullable=True),
    sa.Column('flow_direction_map_path', sa.String(), nullable=True),
    sa.Column('flow_accumulation_map_path', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topography_analysis_results_id'), 'topography_analysis_results', ['id'], unique=False)
    op.create_index(op.f('ix_topography_analysis_results_site_id'), 'topography_analysis_results', ['site_id'], unique=False)

    # --- Runoff ---
    op.create_table('runoff_calculation_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('precipitation_mm', sa.Float(), nullable=True),
    sa.Column('curve_number', sa.Float(), nullable=True),
    sa.Column('area_ha', sa.Float(), nullable=True),
    sa.Column('method', sa.String(), nullable=True),
    sa.Column('volume_m3', sa.Float(), nullable=True),
    sa.Column('peak_flow_m3s', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_runoff_calculation_results_id'), 'runoff_calculation_results', ['id'], unique=False)
    op.create_index(op.f('ix_runoff_calculation_results_site_id'), 'runoff_calculation_results', ['site_id'], unique=False)

    # --- Groundwater ---
    op.create_table('groundwater_model_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('model_type', sa.String(), nullable=True),
    sa.Column('transmissivity_m2day', sa.Float(), nullable=True),
    sa.Column('storativity', sa.Float(), nullable=True),
    sa.Column('pumping_rate_m3day', sa.Float(), nullable=True),
    sa.Column('observation_distance_m', sa.Float(), nullable=True),
    sa.Column('time_days', sa.Float(), nullable=True),
    sa.Column('drawdown_m', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groundwater_model_results_id'), 'groundwater_model_results', ['id'], unique=False)
    op.create_index(op.f('ix_groundwater_model_results_site_id'), 'groundwater_model_results', ['site_id'], unique=False)

    # --- Crop Water Requirement ---
    op.create_table('crop_water_req_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('crop_type', sa.String(), nullable=True),
    sa.Column('planting_date', sa.DateTime(), nullable=True),
    sa.Column('harvest_date', sa.DateTime(), nullable=True),
    sa.Column('seasonal_water_requirement_mm', sa.Float(), nullable=True),
    sa.Column('daily_et_crop_data', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_water_req_results_id'), 'crop_water_req_results', ['id'], unique=False)
    op.create_index(op.f('ix_crop_water_req_results_site_id'), 'crop_water_req_results', ['site_id'], unique=False)

    # --- Structure Design ---
    op.create_table('structure_design_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('design_id', sa.String(), nullable=True),
    sa.Column('site_location_lat', sa.Float(), nullable=True),
    sa.Column('site_location_lon', sa.Float(), nullable=True),
    sa.Column('structure_type', sa.String(), nullable=True),
    sa.Column('area_ha', sa.Float(), nullable=True),
    sa.Column('max_flow_m3s', sa.Float(), nullable=True),
    sa.Column('geometry_geojson', sa.Text(), nullable=True),
    sa.Column('material_estimate', sa.Text(), nullable=True),
    sa.Column('cost_estimate_usd', sa.Float(), nullable=True),
    sa.Column('design_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('design_id')
    )
    op.create_index(op.f('ix_structure_design_results_design_id'), 'structure_design_results', ['design_id'], unique=False)
    op.create_index(op.f('ix_structure_design_results_id'), 'structure_design_results', ['id'], unique=False)

    # --- Irrigation Design ---
    op.create_table('irrigation_design_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('design_id', sa.String(), nullable=True),
    sa.Column('site_location_lat', sa.Float(), nullable=True),
    sa.Column('site_location_lon', sa.Float(), nullable=True),
    sa.Column('crop_type', sa.String(), nullable=True),
    sa.Column('area_ha', sa.Float(), nullable=True),
    sa.Column('irrigation_type', sa.String(), nullable=True),
    sa.Column('layout_geojson', sa.Text(), nullable=True),
    sa.Column('equipment_list', sa.Text(), nullable=True),
    sa.Column('irrigation_schedule', sa.Text(), nullable=True),
    sa.Column('design_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('design_id')
    )
    op.create_index(op.f('ix_irrigation_design_results_design_id'), 'irrigation_design_results', ['design_id'], unique=False)
    op.create_index(op.f('ix_irrigation_design_results_id'), 'irrigation_design_results', ['id'], unique=False)

    # --- Calibration ---
    op.create_table('calibration_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_name', sa.String(), nullable=True),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('calibrated_parameters', sa.Text(), nullable=True),
    sa.Column('best_objective_value', sa.Float(), nullable=True),
    sa.Column('history', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calibration_results_id'), 'calibration_results', ['id'], unique=False)
    op.create_index(op.f('ix_calibration_results_model_name'), 'calibration_results', ['model_name'], unique=False)
    op.create_index(op.f('ix_calibration_results_site_id'), 'calibration_results', ['site_id'], unique=False)


def downgrade() -> None:
    op.drop_table('calibration_results')
    op.drop_table('irrigation_design_results')
    op.drop_table('structure_design_results')
    op.drop_table('crop_water_req_results')
    op.drop_table('groundwater_model_results')
    op.drop_table('runoff_calculation_results')
    op.drop_table('topography_analysis_results')
