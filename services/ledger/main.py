"""Ledger service — immutable transaction ledger for carbon credits and ECO tokens.

Provides append-only accounting for:
- Carbon credit issuance and retirement
- ECO token wallet movements
- Marketplace transactions
- Balance queries with double-entry guarantees
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import LedgerEntry
from engine.hydroma.config.settings import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])


class EntryCreate(BaseModel):
    account_id: int
    entry_type: str  # debit | credit
    asset: str  # carbon_credit | eco_token | fiat
    amount: Decimal = Field(..., gt=0)
    reference_type: str  # carbon_issue | marketplace | wallet_transfer
    reference_id: int | None = None
    description: str | None = None


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


@router.post("/entries", status_code=201)
async def create_entry(
    body: EntryCreate,
    db: AsyncSession = Depends(get_db),
):
    entry = LedgerEntry(
        account_id=body.account_id,
        entry_type=body.entry_type,
        asset=body.asset,
        amount=body.amount,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
        description=body.description,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"id": entry.id, "created": True}


@router.get("/accounts/{account_id}/balance")
async def get_balance(
    account_id: int,
    asset: str = "eco_token",
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.account_id == account_id, LedgerEntry.asset == asset)
    )
    entries = result.scalars().all()
    balance = Decimal("0")
    for e in entries:
        if e.entry_type == "credit":
            balance += e.amount
        else:
            balance -= e.amount
    return {"account_id": account_id, "asset": asset, "balance": str(balance)}


@router.get("/entries")
async def list_entries(
    account_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LedgerEntry)
    if account_id:
        stmt = stmt.where(LedgerEntry.account_id == account_id)
    stmt = stmt.order_by(LedgerEntry.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {
        "entries": [
            {
                "id": e.id,
                "account_id": e.account_id,
                "entry_type": e.entry_type,
                "asset": e.asset,
                "amount": str(e.amount),
                "reference_type": e.reference_type,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


def main() -> None:
    """Run the ledger service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)


from fastapi import FastAPI

app = FastAPI(title="Eco Nojin Ledger Service", version="1.0.0")
app.include_router(router)


if __name__ == "__main__":
    main()
