"""
سرویس کامل بازارچه روستایی
═══════════════════════════════════════════════════════════════════════
این سرویس شامل:
- مدیریت محصولات و فروشندگان
- پردازش سفارشات
- اقلام سفارش (MarketplaceOrderItem) با ثبت نام و قیمت لحظهٔ خرید
  و خواندن دوباره از دیتابیس (get_order_items)
- محاسبه و تقسیم کارمزد
- ادغام با سیستم پرداخت
"""

import logging
import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.marketplace.models import (
    Marketplace,
    MarketplaceCommissionRule,
    MarketplaceMember,
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)

logger = logging.getLogger(__name__)


async def _emit_marketplace_event(
    event_type: str, aggregate_type: str, aggregate_id: str, payload: dict
) -> None:
    """Publish a marketplace domain event (best-effort, failure-isolated).

    A broker outage must never break the business transaction that just
    committed, so every failure is logged and swallowed. Gated on the same
    ``enable_event_bus`` flag the gateway uses, so a deployment with the bus
    disabled does no work here. Imported lazily to keep the heavy gateway
    stack (and its NATS graph) out of the module import path.
    """
    try:
        from engine.hydroma.config.settings import get_settings

        if not get_settings().enable_event_bus:
            return
        from services.api_gateway.eventbus.publisher import publish_marketplace_event

        await publish_marketplace_event(event_type, aggregate_type, aggregate_id, payload)
    except Exception as exc:  # noqa: BLE001 - broker failure must not propagate
        logger.warning("marketplace event %r not published: %s", event_type, exc)


def _notify(
    user_id: str, title: str, body: str = "", ntype: str = "system", link: str | None = None
) -> None:
    """Deliver one owner-scoped in-app notification (best-effort, failure-isolated).

    ``NotificationDbService`` is a synchronous session API, so the notification
    is written on its own short-lived session rather than the caller's
    ``AsyncSession``; a failure here never breaks the already-committed row.
    Imported lazily to avoid importing the gateway stack at module load.
    """
    try:
        from database.hub import hub
        from services.notification.db_service import NotificationDbService

        with hub.get_session() as session:
            NotificationDbService(session).notify(user_id, title, body=body, ntype=ntype, link=link)
    except Exception as exc:  # noqa: BLE001 - notification failure must not propagate
        logger.warning("notification to %s not delivered: %s", user_id, exc)


