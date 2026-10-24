"""Carbon Credits + CBDC router — Phase 9.

Exposes the carbon credit lifecycle (issue, transfer, retire), tokenized carbon
credit management (mint, transfer, burn), CBDC settlement, and the swap market,
all mounted under ``/finance/carbon-credits/*``.

Endpoints:
  GET    /carbon-credits/                  — portfolio summary
  GET    /carbon-credits/credits             — list carbon credits held
  POST   /carbon-credits/credits/issue       — issue a new carbon credit
  POST   /carbon-credits/credits/{id}/transfer — transfer a carbon credit
  POST   /carbon-credits/credits/{id}/retire  — retire a carbon credit
  GET    /carbon-credits/tokens/balance/{address} — token balance
  POST   /carbon-credits/tokens/mint         — mint tokenized credits
  POST   /carbon-credits/tokens/transfer     — transfer tokenized credits
  POST   /carbon-credits/cbdc/transfer       — CBDC RTGS settlement (503 if unconfigured)
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import ComPaymentIntent
from services.api_gateway.auth import require_admin, require_user
from services.finance.carbon_cbdc import (
    CarbonCreditProvider,
    CarbonSwapProvider,
    CarbonTokenProvider,
    CBDCProvider,
)

router = APIRouter(prefix="/api/v1/finance/carbon-credits", tags=["finance", "carbon_credits"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic schemas
# ═══════════════════════════════════════════════════════════════════════════════


class IssueCreditRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    holder_id: str = Field(..., min_length=1)
    serial: str | None = None
    vintage_year: int | None = None
    methodology: str | None = None
    credit_type: str | None = None


class TransferCreditRequest(BaseModel):
    from_holder: str = Field(..., min_length=1)
    to_holder: str = Field(..., min_length=1)


class RetireCreditRequest(BaseModel):
    owner: str = Field(..., min_length=1)
    justification: str = ""


class MintTokenRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    recipient_address: str | None = None
    credit_type: str = "VCS"


class TransferTokenRequest(BaseModel):
    token_id: str = Field(..., min_length=1)
    from_address: str = Field(..., min_length=1)
    to_address: str = Field(..., min_length=1)


class BurnTokenRequest(BaseModel):
    token_id: str = Field(..., min_length=1)
    owner_address: str = Field(..., min_length=1)
    justification: str = ""


class CBDCTransferRequest(BaseModel):
    from_address: str = Field(..., min_length=1)
    to_address: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    order_id: str | None = None


class SwapQuoteRequest(BaseModel):
    credit_amount: Decimal = Field(..., gt=0)
    target_currency: str = "USD"


class SwapExecuteRequest(BaseModel):
    credit_id: str = Field(..., min_length=1)
    holder_id: str = Field(..., min_length=1)
    target_currency: str = "USD"
    target_address: str = Field(..., min_length=1)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Portfolio summary
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/", response_model=dict)
async def get_carbon_portfolio(
    holder_id: Annotated[str | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_user)] = None,
):
    """Get a portfolio summary: total carbon credits + token balances for a holder."""
    current_user = str(user.id) if hasattr(user, "id") else str(user.get("id"))
    target_holder = holder_id or current_user

    provider = CarbonCreditProvider(db)
    token_provider = CarbonTokenProvider(db)

    try:
        balance = await provider.get_balance(target_holder)
    except Exception:
        balance = Decimal("0")

    try:
        token_balance = await token_provider.balance(target_holder)
    except Exception:
        token_balance = {"owner_address": target_holder, "token_balance": 0}

    return {
        "holder_id": target_holder,
        "carbon_credits_balance": str(balance),
        "carbon_credits_unit": "tCO2e",
        "token_balance": token_balance,
        "as_of": datetime.now(UTC).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. List carbon credits
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/credits", response_model=list[dict])
async def list_carbon_credits(
    holder_id: Annotated[str | None, Query()] = None,
    retired: Annotated[bool | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[dict, Depends(require_user)] = None,
):
    """List carbon credits held by a holder, optionally filtering retired."""
    current_user = str(user.id) if hasattr(user, "id") else str(user.get("id"))
    target_holder = holder_id or current_user

    provider = CarbonCreditProvider(db)
    try:
        return await provider.list_credits(holder_id=target_holder, retired=retired)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Carbon credit provider unavailable: {e}",
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Issue a new carbon credit
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/credits/issue", response_model=dict)
async def issue_carbon_credit(
    body: IssueCreditRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    """Issue a new carbon credit to a holder."""
    provider = CarbonCreditProvider(db)
    try:
        result = await provider.issue(
            project_id=body.project_id,
            amount=body.amount,
            holder_id=body.holder_id,
            metadata={
                "serial": body.serial,
                "vintage_year": body.vintage_year,
                "methodology": body.methodology,
                "credit_type": body.credit_type,
                "issued_by": str(user.id) if hasattr(user, "id") else str(user.get("id")),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Carbon credit provider unavailable: {e}",
        ) from e

    return {
        "credit_id": result.credit_id,
        "status": result.status,
        "amount": str(result.amount),
        "holder_id": result.holder_id,
        "metadata": result.metadata,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Transfer a carbon credit
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/credits/{credit_id}/transfer", response_model=dict)
async def transfer_carbon_credit(
    credit_id: str,
    body: TransferCreditRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    """Transfer a carbon credit from one holder to another."""
    provider = CarbonCreditProvider(db)
    try:
        result = await provider.transfer(
            credit_id=credit_id,
            from_holder=body.from_holder,
            to_holder=body.to_holder,
            metadata={"initiated_by": str(user.id) if hasattr(user, "id") else str(user.get("id"))},
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return {
        "credit_id": result.credit_id,
        "status": result.status,
        "holder_id": result.holder_id,
        "metadata": result.metadata,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Retire a carbon credit
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/credits/{credit_id}/retire", response_model=dict)
async def retire_carbon_credit(
    credit_id: str,
    body: RetireCreditRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)],
):
    """Permanently retire a carbon credit (remove from circulation)."""
    provider = CarbonCreditProvider(db)
    try:
        result = await provider.retire(
            credit_id=credit_id,
            owner=body.owner,
            justification=body.justification,
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return {
        "credit_id": result.credit_id,
        "status": result.status,
        "retired_amount": str(result.retired_amount),
        "justification": result.metadata.get("justification", ""),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Token balance
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/tokens/balance/{address}", response_model=dict)
async def get_token_balance(
    address: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)] = None,
):
    """Get the tokenized carbon credit balance for an address."""
    provider = CarbonTokenProvider(db)
    try:
        return await provider.balance(address)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Carbon token provider unavailable: {e}",
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Mint tokenized carbon credits
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/tokens/mint", response_model=dict)
async def mint_tokenized_credit(
    body: MintTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    """Mint tokenized carbon credits on-chain (falls back to simulation)."""
    provider = CarbonTokenProvider(db)
    try:
        result = await provider.mint(
            project_id=body.project_id,
            amount=body.amount,
            recipient_address=body.recipient_address,
            credit_type=body.credit_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return {
        "token_id": result.get("token_id"),
        "status": result.get("status"),
        "amount_tonnes": result.get("amount_tonnes"),
        "transaction_hash": result.get("transaction_hash"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Transfer tokenized carbon credits
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/tokens/transfer", response_model=dict)
async def transfer_tokenized_credit(
    body: TransferTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)] = None,
):
    """Transfer a tokenized carbon credit (on-chain, falls back to simulation).

    The transfer is wired to the ``CarbonTokenService.transfer_credits`` stub
    which performs an in-memory simulation when no RPC endpoint is available.
    """
    provider = CarbonTokenProvider(db)
    try:
        result = await provider.transfer_token(
            token_id=body.token_id,
            from_address=body.from_address,
            to_address=body.to_address,
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return {
        "token_id": result.get("token_id"),
        "from": result.get("from"),
        "to": result.get("to"),
        "status": result.get("status"),
        "transaction_hash": result.get("transaction_hash"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 9. CBDC RTGS settlement (fail-closed: 503 if CBDC_ENDPOINT_URL unset)
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/cbdc/transfer", response_model=dict)
async def cbdc_transfer(
    body: CBDCTransferRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)] = None,
):
    """Initiate a CBDC RTGS transfer for carbon credit settlement.

    Requires ``CBDC_ENDPOINT_URL`` to be configured; otherwise returns 503.
    """
    provider = CBDCProvider(db)
    try:
        result = await provider.transfer(
            from_address=body.from_address,
            to_address=body.to_address,
            amount=body.amount,
            currency=body.currency,
            metadata={"order_id": body.order_id} if body.order_id else {},
            idempotency_key=str(uuid4()),
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return {
        "transaction_id": result.transaction_id,
        "status": result.status,
        "amount": str(result.amount),
        "currency": result.currency,
        "from_address": result.from_address,
        "to_address": result.to_address,
        "transaction_hash": result.transaction_hash,
        "metadata": result.metadata,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CBDC webhook
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/cbdc/webhook")
async def cbdc_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """CBDC settlement webhook — fails closed if CBDC_ENDPOINT_URL is unset."""
    provider = CBDCProvider(db)
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")
    try:
        event = await provider.verify_webhook(raw_body, signature)
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    # Update the payment intent if referenced.
    payment_id = event.get("payment_id") or event.get("transaction_id")
    if payment_id:
        result = await db.execute(
            select(ComPaymentIntent).where(ComPaymentIntent.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = event.get("status", "succeeded")
            db.add(payment)
            await db.commit()

    return {"processed": True, "event": event.get("event_type", "settled")}


# ═══════════════════════════════════════════════════════════════════════════════
# Swap market
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/swap/quote", response_model=dict)
async def carbon_swap_quote(
    body: SwapQuoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_user)] = None,
):
    """Quote the conversion of carbon credits to a target currency."""
    provider = CarbonSwapProvider(db)
    try:
        return await provider.quote(body.credit_amount, body.target_currency)
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e


@router.post("/swap", response_model=dict)
async def carbon_swap(
    body: SwapExecuteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(require_admin)],
):
    """Execute a carbon credit swap (quote-only in this phase)."""
    provider = CarbonSwapProvider(db)
    try:
        result = await provider.swap(
            credit_id=body.credit_id,
            holder_id=body.holder_id,
            target_currency=body.target_currency,
            target_address=body.target_address,
        )
    except Exception as e:
        raise HTTPException(
            status_code=str(getattr(e, "status_code", 500)) if hasattr(e, "status_code") else 500,
            detail=str(e),
        ) from e

    return result
