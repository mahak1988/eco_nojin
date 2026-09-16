"""Phase 0: Add commerce models (order state machine, payment intents, settlements, invoices)

Revision ID: b2c3d4e5_phase0_commerce_models
Revises: a1b2c3d4_phase0_financial_schema
Create Date: 2026-09-15 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5_phase0_commerce_models"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4_phase0_financial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("com_order",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_number", sa.String(length=50), nullable=False),
        sa.Column("buyer_id", sa.String(), nullable=False),
        sa.Column("seller_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("subtotal", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("platform_fee", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("landscape_fee", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IRR"),
        sa.Column("shipping_address", sa.JSON(), nullable=True),
        sa.Column("tracking_code", sa.String(length=100), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    with op.batch_alter_table("com_order", schema=None) as batch_op:
        batch_op.create_index("ix_com_order_status", ["status"])
        batch_op.create_index("ix_com_order_buyer", ["buyer_id"])
        batch_op.create_index("ix_com_order_seller_status", ["seller_id", "status"])
        batch_op.create_index(batch_op.f("ix_com_order_idempotency_key"), ["idempotency_key"], unique=True)

    op.create_table("com_order_item",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=False),
        sa.Column("sku_id", sa.Integer(), nullable=True),
        sa.Column("sku_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("quantity", Numeric(18, 4), nullable=False),
        sa.Column("unit_price", Numeric(18, 4), nullable=False),
        sa.Column("line_total", Numeric(18, 4), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.Column("reservation_id", sa.Integer(), nullable=True),
        sa.Column("fulfilled_qty", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["com_order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sku_id"], ["inv_sku.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inv_warehouse.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["inv_reservation.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("com_order_item", schema=None) as batch_op:
        batch_op.create_index("ix_com_order_item_order_id", ["order_id"])
        batch_op.create_index("ix_com_order_item_sku_id", ["sku_id"])

    op.create_table("com_payment_intent",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=False),
        sa.Column("buyer_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="wallet"),
        sa.Column("amount", Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IRR"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requires_action"),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("payment_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["com_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("com_payment_intent", schema=None) as batch_op:
        batch_op.create_index("ix_com_payment_order", ["order_id"])
        batch_op.create_index("ix_com_payment_buyer", ["buyer_id"])
        batch_op.create_index("ix_com_payment_provider", ["provider"])
        batch_op.create_index("ix_com_payment_status", ["status"])

    op.create_table("com_settlement",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=False),
        sa.Column("seller_id", sa.String(), nullable=False),
        sa.Column("amount", Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IRR"),
        sa.Column("commission_fee", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("landscape_fee", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("journal_batch_id", sa.Integer(), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["com_order.id"]),
        sa.ForeignKeyConstraint(["journal_batch_id"], ["fin_journal_batch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("com_settlement", schema=None) as batch_op:
        batch_op.create_index("ix_com_settlement_seller", ["seller_id"])
        batch_op.create_index("ix_com_settlement_status", ["status"])

    op.create_table("com_invoice",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("seller_id", sa.String(), nullable=False),
        sa.Column("buyer_id", sa.String(), nullable=False),
        sa.Column("subtotal", Numeric(18, 4), nullable=False),
        sa.Column("tax_amount", Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total", Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IRR"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["com_order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("com_invoice", schema=None) as batch_op:
        batch_op.create_index("ix_com_invoice_number", ["invoice_number"])
        batch_op.create_index("ix_com_invoice_seller", ["seller_id"])

    op.create_table("com_invoice_line",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("invoice_id", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", Numeric(18, 4), nullable=False),
        sa.Column("unit_price", Numeric(18, 4), nullable=False),
        sa.Column("line_total", Numeric(18, 4), nullable=False),
        sa.Column("tax_rate", Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("tax_amount", Numeric(18, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["invoice_id"], ["com_invoice.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("com_invoice_line")
    with op.batch_alter_table("com_invoice", schema=None) as batch_op:
        batch_op.drop_index("ix_com_invoice_seller")
        batch_op.drop_index("ix_com_invoice_number")
    op.drop_table("com_invoice")
    with op.batch_alter_table("com_settlement", schema=None) as batch_op:
        batch_op.drop_index("ix_com_settlement_status")
        batch_op.drop_index("ix_com_settlement_seller")
    op.drop_table("com_settlement")
    with op.batch_alter_table("com_payment_intent", schema=None) as batch_op:
        batch_op.drop_index("ix_com_payment_status")
        batch_op.drop_index("ix_com_payment_provider")
        batch_op.drop_index("ix_com_payment_buyer")
        batch_op.drop_index("ix_com_payment_order")
    op.drop_table("com_payment_intent")
    with op.batch_alter_table("com_order_item", schema=None) as batch_op:
        batch_op.drop_index("ix_com_order_item_sku_id")
        batch_op.drop_index("ix_com_order_item_order_id")
    op.drop_table("com_order_item")
    with op.batch_alter_table("com_order", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_com_order_idempotency_key"))
        batch_op.drop_index("ix_com_order_seller_status")
        batch_op.drop_index("ix_com_order_buyer")
        batch_op.drop_index("ix_com_order_status")
    op.drop_table("com_order")
