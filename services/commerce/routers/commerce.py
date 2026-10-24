"""Commerce router — order state machine, payment intents, settlements."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import ComOrder, ComOrderItem, ComPaymentIntent, InvReservation
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.commerce.service import OrderService, OrderStateMachine

router = APIRouter(prefix="/api/v1/commerce", tags=["commerce"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


async def _fulfilled_qty_by_reservation(db: AsyncSession, items) -> dict[int, Decimal]:
    """Map reservation id -> consumed quantity for the given order lines.

    A line is fulfilled by the quantity its reservation has actually consumed
    (``ship_order`` consumes reservations), so the reported value can never
    exceed what left stock. Lines without a reservation report ``0``.
    """
    reservation_ids = [item.reservation_id for item in items if item.reservation_id]
    if not reservation_ids:
        return {}
    result = await db.execute(
        select(InvReservation).where(InvReservation.id.in_(reservation_ids))
    )
    return {r.id: r.consumed_qty or Decimal("0") for r in result.scalars().all()}


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
    discount_bps: int | None = None


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
    body: OrderCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = OrderService(db)
    try:
        order = await service.create_order(
            buyer_id=_uid(user),
            items=[i.model_dump() for i in body.items],
            shipping_address=body.shipping_address,
            idempotency_key=body.idempotency_key,
            discount_bps=Decimal(str(body.discount_bps)) if body.discount_bps is not None else None,
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
async def get_order(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
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

    # The real fulfilment of a line lives on its stock reservation, not on the
    # unused ``ComOrderItem.fulfilled_qty`` column (which nothing writes).
    # ``ship_order`` consumes the reservation, so ``consumed_qty`` is the
    # quantity that actually left the warehouse.
    fulfilled_by_reservation = await _fulfilled_qty_by_reservation(db, items)

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
                "fulfilled_qty": str(
                    fulfilled_by_reservation.get(i.reservation_id, Decimal("0"))
                ),
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
    offset: int = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = OrderService(db)
    orders = await service.list_orders(
        buyer_id=buyer_id or _uid(user),
        status=status,
        limit=limit,
    )
    # Offset pagination: slice the already-limited result.
    paginated = orders[offset : offset + limit]
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
            for o in paginated
        ],
        "count": len(paginated),
        "limit": limit,
        "offset": offset,
        "api_version": "1.0.0",
    }


@router.post("/orders/{order_id}/pay", response_model=dict)
async def pay_order(
    order_id: str,
    body: PaymentIntentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = OrderService(db)
    try:
        order = await service.confirm_payment(order_id, payment_confirmed=True)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "payment_status": order.payment_status}


@router.post("/orders/{order_id}/ship", response_model=dict)
async def ship_order(
    order_id: str,
    body: ShipRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = OrderService(db)
    try:
        order = await service.ship_order(order_id, body.tracking_code, _uid(user))
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}


@router.post("/orders/{order_id}/mark-delivered", response_model=dict)
async def mark_delivered(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = OrderService(db)
    try:
        order = await service.mark_delivered(order_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status}


@router.post("/orders/{order_id}/settle", response_model=dict)
async def settle_order(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
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
    reason: Annotated[str | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = OrderService(db)
    try:
        order = await service.cancel_order(order_id, reason, _uid(user))
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"order_id": order.id, "status": order.status, "cancel_reason": order.cancel_reason}


@router.get("/orders/{order_id}/transitions", response_model=list[str])
async def get_transitions(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    """Get allowed state transitions for an order."""
    result = await db.execute(select(ComOrder).where(ComOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return list(OrderStateMachine.get_allowed_transitions(order.status))
