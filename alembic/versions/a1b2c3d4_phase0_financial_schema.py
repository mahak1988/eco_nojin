"""Phase 0: Complete financial schema — created_at on journal entries, FK constraints, walver version column

Revision ID: a1b2c3d4_phase0_financial_schema
Revises: f7b9c1d3e5a2
Create Date: 2026-09-15 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4_phase0_financial_schema"
down_revision: str | Sequence[str] | None = "f7b9c1d3e5a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Check if table exists (may not exist on village_hub branch)
    tables = inspector.get_table_names()
    if "fin_journal_entry" not in tables:
        return  # table doesn't exist (e.g., village_hub branch), skip

    # 1) Add created_at to fin_journal_entry (was missing from initial migration)
    with op.batch_alter_table("fin_journal_entry", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )

        # Only drop constraint if it exists
        fks = inspector.get_foreign_keys("fin_journal_entry")
        fk_names = [fk["name"] for fk in fks if fk["name"]]
        if "fk_fin_journal_entry_batch_id" in fk_names:
            batch_op.drop_constraint("fk_fin_journal_entry_batch_id", type_="foreignkey")

        batch_op.create_foreign_key(
            "fk_fin_journal_entry_batch_id",
            "fin_journal_batch",
            ["batch_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "ix_fin_journal_entry_asset_entry", ["asset", "entry_type"], unique=False
        )

    # 2) Add version column to ecowallet for optimistic locking
    if "ecowallet" in tables:
        with op.batch_alter_table("ecowallet", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("version", sa.Integer(), nullable=False, server_default="0")
            )

    # 3) Add parent_id foreign key to fin_account
    if "fin_account" in tables:
        with op.batch_alter_table("fin_account", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_fin_account_parent_id",
                "fin_account",
                ["parent_id"],
                ["id"],
            )

    # 4) Add unique constraint on user_id for ecowallet
    if "ecowallet" in tables:
        with op.batch_alter_table("ecowallet", schema=None) as batch_op:
            batch_op.create_unique_constraint("uq_ecowallet_user_id", ["user_id"])

    # 5) Add CHECK constraints for data integrity
    for table, constraint_name, constraint_sql in [
        (
            "inv_inventory_balance",
            "ck_inv_balance_non_negative",
            "on_hand >= 0 AND reserved >= 0 AND blocked >= 0 AND in_transit >= 0",
        ),
        ("inv_reservation", "ck_inv_reservation_qty_positive", "qty > 0"),
        ("inv_stock_movement", "ck_inv_movement_qty_positive", "qty > 0"),
        ("fin_journal_entry", "ck_fin_entry_amount_positive", "amount > 0"),
        ("fin_journal_entry", "ck_fin_entry_type_valid", "entry_type IN ('debit', 'credit')"),
    ]:
        if table in tables:
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.create_check_constraint(constraint_name, constraint_sql)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "fin_journal_entry" in tables:
        with op.batch_alter_table("fin_journal_entry", schema=None) as batch_op:
            # Only drop check constraints if they exist
            checks = inspector.get_check_constraints("fin_journal_entry")
            check_names = [c["name"] for c in checks if c["name"]]
            if "ck_fin_entry_type_valid" in check_names:
                batch_op.drop_constraint("ck_fin_entry_type_valid", type_="check")
            if "ck_fin_entry_amount_positive" in check_names:
                batch_op.drop_constraint("ck_fin_entry_amount_positive", type_="check")

            batch_op.drop_index("ix_fin_journal_entry_asset_entry")

            # Only drop FK if it exists
            fks = inspector.get_foreign_keys("fin_journal_entry")
            fk_names = [fk["name"] for fk in fks if fk["name"]]
            if "fk_fin_journal_entry_batch_id" in fk_names:
                batch_op.drop_constraint("fk_fin_journal_entry_batch_id", type_="foreignkey")

            batch_op.drop_column("created_at")

    if "ecowallet" in tables:
        with op.batch_alter_table("ecowallet", schema=None) as batch_op:
            uniques = inspector.get_unique_constraints("ecowallet")
            unique_names = [u["name"] for u in uniques if u["name"]]
            if "uq_ecowallet_user_id" in unique_names:
                batch_op.drop_constraint("uq_ecowallet_user_id", type_="unique")
            batch_op.drop_column("version")

    if "fin_account" in tables:
        with op.batch_alter_table("fin_account", schema=None) as batch_op:
            fks = inspector.get_foreign_keys("fin_account")
            fk_names = [fk["name"] for fk in fks if fk["name"]]
            if "fk_fin_account_parent_id" in fk_names:
                batch_op.drop_constraint("fk_fin_account_parent_id", type_="foreignkey")

    for table, constraint_name in [
        ("inv_inventory_balance", "ck_inv_balance_non_negative"),
        ("inv_reservation", "ck_inv_reservation_qty_positive"),
        ("inv_stock_movement", "ck_inv_movement_qty_positive"),
    ]:
        if table in tables:
            checks = inspector.get_check_constraints(table)
            check_names = [c["name"] for c in checks if c["name"]]
            if constraint_name in check_names:
                with op.batch_alter_table(table, schema=None) as batch_op:
                    batch_op.drop_constraint(constraint_name, type_="check")
