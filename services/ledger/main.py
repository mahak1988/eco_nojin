"""Ledger service â€” standalone app for the ECO/carbon ledger.

Consolidated in phase 4 (S-MONEY). This module previously:

* declared its **own** asset vocabulary (``carbon_credit | eco_token | fiat``,
  defaulting to ``eco_token``) alongside three others in the repository;
* wrote ``LedgerEntry`` rows directly, with no batch-balance check, no amount
  check and no asset allowlist;
* summed balances inline with a **third** sign convention, separate from the
  two that already existed.

It now delegates to ``services.ledger.service.LedgerService``, which validates
and applies the single documented sign convention (credit positive, debit
negative).

Scope note: this app is not mounted in the API gateway. It exposes an
unauthenticated write endpoint on its own port, which is why every write goes
through the validating service rather than the ORM.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import LedgerEntry
from services.ledger.service import ALLOWED_ASSETS, DEFAULT_ASSET, SingleEntryLedgerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])


class EntryCreate(BaseModel):
    account_id: str
    entry_type: str
    asset: str = DEFAULT_ASSET
    amount: Decimal = Field(..., gt=0)
    reference_type: str
    reference_id: str | None = None
    description: str | None = None

    @field_validator("entry_type")
    @classmethod
    def _check_entry_type(cls, value: str) -> str:
        if value not in {"debit", "credit"}:
            raise ValueError("entry_type must be 'debit' or 'credit'")
        return value

    @field_validator("asset")
    @classmethod
    def _check_asset(cls, value: str) -> str:
        if value not in ALLOWED_ASSETS:
            raise ValueError(f"asset must be one of {sorted(ALLOWED_ASSETS)}")
        return value


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


async def get_ledger_service(db: AsyncSession = Depends(get_db)) -> SingleEntryLedgerService:
    return SingleEntryLedgerService(db)


@router.post("/entries", status_code=201)
async def create_entry(
    body: EntryCreate,
    service: SingleEntryLedgerService = Depends(get_ledger_service),
):
    """Post a single validated entry.

    Posting one entry at a time means the batch-balance check cannot run, so
    the caller owns the other side of the double entry. A ``validate_balance``
    flag is provided for callers that would rather assert the invariant here
    than rely on the balancing counterpart being posted.
    """
    try:
        record = await service.post_entry(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": record["id"], "created": True, "entry": record}


@router.get("/accounts/{account_id}/balance")
async def get_balance(
    account_id: str,
    asset: str = DEFAULT_ASSET,
    service: SingleEntryLedgerService = Depends(get_ledger_service),
):
    """Balance for an account.

    Uses the service, so the sign convention matches the one every other
    balance query in the codebase uses.
    """
    if asset not in ALLOWED_ASSETS:
        raise HTTPException(
            status_code=400, detail=f"asset must be one of {sorted(ALLOWED_ASSETS)}"
        )
    balance = await service.get_balance(account_id, asset)
    return {"account_id": account_id, "asset": asset, "balance": str(balance)}


@router.get("/entries")
async def list_entries(
    account_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LedgerEntry)
    if account_id:
        stmt = stmt.where(LedgerEntry.account_id == account_id)
    stmt = stmt.order_by(LedgerEntry.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
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
            for e in result.scalars().all()
        ]
    }


@router.get("/verify")
async def verify_integrity(service: SingleEntryLedgerService = Depends(get_ledger_service)):
    """Integrity verification status.

    Not implemented: ``LedgerEntry`` has no ``hash``/``prev_hash`` columns.
    Reporting ``{"valid": false}`` here was indistinguishable from tampering,
    which is the confusion the S-HONEST status contract exists to remove.
    """
    return {
        "verified": False,
        "status": "not_implemented",
        "reason": (
            "LedgerEntry has no hash/prev_hash columns, so there is no chain to verify. "
            "A 'valid: false' answer would be indistinguishable from tampering."
        ),
    }


app = FastAPI(title="Eco Nojin Ledger Service", version="2.0.0")
app.include_router(router)


def main() -> None:
    """Run the ledger service."""
    import uvicorn

    logger.info("Starting ledger service on port 8002 (not mounted in the API gateway)")
    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    main()
