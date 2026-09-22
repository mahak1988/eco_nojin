"""Commerce router — order state machine, payment intents, settlements."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import ComOrder, ComOrderItem, ComPaymentIntent
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.commerce.service import OrderService, OrderStateMachine

router = APIRouter(prefix="/api/v1/commerce", tags=["commerce"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OrderItemRequest(BaseModel):
    sku_code: str
    quantity: Decimal = Field(..., gt=0, le=9999)
    unit_price: Decimal | None = None
    warehouse_id: int | None = None


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: dict | None = None
    idempotency_key: str | None = None


class PaymentIntentRequest(BaseModel):
    order_id: str
    provider: str = "wallet"
    idempotency_key: str | None = None


class ShipRequest(BaseModel):
    order_id: str
    tracking_code: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Order endpoints
# ---------------------------------------------------------------------------


@router.post("/orders", response_model=dict)
async def create_order(
    body: OrderCreateRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)
):
    service = OrderService(db)
    try:
        order = await service.create_order(
            buyer_id=_uid(user),
            items=[i.model_dump() for i in body.items],
            shipping_address=body.shipping_address,
            idempotency_key=body.idempotency_key,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e

    items_result = await db.execute(select(ComOrderItem).where(ComOrderItem.order_id == order.id))
    items = items_result.scalars().all()
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "subtotal": str(order.subtotal),
        "platform_fee": str(order.platform_fee),
        "landscape_fee": str(order.landscape_fee),
        "total": str(order.total),
        "items": [
            {"sku_code": i.sku_code, "quantity": str(i.quantity), "unit_price": str(i.unit_price)}
            for i in items
        ],
        "allowed_transitions": list(OrderStateMachine.get_allowed_transitions(order.status)),
    }


@router.get("/orders/{order_id}", response_model=dict)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
    service = OrderService(db)
    try:
        order = await service.get_order(order_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 404, detail=e.message) from e
    items_result = await db.execute(select(ComOrderItem).where(ComOrderItem.order_id == order_id))
    items = items_result.scalars().all()
    payments_result = await db.execute(
        select(ComPaymentIntent).where(ComPaymentIntent.order_id == order_id)
    )
    payments = payments_result.scalars().all()
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "buyer_id": order.buyer_id,
        "status": order.status,
        "payment_status": order.payment_status,
        "subtotal": str(order.subtotal),
        "platform_fee": str(order.platform_fee),
        "landscape_fee": str(order.landscape_fee),
        "total": str(order.total),
        "currency": order.currency,
        "tracking_code": order.tracking_code,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": i.id,
                "sku_code": i.sku_code,
                "name": i.name,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "fulfilled_qty": str(i.fulfilled_qty),
            }
            for i in items
        ],
        "payments": [
            {"id": p.id, "provider": p.provider, "amount": str(p.amount), "status": p.status}
            for p in payments
        ],
        "allowed_transitions": list(OrderStateMachine.get_allowed_transitions(order.status)),
    }


@router.get("/orders", response_model=dict)
async def list_orders(
    status: str | None = None,
    buyer_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = OrderService(db)
    orders = await service.list_orders(
        buyer_id=buyer_id or _uid(user),
        status=status,
        limit=limit,
    )
    return {
        "orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "status": o.status,
                "payment_status": o.payment_status,
                "total": str(o.total),
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "count": len(orders),
    }


@router.post("/orders/{order_id}/pay", response_model=dict)
async def pay_order(
    order_id: str,
    body: PaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = OrderService(db)
    try:
        payment = await service.create_payment_intent(
            order_id=order_id,
            provider_name=body.provider,
            idempotency_key=body.idempotency_key,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "provider": payment.provider,
    }


@router.post("/orders/{order_id}/confirm-payment", response_model=dict)
async def confirm_payment(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = OrderService(db)
    try:
        order = await service.confirm_payment(order_id, payment_confirmed=True)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "payment_status": order.payment_status}


@router.post("/orders/{order_id}/ship", response_model=dict)
async def ship_order(
    order_id: str, body: ShipRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)
):
    service = OrderService(db)
    try:
        order = await service.ship_order(order_id, body.tracking_code, _uid(user))
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}


@router.post("/orders/{order_id}/mark-delivered", response_model=dict)
async def mark_delivered(
    order_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_user)
):
    service = OrderService(db)
    try:
        order = await service.mark_delivered(order_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status}


@router.post("/orders/{order_id}/settle", response_model=dict)
async def settle_order(
    order_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_admin)
):
    service = OrderService(db)
    try:
        settlement = await service.settle_order(order_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {
        "settlement_id": settlement.id,
        "amount": str(settlement.amount),
        "status": settlement.status,
        "journal_batch_id": settlement.journal_batch_id,
    }


@router.post("/orders/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: str,
    reason: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = OrderService(db)
    try:
        order = await service.cancel_order(order_id, reason, _uid(user))
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "cancel_reason": order.cancel_reason}


@router.get("/orders/{order_id}/transitions", response_model=list[str])
async def get_transitions(
    order_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_user)
):
    """Get allowed state transitions for an order."""
    result = await db.execute(select(ComOrder).where(ComOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return list(OrderStateMachine.get_allowed_transitions(order.status))
