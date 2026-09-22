"""Shared conftest fixtures for finance tests."""

from __future__ import annotations

import pytest_asyncio


@pytest_asyncio.fixture
async def finance_wallet_service(db_session):
    from services.finance.wallet_service import WalletService

    return WalletService(db_session)


@pytest_asyncio.fixture
async def finance_ledger_service(db_session):
    from services.finance.ledger_service import LedgerService

    return LedgerService(db_session)


@pytest_asyncio.fixture
async def finance_reconciliation_service(db_session):
    from services.finance.reconciliation import ReconciliationService

    return ReconciliationService(db_session)


# Re-export for test files that use `fresh_` prefixed names
@pytest_asyncio.fixture
async def fresh_wallet_service(db_session):
    from services.finance.wallet_service import WalletService

    return WalletService(db_session)


@pytest_asyncio.fixture
async def fresh_ledger_service(db_session):
    from services.finance.ledger_service import LedgerService

    return LedgerService(db_session)


@pytest_asyncio.fixture
async def fresh_stock_service(db_session):
    from services.inventory.service import StockService

    service = StockService(db_session)
    existing = await service._get_or_create_wallet  # no-op, just to ensure import
    wh = await service.create_warehouse("DEFAULT", "Default Warehouse", city="Tehran")
    service._default_wh = wh
    return service


@pytest_asyncio.fixture
async def fresh_order_service(db_session):
    from services.commerce.service import OrderService

    return OrderService(db_session)
