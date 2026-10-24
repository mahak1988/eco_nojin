"""Create the six engine-result persistence tables.

Revision ID: 20260927_010000_engine_result_tables
Revises: 20260926_020000_sponsorships
Create Date: 2026-09-27 01:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "20260927_010000_engine_result_tables"
down_revision = "20260926_020000_sponsorships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name, cols in (
        (
            "runoff_calculation_results",
            [
                ("id", sa.Integer(), True),
                ("land_profile_id", sa.String(36), False),
                ("method", sa.String(50), False),
                ("rainfall_mm", sa.Numeric(10, 2), False),
                ("runoff_mm", sa.Numeric(10, 2), False),
                ("runoff_volume_m3", sa.Numeric(14, 2), True),
                ("cn_number", sa.Float(), True),
                ("peak_flow_cms", sa.Float(), True),
                ("time_of_concentration_min", sa.Float(), True),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
        (
            "groundwater_model_results",
            [
                ("id", sa.Integer(), True),
                ("land_profile_id", sa.String(36), True),
                ("model_name", sa.String(100), False),
                ("drawdown_m", sa.Numeric(10, 4), False),
                ("hydraulic_conductivity", sa.Float(), True),
                ("transmissivity", sa.Float(), True),
                ("storativity", sa.Float(), True),
                ("well_radius_m", sa.Float(), True),
                ("pumping_rate_m3_day", sa.Numeric(14, 2), True),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
        (
            "crop_water_req_results",
            [
                ("id", sa.Integer(), True),
                ("land_profile_id", sa.String(36), False),
                ("crop_type", sa.String(100), False),
                ("et_crop_mm", sa.Numeric(10, 2), False),
                ("seasonal_water_mm", sa.Numeric(10, 2), False),
                ("kc_average", sa.Float(), True),
                ("growing_days", sa.Integer(), True),
                ("irrigation_requirement_mm", sa.Numeric(10, 2), True),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
        (
            "structure_design_results",
            [
                ("id", sa.Integer(), True),
                ("land_profile_id", sa.String(36), False),
                ("structure_type", sa.String(50), False),
                ("design_method", sa.String(50), False),
                ("crest_length_m", sa.Numeric(8, 2), False),
                ("crest_height_m", sa.Numeric(8, 2), False),
                ("storage_m3", sa.Numeric(14, 2), False),
                ("freeboard_m", sa.Numeric(6, 2), True),
                ("spillway_discharge_cms", sa.Float(), True),
                ("factor_of_safety", sa.Float(), True),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
        (
            "irrigation_design_results",
            [
                ("id", sa.Integer(), True),
                ("land_profile_id", sa.String(36), False),
                ("system_type", sa.String(50), False),
                ("method", sa.String(50), False),
                ("area_ha", sa.Numeric(10, 2), False),
                ("discharge_lps", sa.Numeric(8, 2), False),
                ("emitter_spacing_m", sa.Float(), True),
                ("operating_pressure_bar", sa.Float(), True),
                ("total_demand_m3_day", sa.Numeric(14, 2), True),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
        (
            "calibration_results",
            [
                ("id", sa.Integer(), True),
                ("model_name", sa.String(100), False),
                ("objective_function", sa.String(100), False),
                ("best_parameters", sa.JSON(), False),
                ("rmse", sa.Float(), False),
                ("nash_sutcliffe", sa.Float(), True),
                ("iterations", sa.Integer(), True),
                ("converged", sa.Integer(), False),
                ("metadata_", sa.JSON(), True),
                ("computed_at", sa.DateTime(timezone=True), True),
            ],
        ),
    ):
        fks = {}
        if table_name != "calibration_results":
            fks = {"land_profile_id": ("land_profiles", "id")}

        columns = []
        for i, (name, typ, _nullable) in enumerate(cols):
            if name in fks:
                ref_table, ref_col = fks[name]
                col = sa.Column(name, typ, sa.ForeignKey(f"{ref_table}.{ref_col}"), primary_key=(i == 0))
            else:
                col = sa.Column(name, typ, primary_key=(i == 0))
            columns.append(col)
        op.create_table(table_name, *columns)


def downgrade() -> None:
    for table_name in (
        "calibration_results",
        "irrigation_design_results",
        "structure_design_results",
        "crop_water_req_results",
        "groundwater_model_results",
        "runoff_calculation_results",
    ):
        op.drop_table(table_name)