class MarketplaceService:
    """سرویس مدیریت بازارچه روستایی با قابلیت‌های پیشرفته."""

    DEFAULT_PLATFORM_FEE_BPS = 300
    DEFAULT_LANDSCAPE_FEE_BPS = 100

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_seller(
        self,
        user_id: str,
        village_id: str,
        shop_name: str,
        shop_description: str | None = None,
    ) -> MarketplaceSeller:
        """ثبت فروشنده جدید — فقط برای روستاهای تایید KYC (P7.1 gate)."""
        if not shop_name or len(shop_name.strip()) == 0:
            raise ValueError("نام فروشگاه نمی‌تواند خالی باشد")

        # P7.1 Gate: village must be governance-ACTIVE and KYC-approved.
        from services.marketplace.hub_service import VillageDevelopmentHubService

        hub = VillageDevelopmentHubService(self.db)
        if not await hub.is_marketplace_eligible(village_id):
            raise ValueError(
                f"روستا {village_id} برایMarkeetplace تایید نشده است: "
                "پیش از این فضای حکمرانی باید ACTIVE شود و KYC edustنده تایید گردد"
            )

        existing = await self.db.execute(
            select(MarketplaceSeller).where(MarketplaceSeller.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("این کاربر قبلاً فروشنده ثبت کرده است")

        seller = MarketplaceSeller(
            user_id=user_id,
            village_id=village_id,
            shop_name=shop_name,
            shop_description=shop_description,
            status="pending",
            is_verified=False,
        )

        self.db.add(seller)
        await self.db.commit()
        await self.db.refresh(seller)

        await _emit_marketplace_event(
            "shop_created",
            "seller",
            str(seller.id),
            {
                "shop_name": seller.shop_name,
                "village_id": seller.village_id,
                "user_id": str(seller.user_id),
            },
        )
        _notify(str(seller.user_id), "Your shop was created and is pending review.", ntype="system")

        return seller

    async def verify_seller(self, seller_id: str, verified_by: str) -> MarketplaceSeller:
        """تأیید فروشنده توسط مدیر منظر."""
        result = await self.db.execute(
            select(MarketplaceSeller).where(MarketplaceSeller.id == seller_id)
        )
        seller = result.scalar_one_or_none()

        if not seller:
            raise ValueError(f"فروشنده یافت نشد: {seller_id}")

        seller.is_verified = True
        seller.status = "active"
        seller.verified_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(seller)

        await _emit_marketplace_event(
            "seller_verified",
            "seller",
            str(seller.id),
            {
                "shop_name": seller.shop_name,
                "user_id": str(seller.user_id),
                "verified_by": str(verified_by),
            },
        )
        _notify(str(seller.user_id), "Your shop has been verified.", ntype="system")

        return seller

    async def create_product(
        self,
        seller_id: str,
        name: str,
        price: Decimal,
        village_id: str,
        category: str,
        description: str | None = None,
        stock: int = 0,
        unit: str = "piece",
        story: str | None = None,
        pgs_certified: bool = False,
        organic: bool = False,
    ) -> MarketplaceProduct:
        """ثبت محصول جدید."""
        if not name or len(name.strip()) == 0:
            raise ValueError("نام محصول نمی‌تواند خالی باشد")

        if price <= 0:
            raise ValueError("قیمت باید مثبت باشد")

        if stock < 0:
            raise ValueError("موجودی نمی‌تواند منفی باشد")

        seller_result = await self.db.execute(
            select(MarketplaceSeller).where(MarketplaceSeller.id == seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        if not seller:
            raise ValueError(f"فروشنده یافت نشد: {seller_id}")

        if not seller.is_verified:
            raise ValueError("فروشنده هنوز تأیید نشده است")

        slug = self._generate_slug(name)

        product = MarketplaceProduct(
            seller_id=seller_id,
            name=name,
            slug=slug,
            description=description,
            category=category,
            price=price,
            stock=stock,
            unit=unit,
            village_id=village_id,
            uses_village_brand=True,
            status=MarketplaceProductStatus.PENDING_APPROVAL,
            pgs_certified=pgs_certified,
            organic=organic,
            story=story,
        )

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)

        return product

    async def approve_product(
        self, product_id: str, approved_by: str, approve: bool = True
    ) -> MarketplaceProduct:
        """تأیید یا رد محصول توسط مدیر منظر."""
        result = await self.db.execute(
            select(MarketplaceProduct).where(MarketplaceProduct.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError(f"محصول یافت نشد: {product_id}")

        if approve:
            product.status = MarketplaceProductStatus.APPROVED
            product.approved_by = approved_by
            product.approved_at = datetime.now(UTC)
        else:
            product.status = MarketplaceProductStatus.REJECTED

        await self.db.commit()
        await self.db.refresh(product)

        await _emit_marketplace_event(
            "product_approved" if approve else "product_rejected",
            "product",
            str(product.id),
            {
                "seller_id": str(product.seller_id),
                "approved_by": str(approved_by),
                "approved": bool(approve),
            },
        )
        try:
            seller_row = await self.db.execute(
                select(MarketplaceSeller).where(MarketplaceSeller.id == product.seller_id)
            )
            seller = seller_row.scalar_one_or_none()
            if seller is not None and seller.user_id:
                _notify(
                    str(seller.user_id),
                    f"Your product was {'approved' if approve else 'rejected'}.",
                    ntype="system",
                )
        except Exception as exc:  # noqa: BLE001 - notify must not affect a committed approval
            logger.warning("product approval notification not delivered: %s", exc)

        return product

    async def create_order(
        self,
        buyer_id: str,
        items: list[dict],
        village_id: str,
        shipping_address: dict,
    ) -> MarketplaceOrder:
        """ایجاد سفارش جدید با محاسبه خودکار کارمزد."""
        if not items:
            raise ValueError("سبد خرید نمی‌تواند خالی باشد")

        # Phase 4 group 4: the unit price used to be read straight out of the
        # request body, so a buyer could post `price: 1` for a 350,000 IRR
        # product and the order total, the platform fee and the landscape fee
        # were all computed from the attacker's number. The catalogue is now
        # the only pricing authority; a `price` in the payload is ignored, and
        # a mismatch is refused rather than silently overridden so a client with
        # a stale cart learns why.
        subtotal = Decimal("0")
        priced_items: list[dict[str, Any]] = []
        for item in items:
            if "product_id" not in item or "quantity" not in item:
                raise ValueError("هر آیتم باید product_id و quantity داشته باشد")

            quantity = Decimal(str(item["quantity"]))
            if quantity <= 0:
                raise ValueError("quantity must be positive")

            product = await self._get_product_for_pricing(item["product_id"])
            catalogue_price = Decimal(str(product.price))

            claimed = item.get("price")
            if claimed is not None and Decimal(str(claimed)) != catalogue_price:
                raise ValueError(
                    f"price for product {item['product_id']} is {catalogue_price} "
                    f"in the catalogue, not {claimed}; refresh the cart"
                )

            line_total = catalogue_price * quantity
            subtotal += line_total
            priced_items.append(
                {
                    "product_id": product.id,
                    # Stock is an Integer column, and an aiosqlite binding
                    # rejects Decimal. Convert once, here, rather than letting a
                    # Decimal reach the driver.
                    "quantity": int(quantity)
                    if quantity == quantity.to_integral_value()
                    else quantity,
                    "seller_id": getattr(product, "seller_id", None),
                    # The name is frozen here on purpose: a product renamed
                    # after the order must not rewrite an existing receipt.
                    "product_name": product.name,
                    "unit": getattr(product, "unit", None),
                    "unit_price": catalogue_price,
                    "line_total": line_total,
                }
            )

        commission_rule = await self._get_commission_rule(village_id)

        # The fee lines are quantised to the cent here, before the total is
        # formed, mirroring ``commerce/service.py:OrderService._compute_fees``:
        # the order used to be built from the unrounded divisions, so the
        # ``Numeric(15, 2)`` columns rounded the four figures independently and
        # the stored lines need not sum to the stored total -- a 0.13 subtotal
        # at 300 + 100 bps stored fees of 0.00 each against a total of 0.14, a
        # cent no line accounted for.
        platform_fee = (
            subtotal * Decimal(commission_rule.platform_fee_bps) / Decimal(10000)
        ).quantize(Decimal("0.01"))
        landscape_fee = (
            subtotal * Decimal(commission_rule.landscape_fee_bps) / Decimal(10000)
        ).quantize(Decimal("0.01"))
        total = subtotal + platform_fee + landscape_fee

        order_number = self._generate_order_number()

        order = MarketplaceOrder(
            order_number=order_number,
            buyer_id=buyer_id,
            village_id=village_id,
            subtotal=subtotal,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            total=total,
            shipping_address=shipping_address,
            status=MarketplaceOrderStatus.PENDING,
            payment_status="pending",
        )

        # Order header, basket rows and the stock decrements are ONE unit of
        # work. The header used to be committed on its own and the stock was
        # decremented afterwards, so a failed decrement left a committed order
        # the warehouse could never fill — and no basket to explain it with.
        # Everything below now shares a single transaction: if the stock guard
        # rejects one item the rollback takes the order and its items with it.
        try:
            order.items = [
                MarketplaceOrderItem(
                    order_id=order.id,
                    product_id=str(priced["product_id"]),
                    seller_id=priced["seller_id"],
                    product_name=priced["product_name"],
                    quantity=priced["quantity"],
                    unit=priced["unit"],
                    unit_price=priced["unit_price"],
                    line_total=priced["line_total"],
                )
                for priced in priced_items
            ]

            self.db.add(order)

            for item in priced_items:
                await self._decrease_stock(item["product_id"], item["quantity"])

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        await self.db.refresh(order)

        await _emit_marketplace_event(
            "order_placed",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "village_id": str(order.village_id),
                "total": str(order.total),
                "buyer_id": str(order.buyer_id),
            },
        )
        _notify(str(order.buyer_id), "Your order has been placed.", ntype="order")

        return order

    async def get_order_items(self, order_id: str) -> list[MarketplaceOrderItem]:
        """ردیف‌های سبد خرید یک سفارش.

        The basket is stored per line item, so it survives a reload: the order
        header alone only carries money totals.
        """
        result = await self.db.execute(
            select(MarketplaceOrderItem)
            .where(MarketplaceOrderItem.order_id == order_id)
            .order_by(MarketplaceOrderItem.created_at, MarketplaceOrderItem.id)
        )
        return list(result.scalars().all())

    async def _get_product_for_pricing(self, product_id: str) -> MarketplaceProduct:
        """Load the catalogue row that governs an item's price.

        Raises rather than defaulting: a product the server cannot price is not
        an order it should accept.
        """
        product = await self.db.get(MarketplaceProduct, str(product_id))
        if product is None:
            raise ValueError(f"product not found: {product_id}")
        if product.price is None:
            raise ValueError(f"product {product_id} has no catalogue price")
        return product

    async def confirm_payment(self, order_id: str, payment_tx_hash: str) -> MarketplaceOrder:
        """تأیید پرداخت سفارش."""
        result = await self.db.execute(
            select(MarketplaceOrder).where(MarketplaceOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"سفارش یافت نشد: {order_id}")

        order.payment_status = "paid"
        order.status = MarketplaceOrderStatus.PAID
        order.paid_at = datetime.now(UTC)
        order.blockchain_tx_hash = payment_tx_hash

        await self.db.commit()
        await self.db.refresh(order)

        await _emit_marketplace_event(
            "payment_completed",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "payment_tx_hash": str(payment_tx_hash),
                "total": str(order.total),
                "buyer_id": str(order.buyer_id),
            },
        )
        _notify(str(order.buyer_id), "Your payment has been received.", ntype="payment")

        return order

    async def ship_order(self, order_id: str, tracking_code: str) -> MarketplaceOrder:
        """ارسال سفارش."""
        result = await self.db.execute(
            select(MarketplaceOrder).where(MarketplaceOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"سفارش یافت نشد: {order_id}")

        if order.payment_status != "paid":
            raise ValueError("سفارش هنوز پرداخت نشده است")

        order.status = MarketplaceOrderStatus.SHIPPED
        order.tracking_code = tracking_code

        await self.db.commit()
        await self.db.refresh(order)

        await _emit_marketplace_event(
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

    async def complete_order(self, order_id: str) -> MarketplaceOrder:
        """تکمیل سفارش (تحویل به مشتری)."""
        result = await self.db.execute(
            select(MarketplaceOrder).where(MarketplaceOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"سفارش یافت نشد: {order_id}")

        if order.status != MarketplaceOrderStatus.SHIPPED:
            raise ValueError("سفارش هنوز ارسال نشده است")

        order.status = MarketplaceOrderStatus.DELIVERED
        order.delivered_at = datetime.now(UTC)
        order.settlement_status = "completed"

        await self.db.commit()
        await self.db.refresh(order)

        await _emit_marketplace_event(
            "order_completed",
            "order",
            str(order.id),
            {
                "order_id": str(order.id),
                "buyer_id": str(order.buyer_id),
                "settlement_status": str(order.settlement_status),
            },
        )
        _notify(str(order.buyer_id), "Your order is complete.", ntype="order")

        return order

    async def register_marketplace(self, data: dict) -> Marketplace:
        """ثبت بازارچه جدید."""
        marketplace = Marketplace(**data)
        self.db.add(marketplace)
        await self.db.commit()
        await self.db.refresh(marketplace)

        for founder_id in data.get("founder_ids", []):
            await self.db.execute(
                insert(MarketplaceMember).values(
                    marketplace_id=marketplace.id, user_id=founder_id, role="founder"
                )
            )
        await self.db.commit()

        return marketplace

    async def get_marketplace(self, marketplace_id: str) -> Marketplace | None:
        result = await self.db.execute(select(Marketplace).where(Marketplace.id == marketplace_id))
        return result.scalar_one_or_none()

    async def list_marketplaces(
        self,
        marketplace_type: str | None = None,
        village_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Marketplace]:
        stmt = select(Marketplace)
        if marketplace_type:
            stmt = stmt.where(Marketplace.marketplace_type == marketplace_type)
        if village_id:
            stmt = stmt.where(Marketplace.village_id == village_id)
        if status:
            stmt = stmt.where(Marketplace.status == status)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def verify_marketplace(
        self, marketplace_id: str, approved: bool, verified_by: str
    ) -> Marketplace:
        result = await self.db.execute(select(Marketplace).where(Marketplace.id == marketplace_id))
        marketplace = result.scalar_one_or_none()
        if not marketplace:
            raise ValueError(f"بازارچه یافت نشد: {marketplace_id}")
        if approved:
            marketplace.admin_approved = True
            marketplace.status = "approved"
        else:
            marketplace.status = "rejected"
        await self.db.commit()
        await self.db.refresh(marketplace)

        await _emit_marketplace_event(
            "marketplace_approved" if approved else "marketplace_rejected",
            "marketplace",
            str(marketplace.id),
            {"status": str(marketplace.status), "verified_by": str(verified_by)},
        )
        try:
            member_rows = await self.db.execute(
                select(MarketplaceMember).where(
                    MarketplaceMember.marketplace_id == marketplace.id,
                    MarketplaceMember.role == "founder",
                )
            )
            for member in member_rows.scalars().all():
                _notify(
                    str(member.user_id),
                    "Marketplace approved." if approved else "Marketplace application rejected.",
                    ntype="system",
                )
        except Exception as exc:  # noqa: BLE001 - notify must not affect a committed decision
            logger.warning("marketplace approval notification not delivered: %s", exc)
        return marketplace

    async def add_marketplace_member(
        self, marketplace_id: str, user_id: str, role: str = "member"
    ) -> MarketplaceMember:
        existing = await self.db.execute(
            select(MarketplaceMember).where(
                MarketplaceMember.marketplace_id == marketplace_id,
                MarketplaceMember.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("این کاربر قبلاً عضو بازارچه است")
        member = MarketplaceMember(
            marketplace_id=marketplace_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def create_marketplace_shop(
        self, marketplace_id: str, user_id: str, data: dict
    ) -> MarketplaceSeller:
        result = await self.db.execute(select(Marketplace).where(Marketplace.id == marketplace_id))
        marketplace = result.scalar_one_or_none()
        if not marketplace:
            raise ValueError(f"بازارچه یافت نشد: {marketplace_id}")
        if marketplace.status != "approved":
            raise ValueError("بازارچه هنوز تأیید نشده است")

        existing = await self.db.execute(
            select(MarketplaceSeller).where(
                MarketplaceSeller.marketplace_id == marketplace_id,
                MarketplaceSeller.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("این کاربر قبلاً فروشگاه دارد")

        shop = MarketplaceSeller(
            marketplace_id=marketplace_id,
            user_id=user_id,
            village_id=data.get("village_id", ""),
            shop_name=data["shop_name"],
            shop_description=data.get("shop_description", ""),
            status="pending",
        )
        self.db.add(shop)
        await self.db.commit()
        await self.db.refresh(shop)

        await _emit_marketplace_event(
            "shop_created",
            "seller",
            str(shop.id),
            {
                "marketplace_id": str(marketplace_id),
                "shop_name": shop.shop_name,
                "village_id": str(shop.village_id),
                "user_id": str(shop.user_id),
            },
        )
        _notify(str(shop.user_id), "Your shop was created and is pending review.", ntype="system")
        return shop

    async def list_marketplace_shops(
        self, marketplace_id: str, limit: int = 50
    ) -> list[MarketplaceSeller]:
        result = await self.db.execute(
            select(MarketplaceSeller)
            .where(MarketplaceSeller.marketplace_id == marketplace_id)
            .limit(limit)
        )
        return result.scalars().all()

    async def _get_commission_rule(self, village_id: str) -> MarketplaceCommissionRule:
        """دریافت قانون کارمزد برای روستا یا قانون پیش‌فرض."""
        result = await self.db.execute(
            select(MarketplaceCommissionRule).where(
                MarketplaceCommissionRule.village_id == village_id,
                MarketplaceCommissionRule.is_active,
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            result = await self.db.execute(
                select(MarketplaceCommissionRule).where(
                    MarketplaceCommissionRule.village_id is None,
                    MarketplaceCommissionRule.is_active,
                )
            )
            rule = result.scalar_one_or_none()

            if not rule:
                rule = MarketplaceCommissionRule(
                    platform_fee_bps=self.DEFAULT_PLATFORM_FEE_BPS,
                    landscape_fee_bps=self.DEFAULT_LANDSCAPE_FEE_BPS,
                )
                self.db.add(rule)
                await self.db.commit()

        return rule

    async def _decrease_stock(self, product_id: str, quantity: int | Decimal):
        """کاهش موجودی محصول.

        Deliberately does not commit: ``create_order`` calls this inside its
        own transaction, so a rejected decrement rolls the whole order back
        instead of leaving a committed order with unfulfilled stock. The old
        per-call ``commit()`` is what made the two operations inseparable.
        """
        # Coerce at the boundary: stock is an Integer column, and passing a
        # Decimal through to the driver raises a binding error.
        if isinstance(quantity, Decimal):
            quantity = int(quantity) if quantity == quantity.to_integral_value() else quantity
        result = await self.db.execute(
            select(MarketplaceProduct).where(MarketplaceProduct.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError(f"محصول یافت نشد: {product_id}")

        if product.stock < quantity:
            raise ValueError(f"موجودی کافی نیست. موجودی: {product.stock}, درخواست: {quantity}")

        product.stock -= quantity
        product.sales_count += quantity

        if product.stock == 0:
            product.status = MarketplaceProductStatus.OUT_OF_STOCK

    def _generate_slug(self, name: str) -> str:
        """تولید slug یکتا از نام محصول."""
        base_slug = name.lower().replace(" ", "-")[:100]
        random_suffix = secrets.token_hex(4)
        return f"{base_slug}-{random_suffix}"

    def _generate_order_number(self) -> str:
        """تولید شماره سفارش یکتا."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"ORD-{timestamp}-{random_suffix}"


_marketplace_service: MarketplaceService | None = None


def get_marketplace_service(db=None) -> MarketplaceService:
    """Get or create singleton marketplace service."""
    global _marketplace_service
    if _marketplace_service is None:
        _marketplace_service = MarketplaceService(db)
    return _marketplace_service


# ===================================================================
# Village Development Hub Service
# ===================================================================

from services.marketplace.hub_service import VillageDevelopmentHubService

_hub_service: VillageDevelopmentHubService | None = None


def get_hub_service(db=None) -> VillageDevelopmentHubService:
    """Get or create singleton VillageDevelopmentHubService."""
    global _hub_service
    if _hub_service is None or db is not None:
        _hub_service = VillageDevelopmentHubService(db)
    return _hub_service
