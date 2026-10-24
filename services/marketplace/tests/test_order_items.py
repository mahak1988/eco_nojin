"""Regression tests for P1-6: marketplace order line items.

Before this fix ``create_order`` priced the basket into a local list, committed
the order header, and only then decremented stock. The priced list was dropped,
so a reloaded order carried nothing but money totals, and a failed stock
decrement left a committed order behind. These tests pin both halves down.

Runs on an in-memory SQLite database with the shared Base metadata, async to
match the async service layer.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from database.base import Base
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplaceProduct,
)
from services.marketplace.service import MarketplaceService


@pytest.fixture
async def db_session():
    """Provide an async in-memory SQLite session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def service(db_session):
    return MarketplaceService(db_session)


async def _seed_product(
    service: MarketplaceService,
    *,
    seller_id: str | None = None,
    name: str = "عسل natural",
    price: Decimal = Decimal("350000"),
    stock: int = 10,
    unit: str = "piece",
) -> tuple[str, str]:
    """Register + verify a seller and create an approved product.

    Returns plain ids: after a rollback every ORM attribute on this session is
    expired, so any later access would need IO from a sync context.
    """
    if seller_id is None:
        seller = await service.register_seller(
            user_id="user_1",
            village_id="village_1",
            shop_name="فروشگاه تست",
        )
        seller_id = str(seller.id)
        await service.verify_seller(seller_id, "manager_1")

    product = await service.create_product(
        seller_id=seller_id,
        name=name,
        price=price,
        village_id="village_1",
        category="food",
        stock=stock,
        unit=unit,
    )
    return seller_id, str(product.id)


async def _reload_product(db_session, product_id: str) -> MarketplaceProduct:
    result = await db_session.execute(
        select(MarketplaceProduct).where(MarketplaceProduct.id == product_id)
    )
    return result.scalar_one()


# --- items survive a reload ---


@pytest.mark.asyncio
async def test_order_items_persist_and_reload(service, db_session):
    """(a) A successful order keeps its basket, with fresh snapshots."""
    seller_id, honey_id = await _seed_product(
        service, name="عسل طبیعی", price=Decimal("350000"), stock=10
    )
    _, walnut_id = await _seed_product(
        service,
        seller_id=seller_id,
        name="گردوی ارزان",
        price=Decimal("1200000"),
        stock=5,
        unit="kg",
    )

    order = await service.create_order(
        buyer_id="buyer_1",
        items=[
            {"product_id": honey_id, "quantity": 2},
            {"product_id": walnut_id, "quantity": 1, "price": 1200000},
        ],
        village_id="village_1",
        shipping_address={"city": "کرمانشاه", "address": "..."},
    )

    # The order itself is unchanged by this fix.
    assert order.subtotal == Decimal("1900000")
    assert order.total > order.subtotal

    # (a) The basket is no longer discarded.
    items = await service.get_order_items(str(order.id))
    assert len(items) == 2

    by_product = {str(item.product_id): item for item in items}
    assert set(by_product) == {honey_id, walnut_id}

    honey_item = by_product[honey_id]
    assert honey_item.quantity == Decimal("2")
    assert honey_item.unit == "piece"
    assert honey_item.unit_price == Decimal("350000")
    assert honey_item.line_total == Decimal("700000")
    assert honey_item.product_name == "عسل طبیعی"
    assert honey_item.seller_id == seller_id
    assert honey_item.order_id == str(order.id)

    walnut_item = by_product[walnut_id]
    assert walnut_item.quantity == Decimal("1")
    assert walnut_item.unit == "kg"
    assert walnut_item.unit_price == Decimal("1200000")
    assert walnut_item.line_total == Decimal("1200000")

    # The line totals add up to the header's subtotal.
    assert sum(item.line_total for item in items) == order.subtotal

    # The relationship on the order exposes the same rows.
    result = await db_session.execute(
        select(MarketplaceOrder)
        .where(MarketplaceOrder.id == order.id)
        .options(selectinload(MarketplaceOrder.items))
    )
    reloaded = result.scalar_one()
    assert {str(item.product_id) for item in reloaded.items} == {honey_id, walnut_id}

    # Stock was still decremented.
    assert (await _reload_product(db_session, honey_id)).stock == 8


