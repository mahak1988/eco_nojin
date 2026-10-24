"""
تست‌های Integration برای Marketplace
═══════════════════════════════════════════════════════════════════════
"""

from decimal import Decimal

import pytest


class TestMarketplaceIntegration:
    """تست‌های یکپارچگی بازارچه."""

    @pytest.mark.asyncio
    async def test_complete_order_flow(self, marketplace_service):
        """تست جریان کامل سفارش."""
        # 1. ثبت فروشنده
        seller = await marketplace_service.register_seller(
            user_id="user_123",
            village_id="hejij",
            shop_name="فروشگاه علی",
        )
        assert seller is not None

        # 2. تأیید فروشنده
        seller = await marketplace_service.verify_seller(str(seller.id), "admin_123")
        assert seller.is_verified

        # 3. ایجاد محصول
        product = await marketplace_service.create_product(
            seller_id=str(seller.id),
            name="عسل طبیعی",
            price=Decimal("350000"),
            village_id="hejij",
            category="food",
            stock=50,
        )
        assert product is not None

        # 4. تأیید محصول
        product = await marketplace_service.approve_product(str(product.id), "manager_123")
        assert product.status.value == "approved"

        # 5. ایجاد سفارش
        order = await marketplace_service.create_order(
            buyer_id="buyer_123",
            items=[{"product_id": str(product.id), "quantity": 2, "price": 350000}],
            village_id="hejij",
            shipping_address={"city": "کرمانشاه", "address": "..."},
        )
        assert order is not None
        assert order.total > 0

        # 6. تأیید پرداخت
        order = await marketplace_service.confirm_payment(str(order.id), "tx_hash_123")
        assert order.payment_status == "paid"

        # 7. ارسال سفارش
        order = await marketplace_service.ship_order(str(order.id), "TRACK123")
        assert order.status.value == "shipped"

        # 8. تکمیل سفارش
        order = await marketplace_service.complete_order(str(order.id))
        assert order.status.value == "delivered"
