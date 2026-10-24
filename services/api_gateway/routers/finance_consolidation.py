"""Consolidated position router (P2-13).

Exposes the read-only cross-store consolidation built by
``services.finance.consolidation.ConsolidatedPositionService``. Admin-only, the
same guard the finance reporting endpoints (trial balance, profit & loss) use.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.auth import require_admin
from services.finance.consolidation import ConsolidatedPositionService

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


@router.get("/consolidated/position", response_model=dict)
async def get_consolidated_position(
    as_of: date | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """Consolidated, read-only position across the five independent money stores.

    Reports each store's contribution per asset currency, the wallet-vs-ledger
    reconciliation gap, and an overall roll-up. Does not merge, migrate, rewrite
    or delete any store.
    """
    service = ConsolidatedPositionService(db)
    return await service.position(as_of=as_of)
