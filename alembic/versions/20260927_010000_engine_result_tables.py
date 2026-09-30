"""Migration: add the six engine result tables.

Purely additive. No existing table is touched, no column is altered, no data is
read or written. The tables are created empty, which is correct: they have never
existed, so there is nothing to migrate.

Parent is the most recent head, 20260926_020000_sponsorships. Note that the
repository already carries eight heads, so ``alembic upgrade head`` does not
resolve while ``alembic upgrade heads`` does. That condition predates this
migration, and merging the heads is a decision about which histories are real
rather than something a new migration should decide.

Column sets are those the shadowed ``database/models/database_models.py``
declared. None was verified against a caller, because there were none.
"""

revision = "20260927_010000_engine_result_tables"
down_revision = "20260926_020000_sponsorships"
branch_labels = None
depends_on = None

import sqlalchemy as sa

from alembic import op

# (table, columns, [(index_name, indexed_column), ...])
TABLE_SPECS = [
    (
        "runoff_calculation_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("site_id", sa.String(), index=True),
            sa.Column("precipitation_mm", sa.Float()),
            sa.Column("curve_number", sa.Float()),
            sa.Column("area_ha", sa.Float()),
            sa.Column("method", sa.String()),
            sa.Column("volume_m3", sa.Float()),
            sa.Column("peak_flow_m3s", sa.Float()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
    (
        "groundwater_model_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("site_id", sa.String(), index=True),
            sa.Column("model_type", sa.String()),
            sa.Column("transmissivity_m2day", sa.Float()),
            sa.Column("storativity", sa.Float()),
            sa.Column("pumping_rate_m3day", sa.Float()),
            sa.Column("observation_distance_m", sa.Float()),
            sa.Column("time_days", sa.Float()),
            sa.Column("drawdown_m", sa.Float()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
    (
        "crop_water_req_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("site_id", sa.String(), index=True),
            sa.Column("crop_type", sa.String()),
            sa.Column("planting_date", sa.DateTime()),
            sa.Column("harvest_date", sa.DateTime()),
            sa.Column("seasonal_water_requirement_mm", sa.Float()),
            sa.Column("daily_et_crop_data", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
    (
        "structure_design_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("design_id", sa.String(), unique=True, index=True),
            sa.Column("site_location_lat", sa.Float()),
            sa.Column("site_location_lon", sa.Float()),
            sa.Column("structure_type", sa.String()),
            sa.Column("area_ha", sa.Float()),
            sa.Column("max_flow_m3s", sa.Float()),
            sa.Column("geometry_geojson", sa.Text()),
            sa.Column("material_estimate", sa.Text()),
            sa.Column("cost_estimate_usd", sa.Float()),
            sa.Column("design_summary", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
    (
        "irrigation_design_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("design_id", sa.String(), unique=True, index=True),
            sa.Column("site_location_lat", sa.Float()),
            sa.Column("site_location_lon", sa.Float()),
            sa.Column("crop_type", sa.String()),
            sa.Column("area_ha", sa.Float()),
            sa.Column("irrigation_type", sa.String()),
            sa.Column("layout_geojson", sa.Text()),
            sa.Column("equipment_list", sa.Text()),
            sa.Column("irrigation_schedule", sa.Text()),
            sa.Column("design_summary", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
    (
        "calibration_results",
        [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("model_name", sa.String(), index=True),
            sa.Column("site_id", sa.String(), index=True),
            sa.Column("calibrated_parameters", sa.Text()),
            sa.Column("best_objective_value", sa.Float()),
            sa.Column("history", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        ],
        [],
    ),
]


def upgrade() -> None:
    for table, columns, _indexes in TABLE_SPECS:
        op.create_table(table, *columns)


def downgrade() -> None:
    for table, _columns, _indexes in reversed(TABLE_SPECS):
        op.drop_table(table)
