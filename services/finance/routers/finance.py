"""Finance router — exposes LedgerService, WalletService, PaymentProvider, and Reconciliation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import (
    EcoWallet,
    FinAccount,
    FinIdempotencyKey,
)
from services.api_gateway.auth import require_admin, require_api_key, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.finance.ledger_service import LedgerService
from services.finance.payment_provider import (
    payment_registry,
)
from services.finance.reconciliation import ReconciliationService
from services.finance.wallet_service import WalletService

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class JournalEntryCreate(BaseModel):
    account_id: str
    entry_type: str = Field(..., pattern=r"^(debit|credit)$")
    asset: str = Field(..., pattern=r"^(IRR|ECO|CARBON_tCO2e|USD)$")
    amount: Decimal = Field(..., gt=0)
    description: str | None = None


class JournalBatchCreate(BaseModel):
    batch_number: str | None = None
    batch_date: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    description: str | None = None
    entries: list[JournalEntryCreate] = Field(..., min_length=2)


class JournalBatchResponse(BaseModel):
    id: int
    batch_number: str
    batch_date: str
    reference_type: str | None
    is_posted: bool
    entries: list[dict]


class WalletBalanceResponse(BaseModel):
    user_id: str
    balance: Decimal
    total_earned: Decimal
    total_redeemed: Decimal
    is_active: bool


class EarnRequest(BaseModel):
    category: str = Field(..., pattern=r"^(tree_planting|soil_health|water_saving|carbon_credit|education|community)$")
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    idempotency_key: str | None = None
    reference_id: str | None = None


class EarnResponse(BaseModel):
    amount_earned: Decimal
    new_balance: Decimal
    category: str


class RedeemRequest(BaseModel):
    category: str = Field(..., pattern=r"^(consultation|satellite_report|marketplace_discount)$")
    idempotency_key: str | None = None
    reference_id: str | None = None


class RedeemResponse(BaseModel):
    amount_redeemed: Decimal
    new_balance: Decimal
    category: str


class AccountResponse(BaseModel):
    id: int
    code: str
    name: str
    type: str
    asset: str | None
    currency: str
    is_active: bool


class PaymentIntentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = "IRR"
    order_id: str
    provider: str = "wallet"
    metadata: dict | None = None


class ReconciliationResponse(BaseModel):
    checked_at: str
    total_checked: int
    discrepancies_count: int
    discrepancies: list[dict]
    overall_ok: bool


# ---------------------------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------------------------

@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    asset: str | None = None,
    is_active: bool | None = True,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    stmt = select(FinAccount)
    if asset:
        stmt = stmt.where(FinAccount.asset == asset)
    if is_active is not None:
        stmt = stmt.where(FinAccount.is_active == is_active)
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [
        AccountResponse(
            id=a.id, code=a.code, name=a.name, type=a.type,
            asset=a.asset, currency=a.currency, is_active=a.is_active,
        )
        for a in accounts
    ]


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    code: str,
    name: str,
    type: str,
    asset: str | None = None,
    currency: str = "IRR",
    parent_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    stmt = pg_insert(FinAccount).values(
        code=code, name=name, type=type, asset=asset, currency=currency,
        parent_id=parent_id, is_active=True,
    ).on_conflict_do_nothing(index_elements=["code"]).returning(FinAccount)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        result = await db.execute(select(FinAccount).where(FinAccount.code == code))
        account = result.scalar_one()
    await db.commit()
    return AccountResponse(
        id=account.id, code=account.code, name=account.name, type=account.type,
        asset=account.asset, currency=account.currency, is_active=account.is_active,
    )


# ---------------------------------------------------------------------------
# Ledger (double-entry)
# ---------------------------------------------------------------------------

@router.post("/ledger/batch", response_model=JournalBatchResponse)
async def create_journal_batch(
    body: JournalBatchCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    entries_data = [
        {
            "account_id": e.account_id,
            "entry_type": e.entry_type,
            "asset": e.asset,
            "amount": str(e.amount),
            "description": e.description,
        }
        for e in body.entries
    ]

    service = LedgerService(db)
    try:
        batch = await service.create_journal_batch(
            reference_type=body.reference_type or "manual",
            reference_id=body.reference_id or str(uuid4()),
            entries=entries_data,
            description=body.description,
            created_by=str(user.id) if hasattr(user, 'id') else str(user.get('id')),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=400, detail=e.message)

    return JournalBatchResponse(
        id=batch.id,
        batch_number=batch.batch_number,
        batch_date=batch.batch_date.isoformat(),
        reference_type=batch.reference_type,
        is_posted=batch.is_posted,
        entries=[],
    )


@router.post("/ledger/batch/{batch_id}/post")
async def post_journal_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    service = LedgerService(db)
    try:
        batch = await service.post_journal_batch(batch_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=404, detail=e.message)
    return {"batch_id": batch.id, "is_posted": batch.is_posted, "posted_at": batch.posted_at.isoformat() if batch.posted_at else None}


@router.get("/ledger/accounts/{account_id}/balance", response_model=dict)
async def get_account_balance(
    account_id: str,
    asset: str = "ECO",
    as_of: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    service = LedgerService(db)
    balance = await service.get_account_balance(account_id=account_id, asset=asset, as_of=as_of)
    return {"account_id": account_id, "asset": asset, "balance": str(balance)}


@router.get("/ledger/entries", response_model=list[dict])
async def list_journal_entries(
    account_id: str | None = None,
    batch_id: int | None = None,
    asset: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    service = LedgerService(db)
    entries = await service.list_entries(account_id=account_id, asset=asset, limit=limit)
    return [
        {
            "id": e.id,
            "batch_id": e.batch_id,
            "account_id": e.account_id,
            "entry_type": e.entry_type,
            "asset": e.asset,
            "amount": str(e.amount),
            "description": e.description,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


# ---------------------------------------------------------------------------
# Wallet (uses finance service)
# ---------------------------------------------------------------------------

@router.get("/wallet", response_model=WalletBalanceResponse)
async def get_wallet(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    service = WalletService(db)
    state = await service.get_wallet_state(str(user.id) if hasattr(user, 'id') else str(user.get('id')))
    return WalletBalanceResponse(**state)


@router.post("/wallet/earn", response_model=EarnResponse)
async def earn_tokens(
    body: EarnRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    service = WalletService(db)
    try:
        amount, balance = await service.earn(
            user_id=str(user.id) if hasattr(user, 'id') else str(user.get('id')),
            category=body.category,
            quantity=body.quantity,
            idempotency_key=body.idempotency_key,
            reference_id=body.reference_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return EarnResponse(amount_earned=amount, new_balance=balance, category=body.category)


@router.post("/wallet/redeem", response_model=RedeemResponse)
async def redeem_tokens(
    body: RedeemRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    service = WalletService(db)
    try:
        amount, balance = await service.redeem(
            user_id=str(user.id) if hasattr(user, 'id') else str(user.get('id')),
            category=body.category,
            idempotency_key=body.idempotency_key,
            reference_id=body.reference_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return RedeemResponse(amount_redeemed=amount, new_balance=balance, category=body.category)


@router.get("/wallet/stats", response_model=dict)
async def wallet_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    result = await db.execute(select(EcoWallet))
    wallets = result.scalars().all()
    return {
        "total_wallets": len(wallets),
        "total_tokens_issued": sum(float(w.balance) for w in wallets),
        "total_tokens_earned": sum(float(w.total_earned) for w in wallets),
        "total_tokens_redeemed": sum(float(w.total_redeemed) for w in wallets),
    }


# ---------------------------------------------------------------------------
# Payment Provider
# ---------------------------------------------------------------------------

@router.post("/payments/intent", response_model=dict)
async def create_payment_intent(
    body: PaymentIntentCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_user),
):
    provider = payment_registry.get(body.provider)
    intent = await provider.create_payment_intent(
        amount=body.amount,
        currency=body.currency,
        order_id=body.order_id,
        metadata=body.metadata or {},
        idempotency_key=str(uuid4()),
    )
    return {
        "id": intent.id,
        "amount": str(intent.amount),
        "currency": intent.currency,
        "status": intent.status,
        "provider": intent.provider,
        "metadata": intent.metadata,
    }


@router.post("/payments/webhook/{provider_name}")
async def payment_webhook(
    provider_name: str,
    request: Request,
    api_key: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    signature = request.headers.get("X-Signature") or request.headers.get("Stripe-Signature", "")
    provider = payment_registry.get(provider_name)
    event = await provider.verify_webhook(raw_body, signature)

    outcome = await provider.handle_webhook(event, db)
    return {"processed": True, "event_id": event.provider_event_id, "outcome": outcome}


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

@router.post("/reconciliation/wallet-ledger", response_model=dict)
async def reconcile_wallet_ledger(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    service = ReconciliationService(db)
    return await service.reconcile_wallet_ledger()


@router.post("/reconciliation/full", response_model=dict)
async def full_reconciliation(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    service = ReconciliationService(db)
    return await service.run_full_reconciliation()


# ---------------------------------------------------------------------------
# Idempotency utility
# ---------------------------------------------------------------------------

@router.get("/idempotency/keys", response_model=list[dict])
async def list_idempotency_keys(
    user_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    stmt = select(FinIdempotencyKey)
    if user_id:
        stmt = stmt.where(FinIdempotencyKey.user_id == user_id)
    if status:
        stmt = stmt.where(FinIdempotencyKey.status == status)
    stmt = stmt.order_by(FinIdempotencyKey.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    keys = result.scalars().all()
    return [
        {
            "key": k.key,
            "user_id": k.user_id,
            "route": k.route,
            "status": k.status,
            "request_hash": k.request_hash,
            "response_code": k.response_code,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
        }
        for k in keys
    ]
