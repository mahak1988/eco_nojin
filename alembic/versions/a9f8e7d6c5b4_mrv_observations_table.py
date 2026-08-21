"""mrv_observations table (EM-01 three-level MRV)

Revision ID: a9f8e7d6c5b4
Revises: f6a2b3c4d5e6
Create Date: 2026-08-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a9f8e7d6c5b4"
down_revision = "f6a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create mrv_observations (satellite/iot/citizen observations)."""
    op.create_table(
        "mrv_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.String(length=200), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("sensor_type", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("data_source", sa.String(length=20), server_default="real", nullable=False),
        sa.Column("qa_status", sa.String(length=20), server_default="ok", nullable=False),
        sa.Column("qa_message", sa.String(length=500), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("mrv_observations", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mrv_observations_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_mrv_observations_site_id"), ["site_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_mrv_observations_level"), ["level"], unique=False)
        batch_op.create_index(batch_op.f("ix_mrv_observations_source"), ["source"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_mrv_observations_observed_at"), ["observed_at"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_mrv_observations_created_at"), ["created_at"], unique=False
        )


def downgrade() -> None:
    """Drop mrv_observations."""
    with op.batch_alter_table("mrv_observations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mrv_observations_created_at"))
        batch_op.drop_index(batch_op.f("ix_mrv_observations_observed_at"))
        batch_op.drop_index(batch_op.f("ix_mrv_observations_source"))
        batch_op.drop_index(batch_op.f("ix_mrv_observations_level"))
        batch_op.drop_index(batch_op.f("ix_mrv_observations_site_id"))
        batch_op.drop_index(batch_op.f("ix_mrv_observations_id"))
    op.drop_table("mrv_observations")