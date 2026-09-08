"""Marketplace repositories — database-backed persistence for sellers, products, and orders."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from services.marketplace.models import MarketplaceOrder, MarketplaceProduct, MarketplaceSeller


class SellerRepository:
    """Repository for marketplace sellers."""

    def __init__(self, db: Session):
        self.db = db

    def create_seller(
        self,
        user_id: str,
        shop_name: str,
        village_id: str,
        shop_description: str = "",
        status: str = "pending",
        is_verified: bool = False,
        certifications: list = None,
    ) -> MarketplaceSeller:
        """Create a new seller."""
        seller = MarketplaceSeller(
            user_id=user_id,
            village_id=village_id,
            shop_name=shop_name,
            shop_description=shop_description,
            status=status,
            is_verified=is_verified,
            certifications=certifications or [],
        )
        self.db.add(seller)
        self.db.commit()
        self.db.refresh(seller)
        return seller

    def get_seller(self, seller_id: str) -> Optional[MarketplaceSeller]:
        """Get seller by ID."""
        return self.db.query(MarketplaceSeller).filter(MarketplaceSeller.id == seller_id).first()

    def get_seller_by_user(self, user_id: str) -> Optional[MarketplaceSeller]:
        """Get seller by user ID."""
        return self.db.query(MarketplaceSeller).filter(MarketplaceSeller.user_id == user_id).first()

    def list_sellers(self, village_id: Optional[str] = None, status: Optional[str] = None):
        """List sellers with optional filters."""
        query = self.db.query(MarketplaceSeller)
        if village_id is not None:
            query = query.filter(MarketplaceSeller.village_id == village_id)
        if status is not None:
            query = query.filter(MarketplaceSeller.status == status)
        return query.order_by(MarketplaceSeller.created_at.desc()).all()

    def update_seller(self, seller_id: str, **kwargs) -> Optional[MarketplaceSeller]:
        """Update seller fields."""
        seller = self.get_seller(seller_id)
        if not seller:
            return None
        for key, value in kwargs.items():
            if hasattr(seller, key):
                setattr(seller, key, value)
        seller.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(seller)
        return seller


class ProductRepository:
    """Repository for marketplace products."""

    def __init__(self, db: Session):
        self.db = db

    def create_product(
        self,
        seller_id: str,
        name: str,
        category: str,
        price: Decimal,
        village_id: str,
        description: str = "",
        stock: int = 0,
        unit: str = "piece",
        status: str = "draft",
        organic: bool = False,
        pgs_certified: bool = False,
    ) -> MarketplaceProduct:
        """Create a new product."""
        product = MarketplaceProduct(
            seller_id=seller_id,
            name=name,
            category=category,
            price=price,
            village_id=village_id,
            description=description,
            stock=stock,
            unit=unit,
            status=status,
            organic=organic,
            pgs_certified=pgs_certified,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: str) -> Optional[MarketplaceProduct]:
        """Get product by ID."""
        return self.db.query(MarketplaceProduct).filter(MarketplaceProduct.id == product_id).first()

    def list_products(
        self,
        category: Optional[str] = None,
        village_id: Optional[str] = None,
        status: Optional[str] = None,
        organic_only: bool = False,
        limit: int = 50,
    ):
        """List products with optional filters."""
        query = self.db.query(MarketplaceProduct)
        if category is not None:
            query = query.filter(MarketplaceProduct.category == category)
        if village_id is not None:
            query = query.filter(MarketplaceProduct.village_id == village_id)
        if status is not None:
            query = query.filter(MarketplaceProduct.status == status)
        if organic_only:
            query = query.filter(MarketplaceProduct.organic == True)
        return query.limit(limit).all()

    def update_product(self, product_id: str, **kwargs) -> Optional[MarketplaceProduct]:
        """Update product fields."""
        product = self.get_product(product_id)
        if not product:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stock(self, product_id: str, quantity_change: int) -> bool:
        """Update product stock."""
        product = self.get_product(product_id)
        if not product:
            return False
        product.stock = max(0, product.stock + quantity_change)
        self.db.commit()
        self.db.refresh(product)
        return True


class OrderRepository:
    """Repository for marketplace orders."""

    def __init__(self, db: Session):
        self.db = db

    def create_order(
        self,
        order_number: str,
        buyer_id: str,
        village_id: str,
        subtotal: Decimal,
        total: Decimal,
        product_id: Optional[str] = None,
        status: str = "pending",
        payment_status: str = "pending",
        shipping_address: dict = None,
    ) -> MarketplaceOrder:
        """Create a new order."""
        order = MarketplaceOrder(
            order_number=order_number,
            buyer_id=buyer_id,
            village_id=village_id,
            subtotal=subtotal,
            total=total,
            product_id=product_id,
            status=status,
            payment_status=payment_status,
            shipping_address=shipping_address or {},
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_order(self, order_id: str) -> Optional[MarketplaceOrder]:
        """Get order by ID."""
        return self.db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()

    def get_order_by_number(self, order_number: str) -> Optional[MarketplaceOrder]:
        """Get order by order number."""
        return self.db.query(MarketplaceOrder).filter(MarketplaceOrder.order_number == order_number).first()

    def list_orders(
        self,
        buyer_id: Optional[str] = None,
        village_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ):
        """List orders with optional filters."""
        query = self.db.query(MarketplaceOrder)
        if buyer_id is not None:
            query = query.filter(MarketplaceOrder.buyer_id == buyer_id)
        if village_id is not None:
            query = query.filter(MarketplaceOrder.village_id == village_id)
        if status is not None:
            query = query.filter(MarketplaceOrder.status == status)
        return query.limit(limit).all()

    def update_order(self, order_id: str, **kwargs) -> Optional[MarketplaceOrder]:
        """Update order fields."""
        order = self.get_order(order_id)
        if not order:
            return None
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        order.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order
