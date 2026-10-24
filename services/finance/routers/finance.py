"""Finance router — exposes LedgerService, WalletService, PaymentProvider, and Reconciliation."""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import (
    ComPaymentIntent,
    EcoWallet,
    FinAccount,
    FinIdempotencyKey,
)
from services.api_gateway.auth import require_admin, require_api_key, require_user
from services.api_gateway.errors import domain_detail
from services.api_gateway.exceptions import EcoNojinException
from services.finance import earning_rates
from services.finance.ai_agent import FinanceAIAgent
from services.finance.automated_marketplace_settlement import (
    AutomatedMarketplaceSettlementService,
    SettlementBatch,
    SettlementResult,
)
from services.finance.chart_of_accounts import (
    ACCOUNT_ASSETS,
    ACCOUNT_TYPES,
    UnknownAccountCode,
    ensure_account,
)
from services.finance.ledger_service import LedgerService
from services.finance.open_banking_rtp import (
    _LazyOpenBankingProvider,
    _LazyRTPProvider,
)
from services.finance.payment_provider import (
    BANK_CALLBACK_SIGNATURE_HEADER,
    BANK_CALLBACK_SIGNATURE_HEADER_ALT,
    BANK_WEBHOOK_SECRET_ENV,
    BankTransferProvider,
    WebhookEvent,
    payment_registry,
    verify_bank_callback,
)
from services.finance.reconciliation import ReconciliationService
from services.finance.wallet_service import WalletService

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


class _LazyBankTransferProvider(BankTransferProvider):
    """``bank_transfer`` provider whose database session is bound per call.

    Registration stays on the import path so the provider is reachable before
    any order flow constructs an ``OrderService``, but the *engine* does not: an
    engine resolved while this module is imported is bound to the event loop
    that happened to be running (or to no loop at all, during collection), so
    the session built on it is stale for every later request and the import
    itself fails whenever the hub's async engine is not initialised yet — an
    ordering hazard that only surfaces in some full-suite runs. Instantiating
    this provider therefore performs no I/O and cannot fail.
    """

    def __init__(self) -> None:
        self.db: AsyncSession | None = None

    @asynccontextmanager
    async def _session(self):
        """Bind the provider to one hub session for a single operation.

        The session is never carried across calls: a failed transaction leaves
        a session that SQLAlchemy requires be rolled back before reuse, and
        holding one open keeps a checkout on the shared-cache engine's single
        pooled connection. ``hub.get_async_session`` also ensures the async
        engine (and its tables) exist for the loop actually running, mirroring
        what ``get_db`` gives the route.
        """
        async with hub.get_async_session() as session:
            self.db = session
            try:
                yield session
            finally:
                self.db = None

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ):
        async with self._session():
            return await super().create_payment_intent(
                amount=amount,
                currency=currency,
                order_id=order_id,
                metadata=metadata,
                idempotency_key=idempotency_key,
            )

    async def verify_transfer(
        self,
        payment_id,
        transferred_amount: Decimal,
        verified_by: str,
        description: str | None = None,
    ):
        async with self._session():
            return await super().verify_transfer(
                payment_id, transferred_amount, verified_by, description
            )

    async def cancel_payment(self, payment_id: str, reason: str):
        async with self._session():
            return await super().cancel_payment(payment_id, reason)


def _ensure_bank_transfer_registered() -> None:
    """Make ``provider=bank_transfer`` usable without an order flow.

    The registry was populated only by ``OrderService.__init__`` (the wallet
    provider, services/commerce/service.py), so ``POST /payments/intent`` raised
    ``ValueError`` until some order flow happened to construct an
    ``OrderService``. Called at import time and again from the payment-intent
    route. The guard is the registry's own key set — the same check
    ``OrderService.__init__`` makes for ``wallet`` — so a repeat import, a
    second call or a later commerce construction never duplicates the provider
    and never replaces one another component installed (a test binding its own
    instance on a fixture session keeps it).
    """
    if "bank_transfer" not in [p.provider_name for p in payment_registry.get_all()]:
        payment_registry.register(_LazyBankTransferProvider())


