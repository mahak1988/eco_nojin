"""Commerce service — order state machine, payment, and settlement.

Bounded Context: Commerce/Orders
Implements the order lifecycle: DRAFT → RESERVED → PAID → PROCESSING →
SHIPPED → DELIVERED → SETTLED with atomic stock reservation and payment.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
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
from services.finance.chart_of_accounts import ensure_settlement_accounts
from services.finance.ledger_service import LedgerService
from services.finance.payment_provider import WalletProvider, payment_registry
from services.finance.revenue_indicators import (
    clamped_discount_bps,
    commerce_schedule,
    projected_revenue,
)
from services.finance.wallet_service import WalletService
from services.inventory.service import StockService
from services.landscape.models import LandscapeFund, LandscapeFundCredit

logger = logging.getLogger(__name__)

VALID_ORDER_TRANSITIONS = ORDER_STATE_MACHINE

#: The landscape fee is charged in the order's currency and credited to a
#: single-currency village fund, so a settlement in any other currency has
#: no fund to credit and is skipped rather than mixed in.
FUND_CURRENCY = "IRR"

#: The fees are charged in cents; the order columns keep eight decimals.
CENT = Decimal("0.01")


def _cents(value: Decimal) -> Decimal:
    """A stored fee quantised to the cents it was charged in (reporting only)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_EVEN)


async def _emit_commerce_event(
    event_type: str, aggregate_type: str, aggregate_id: str, payload: dict
) -> None:
    """Publish a commerce domain event (best-effort, failure-isolated).

    Gated on the same ``enable_event_bus`` flag the gateway uses, and every
    failure is logged and swallowed so a broker outage never breaks the
    committed order row. Uses the generic publisher (there is no dedicated
    commerce publisher) on the ``commerce`` domain. Imported lazily to keep the
    gateway stack off the module import path.
    """
    try:
        from engine.hydroma.config.settings import get_settings

        if not get_settings().enable_event_bus:
            return
        from services.api_gateway.eventbus.publisher import publish_event

        await publish_event("commerce", event_type, aggregate_type, aggregate_id, payload)
    except Exception as exc:  # noqa: BLE001 - broker failure must not propagate
        logger.warning("commerce event %r not published: %s", event_type, exc)


