"""Commerce service — order state machine, payment, and settlement.

Bounded Context: Commerce/Orders
Implements the order lifecycle: DRAFT → RESERVED → PAID → PROCESSING →
SHIPPED → DELIVERED → SETTLED with atomic stock reservation and payment.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ORDER_STATE_MACHINE,
    AuditEvent,
    ComOrder,
    ComOrderItem,
    ComPaymentIntent,
    ComSettlement,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.ledger_service import LedgerService
from services.finance.payment_provider import WalletProvider, payment_registry
from services.finance.wallet_service import WalletService
from services.inventory.service import StockService

logger = logging.getLogger(__name__)

VALID_ORDER_TRANSITIONS = ORDER_STATE_MACHINE


class OrderStateMachine:
    """Validates and executes order state transitions."""

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        rules = VALID_ORDER_TRANSITIONS.get(current)
        if not rules:
            return False
        return target in rules["allowed"]

    @staticmethod
    def get_allowed_transitions(current: str) -> set:
        rules = VALID_ORDER_TRANSITIONS.get(current)
        return rules["allowed"] if rules else set()

    @staticmethod
    def validate(current: str, target: str, **context) -> None:
        if not OrderStateMachine.can_transition(current, target):
            raise EcoNojinException(
                f"Invalid order state transition: {current} → {target}",
                code="INVALID_STATE_TRANSITION",
                status_code=400,
            )
        rules = VALID_ORDER_TRANSITIONS.get(current, {})
        reqs = rules.get("requires", {})
        target_reqs = reqs.get(target, []) if isinstance(reqs, dict) else reqs
        for req in target_reqs:
            if req == "payment" and not context.get("payment_verified"):
                raise EcoNojinException(
                    f"Transition requires: {req}",
                    code="TRANSITION_REQUIREMENT_NOT_MET",
                    status_code=400,
                )
            if req == "tracking_code" and not context.get("tracking_code"):
                raise EcoNojinException(
                    f"Transition requires: {req}",
                    code="TRANSITION_REQUIREMENT_NOT_MET",
                    status_code=400,
                )


class OrderService:
    """Order service with state machine, atomic reservation, and payment."""

    PLATFORM_FEE_BPS = Decimal("300")  # 3%
    LANDSCAPE_FEE_BPS = Decimal("100")  # 1%

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stock = StockService(db)
        self.ledger = LedgerService(db)
        if "wallet" not in [p.provider_name for p in payment_registry.get_all()]:
            payment_registry.register(WalletProvider(WalletService(db)))

    @staticmethod
    def _compute_fees(subtotal: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        platform_fee = (subtotal * OrderService.PLATFORM_FEE_BPS / Decimal("10000")).quantize(Decimal("0.01"))
        landscape_fee = (subtotal * OrderService.LANDSCAPE_FEE_BPS / Decimal("10000")).quantize(Decimal("0.01"))
        total = subtotal + platform_fee + landscape_fee
        return platform_fee, landscape_fee, total

    async def _check_order_idempotency(self, idempotency_key: str) -> ComOrder | None:
        """If the idempotency key was used for a completed order, return it."""
        result = await self.db.execute(
            select(ComOrder).where(ComOrder.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create_order(
        self,
        buyer_id: str,
        items: list[dict],
        shipping_address: dict | None = None,
        idempotency_key: str | None = None,
    ) -> ComOrder:
        """Create a new order in DRAFT state with idempotency support.

        Args:
            items: List of {sku_code, quantity, unit_price? (optional, fetched from product)}
        """
        from decimal import Decimal as D

        if idempotency_key:
            existing = await self._check_order_idempotency(idempotency_key)
            if existing and existing.payment_status != "failed":
                return existing

        # Reserve stock atomically BEFORE creating the order
        reservations = []
        for item in items:
            sku = await self.stock.get_sku(item["sku_code"])
            qty = D(str(item["quantity"]))
            warehouse_id = item.get("warehouse_id", sku.default_warehouse_id)
            if not warehouse_id:
                raise EcoNojinException(
                    f"No warehouse for SKU {item['sku_code']}",
                    code="NO_WAREHOUSE",
                    status_code=400,
                )

            unit_price = D(str(item.get("unit_price", 0))) if item.get("unit_price") else D("0")

            reservation = await self.stock.reserve_stock(
                sku_id=sku.id,
                warehouse_id=warehouse_id,
                qty=qty,
                reference_type="order",
                reference_id=f"pending-order-{idempotency_key or str(uuid4())}",
                created_by=buyer_id,
            )
            reservations.append({
                "sku": sku,
                "qty": qty,
                "warehouse_id": warehouse_id,
                "unit_price": unit_price,
                "reservation_id": reservation.id,
            })

        # Compute totals
        subtotal = sum(r["qty"] * r["unit_price"] for r in reservations)
        if subtotal == 0:
            # If no unit_price provided, use standard cost from SKU
            for r in reservations:
                if r["unit_price"] == 0:
                    r["unit_price"] = r["sku"].standard_cost or D("0")
            subtotal = sum(r["qty"] * r["unit_price"] for r in reservations)

        platform_fee, landscape_fee, total = self._compute_fees(subtotal)

        order_id = str(uuid4())
        order = ComOrder(
            id=order_id,
            order_number=f"ORD-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{order_id[:8]}",
            buyer_id=buyer_id,
            seller_id=None,
            status="reserved",  # immediately reserved since stock is locked
            payment_status="pending",
            subtotal=subtotal,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            total=total,
            shipping_address=shipping_address,
            idempotency_key=idempotency_key,
            version=0,
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items
        for r in reservations:
            item = ComOrderItem(
                id=str(uuid4()),
                order_id=order_id,
                sku_id=r["sku"].id,
                sku_code=r["sku"].sku_code,
                name=r["sku"].name,
                quantity=r["qty"],
                unit_price=r["unit_price"],
                line_total=r["qty"] * r["unit_price"],
                warehouse_id=r["warehouse_id"],
                reservation_id=r["reservation_id"],
            )
            self.db.add(item)

        # Update reservation reference_id to actual order_id
        for r in reservations:
            await self.db.execute(
                text("UPDATE inv_reservation SET reference_id = :oid, reference_line_id = :lid WHERE id = :rid"),
                {"oid": order_id, "lid": str(r["reservation_id"]), "rid": r["reservation_id"]},
            )

        # Audit event
        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id=buyer_id,
            action="order_create",
            resource_type="order",
            resource_id=order_id,
            after_state={
                "status": "reserved",
                "total": str(total),
                "items_count": len(items),
            },
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def create_payment_intent(
        self,
        order_id: str,
        provider_name: str = "wallet",
        idempotency_key: str | None = None,
    ) -> ComPaymentIntent:
        """Create a payment intent for an order."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        if order.payment_status not in ("pending", "failed"):
            raise EcoNojinException(
                f"Cannot create payment for order in state: {order.payment_status}",
                code="INVALID_PAYMENT_STATE",
                status_code=400,
            )

        provider = payment_registry.get(provider_name)
        intent = await provider.create_payment_intent(
            amount=order.total,
            currency=order.currency,
            order_id=order_id,
            metadata={"order_number": order.order_number, "buyer_id": order.buyer_id},
            idempotency_key=idempotency_key or str(uuid4()),
        )

        payment = ComPaymentIntent(
            id=intent.id,
            order_id=order_id,
            buyer_id=order.buyer_id,
            provider=provider_name,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status,
            provider_reference=intent.provider_reference,
            payment_metadata=intent.metadata,
        )
        self.db.add(payment)

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id=order.buyer_id,
            action="payment_intent_create",
            resource_type="payment_intent",
            resource_id=payment.id,
            after_state={"status": intent.status, "amount": str(intent.amount)},
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def confirm_payment(
        self,
        order_id: str,
        payment_confirmed: bool = True,
        failure_reason: str | None = None,
    ) -> ComOrder:
        """Confirm payment and advance order state."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        if payment_confirmed:
            order.payment_status = "paid"
            order.paid_at = datetime.now(UTC)
            OrderStateMachine.validate(order.status, "paid", payment_verified=True)
            order.status = "paid"
            order.version += 1

            self.db.add(AuditEvent(
                correlation_id=order_id,
                actor_id=order.buyer_id,
                action="payment_confirm",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "paid", "payment_status": "paid"},
                created_at=datetime.now(UTC),
            ))
        else:
            order.payment_status = "failed"
            self.db.add(AuditEvent(
                correlation_id=order_id,
                actor_id=order.buyer_id,
                action="payment_failed",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": order.status, "payment_status": "failed", "reason": failure_reason},
                created_at=datetime.now(UTC),
            ))

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def process_order(self, order_id: str, processed_by: str = "system") -> ComOrder:
        """Transition order from paid to processing."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id).with_for_update())
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        OrderStateMachine.validate(order.status, "processing")
        order.status = "processing"
        order.version += 1

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id=processed_by,
            action="order_process",
            resource_type="order",
            resource_id=order_id,
            after_state={"status": "processing"},
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def ship_order(
        self,
        order_id: str,
        tracking_code: str,
        shipped_by: str,
    ) -> ComOrder:
        """Mark order as shipped with tracking code."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id).with_for_update())
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        if order.status != "processing":
            raise EcoNojinException(
                f"Cannot ship order in state: {order.status}",
                code="INVALID_SHIP_STATE",
                status_code=400,
            )

        OrderStateMachine.validate(order.status, "shipped", tracking_code=tracking_code)
        order.status = "shipped"
        order.tracking_code = tracking_code
        order.shipped_at = datetime.now(UTC)
        order.version += 1

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id=shipped_by,
            action="order_ship",
            resource_type="order",
            resource_id=order_id,
            after_state={"status": "shipped", "tracking_code": tracking_code},
            created_at=datetime.now(UTC),
        ))

        # Create stock movements (issue for shipped items)
        result = await self.db.execute(
            select(ComOrderItem).where(ComOrderItem.order_id == order_id)
        )
        items = result.scalars().all()
        for item in items:
            if item.reservation_id:
                await self.stock.consume_reservation(item.reservation_id)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def mark_delivered(self, order_id: str) -> ComOrder:
        """Mark order as delivered."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        OrderStateMachine.validate(order.status, "delivered")
        order.status = "delivered"
        order.delivered_at = datetime.now(UTC)
        order.version += 1

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id="system",
            action="order_delivered",
            resource_type="order",
            resource_id=order_id,
            after_state={"status": "delivered"},
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def settle_order(self, order_id: str) -> ComSettlement:
        """Settle order — release escrow to seller via ledger."""
        result = await self.db.execute(
            select(ComOrder).where(ComOrder.id == order_id).with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        if order.status != "delivered":
            raise EcoNojinException(
                f"Cannot settle order in state: {order.status}",
                code="INVALID_SETTLE_STATE",
                status_code=400,
            )

        OrderStateMachine.validate(order.status, "settled")
        order.status = "settled"
        order.version += 1

        # Create settlement with ledger entries
        seller_amount = order.total - order.platform_fee - order.landscape_fee
        ref_id = str(uuid4())

        batch = await self.ledger.create_journal_batch(
            reference_type="settlement",
            reference_id=ref_id,
            entries=[
                {
                    "account_id": "ECO_PLATFORM_REVENUE",
                    "entry_type": "credit",
                    "asset": order.currency,
                    "amount": str(order.platform_fee + order.landscape_fee),
                    "description": "Platform + landscape fees",
                },
                {
                    "account_id": "ECO_SELLER_PAYABLE",
                    "entry_type": "credit",
                    "asset": order.currency,
                    "amount": str(seller_amount),
                    "description": "Settlement to seller",
                },
                {
                    "account_id": "ECO_CASH",
                    "entry_type": "debit",
                    "asset": order.currency,
                    "amount": str(order.total),
                    "description": f"Order settlement: {order.order_number}",
                },
            ],
            description=f"Settlement for order {order.order_number}",
            created_by="system",
        )

        settlement = ComSettlement(
            id=str(uuid4()),
            order_id=order_id,
            seller_id=order.seller_id or "marketplace",
            amount=seller_amount,
            currency=order.currency,
            commission_fee=order.platform_fee,
            landscape_fee=order.landscape_fee,
            status="paid",
            journal_batch_id=batch.id,
            settled_at=datetime.now(UTC),
        )
        self.db.add(settlement)

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id="system",
            action="order_settled",
            resource_type="order",
            resource_id=order_id,
            after_state={"status": "settled", "settlement_id": settlement.id},
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(settlement)
        return settlement

    async def cancel_order(self, order_id: str, reason: str | None = None, cancelled_by: str = "system") -> ComOrder:
        """Cancel an order and release reservations."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id).with_for_update())
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)

        if order.status in ("settled", "cancelled", "refunded"):
            raise EcoNojinException(
                f"Cannot cancel order in terminal state: {order.status}",
                code="INVALID_CANCEL_STATE",
                status_code=400,
            )

        OrderStateMachine.validate(order.status, "cancelled")
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        order.cancel_reason = reason
        order.version += 1

        # Release all reservations
        result = await self.db.execute(
            select(ComOrderItem).where(ComOrderItem.order_id == order_id)
        )
        items = result.scalars().all()
        for item in items:
            if item.reservation_id:
                try:
                    await self.stock.release_reservation(item.reservation_id)
                except EcoNojinException:
                    pass  # already released/consumed

        self.db.add(AuditEvent(
            correlation_id=order_id,
            actor_id=cancelled_by,
            action="order_cancelled",
            resource_type="order",
            resource_id=order_id,
            after_state={"status": "cancelled", "cancel_reason": reason},
            created_at=datetime.now(UTC),
        ))

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order(self, order_id: str) -> ComOrder:
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404)
        return order

    async def list_orders(
        self,
        buyer_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ComOrder]:
        stmt = select(ComOrder).order_by(ComOrder.created_at.desc())
        if buyer_id:
            stmt = stmt.where(ComOrder.buyer_id == buyer_id)
        if status:
            stmt = stmt.where(ComOrder.status == status)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# Import text for raw SQL updates
