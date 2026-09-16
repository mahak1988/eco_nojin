"""Phase 0: Complete financial schema — created_at on journal entries, FK constraints, walver version column

Revision ID: a1b2c3d4_phase0_financial_schema
Revises: f7b9c1d3e5a2
Create Date: 2026-09-15 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4_phase0_financial_schema"
down_revision: Union[str, Sequence[str], None] = "f7b9c1d3e5a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Add created_at to fin_journal_entry (was missing from initial migration)
    with op.batch_alter_table("fin_journal_entry", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("now()"))
        )
        batch_op.drop_constraint("fk_fin_journal_entry_batch_id", batch_op, type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_fin_journal_entry_batch_id",
            "fin_journal_batch",
            ["batch_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_fin_journal_entry_asset_entry", ["asset", "entry_type"], unique=False)

    # 2) Add version column to ecowallet for optimistic locking
    with op.batch_alter_table("ecowallet", schema=None) as batch_op:
        batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="0"))

    # 3) Add parent_id foreign key to fin_account
    with op.batch_alter_table("fin_account", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_fin_account_parent_id",
            "fin_account",
            ["parent_id"],
            ["id"],
        )

    # 4) Add unique constraint on user_id for ecowallet
    with op.batch_alter_table("ecowallet", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_ecowallet_user_id", ["user_id"])

    # 5) Add CHECK constraints for data integrity
    with op.batch_alter_table("inv_inventory_balance", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_inv_balance_non_negative", "on_hand >= 0 AND reserved >= 0 AND blocked >= 0 AND in_transit >= 0"
        )

    with op.batch_alter_table("inv_reservation", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_inv_reservation_qty_positive", "qty > 0"
        )

    with op.batch_alter_table("inv_stock_movement", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_inv_movement_qty_positive", "qty > 0"
        )

    with op.batch_alter_table("fin_journal_entry", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_fin_entry_amount_positive", "amount > 0"
        )
        batch_op.create_check_constraint(
            "ck_fin_entry_type_valid", "entry_type IN ('debit', 'credit')"
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("fin_journal_entry", schema=None) as batch_op:
        batch_op.drop_constraint("ck_fin_entry_type_valid", type_="check")
        batch_op.drop_constraint("ck_fin_entry_amount_positive", type_="check")
        batch_op.drop_index("ix_fin_journal_entry_asset_entry")
        batch_op.drop_constraint("fk_fin_journal_entry_batch_id", type_="foreignkey")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("ecowallet", schema=None) as batch_op:
        batch_op.drop_constraint("uq_ecowallet_user_id", type_="unique")
        batch_op.drop_column("version")

    with op.batch_alter_table("fin_account", schema=None) as batch_op:
        batch_op.drop_constraint("fk_fin_account_parent_id", type_="foreignkey")

    with op.batch_alter_table("inv_inventory_balance", schema=None) as batch_op:
        batch_op.drop_constraint("ck_inv_balance_non_negative", type_="check")

    with op.batch_alter_table("inv_reservation", schema=None) as batch_op:
        batch_op.drop_constraint("ck_inv_reservation_qty_positive", type_="check")

    with op.batch_alter_table("inv_stock_movement", schema=None) as batch_op:
        batch_op.drop_constraint("ck_inv_movement_qty_positive", type_="check")
