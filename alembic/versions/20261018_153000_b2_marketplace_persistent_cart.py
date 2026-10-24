"""B2: Marketplace persistent cart tables.

Adds persistent DB-backed cart for logged-in buyers (KN-23).
The in-memory ``OrderManager._carts`` is replaced by ``mkt_carts`` and
``mkt_cart_items`` tables with full session/CRUD support.

Tables:
* ``mkt_carts`` - one per buyer (``buyer_id`` unique), tracks subtotal/count
* ``mkt_cart_items`` - line items per cart, quantity + unit_price snapshot

Guarded & idempotent: creates only if missing; offline (``--sql``) renders all.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261018_153000_b2_marketplace_persistent_cart"
down_revision: str | None = "20261017_153000_p71_kyc_digital_identity"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE_CARTS = "mkt_carts"
_TABLE_ITEMS = "mkt_cart_items"


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(table)


def _column_exists(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def _create_carts_table() -> None:
    op.create_table(
        _TABLE_CARTS,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, default=0.0),
        sa.Column("item_count", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def _create_items_table() -> None:
    op.create_table(
        _TABLE_ITEMS,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "cart_id",
            sa.String(36),
            sa.ForeignKey(f"{_TABLE_CARTS}.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("product_id", sa.String(36), nullable=False, index=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_mkt_cart_items_cart_product"),
    )


def upgrade() -> None:
    if context.is_offline_mode():
        _create_carts_table()
        _create_items_table()
        return

    if not _table_exists(_TABLE_CARTS):
        _create_carts_table()

    if not _table_exists(_TABLE_ITEMS):
        _create_items_table()


def downgrade() -> None:
    if context.is_offline_mode():
        return

    # Drop in reverse dependency order
    if _table_exists(_TABLE_ITEMS):
        op.drop_table(_TABLE_ITEMS)
    if _table_exists(_TABLE_CARTS):
        op.drop_table(_TABLE_CARTS)