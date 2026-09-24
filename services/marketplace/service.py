"""
سرویس کامل بازارچه روستایی
═══════════════════════════════════════════════════════════════════════
این سرویس شامل:
- مدیریت محصولات و فروشندگان
- پردازش سفارشات
- محاسبه و تقسیم کارمزد
- ادغام با سیستم پرداخت
"""

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.marketplace.models import (
    Marketplace,
    MarketplaceCommissionRule,
    MarketplaceMember,
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)


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
        """ثبت فروشنده جدید."""
        if not shop_name or len(shop_name.strip()) == 0:
            raise ValueError("نام فروشگاه نمی‌تواند خالی باشد")

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

        subtotal = Decimal("0")
        for item in items:
            if "price" not in item or "quantity" not in item:
                raise ValueError("هر آیتم باید price و quantity داشته باشد")

            subtotal += Decimal(str(item["price"])) * item["quantity"]

        commission_rule = await self._get_commission_rule(village_id)

        platform_fee = subtotal * Decimal(commission_rule.platform_fee_bps) / Decimal(10000)
        landscape_fee = subtotal * Decimal(commission_rule.landscape_fee_bps) / Decimal(10000)
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

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        for item in items:
            await self._decrease_stock(item["product_id"], item["quantity"])

        return order

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

    async def _decrease_stock(self, product_id: str, quantity: int):
        """کاهش موجودی محصول."""
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

        await self.db.commit()

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

from services.marketplace.hub_service import VillageDevelopmentHubService  # noqa: E402

_hub_service: VillageDevelopmentHubService | None = None


def get_hub_service(db=None) -> VillageDevelopmentHubService:
    """Get or create singleton VillageDevelopmentHubService."""
    global _hub_service
    if _hub_service is None or db is not None:
        _hub_service = VillageDevelopmentHubService(db)
    return _hub_service
