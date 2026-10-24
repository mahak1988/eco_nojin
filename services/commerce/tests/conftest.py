"""Shared conftest fixtures for commerce tests."""

from __future__ import annotations

from decimal import Decimal

import pytest_asyncio


@pytest_asyncio.fixture
async def order_service(db_session):
    from services.commerce.service import OrderService

    return OrderService(db_session)


@pytest_asyncio.fixture
async def stock_service(db_session):
    from services.inventory.service import StockService

    service = StockService(db_session)
    wh = await service.create_warehouse("DEFAULT", "Default Warehouse", city="Tehran")
    service._default_wh = wh
    return service


@pytest_asyncio.fixture
async def sku(stock_service):
    s = await stock_service.create_sku(
        "TEST-SKU", "Test Product", uom="kg", standard_cost=Decimal("10")
    )
    # Add stock so orders can be created
    await stock_service.receipt(
        sku_id=s.id,
        warehouse_id=stock_service._default_wh.id,
        qty=Decimal("100"),
        reference_type="test-setup",
        reference_id="test-initial",
        created_by="test-setup",
    )
    return s