_ensure_bank_transfer_registered()


def _ensure_open_banking_registered() -> None:
    if "open_banking" not in [p.provider_name for p in payment_registry.get_all()]:
        payment_registry.register(_LazyOpenBankingProvider())


def _ensure_rtp_registered() -> None:
    if "rtp" not in [p.provider_name for p in payment_registry.get_all()]:
        payment_registry.register(_LazyRTPProvider())


_ensure_open_banking_registered()
_ensure_rtp_registered()


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


_EARNING_CATEGORY_PATTERN = r"^(" + "|".join(
    sorted(set(earning_rates.EARNING_RATES) | set(earning_rates.LEGACY_CATEGORY_ALIASES))
) + r")$"
_REDEMPTION_CATEGORY_PATTERN = (
    r"^(" + "|".join(sorted(earning_rates.REDEMPTION_RATES)) + r")$"
)


class EarnRequest(BaseModel):
    category: str = Field(..., pattern=_EARNING_CATEGORY_PATTERN)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    idempotency_key: str | None = None
    reference_id: str | None = None


class EarnResponse(BaseModel):
    amount_earned: Decimal
    new_balance: Decimal
    category: str


class RedeemRequest(BaseModel):
    category: str = Field(..., pattern=_REDEMPTION_CATEGORY_PATTERN)
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


_ACCOUNT_ASSET_PATTERN = r"^(" + "|".join(sorted(ACCOUNT_ASSETS)) + r")$"


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
    is_active: bool | None = None,
    parent_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_user)] = None,
):
    """List the chart of accounts.

    Each filter is applied only when the caller supplies it: an omitted
    ``is_active`` no longer silently hides deactivated accounts, and
    ``parent_id`` lists one node's children.
    """
    stmt = select(FinAccount)
    if asset:
        stmt = stmt.where(FinAccount.asset == asset)
    if is_active is not None:
        stmt = stmt.where(FinAccount.is_active == is_active)
    if parent_id is not None:
        # ``parent_id`` is a String column holding the parent's decimalised key,
        # so the integer from the query is compared as text.
        stmt = stmt.where(FinAccount.parent_id == str(parent_id))
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [
        AccountResponse(
            id=a.id,
            code=a.code,
            name=a.name,
            type=a.type,
            asset=a.asset,
            currency=a.currency,
            is_active=a.is_active,
        )
        for a in accounts
    ]


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    code: Annotated[str, Query(pattern=r"^[A-Z0-9_]{2,64}$")],
    name: Annotated[str, Query(min_length=1, max_length=200)],
    type: Annotated[str, Query()],
    asset: Annotated[str, Query(pattern=_ACCOUNT_ASSET_PATTERN)],
    currency: Annotated[str, Query(pattern=r"^[A-Z]{3,10}$")] = "IRR",
    parent_code: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool, Query()] = True,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """Create (or re-read) a chart-of-accounts entry.

    ``parent_code`` is resolved through the chart, so a canonical parent that
    has not been seeded yet is created rather than rejected, while a code that
    is neither a row nor in the chart is a 422. The insert itself is the
    get-or-create in ``chart_of_accounts.ensure_account``: it is a single code
    and it is race-safe, so a repeated POST returns the existing row instead of
    a unique-violation 500.
    """
    if type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown account type: {type!r}. Expected one of {sorted(ACCOUNT_TYPES)}",
        )

    result = await db.execute(select(FinAccount).where(FinAccount.code == code))
    created = result.scalar_one_or_none() is None

    try:
        account = await ensure_account(
            db,
            code=code,
            name=name,
            type=type,
            asset=asset,
            currency=currency,
            parent_code=parent_code,
        )
    except UnknownAccountCode as e:
        raise HTTPException(status_code=422, detail=domain_detail(e, 422)) from e

    # A new account honours the requested state; an existing one is returned
    # the way it is, so a repeat POST is not a silent state change.
    if created and not is_active:
        account.is_active = False

    await db.commit()
    await db.refresh(account)
    return AccountResponse(
        id=account.id,
        code=account.code,
        name=account.name,
        type=account.type,
        asset=account.asset,
        currency=account.currency,
        is_active=account.is_active,
    )


