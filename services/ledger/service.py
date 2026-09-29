"""Ledger Service â€” double-entry accounting for carbon credits and marketplace transactions.

Tracks:
- Carbon credit issuance and retirement
- Marketplace order fills and settlements
- Wallet balances and transfers

Scope note
----------
This module does **not** provide hash-chained immutability, and no longer
claims to. ``LedgerEntry`` (``database/models.py``) has no ``hash`` or
``prev_hash`` column, so ``verify_chain`` could only ever return ``False``:
it read those attributes, hit ``AttributeError``, and the bare ``except
Exception`` converted that into a plausible-looking answer. The digest that
``post_entry`` used to compute was never persisted, and the process-local
``_last_hash`` was reset on every request because ``get_ledger_service``
constructs a new instance per call, so no chain ever formed across entries.

This is the single-entry posting service, one of the ledger implementations. ``finance/
ledger_service.py`` is the designated source of truth (it is the only one that
validates batch balance, amount sign and the asset allowlist) and this module
is scheduled for consolidation onto it. Building a hash chain here would mean
a schema migration against the copy that is about to be retired.

Failures now raise. Returning ``{"status": "memory_only"}`` for a lost
accounting write, or ``Decimal("0")`` for a failed query, turned a database
error into a balance that reads as a real one.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import EscrowRecord, EscrowState, LedgerEntry

logger = logging.getLogger(__name__)

#: ISO 4217. The module previously defaulted to "fiat" and, in one path, to
#: "IRT" â€” which is not a currency code. The correct code is IRR.
DEFAULT_ASSET = "IRR"

#: Only these assets may be posted. Kept aligned with
#: ``finance/ledger_service.ALLOWED_ASSETS``.
ALLOWED_ASSETS = frozenset({"IRR", "ECO", "CARBON_tCO2e", "USD"})

VALID_ENTRY_TYPES = frozenset({"debit", "credit"})


class EntryCreate(BaseModel):
    account_id: str
    entry_type: str  # debit | credit
    asset: str = DEFAULT_ASSET
    amount: Decimal
    reference_type: str | None = None  # escrow_lock | escrow_release | escrow_reverse
    reference_id: str | None = None
    description: str | None = None


class SingleEntryLedgerService:
    """Single-entry posting API for the standalone ledger app.

    Renamed during the phase 4 S-MONEY consolidation. There were four classes
    named ``LedgerService`` in the repository, which is what made it hard to
    say which one any call site meant:

    * ``finance/ledger_service.py`` â€” the canonical **batch** service, the
      only one that validates balance, amount sign and the asset allowlist.
      This is the source of truth.
    * ``finance/wallet_service.py`` â€” a duplicate with no validation and the
      *opposite* sign convention. Removed.
    * ``ecowallet/ledger.py`` â€” an in-memory ``float`` ledger. Converted to
      ``Decimal``.
    * this one.

    Kept separate from the canonical service because the two have different
    shapes: the canonical one posts a *balanced batch* and is what the gateway
    and wallet use; this one posts a single entry and is what
    ``services/ledger/main.py`` exposes. The batch service is deliberately not
    reachable from an unauthenticated standalone app, because a single-entry
    post cannot assert double-entry on its own.

    Sign convention: ``credit`` is positive, ``debit`` is negative — the same
    one every other balance query in the codebase uses.
    """

    def __init__(self, db: Any = None, session: AsyncSession | None = None) -> None:
        self.db = db
        self.session = session

    async def _get_session(self) -> AsyncSession:
        if self.session is not None:
            return self.session
        return hub.get_async_session()

    def _validate(self, entry: EntryCreate) -> None:
        if entry.entry_type not in VALID_ENTRY_TYPES:
            raise ValueError(
                f"entry_type must be one of {sorted(VALID_ENTRY_TYPES)}, got {entry.entry_type!r}"
            )
        if entry.amount <= 0:
            raise ValueError(f"amount must be positive, got {entry.amount}")
        if entry.asset not in ALLOWED_ASSETS:
            raise ValueError(f"asset must be one of {sorted(ALLOWED_ASSETS)}, got {entry.asset!r}")
        if not entry.account_id:
            raise ValueError("account_id is required")

    async def post_entry(self, entry: EntryCreate) -> dict[str, Any]:
        """Post a new ledger entry.

        Raises on validation failure and on persistence failure. The previous
        implementation logged and returned ``{"hash": ..., "status":
        "memory_only"}``, which the escrow paths treated as a successful post.
        """
        self._validate(entry)

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
                "amount": str(record.amount),
                "entry_type": record.entry_type,
                "asset": record.asset,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }

    async def get_balance(self, account_id: str, asset: str | None = None) -> Decimal:
        """Balance for an account: credits positive, debits negative.

        Raises if the query fails. The previous version returned
        ``Decimal("0")`` on any exception, which is indistinguishable from a
        genuinely empty account.
        """
        signed_amount = case(
            (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
            else_=-LedgerEntry.amount,
        )
        query = select(func.sum(signed_amount)).where(LedgerEntry.account_id == account_id)
        if asset is not None:
            query = query.where(LedgerEntry.asset == asset)

        async with await self._get_session() as session:
            result = await session.execute(query)
            return result.scalar() or Decimal("0")

    async def verify_chain(self) -> bool:
        """Always raises.

        ``LedgerEntry`` has no ``hash``/``prev_hash`` columns, so there is no
        chain to verify. This method used to catch the resulting
        ``AttributeError`` and return ``False``, which read as "the ledger was
        tampered with" rather than "this ledger does not have that property".
        See the module docstring for the consolidation plan.
        """
        raise NotImplementedError(
            "verify_chain requires LedgerEntry.hash / LedgerEntry.prev_hash, which do not exist. "
            "Add the columns and a persisted chain, or rely on database-level append-only "
            "permissions. Until then, no integrity verification is performed."
        )

    async def health(self) -> str:
        return "ok"


class EscrowService:
    """Escrow state machine: created â†’ locked â†’ released | reversed.

    Integrates with SingleEntryLedgerService to post debit/credit entries
    on each state transition, maintaining double-entry integrity.
    """

    DISPUTE_WINDOW_HOURS = 48

    def __init__(self, db: Any = None, session: AsyncSession | None = None) -> None:
        self._ledger = SingleEntryLedgerService(db=db, session=session)
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
        asset: str = DEFAULT_ASSET,
        payment_id: str | None = None,
    ) -> EscrowRecord:
        """Step 1: Create escrow record in 'created' state.

        The default asset was "IRT", which is not a currency code. The correct
        ISO 4217 code is IRR, now the module-wide ``DEFAULT_ASSET``.
        """
        if asset not in ALLOWED_ASSETS:
            raise ValueError(f"asset must be one of {sorted(ALLOWED_ASSETS)}, got {asset!r}")
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
        """Step 2: Transition created â†’ locked (funds verified and held).

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
        """Step 3: Transition locked â†’ released (funds to seller)."""
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
        """Step 3 alt: Transition locked â†’ reversed (funds back to buyer)."""
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

        Only valid after released or reversed â€” final settlement step.
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


async def get_ledger_service() -> SingleEntryLedgerService:
    return SingleEntryLedgerService()


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
        service: SingleEntryLedgerService = Depends(get_ledger_service),
    ):
        return await service.post_entry(body)

    @router.get("/balance/{account_id}")
    async def get_balance(
        account_id: str, service: SingleEntryLedgerService = Depends(get_ledger_service)
    ):
        return {"account_id": account_id, "balance": str(await service.get_balance(account_id))}

    @router.get("/verify")
    async def verify(service: SingleEntryLedgerService = Depends(get_ledger_service)):
        """Integrity verification status.

        Not implemented: ``LedgerEntry`` has no hash columns. The endpoint
        reports the capability as unavailable rather than answering
        ``{"valid": false}``, which used to be what every caller received.
        """
        return {
            "verified": False,
            "status": "not_implemented",
            "reason": (
                "LedgerEntry has no hash/prev_hash columns, so there is no chain to verify. "
                "A 'valid: false' answer would be indistinguishable from tampering."
            ),
        }

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8006)


if __name__ == "__main__":
    main()