@pytest.mark.asyncio
async def test_order_items_snapshot_name_and_price(service, db_session):
    """Snapshot fields must not follow later catalogue edits."""
    _, product_id = await _seed_product(
        service, name="عسل قدیمی", price=Decimal("350000")
    )

    order = await service.create_order(
        buyer_id="buyer_1",
        items=[{"product_id": product_id, "quantity": 1}],
        village_id="village_1",
        shipping_address={},
    )

    db_product = await _reload_product(db_session, product_id)
    db_product.name = "عسل تغییرنام‌یافته"
    db_product.price = Decimal("999000")
    await db_session.commit()

    items = await service.get_order_items(str(order.id))
    assert len(items) == 1
    assert items[0].product_name == "عسل قدیمی"
    assert items[0].unit_price == Decimal("350000")
    assert items[0].line_total == Decimal("350000")


# --- the whole order is one transaction ---


@pytest.mark.asyncio
async def test_insufficient_stock_rolls_back_whole_order(service, db_session):
    """(b) A failing decrement must not leave an orphaned order behind."""
    seller_id, first_id = await _seed_product(
        service, name="عسل طبیعی", price=Decimal("350000"), stock=10
    )
    _, second_id = await _seed_product(
        service,
        seller_id=seller_id,
        name="گردوی ارزان",
        price=Decimal("1200000"),
        stock=1,
    )

    with pytest.raises(ValueError, match="موجودی کافی نیست"):
        await service.create_order(
            buyer_id="buyer_1",
            items=[
                {"product_id": first_id, "quantity": 2},
                {"product_id": second_id, "quantity": 5},
            ],
            village_id="village_1",
            shipping_address={},
        )

    # No order row survived.
    order_count = await db_session.execute(select(func.count()).select_from(MarketplaceOrder))
    assert order_count.scalar_one() == 0

    # No orphaned basket rows either.
    item_count = await db_session.execute(select(func.count()).select_from(MarketplaceOrderItem))
    assert item_count.scalar_one() == 0

    # Stock is untouched for both items, including the one already decremented
    # in-memory before the second item failed.
    for product_id, expected in ((first_id, 10), (second_id, 1)):
        reloaded = await _reload_product(db_session, product_id)
        assert reloaded.stock == expected
        assert reloaded.sales_count == 0


@pytest.mark.asyncio
async def test_stock_runs_out_exactly_at_zero(service, db_session):
    """A decrement that lands on zero still commits the order."""
    _, product_id = await _seed_product(
        service, name="عسل طبیعی", price=Decimal("350000"), stock=2
    )

    order = await service.create_order(
        buyer_id="buyer_1",
        items=[{"product_id": product_id, "quantity": 2}],
        village_id="village_1",
        shipping_address={},
    )

    assert order is not None
    reloaded = await _reload_product(db_session, product_id)
    assert reloaded.stock == 0
    assert reloaded.sales_count == 2

    items = await service.get_order_items(str(order.id))
    assert len(items) == 1
    assert items[0].unit_price == Decimal("350000")


# --- price authority ---


@pytest.mark.asyncio
async def test_stored_prices_come_from_catalogue_not_request(service, db_session):
    """(c) The stored item prices are the catalogue's, never the request's."""
    _, product_id = await _seed_product(
        service, name="گردو", price=Decimal("350000"), stock=10
    )

    # No `price` key at all: the service must price it from the catalogue.
    order = await service.create_order(
        buyer_id="buyer_1",
        items=[{"product_id": product_id, "quantity": 3}],
        village_id="village_1",
        shipping_address={},
    )

    items = await service.get_order_items(str(order.id))
    assert len(items) == 1
    assert items[0].unit_price == Decimal("350000")
    assert items[0].line_total == Decimal("1050000")
    assert order.subtotal == Decimal("1050000")


@pytest.mark.asyncio
async def test_price_mismatch_still_refused(service, db_session):
    """A stale-cart price must still be refused, not silently overridden."""
    _, product_id = await _seed_product(
        service, name="گردو", price=Decimal("350000"), stock=10
    )

    with pytest.raises(ValueError, match="in the catalogue, not"):
        await service.create_order(
            buyer_id="buyer_1",
            items=[{"product_id": product_id, "quantity": 1, "price": 1}],
            village_id="village_1",
            shipping_address={},
        )

    order_count = await db_session.execute(select(func.count()).select_from(MarketplaceOrder))
    assert order_count.scalar_one() == 0


@pytest.mark.asyncio
async def test_get_order_items_unknown_order(service):
    """A read-back for an unknown order is empty rather than an error."""
    items = await service.get_order_items("does-not-exist")
    assert items == []