# ---------------------------------------------------------------------------
# Ledger (double-entry)
# ---------------------------------------------------------------------------


@router.post("/ledger/batch", response_model=JournalBatchResponse)
async def create_journal_batch(
    body: JournalBatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
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
            created_by=str(user.id) if hasattr(user, "id") else str(user.get("id")),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=400, detail=e.message) from e

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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    service = LedgerService(db)
    try:
        batch = await service.post_journal_batch(batch_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    return {
        "batch_id": batch.id,
        "is_posted": batch.is_posted,
        "posted_at": batch.posted_at.isoformat() if batch.posted_at else None,
    }


@router.get("/ledger/accounts/{account_id}/balance", response_model=dict)
async def get_account_balance(
    account_id: str,
    asset: str = "ECO",
    as_of: datetime | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_user)] = None,
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
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_user)] = None,
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


class TrialBalanceRow(BaseModel):
    account_id: str
    asset: str
    debit_balance: str
    credit_balance: str
    total_debits: str
    total_credits: str


class TrialBalanceTotals(BaseModel):
    asset: str
    debit: str
    credit: str
    balanced: bool


class TrialBalanceResponse(BaseModel):
    as_of: str | None
    rows: list[TrialBalanceRow]
    totals: list[TrialBalanceTotals]


VALID_TRIAL_BALANCE_ASSETS = {"IRR", "ECO", "CARBON_tCO2e", "USD"}


# ---------------------------------------------------------------------------
# Reporting — auditor's trial balance (admin only)
# ---------------------------------------------------------------------------


