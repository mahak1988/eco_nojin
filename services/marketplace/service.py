"""
سرویس کامل بازارچه روستایی
═══════════════════════════════════════════════════════════════════════
این سرویس شامل:
- مدیریت محصولات و فروشندگان
- پردازش سفارشات
- محاسبه و تقسیم کارمزد
- ادغام با سیستم پرداخت
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.marketplace.models import (
    MarketplaceProduct, MarketplaceSeller, MarketplaceOrder, MarketplaceCommissionRule,
    MarketplaceProductStatus, MarketplaceOrderStatus
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
        shop_description: Optional[str] = None,
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
        seller.verified_at = datetime.now(timezone.utc)
        
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
        description: Optional[str] = None,
        stock: int = 0,
        unit: str = "piece",
        story: Optional[str] = None,
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
        self,
        product_id: str,
        approved_by: str,
        approve: bool = True
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
            product.approved_at = datetime.now(timezone.utc)
        else:
            product.status = MarketplaceProductStatus.REJECTED
        
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def create_order(
        self,
        buyer_id: str,
        items: List[dict],
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
        order.paid_at = datetime.now(timezone.utc)
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
        order.delivered_at = datetime.now(timezone.utc)
        order.settlement_status = "completed"
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def _get_commission_rule(self, village_id: str) -> MarketplaceCommissionRule:
        """دریافت قانون کارمزد برای روستا یا قانون پیش‌فرض."""
        result = await self.db.execute(
            select(MarketplaceCommissionRule).where(
                MarketplaceCommissionRule.village_id == village_id,
                MarketplaceCommissionRule.is_active == True
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            result = await self.db.execute(
                select(MarketplaceCommissionRule).where(
                    MarketplaceCommissionRule.village_id == None,
                    MarketplaceCommissionRule.is_active == True
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
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"ORD-{timestamp}-{random_suffix}"
