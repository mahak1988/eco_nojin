"""Shared conftest fixtures for inventory tests."""

from __future__ import annotations

from decimal import Decimal

import pytest_asyncio


@pytest_asyncio.fixture
async def stock_service(db_session):
    from services.inventory.service import StockService

    service = StockService(db_session)
    wh = await service.create_warehouse("DEFAULT", "Default Warehouse", city="Tehran")
    service._default_wh = wh
    return service


@pytest_asyncio.fixture
async def sku(stock_service):
    return await stock_service.create_sku(
        "TEST-SKU", "Test Product", uom="kg", standard_cost=Decimal("10")
    )