@router.get("/ledger/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    as_of: date | None = None,
    asset: Literal["IRR", "ECO", "CARBON_tCO2e", "USD"] | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """تراز آزمایشی حسابداری (فقط ادمین): فقط اسناد posted؛ تفکیک بر اساس حساب و دارایی.

    Auditor's trial balance over posted journal batches (admin only).
    """
    service = LedgerService(db)
    report = await service.trial_balance(as_of=as_of, asset=asset)
    return TrialBalanceResponse(
        as_of=as_of.isoformat() if as_of else None,
        rows=report["rows"],
        totals=report["totals"],
    )


class ProfitAndLossLine(BaseModel):
    account_id: str
    account_code: str | None
    account_name: str | None
    asset: str
    amount: str


class ProfitAndLossTotals(BaseModel):
    asset: str
    income: str
    expense: str
    net: str
    profitable: bool


class ProfitAndLossResponse(BaseModel):
    from_date: str | None
    to_date: str | None
    asset: str | None
    income: list[ProfitAndLossLine]
    expense: list[ProfitAndLossLine]
    unclassified: list[dict]
    totals: list[ProfitAndLossTotals]


# ---------------------------------------------------------------------------
# Reporting — profit & loss (admin only)
# ---------------------------------------------------------------------------


@router.get("/ledger/profit-and-loss", response_model=ProfitAndLossResponse)
async def get_profit_and_loss(
    from_date: date | None = None,
    to_date: date | None = None,
    asset: Literal["IRR", "ECO", "CARBON_tCO2e", "USD"] | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """گزارش سود و زیان (فقط ادمین): درآمد و هزینه از اسناد posted در بازه تاریخ.

    Profit & loss over posted journal batches (admin only). Accounts referenced
    by entries but missing from the chart of accounts are surfaced in
    ``unclassified`` instead of being silently dropped.
    """
    service = LedgerService(db)
    return await service.profit_and_loss(from_date=from_date, to_date=to_date, asset=asset)


# ---------------------------------------------------------------------------
# Wallet (uses finance service)
# ---------------------------------------------------------------------------


@router.get("/wallet", response_model=WalletBalanceResponse)
async def get_wallet(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    service = WalletService(db)
    state = await service.get_wallet_state(
        str(user.id) if hasattr(user, "id") else str(user.get("id"))
    )
    return WalletBalanceResponse(**state)


@router.post("/wallet/earn", response_model=EarnResponse)
async def earn_tokens(
    body: EarnRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    service = WalletService(db)
    try:
        amount, balance = await service.earn(
            user_id=str(user.id) if hasattr(user, "id") else str(user.get("id")),
            category=earning_rates.resolve_category(body.category),
            quantity=body.quantity,
            reference_id=body.reference_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return EarnResponse(amount_earned=amount, new_balance=balance, category=body.category)


@router.post("/wallet/redeem", response_model=RedeemResponse)
async def redeem_tokens(
    body: RedeemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    service = WalletService(db)
    try:
        amount, balance = await service.redeem(
            user_id=str(user.id) if hasattr(user, "id") else str(user.get("id")),
            category=body.category,
            reference_id=body.reference_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return RedeemResponse(amount_redeemed=amount, new_balance=balance, category=body.category)


@router.get("/wallet/stats", response_model=dict)
async def wallet_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    # Registration is idempotent and does no I/O: it is a no-op here unless
    # something replaced the registry entry, and it keeps the endpoint usable
    # even when no order flow ever constructed an OrderService.
    _ensure_bank_transfer_registered()
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


def _parse_bank_transfer_callback(raw_body: bytes, signature: str) -> WebhookEvent:
    """Normalise a bank push callback into the shared ``WebhookEvent`` shape.

    ``BankTransferProvider.verify_webhook`` raises ``NotImplementedError`` — a
    bank transfer is verified against the recorded amount, not against a signed
    provider envelope — so the route cannot lean on it. This parser is the
    bank-side equivalent and is deliberately strict: a payload that does not
    carry a resolvable payment is a 400, never a silent success.

    ``signature`` is accepted for parity with ``verify_webhook`` and kept out
    of the event on purpose: the route has already verified the HMAC over
    ``raw_body`` (``verify_bank_callback``) before this parser runs, so this
    layer sees only an authenticated body and the header value is carried
    unchanged for traceability rather than re-checked here.
    """
    try:
        payload = json.loads(raw_body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail="Webhook payload is not valid JSON") from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object")

    payment_id = (
        payload.get("payment_id")
        or payload.get("id")
        or payload.get("provider_reference")
        or payload.get("reference_number")
    )
    if not payment_id:
        raise HTTPException(status_code=400, detail="Webhook payload is missing 'payment_id'")

    try:
        amount = Decimal(str(payload.get("amount", "")))
    except (InvalidOperation, ValueError) as e:
        raise HTTPException(
            status_code=400, detail="Webhook payload has an invalid 'amount'"
        ) from e

    return WebhookEvent(
        provider="bank_transfer",
        event_type=str(payload.get("event_type") or "transfer.settled"),
        provider_event_id=str(payload.get("event_id") or f"bt-{payment_id}-{amount}"),
        payment_id=str(payment_id),
        amount=amount,
        currency=str(payload.get("currency") or "IRR"),
        status=str(payload.get("status") or "succeeded"),
        raw_payload=payload,
        received_at=datetime.now(UTC),
    )


async def _bank_transfer_webhook(event: WebhookEvent, db: AsyncSession) -> dict:
    """Map a bank callback onto ``BankTransferProvider.verify_transfer``.

    The provider's own verification path is reused verbatim: it persists the
    status transition, keeps the partial/full/already-verified semantics and
    writes the immutable ``AuditEvent``. ``PaymentProvider`` declares no
    ``handle_webhook``, so this adapter — not a provider method — is what the
    route dispatches to.

    A redelivered callback is acknowledged as a no-op instead of a 500: the
    provider raises ``ALREADY_VERIFIED`` for a payment it has already settled,
    which is exactly the idempotent answer a webhook redelivery expects.
    """
    provider = BankTransferProvider(db)
    try:
        intent = await provider.verify_transfer(
            payment_id=event.payment_id,
            transferred_amount=event.amount,
            verified_by=f"webhook:{event.provider_event_id}",
            description=f"bank callback {event.event_type}",
        )
    except EcoNojinException as e:
        if e.code == "ALREADY_VERIFIED":
            return {
                "payment_id": event.payment_id,
                "status": "succeeded",
                "amount": str(event.amount),
                "duplicate": True,
            }
        raise HTTPException(
            status_code=e.status_code if 400 <= e.status_code < 500 else 400,
            detail=e.message,
        ) from e

    if intent is None:
        raise HTTPException(status_code=404, detail=f"Unknown payment: {event.payment_id}")

    return {
        "payment_id": intent.id,
        "status": intent.status,
        "amount": str(intent.amount),
        "currency": intent.currency,
        "duplicate": False,
    }


def _bank_webhook_secret() -> bytes:
    """Read the bank's shared secret from the environment, per request.

    ``os.environ`` rather than a module constant, for the same reason
    ``BankTransferProvider._bank_account`` reads ``BANK_TRANSFER_SHEBA`` that
    way: the value is deployment configuration, and reading it at call time
    means rotation does not need a code change and a test can provision one
    without reaching into a module global. It deliberately does **not** fall
    back to ``SECRET_KEY``/``JWT_SECRET`` — reusing signing material for a
    webhook means rotating the token key silently invalidates every bank's
    signature, and a secret shared across two trust relationships is not a
    secret either of them controls.

    An empty (or whitespace-only) value means *not configured*; the caller
    rejects rather than continuing, because an empty HMAC key is a valid key
    and would make the signature check satisfiable by anyone holding this
    source file.
    """
    return os.environ.get(BANK_WEBHOOK_SECRET_ENV, "").strip().encode("utf-8")


@router.post("/payments/webhook/{provider_name}")
async def payment_webhook(
    provider_name: str,
    request: Request,
    api_key: Annotated[str, Depends(require_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    raw_body = await request.body()

    # Authenticity before anything else. The body names a payment and the
    # amount the bank says was transferred for it, so accepting an unsigned
    # one is accepting a request to mark someone else's intent paid.
    # ``require_api_key`` stays as the second factor, but while
    # ``telco_webhook_key`` is empty it admits any caller outside production,
    # which is exactly why this check cannot be the optional one.
    secret = _bank_webhook_secret()
    if not secret:
        # Fail closed: an unconfigured secret must not become an open door.
        raise HTTPException(
            status_code=503,
            detail=(
                f"{BANK_WEBHOOK_SECRET_ENV} is not configured; "
                "bank webhook callbacks are refused until it is set"
            ),
        )
    signature = request.headers.get(BANK_CALLBACK_SIGNATURE_HEADER) or request.headers.get(
        BANK_CALLBACK_SIGNATURE_HEADER_ALT
    )
    if not verify_bank_callback(secret, raw_body, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid bank callback signature")

    try:
        payment_registry.get(provider_name)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Unknown payment provider: {provider_name}"
        ) from e

    if provider_name != "bank_transfer":
        # No registered provider implements a webhook handler (the previous
        # ``provider.handle_webhook`` call existed nowhere and raised
        # AttributeError), and none but bank_transfer even parses a callback.
        raise HTTPException(
            status_code=501,
            detail=f"Provider {provider_name!r} does not support webhook callbacks",
        )

    event = _parse_bank_transfer_callback(raw_body, signature or "")
    outcome = await _bank_transfer_webhook(event, db)
    return {"processed": True, "event_id": event.provider_event_id, "outcome": outcome}


# ---------------------------------------------------------------------------
# Open Banking + RTP payment intents (Phase 8)
# ---------------------------------------------------------------------------


class OpenBankingIntentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = "IRR"
    order_id: str
    iban: str | None = None
    bic: str | None = None
    buyer_id: str | None = None


class RTPIntentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = "IRR"
    order_id: str
    buyer_id: str | None = None


@router.post("/payments/open-banking/intent", response_model=dict)
async def create_open_banking_intent(
    body: OpenBankingIntentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    """Create an Open Banking (PSD2) payment intent.

    Initiates a bank transfer from the user's linked account. Requires
    ``OPEN_BANKING_BASE_URL``, ``OPEN_BANKING_CLIENT_ID`` and
    ``OPEN_BANKING_SECRET`` to be configured; otherwise returns 503.
    """
    _ensure_open_banking_registered()
    provider = payment_registry.get("open_banking")
    intent = await provider.create_payment_intent(
        amount=body.amount,
        currency=body.currency,
        order_id=body.order_id,
        metadata={
            "buyer_id": body.buyer_id,
            "iban": body.iban,
            "bic": body.bic,
        },
        idempotency_key=str(uuid4()),
    )
    return {
        "id": intent.id,
        "amount": str(intent.amount),
        "currency": intent.currency,
        "status": intent.status,
        "provider": intent.provider,
        "provider_reference": intent.provider_reference,
        "metadata": intent.metadata,
    }


@router.post("/payments/rtp/intent", response_model=dict)
async def create_rtp_intent(
    body: RTPIntentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    """Create a Real-Time Payment (RTP) intent.

    Settles instantly, 24/7/365, irrevocable. Ideal for escrow release,
    marketplace payouts and village development fund disbursement. Requires
    ``RTP_BASE_URL`` and ``RTP_API_KEY`` to be configured; otherwise returns
    503.
    """
    _ensure_rtp_registered()
    provider = payment_registry.get("rtp")
    intent = await provider.create_payment_intent(
        amount=body.amount,
        currency=body.currency,
        order_id=body.order_id,
        metadata={"buyer_id": body.buyer_id},
        idempotency_key=str(uuid4()),
    )
    return {
        "id": intent.id,
        "amount": str(intent.amount),
        "currency": intent.currency,
        "status": intent.status,
        "provider": intent.provider,
        "provider_reference": intent.provider_reference,
        "metadata": intent.metadata,
    }


@router.post("/payments/webhook/open-banking")
async def open_banking_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Open Banking payment status webhook.

    The bank signs the callback with HMAC-SHA256 using
    ``OPEN_BANKING_SECRET``. Verifies the signature and marks the payment
    succeeded/failed accordingly.
    """
    _ensure_open_banking_registered()
    provider = payment_registry.get("open_banking")
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")
    try:
        event = await provider.verify_webhook(raw_body, signature)
    except EcoNojinException as e:
        raise HTTPException(
            status_code=e.status_code if 400 <= e.status_code < 500 else 400,
            detail=e.message,
        ) from e

    # Map webhook status to payment intent status.
    intent = await db.execute(
        select(ComPaymentIntent).where(ComPaymentIntent.id == event.payment_id)
    )
    payment = intent.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail=f"Unknown payment: {event.payment_id}")

    status_map = {
        "ACCP": "succeeded",
        "ACSC": "succeeded",
        "RCVD": "processing",
        "RJCT": "failed",
        "paymentCompleted": "succeeded",
        "paymentFailed": "failed",
    }
    new_status = status_map.get(event.status, "processing")
    payment.status = new_status
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {
        "processed": True,
        "payment_id": payment.id,
        "status": payment.status,
        "event_id": event.provider_event_id,
    }


@router.post("/payments/webhook/rtp")
async def rtp_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """RTP payment status webhook.

    The switch signs the callback with HMAC-SHA256 using ``RTP_API_KEY``.
    RTP is irrevocable by design — once succeeded, the payment cannot be
    refunded through this provider.
    """
    _ensure_rtp_registered()
    provider = payment_registry.get("rtp")
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")
    try:
        event = await provider.verify_webhook(raw_body, signature)
    except EcoNojinException as e:
        raise HTTPException(
            status_code=e.status_code if 400 <= e.status_code < 500 else 400,
            detail=e.message,
        ) from e

    intent = await db.execute(
        select(ComPaymentIntent).where(ComPaymentIntent.id == event.payment_id)
    )
    payment = intent.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail=f"Unknown payment: {event.payment_id}")

    new_status = "succeeded" if event.status in ("completed", "ACSC") else "failed"
    payment.status = new_status
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {
        "processed": True,
        "payment_id": payment.id,
        "status": payment.status,
        "event_id": event.provider_event_id,
    }


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


@router.post("/reconciliation/wallet-ledger", response_model=dict)
async def reconcile_wallet_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    service = ReconciliationService(db)
    return await service.reconcile_wallet_ledger()


@router.post("/reconciliation/full", response_model=dict)
async def full_reconciliation(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
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
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
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


@router.get("/reconciliation/user/{user_id}")
async def admin_user_reconciliation(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """The five money stores for one user, side by side (D-10 / KN-02).

    The sanctioned per-user attribution view: it reports the stores beside each
    other under the shared `users.id` key with the source named for each
    figure — it never merges them and never presents an empty store as zero.
    Admin-scoped: the figures are personal financial records.
    """
    from services.finance.cross_ledger_report import reconcile_ledgers_by_user

    return await reconcile_ledgers_by_user(db, user_id)


# ---------------------------------------------------------------------------
# AI Agent — settlement & reconciliation (Phase 7)
# ---------------------------------------------------------------------------


class AIDetectRequest(BaseModel):
    as_of: str | None = None
    auto_post: bool = False
    confidence_floor: float = Field(default=0.0, ge=0.0, le=1.0)


class AIProposalResponse(BaseModel):
    type: str
    severity: str
    action: str
    description: str | None = None
    confidence: float | None = None
    batch_id: int | None = None
    batch_number: str | None = None
    error: str | None = None


class AIDetectResponse(BaseModel):
    checked_at: str
    as_of: str | None
    auto_post: bool
    total_proposals: int
    posted: list[AIProposalResponse]
    suggested: list[AIProposalResponse]


class AIStatusResponse(BaseModel):
    agent: str
    version: str
    auto_post_enabled: bool
    confidence_threshold: float
    valid_assets: list[str]


AIA_CONFIDENCE_THRESHOLD = 0.95
AIA_VALID_ASSETS = ["IRR", "ECO", "CARBON_tCO2e", "USD"]


@router.post("/ai/detect", response_model=AIDetectResponse)
async def ai_detect(
    body: AIDetectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    """Run the AI settlement & reconciliation agent.

    Detects wallet-vs-ledger drift, order/payment/settlement mismatches,
    inventory on-hand drift, and unbalanced journal batches. Returns proposed
    correcting journal entries. When ``auto_post=true``, proposals at or above
    the confidence threshold are posted immediately; otherwise they are
    returned as drafts for admin review.
    """
    as_of = None
    if body.as_of:
        try:
            as_of = datetime.fromisoformat(body.as_of)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid as_of timestamp (use ISO-8601)"
            ) from exc

    agent = FinanceAIAgent(db, auto_post=body.auto_post)
    result = await agent.detect_and_propose(
        as_of=as_of,
        confidence_floor=Decimal(str(body.confidence_floor)),
    )

    def _map_proposal(p: dict) -> AIProposalResponse:
        return AIProposalResponse(
            type=p.get("type", ""),
            severity=p.get("severity", ""),
            action=p.get("action", ""),
            description=p.get("description"),
            confidence=float(p.get("confidence", 0)) if p.get("confidence") else None,
            batch_id=p.get("batch_id"),
            batch_number=p.get("batch_number"),
            error=p.get("error"),
        )

    return AIDetectResponse(
        checked_at=result["checked_at"],
        as_of=result.get("as_of"),
        auto_post=result["auto_post"],
        total_proposals=result["total_proposals"],
        posted=[_map_proposal(p) for p in result.get("posted", [])],
        suggested=[_map_proposal(p) for p in result.get("suggested", [])],
    )


@router.get("/ai/status", response_model=AIStatusResponse)
async def ai_status(
    user: Annotated[dict, Depends(require_admin)],
):
    """Report the AI agent configuration and thresholds."""
    return AIStatusResponse(
        agent="finance_ai_agent",
        version="1.0.0",
        auto_post_enabled=False,
        confidence_threshold=AIA_CONFIDENCE_THRESHOLD,
        valid_assets=AIA_VALID_ASSETS,
    )


# ---------------------------------------------------------------------------
# Idempotency utility
# ---------------------------------------------------------------------------


@router.post("/marketplace/settle-batch", response_model=dict)
async def settle_marketplace_batch(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """Run the automated settlement pipeline for eligible delivered orders.

    For each order:
    1. CBDCProvider.transfer (simulated if CBDC_ENDPOINT_URL unset)
    2. CarbonCreditProvider.issue for the ecosystem fee
    3. LedgerService.create_journal_batch (balanced double-entry)
    4. ComSettlement row + AuditEvent + SSE outbox event

    Returns a summary of settled / errored orders.
    """
    service = AutomatedMarketplaceSettlementService(db)
    batch: SettlementBatch = await service.settle_batch(limit=limit)

    return {
        "settled_count": len(batch.settled),
        "error_count": len(batch.errors),
        "errors": batch.errors,
        "settled": [
            {
                "order_id": r.order_id,
                "status": r.status,
                "seller_amount": str(r.seller_amount),
                "platform_fee": str(r.platform_fee),
                "landscape_fee": str(r.landscape_fee),
                "cbdc_transaction_id": r.cbdc_transaction_id,
                "carbon_credit_id": r.carbon_credit_id,
                "journal_batch_id": r.journal_batch_id,
                "settled_at": r.settled_at,
            }
            for r in batch.settled
        ],
    }


@router.post("/marketplace/settle/{order_id}", response_model=dict)
async def settle_single_order(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """Settle a single marketplace order by ID."""
    service = AutomatedMarketplaceSettlementService(db)
    result: SettlementResult = await service.settle_order(order_id)

    return {
        "order_id": result.order_id,
        "status": result.status,
        "seller_amount": str(result.seller_amount),
        "platform_fee": str(result.platform_fee),
        "landscape_fee": str(result.landscape_fee),
        "cbdc_transaction_id": result.cbdc_transaction_id,
        "carbon_credit_id": result.carbon_credit_id,
        "journal_batch_id": result.journal_batch_id,
        "settled_at": result.settled_at,
    }


@router.get("/marketplace/eligible-orders", response_model=list[dict])
async def get_eligible_orders(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_admin)] = None,
):
    """List orders that are eligible for automated settlement."""
    service = AutomatedMarketplaceSettlementService(db)
    orders = await service.find_eligible_orders(limit=limit)

    return [
        {
            "id": order.id,
            "order_number": order.order_number,
            "buyer_id": order.buyer_id,
            "seller_id": order.seller_id,
            "status": order.status,
            "payment_status": order.payment_status,
            "currency": order.currency,
            "total": str(order.total),
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        for order in orders
    ]


# ---------------------------------------------------------------------------
# Idempotency utility
# ---------------------------------------------------------------------------
