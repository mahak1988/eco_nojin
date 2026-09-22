"""Async fixtures for the carbon-credit test module.

CarbonService is an async service (AsyncSession), so these tests need an async
session rather than the project-wide synchronous ``sync_db_session`` fixture.
"""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import database.models  # noqa: F401  (register all tables on Base.metadata)
from database.base import Base


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_engine):
    maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with maker() as session:
        yield session
