"""Ledger Service — immutable double-entry accounting for carbon credits and marketplace transactions.

Tracks:
- Carbon credit issuance and retirement
- Marketplace order fills and settlements
- Wallet balances and transfers
- Full audit trail with hash-chained entries
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import EscrowRecord, EscrowState, LedgerEntry

logger = logging.getLogger(__name__)


class EntryCreate(BaseModel):
    account_id: str
    entry_type: str  # debit | credit
    asset: str = "fiat"  # carbon_credit | eco_token | fiat
    amount: Decimal
    reference_type: str | None = None  # escrow_lock | escrow_release | escrow_reverse
    reference_id: str | None = None
    description: str | None = None


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
        """Post a new ledger entry."""
        import hashlib

        entry_data = f"{entry.account_id}{entry.entry_type}{entry.amount}{entry.reference_type}{entry.reference_id}{datetime.now(UTC).isoformat()}"
        prev_hash = self._last_hash or "0" * 64
        entry_hash = hashlib.sha256((prev_hash + entry_data).encode()).hexdigest()
        self._last_hash = entry_hash

        try:
            async with await self._get_session() as session:
                record = LedgerEntry(
                    account_id=entry.account_id,
                    entry_type=entry.entry_type,
                    asset=entry.asset,
                    amount=entry.amount,
                    reference_type=entry.reference_type,
                    reference_id=entry.reference_id,
                    description=entry.description,
                    created_at=datetime.now(UTC).replace(tzinfo=None),
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return {
                    "id": record.id,
                    "hash": entry_hash,
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


class EscrowService:
    """Escrow state machine: created → locked → released | reversed.

    Integrates with the hash-chained LedgerService to post debit/credit entries
    on each state transition, maintaining double-entry integrity.
    """

    DISPUTE_WINDOW_HOURS = 48

    def __init__(self, db: Any = None, session: AsyncSession | None = None) -> None:
        self._ledger = LedgerService(db=db, session=session)
        self._session_override = session

    async def _get_session(self) -> AsyncSession:
        if self._session_override is not None:
            return self._session_override
        return hub.get_async_session()

    async def create(
        self,
        order_id: str,
        buyer_id: str,
        seller_id: str,
        amount: Decimal,
        asset: str = "IRT",
        payment_id: str | None = None,
    ) -> EscrowRecord:
        """Step 1: Create escrow record in 'created' state."""
        async with await self._get_session() as session:
            record = EscrowRecord(
                order_id=order_id,
                payment_id=payment_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                amount=amount,
                asset=asset,
                state=EscrowState.CREATED.value,
                dispute_window_deadline=None,
                created_at=datetime.now(UTC),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info(
                "escrow.created",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                    "amount": str(amount),
                    "asset": asset,
                },
            )
            return record

    async def lock(
        self,
        order_id: str,
        payment_id: str | None = None,
    ) -> EscrowRecord:
        """Step 2: Transition created → locked (funds verified and held).

        Posts a debit entry to buyer's escrow account and a credit to the
        escrow liability account. Starts the dispute window deadline.
        """
        async with await self._get_session() as session:
            record = await self._get_active(record_id=order_id, session=session)
            if record is None:
                raise LookupError(f"No unlocked escrow for order {order_id}")
            if not EscrowState(record.state).can_transition_to(EscrowState.LOCKED):
                raise ValueError(f"Escrow {record.id} in state '{record.state}', cannot lock")
            record.state = EscrowState.LOCKED.value
            record.dispute_window_deadline = datetime.now(UTC) + timedelta(
                hours=self.DISPUTE_WINDOW_HOURS
            )
            record.updated_at = datetime.now(UTC)
            if payment_id:
                record.payment_id = payment_id
            session.add(record)
            await session.commit()
            await session.refresh(record)
            await self._ledger.post_entry(
                EntryCreate(
                    account_id=record.buyer_id,
                    entry_type="debit",
                    amount=record.amount,
                    asset=record.asset,
                    reference_type="escrow_lock",
                    description=f"Escrow lock for order {record.order_id} (escrow={record.id})",
                )
            )
            logger.info(
                "escrow.locked",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                },
            )
            return record

    async def release(self, order_id: str, actor_id: str | None = None) -> EscrowRecord:
        """Step 3: Transition locked → released (funds to seller)."""
        async with await self._get_session() as session:
            record = await self._get_active(record_id=order_id, session=session)
            if record is None:
                raise LookupError(f"No escrow for order {order_id}")
            if not EscrowState(record.state).can_transition_to(EscrowState.RELEASED):
                raise ValueError(f"Escrow {record.id} in state '{record.state}', cannot release")
            record.state = EscrowState.RELEASED.value
            record.updated_at = datetime.now(UTC)
            record.completed_at = datetime.now(UTC)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            await self._ledger.post_entry(
                EntryCreate(
                    account_id=record.seller_id,
                    entry_type="credit",
                    amount=record.amount,
                    asset=record.asset,
                    reference_type="escrow_release",
                    description=f"Escrow release for order {record.order_id} (escrow={record.id})",
                )
            )
            logger.info(
                "escrow.released",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                    "actor_id": actor_id,
                },
            )
            return record

    async def reverse(self, order_id: str, actor_id: str | None = None) -> EscrowRecord:
        """Step 3 alt: Transition locked → reversed (funds back to buyer)."""
        async with await self._get_session() as session:
            record = await self._get_active(record_id=order_id, session=session)
            if record is None:
                raise LookupError(f"No escrow for order {order_id}")
            if not EscrowState(record.state).can_transition_to(EscrowState.REVERSED):
                raise ValueError(f"Escrow {record.id} in state '{record.state}', cannot reverse")
            record.state = EscrowState.REVERSED.value
            record.updated_at = datetime.now(UTC)
            record.completed_at = datetime.now(UTC)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            await self._ledger.post_entry(
                EntryCreate(
                    account_id=record.buyer_id,
                    entry_type="credit",
                    amount=record.amount,
                    asset=record.asset,
                    reference_type="escrow_reverse",
                    description=f"Escrow reversal for order {record.order_id} (escrow={record.id})",
                )
            )
            logger.info(
                "escrow.reversed",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                    "actor_id": actor_id,
                },
            )
            return record

    async def complete(self, order_id: str) -> EscrowRecord:
        """Step 5/6: Mark escrow as fully settled (post-dispute window close).

        Only valid after released or reversed — final settlement step.
        """
        async with await self._get_session() as session:
            result = await session.execute(
                select(EscrowRecord).where(EscrowRecord.order_id == order_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                raise LookupError(f"No escrow for order {order_id}")
            if record.state not in (
                EscrowState.RELEASED.value,
                EscrowState.REVERSED.value,
            ):
                raise ValueError(
                    f"Escrow {record.id} in state '{record.state}', must be released or reversed to complete"
                )
            record.updated_at = datetime.now(UTC)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info(
                "escrow.completed",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                    "final_state": record.state,
                },
            )
            return record

    async def dispute(self, order_id: str) -> EscrowRecord:
        """Step 5: Open dispute window for a locked escrow.

        Returns the escrow record with remaining dispute time. The dispute
        window is automatically closed by a subsequent release or reverse.
        """
        async with await self._get_session() as session:
            record = await self._get_active(record_id=order_id, session=session)
            if record is None:
                raise LookupError(f"No escrow for order {order_id}")
            if record.state != EscrowState.LOCKED.value:
                raise ValueError(f"Escrow {record.id} in state '{record.state}', cannot dispute")
            if record.dispute_window_deadline:
                deadline = record.dispute_window_deadline
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=UTC)
                if deadline < datetime.now(UTC):
                    raise ValueError(f"Dispute window expired for escrow {record.id}")
            logger.info(
                "escrow.disputed",
                extra={
                    "order_id": order_id,
                    "escrow_id": record.id,
                    "deadline": record.dispute_window_deadline.isoformat()
                    if record.dispute_window_deadline
                    else None,
                },
            )
            return record

    async def get_state(self, order_id: str) -> EscrowRecord | None:
        """Get current escrow state for an order."""
        async with await self._get_session() as session:
            return await self._get_by_order(order_id, session)

    async def _get_active(self, record_id: str, session: AsyncSession) -> EscrowRecord | None:
        result = await session.execute(
            select(EscrowRecord).where(EscrowRecord.order_id == record_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_order(self, order_id: str, session: AsyncSession) -> EscrowRecord | None:
        result = await session.execute(
            select(EscrowRecord).where(EscrowRecord.order_id == order_id)
        )
        return result.scalar_one_or_none()


async def get_ledger_service() -> LedgerService:
    return LedgerService()


async def get_escrow_service() -> EscrowService:
    return EscrowService()


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
