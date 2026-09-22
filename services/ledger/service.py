"""Ledger Service — immutable double-entry accounting for carbon credits and marketplace transactions.

Tracks:
- Carbon credit issuance and retirement
- Marketplace order fills and settlements
- Wallet balances and transfers
- Full audit trail with hash-chained entries
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import LedgerEntry, LedgerEntryType

logger = logging.getLogger(__name__)


class EntryCreate(BaseModel):
    account_id: str
    entry_type: str  # debit | credit
    amount: Decimal
    currency: str = "IRT"
    reference_type: str  # carbon_credit | marketplace | wallet | adjustment
    reference_id: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LedgerService:
    """Double-entry ledger with hash-chained immutability."""

    def __init__(self, db: Any = None, session: AsyncSession | None = None) -> None:
        self.db = db
        self.session = session
        self._last_hash: str | None = None

    async def _get_session(self) -> AsyncSession:
        if self.session is not None:
            return self.session
        return hub.get_async_session()

    async def post_entry(self, entry: EntryCreate) -> dict[str, Any]:
        """Post a new ledger entry with hash-chain integrity."""
        import hashlib

        entry_data = f"{entry.account_id}{entry.entry_type}{entry.amount}{entry.reference_type}{entry.reference_id}{datetime.now(UTC).isoformat()}"
        prev_hash = self._last_hash or "0" * 64
        entry_hash = hashlib.sha256((prev_hash + entry_data).encode()).hexdigest()
        self._last_hash = entry_hash

        try:
            async with await self._get_session() as session:
                record = LedgerEntry(
                    account_id=entry.account_id,
                    entry_type=LedgerEntryType(entry.entry_type),
                    amount=entry.amount,
                    currency=entry.currency,
                    reference_type=entry.reference_type,
                    reference_id=entry.reference_id,
                    description=entry.description,
                    metadata=entry.metadata,
                    hash=entry_hash,
                    prev_hash=prev_hash,
                    created_at=datetime.now(UTC).replace(tzinfo=None),
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return {
                    "id": record.id,
                    "hash": record.hash,
                    "prev_hash": record.prev_hash,
                    "amount": str(record.amount),
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                }
        except Exception:
            logger.warning("Failed to persist ledger entry", exc_info=True)
            return {"hash": entry_hash, "status": "memory_only"}

    async def get_balance(self, account_id: str) -> Decimal:
        """Compute current balance for an account."""
        try:
            async with await self._get_session() as session:
                result = await session.execute(
                    select(func.sum(LedgerEntry.amount).where(LedgerEntry.account_id == account_id))
                )
                total = result.scalar()
                return total or Decimal("0")
        except Exception:
            logger.warning("Failed to compute balance for %s", account_id, exc_info=True)
            return Decimal("0")

    async def verify_chain(self) -> bool:
        """Verify hash-chain integrity across all entries."""
        import hashlib

        try:
            async with await self._get_session() as session:
                result = await session.execute(select(LedgerEntry).order_by(LedgerEntry.created_at))
                entries = result.scalars().all()
                prev = "0" * 64
                for entry in entries:
                    expected = hashlib.sha256(
                        (
                            prev
                            + f"{entry.account_id}{entry.entry_type}{entry.amount}{entry.reference_type}{entry.reference_id}"
                        ).encode()
                    ).hexdigest()
                    if entry.hash != expected or entry.prev_hash != prev:
                        return False
                    prev = entry.hash
                return True
        except Exception:
            logger.warning("Chain verification failed", exc_info=True)
            return False

    async def health(self) -> str:
        return "ok"


async def get_ledger_service() -> LedgerService:
    return LedgerService()


def main() -> None:
    import uvicorn
    from fastapi import APIRouter, Depends, FastAPI

    app = FastAPI(title="Eco Nojin Ledger Service", version="1.0.0")
    router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])

    @router.post("/entries")
    async def post_entry(
        body: EntryCreate,
        service: LedgerService = Depends(get_ledger_service),
    ):
        return await service.post_entry(body)

    @router.get("/balance/{account_id}")
    async def get_balance(account_id: str, service: LedgerService = Depends(get_ledger_service)):
        return {"account_id": account_id, "balance": str(await service.get_balance(account_id))}

    @router.get("/verify")
    async def verify(service: LedgerService = Depends(get_ledger_service)):
        return {"valid": await service.verify_chain()}

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8006)


if __name__ == "__main__":
    main()