def _notify(
    user_id: str, title: str, body: str = "", ntype: str = "system", link: str | None = None
) -> None:
    """Deliver one owner-scoped in-app notification (best-effort, failure-isolated).

    ``NotificationDbService`` is a synchronous session API, so the notification
    is written on its own short-lived session rather than the caller's
    ``AsyncSession``; a failure here never breaks the committed order row.
    Imported lazily to keep the notification module out of the import path.
    """
    try:
        from database.hub import hub
        from services.notification.db_service import NotificationDbService

        with hub.get_session() as session:
            NotificationDbService(session).notify(user_id, title, body=body, ntype=ntype, link=link)
    except Exception as exc:  # noqa: BLE001 - notification failure must not propagate
        logger.warning("notification to %s not delivered: %s", user_id, exc)


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
        platform_fee = (subtotal * OrderService.PLATFORM_FEE_BPS / Decimal("10000")).quantize(
            Decimal("0.01")
        )
        landscape_fee = (subtotal * OrderService.LANDSCAPE_FEE_BPS / Decimal("10000")).quantize(
            Decimal("0.01")
        )
        total = subtotal + platform_fee + landscape_fee
        return platform_fee, landscape_fee, total

    @staticmethod
    def _resolve_village_id(order: ComOrder) -> str | None:
        """The village whose restoration fund this order's landscape fee funds.

        ``ComOrder`` carries no ``village_id`` column, and ``database.models``
        is not this service's to extend, so the village is read from the
        order's shipping address — the only order-scoped field that can
        carry one (the router already accepts an arbitrary ``dict`` there).
        A missing, blank or non-mapping address means the fee has no village
        behind it; the caller skips the credit rather than guessing.
        """
        address = order.shipping_address
        if not isinstance(address, dict):
            return None
        village_id = address.get("village_id")
        if isinstance(village_id, str) and village_id.strip():
            return village_id.strip()
        return None

    async def _credit_landscape_fund(
        self,
        order: ComOrder,
        settlement: ComSettlement,
        batch,
    ) -> LandscapeFundCredit | None:
        """Credit the village restoration fund with this order's landscape fee.

        The fee has always been charged (``LANDSCAPE_FEE_BPS``, 100 bps) and
        always booked to ``ECO_PLATFORM_REVENUE`` in the settlement batch,
        but nothing ever moved it into ``LandscapeFund`` — the gap recorded
        in ``services/finance/revenue_indicators.py`` under
        ``DISCOUNT_COVERS_LANDSCAPE_FEE``. This closes it: the per-village
        restoration charge now reaches the per-village fund, once per
        settlement, with an audit row naming where the money came from.

        The credited amount is the fee that was actually charged and booked,
        ``order.landscape_fee`` cent-quantised — never re-derived from the
        rate. ``_compute_fees`` rounds each line with banker's rounding and
        ``revenue_indicators``' ``realised_bps`` rounds half up, so the two
        disagree on exact ties (a 0.50 subtotal charges a 0.00 landscape
        fee); changing the service's rounding moves real money, so the drift
        is reported by ``settlement_revenue_report`` instead.

        Returns the credit row, or ``None`` with a logged reason when there
        is nothing to credit.
        """
        village_id = self._resolve_village_id(order)
        if village_id is None:
            logger.info(
                "Landscape fund credit skipped: order %s (%s) has no village_id in its "
                "shipping address; its %s landscape fee stays in platform revenue",
                order.id,
                order.order_number,
                order.landscape_fee,
            )
            return None

        
        amount = _cents(order.landscape_fee)
        if amount <= 0:
            logger.info(
                "Landscape fund credit skipped: order %s landscape fee quantises to %s",
                order.id,
                amount,
            )
            return None

        # One credit per settlement. The state machine already makes a second
        # settle impossible, but this also survives a retry that died between
        # the fund update and its commit.
        already = await self.db.execute(
            select(LandscapeFundCredit).where(LandscapeFundCredit.order_id == order.id)
        )
        if already.scalar_one_or_none() is not None:
            logger.info(
                "Landscape fund credit skipped: order %s already credited", order.id
            )
            return None

        result = await self.db.execute(
            select(LandscapeFund).where(LandscapeFund.village_id == village_id)
        )
        fund = result.scalar_one_or_none()
        if fund is None:
            # The rate comes from the canonical fee schedule, not a literal.
            fund = LandscapeFund(
                village_id=village_id,
                fee_bps=int(commerce_schedule()["landscape"]),
                total_collected=Decimal("0.00"),
                total_distributed=Decimal("0.00"),
                pending_balance=Decimal("0.00"),
                currency=order.currency,
                is_active=True,
            )
            self.db.add(fund)
            await self.db.flush()

        fund.total_collected = Decimal(str(fund.total_collected)) + amount
        fund.pending_balance = Decimal(str(fund.pending_balance)) + amount

        credit = LandscapeFundCredit(
            fund_id=fund.id,
            village_id=village_id,
            order_id=order.id,
            settlement_id=settlement.id,
            journal_batch_id=batch.id,
            amount=amount,
            currency=order.currency,
        )
        self.db.add(credit)
        return credit

    async def _credit_village_development_fund(
        self,
        village_id: str,
        order: ComOrder,
        amount: Decimal,
    ) -> object | None:
        """Route the order's landscape fee into the village development hub.

        Creates (or reuses) a ``Landscape Restoration`` project for the village
        and invests the landscape fee into it via
        ``VillageDevelopmentHubService.create_investment``. This is the bridge
        between commerce fee revenue and village-level development funding.

        Best-effort: a hub-service failure is logged and swallowed so it never
        rolls back the commerce settlement.
        """
        try:
            from services.marketplace.hub_service import VillageDevelopmentHubService

            hub = VillageDevelopmentHubService(self.db)

            # Find or create the village's landscape-restoration project.
            project = await self._find_or_create_landscape_project(hub, village_id)

            investment = await hub.create_investment(
                project_id=str(project.id),
                amount=amount,
                investor_user_id=str(order.buyer_id),
                notes=(
                    f"Landscape fee from order {order.order_number} "
                    f"({order.id})"
                ),
            )
            return investment
        except Exception as exc:  # noqa: BLE001 - hub failure must not roll back commerce
            logger.warning(
                "Village development fund credit skipped for order %s: %s",
                order.id,
                exc,
            )
            return None

    async def _find_or_create_landscape_project(
        self, hub, village_id: str
    ) -> object:
        """Return the village's landscape-restoration project, creating it if absent."""
        from services.marketplace.models.village_hub import VillageProject

        result = await self.db.execute(
            select(VillageProject).where(
                VillageProject.village_id == village_id,
                VillageProject.name.ilike("%landscape%"),
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            project = await hub.create_project(
                village_id=village_id,
                data={
                    "name": "Landscape Restoration Fund",
                    "name_en": "Landscape Restoration Fund",
                    "description": (
                        "Accumulates landscape fees from ecotourism and commerce "
                        "orders for village-level restoration."
                    ),
                    "category": "environment",
                    "status": "planned",
                    "progress_pct": 0,
                    "investment_needed": None,
                    "team_size": 0,
                    "start_date": None,
                    "expected_completion": None,
                },
                user_id="system",
            )
        return project

    async def settlement_revenue_report(self, order_id: str) -> dict:
        """Nominal versus realised fee revenue for a settled order.

        ``revenue_indicators`` is the single source of truth for fee
        arithmetic: the schedule (300 platform + 100 landscape bps) is read
        through ``commerce_schedule()`` and the figures come from
        ``projected_revenue``. The service charges what it charged — the
        stored ``platform_fee``/``landscape_fee`` — and reports the drift
        between the nominal and realised take rates rather than re-deriving
        either. Nothing here writes to the ledger or to a fund.
        """
        order = await self.get_order(order_id)
        schedule = commerce_schedule()
        projection = projected_revenue(Decimal(str(order.subtotal)), schedule)
        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "schedule_bps": {name: str(bps) for name, bps in schedule.items()},
            # The stored columns are Numeric(18, 8); the fees were charged in
            # cents, so the report quotes cents.
            "charged_platform_fee": str(_cents(order.platform_fee)),
            "charged_landscape_fee": str(_cents(order.landscape_fee)),
            "charged_commission": str(_cents(order.platform_fee + order.landscape_fee)),
            "gross": str(projection["gross"]),
            "nominal_commission": str(projection["nominal_commission"]),
            "realised_commission": str(projection["realised_commission"]),
            "nominal_bps": str(projection["nominal_bps"]),
            "realised_bps": str(projection["realised_bps"]),
            "rounding_drift": str(projection["rounding_drift"]),
        }

    async def _check_order_idempotency(
        self, buyer_id: str, idempotency_key: str
    ) -> ComOrder | None:
        """If this buyer already used the idempotency key, return that order.

        The lookup is scoped to ``(buyer_id, idempotency_key)`` so a key only
        ever resolves inside its own buyer's namespace. An idempotency key is a
        client retry token, not a shared resource: without the buyer in the
        query, a key one buyer used resolves to *their* order for every other
        buyer, silently handing a stranger's paid order (and its total) over on
        a replay. :meth:`create_order` refuses a key another buyer has taken.
        """
        result = await self.db.execute(
            select(ComOrder).where(
                ComOrder.idempotency_key == idempotency_key,
                ComOrder.buyer_id == buyer_id,
            )
        )
        return result.scalar_one_or_none()

    async def _reject_idempotency_key_taken_by_other_buyer(
        self, buyer_id: str, idempotency_key: str
    ) -> None:
        """Refuse an idempotency key that already belongs to another buyer.

        The key lives on ``ComOrder``, so two buyers reusing the same value are
        two distinct idempotency namespaces, never one shared order. When this
        buyer has no live order on the key but a different buyer does, the
        collision is rejected outright (``IDEMPOTENCY_KEY_CONFLICT``) — never
        silently remapped to the other buyer's order — so no cross-tenant
        replay can occur. A key reused by *its own* buyer is not a collision
        and is left to ``_check_order_idempotency``.
        """
        result = await self.db.execute(
            select(ComOrder).where(
                ComOrder.idempotency_key == idempotency_key,
                ComOrder.buyer_id != buyer_id,
            )
        )
        if result.scalars().first() is not None:
            raise EcoNojinException(
                f"Idempotency key {idempotency_key!r} is already in use by another buyer",
                code="IDEMPOTENCY_KEY_CONFLICT",
                status_code=409,
            )

    async def create_order(
        self,
        buyer_id: str,
        items: list[dict],
        shipping_address: dict | None = None,
        idempotency_key: str | None = None,
        discount_bps: Decimal | None = None,
    ) -> ComOrder:
        """Create a new order in DRAFT state with idempotency support.

        Args:
            items: List of {sku_code, quantity, unit_price? (optional, fetched from product)}
            discount_bps: Optional marketplace fee discount in basis points,
                clamped to 0..100% of the platform fee line.
        """
        from decimal import Decimal as D

        if idempotency_key:
            existing = await self._check_order_idempotency(buyer_id, idempotency_key)
            if existing and existing.payment_status != "failed":
                return existing
            # No live order for *this* buyer on the key: mint a fresh order,
            # but only after confirming no other buyer has claimed the key —
            # that would be a cross-tenant replay, so it is refused (never
            # silently remapped to the other buyer's order) before any stock
            # is held.
            await self._reject_idempotency_key_taken_by_other_buyer(
                buyer_id, idempotency_key
            )

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
            reservations.append(
                {
                    "sku": sku,
                    "qty": qty,
                    "warehouse_id": warehouse_id,
                    "unit_price": unit_price,
                    "reservation_id": reservation.id,
                }
            )

        # Compute totals
        subtotal = sum(r["qty"] * r["unit_price"] for r in reservations)
        if subtotal == 0:
            # If no unit_price provided, use standard cost from SKU
            for r in reservations:
                if r["unit_price"] == 0:
                    r["unit_price"] = r["sku"].standard_cost or D("0")
            subtotal = sum(r["qty"] * r["unit_price"] for r in reservations)

        platform_fee, landscape_fee, total = self._compute_fees(subtotal)

        # Apply marketplace fee discount (redeemed via MARKET_FEE_DISCOUNT)
        # DISCOUNT_COVERS_LANDSCAPE_FEE is False: discount reaches platform line only.
        if discount_bps is not None:
            applied = clamped_discount_bps(discount_bps)
            waived = (platform_fee * applied / Decimal("10000")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
            platform_fee = max(platform_fee - waived, Decimal("0"))
            total = subtotal + platform_fee + landscape_fee

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
                text(
                    "UPDATE inv_reservations SET reference_id = :oid, reference_line_id = :lid WHERE id = :rid"
                ),
                {"oid": order_id, "lid": str(r["reservation_id"]), "rid": r["reservation_id"]},
            )

        # Audit event
        self.db.add(
            AuditEvent(
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
            )
        )

        await self.db.commit()
        await self.db.refresh(order)

        await _emit_commerce_event(
            "order_created",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "buyer_id": str(order.buyer_id),
                "total": str(order.total),
                "currency": str(order.currency),
                "status": str(order.status),
            },
        )
        _notify(str(order.buyer_id), "Your order has been reserved.", ntype="order")
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
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

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

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id=order.buyer_id,
                action="payment_intent_create",
                resource_type="payment_intent",
                resource_id=payment.id,
                after_state={"status": intent.status, "amount": str(intent.amount)},
                created_at=datetime.now(UTC),
            )
        )

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
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

        if payment_confirmed:
            order.payment_status = "paid"
            order.paid_at = datetime.now(UTC)
            OrderStateMachine.validate(order.status, "paid", payment_verified=True)
            order.status = "paid"
            order.version += 1

            self.db.add(
                AuditEvent(
                    correlation_id=order_id,
                    actor_id=order.buyer_id,
                    action="payment_confirm",
                    resource_type="order",
                    resource_id=order_id,
                    after_state={"status": "paid", "payment_status": "paid"},
                    created_at=datetime.now(UTC),
                )
            )
        else:
            order.payment_status = "failed"
            self.db.add(
                AuditEvent(
                    correlation_id=order_id,
                    actor_id=order.buyer_id,
                    action="payment_failed",
                    resource_type="order",
                    resource_id=order_id,
                    after_state={
                        "status": order.status,
                        "payment_status": "failed",
                        "reason": failure_reason,
                    },
                    created_at=datetime.now(UTC),
                )
            )

        await self.db.commit()
        await self.db.refresh(order)

        if order.payment_status == "paid":
            await _emit_commerce_event(
                "payment_completed",
                "order",
                str(order.id),
                {
                    "order_id": str(order.id),
                    "buyer_id": str(order.buyer_id),
                    "total": str(order.total),
                    "currency": str(order.currency),
                },
            )
            _notify(str(order.buyer_id), "Your payment has been received.", ntype="payment")
        return order

    async def process_order(self, order_id: str, processed_by: str = "system") -> ComOrder:
        """Transition order from paid to processing."""
        result = await self.db.execute(
            select(ComOrder).where(ComOrder.id == order_id).with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

        OrderStateMachine.validate(order.status, "processing")
        order.status = "processing"
        order.version += 1

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id=processed_by,
                action="order_process",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "processing"},
                created_at=datetime.now(UTC),
            )
        )

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
        result = await self.db.execute(
            select(ComOrder).where(ComOrder.id == order_id).with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

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

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id=shipped_by,
                action="order_ship",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "shipped", "tracking_code": tracking_code},
                created_at=datetime.now(UTC),
            )
        )

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

        await _emit_commerce_event(
            "order_shipped",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "tracking_code": str(tracking_code),
                "buyer_id": str(order.buyer_id),
            },
        )
        _notify(str(order.buyer_id), "Your order has been shipped.", ntype="order")
        return order

    async def mark_delivered(self, order_id: str) -> ComOrder:
        """Mark order as delivered."""
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

        OrderStateMachine.validate(order.status, "delivered")
        order.status = "delivered"
        order.delivered_at = datetime.now(UTC)
        order.version += 1

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id="system",
                action="order_delivered",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "delivered"},
                created_at=datetime.now(UTC),
            )
        )

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
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

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

        # The settlement batch names its accounts by code, so every one of them
        # must exist as a chart row before the batch is written. Without this
        # the entries resolved to nothing and profit & loss reported the whole
        # settlement as ``unclassified``.
        await ensure_settlement_accounts(self.db)

        # Build the three settlement legs, then drop any whose amount is zero
        # before the ledger sees them. A zero leg is a no-op entry, and correct
        # double-entry does not require it; ``create_journal_batch`` rightly
        # refuses non-positive amounts, so feeding it the ``platform_fee +
        # landscape_fee`` leg on a cent-granular order (subtotals of 1, 2, 5, 9
        # cents) whose two fee lines both round to 0.00 used to make a paid,
        # delivered order permanently un-settleable. Omitted, a 0.01 order
        # settles with ``debit ECO_CASH 0.01 / credit ECO_SELLER_PAYABLE 0.01``
        # — balanced, both legs positive. For a normal-fee order every leg is
        # positive, so the same three lines pass through unchanged.
        settlement_legs = [
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
        ]
        settlement_legs = [
            leg for leg in settlement_legs if Decimal(str(leg["amount"])) > 0
        ]

        batch = await self.ledger.create_journal_batch(
            reference_type="settlement",
            reference_id=ref_id,
            entries=settlement_legs,
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

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id="system",
                action="order_settled",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "settled", "settlement_id": settlement.id},
                created_at=datetime.now(UTC),
            )
        )

        await self.db.commit()
        await self.db.refresh(settlement)
        # Trial balance and profit & loss aggregate posted batches only, so the
        # settlement batch is posted once its settlement row is durable.
        await self.ledger.post_journal_batch(batch.id)
        # The landscape fee is now posted cash; route it to the per-village
        # restoration fund it was charged for (P1-8). Skipped with a logged
        # reason when the order has no village to fund.
        credit = await self._credit_landscape_fund(order, settlement, batch)
        if credit is not None:
            await self.db.commit()

        # Route the same landscape fee into the village development hub so it
        # can be invested in a village restoration project (P4).
        village_id = self._resolve_village_id(order)
        if village_id is not None and order.landscape_fee > 0:
            await self._credit_village_development_fund(
                village_id=village_id,
                order=order,
                amount=order.landscape_fee,
            )

        await _emit_commerce_event(
            "order_settled",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "settlement_id": str(settlement.id),
                "amount": str(settlement.amount),
                "currency": str(settlement.currency),
                "buyer_id": str(order.buyer_id),
            },
        )
        _notify(str(order.buyer_id), "Your order has been settled.", ntype="payment")
        return settlement

    async def cancel_order(
        self, order_id: str, reason: str | None = None, cancelled_by: str = "system"
    ) -> ComOrder:
        """Cancel an order and release reservations."""
        result = await self.db.execute(
            select(ComOrder).where(ComOrder.id == order_id).with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )

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
                with contextlib.suppress(EcoNojinException):  # already released/consumed
                    await self.stock.release_reservation(item.reservation_id)

        self.db.add(
            AuditEvent(
                correlation_id=order_id,
                actor_id=cancelled_by,
                action="order_cancelled",
                resource_type="order",
                resource_id=order_id,
                after_state={"status": "cancelled", "cancel_reason": reason},
                created_at=datetime.now(UTC),
            )
        )

        await self.db.commit()
        await self.db.refresh(order)

        await _emit_commerce_event(
            "order_cancelled",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "buyer_id": str(order.buyer_id),
                "reason": "" if reason is None else str(reason),
            },
        )
        _notify(str(order.buyer_id), "Your order has been cancelled.", ntype="order")
        return order

    async def get_order(self, order_id: str) -> ComOrder:
        result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise EcoNojinException(
                f"Order not found: {order_id}", code="ORDER_NOT_FOUND", status_code=404
            )
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
