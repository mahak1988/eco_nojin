"""Order management with dependency injection support."""

from datetime import datetime
from typing import Optional

from .models import Order, OrderStatus
from .product_catalog import ProductCatalog, get_catalog


class OrderManager:
    """Manage marketplace orders with injectable catalog dependency."""

    def __init__(self, catalog: ProductCatalog = None, order_repo=None):
        """Initialize with optional catalog injection.

        Args:
            catalog: ProductCatalog instance. If None, uses singleton.
            order_repo: OrderRepository instance for DB persistence.
        """
        self._catalog = catalog if catalog is not None else get_catalog()
        self._orders: dict[str, Order] = {}
        self._order_repo = order_repo
        self._carts: dict[str, dict] = {}  # buyer_id -> cart data
        self._wishlists: dict[str, dict] = {}  # buyer_id -> wishlist data

    def _get_or_create_cart(self, buyer_id: str) -> dict:
        """Get or create a cart for the buyer."""
        if buyer_id not in self._carts:
            self._carts[buyer_id] = {
                "id": f"cart_{buyer_id}",
                "items": [],
                "total_items": 0,
                "subtotal": 0.0,
            }
        return self._carts[buyer_id]

    def add_to_cart(self, buyer_id: str, items: list[dict]) -> dict:
        """Add items to user's cart."""
        cart = self._get_or_create_cart(buyer_id)
        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            # Check if product exists
            product = self._catalog.get_product(product_id)
            if not product:
                raise ValueError(f"Product not found: {product_id}")

            # Check if item already in cart
            existing = next((i for i in cart["items"] if i["product_id"] == product_id), None)
            if existing:
                existing["quantity"] += quantity
            else:
                cart["items"].append({
                    "product_id": product_id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "price": float(product.price_per_kg),
                })

        # Recalculate totals
        cart["total_items"] = sum(i["quantity"] for i in cart["items"])
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])

        return cart

    def get_cart(self, buyer_id: str) -> dict | None:
        """Get user's current cart."""
        return self._carts.get(buyer_id)

    def remove_from_cart(self, buyer_id: str, product_id: str) -> None:
        """Remove item from cart."""
        cart = self._carts.get(buyer_id)
        if not cart:
            raise ValueError("Cart not found")
        cart["items"] = [i for i in cart["items"] if i["product_id"] != product_id]
        cart["total_items"] = sum(i["quantity"] for i in cart["items"])
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])

    def update_cart_item(self, buyer_id: str, product_id: str, quantity: int) -> dict:
        """Update item quantity in cart."""
        cart = self._get_or_create_cart(buyer_id)
        item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
        if not item:
            raise ValueError(f"Item not found in cart: {product_id}")
        if quantity <= 0:
            self.remove_from_cart(buyer_id, product_id)
        else:
            item["quantity"] = quantity
            cart["total_items"] = sum(i["quantity"] for i in cart["items"])
            cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])
        return cart

    # --- Wishlist Methods ---

    def _get_or_create_wishlist(self, buyer_id: str) -> dict:
        """Get or create a wishlist for the buyer."""
        if buyer_id not in self._wishlists:
            self._wishlists[buyer_id] = {
                "id": f"wishlist_{buyer_id}",
                "items": [],
                "count": 0,
            }
        return self._wishlists[buyer_id]

    def add_to_wishlist(self, buyer_id: str, product_id: str) -> dict:
        """Add product to user's wishlist."""
        wishlist = self._get_or_create_wishlist(buyer_id)
        
        # Check if product exists
        product = self._catalog.get_product(product_id)
        if not product:
            raise ValueError(f"Product not found: {product_id}")

        # Check if already in wishlist
        existing = next((i for i in wishlist["items"] if i["product_id"] == product_id), None)
        if existing:
            raise ValueError(f"Product already in wishlist: {product_id}")

        wishlist["items"].append({
            "product_id": product_id,
            "product_name": product.name,
            "price_per_kg": float(product.price_per_kg),
            "images": product.images if hasattr(product, 'images') else [],
            "category": product.category.value if hasattr(product.category, 'value') else str(product.category),
            "organic_certified": product.organic_certified,
        })
        wishlist["count"] = len(wishlist["items"])

        return wishlist

    def get_wishlist(self, buyer_id: str) -> dict:
        """Get user's wishlist."""
        wishlist = self._wishlists.get(buyer_id)
        if not wishlist:
            return {"id": None, "items": [], "count": 0}
        return wishlist

    def remove_from_wishlist(self, buyer_id: str, product_id: str) -> None:
        """Remove item from wishlist."""
        wishlist = self._wishlists.get(buyer_id)
        if not wishlist:
            raise ValueError("Wishlist not found")
        wishlist["items"] = [i for i in wishlist["items"] if i["product_id"] != product_id]
        wishlist["count"] = len(wishlist["items"])

    def register_vendor(
        self,
        user_id: str,
        shop_name: str,
        description: str,
        location: str,
        village_id: str,
        product_types: str = "",
        certifications: str = "",
        production_capacity: str = "",
        years_experience: str = "",
        contact_phone: str = "",
        social_media: str = "",
        operating_hours: str = "",
        delivery_area: str = "",
        currency: str = "IRR",
        marketplace_id: str = "",
    ):
        """Register a new vendor."""
        seller = self._catalog._producers.get(user_id)
        if seller:
            seller.name = shop_name
            seller.location = location
            seller.producer_type = "individual"
            seller.verification_status = "pending"
        return seller or type('Seller', (), {
            'id': user_id,
            'name': shop_name,
            'shop_name': shop_name,
            'description': description,
            'location': location,
            'village_id': village_id,
            'status': 'pending',
            'contact_phone': contact_phone,
            'social_media': social_media,
            'operating_hours': operating_hours,
            'delivery_area': delivery_area,
            'currency': currency,
            'marketplace_id': marketplace_id,
        })()

    def create_order(
        self,
        product_id: str,
        buyer_name: str,
        quantity_kg: float,
        seller_id: str = "",
    ) -> Order:
        """Create a new order."""
        product = self._catalog.get_product(product_id)

        if not product:
            raise ValueError(f"Product not found: {product_id}")

        if not product.can_fulfill_order(quantity_kg):
            raise ValueError(
                f"Cannot fulfill order: min={product.minimum_order_kg}kg, "
                f"available={product.quantity_available_kg}kg"
            )

        order = Order(
            product_id=product_id,
            product_name=product.name,
            buyer_name=buyer_name,
            seller_id=seller_id or getattr(product, 'producer_id', ''),
            quantity_kg=quantity_kg,
            unit_price=product.price_per_kg,
            total_price=product.calculate_total_value(quantity_kg),
            traceability_code=product.traceability_code,
        )

        self._orders[order.id] = order

        if self._order_repo is not None:
            try:
                self._order_repo.create_order(
                    order_number=f"ORD-{order.id[:8].upper()}",
                    buyer_id=buyer_name,
                    village_id="default",
                    subtotal=order.total_price,
                    total=order.total_price,
                    product_id=product_id,
                    status=order.status.value,
                )
            except Exception:
                pass

        # Reserve quantity
        self._catalog.update_quantity(product_id, -quantity_kg)

        return order

    def get_order(self, order_id: str) -> Order | None:
        """Get order by ID."""
        if self._order_repo is not None:
            try:
                db_order = self._order_repo.get_order(order_id)
                if db_order is not None:
                    return Order(
                        id=db_order.id,
                        product_id=db_order.product_id or "",
                        product_name="",
                        buyer_name=db_order.buyer_id,
                        quantity_kg=0.0,
                        unit_price=0.0,
                        total_price=float(db_order.total),
                        status=OrderStatus(db_order.status) if db_order.status in [s.value for s in OrderStatus] else OrderStatus.PENDING,
                        created_at=db_order.created_at,
                    )
            except Exception:
                pass
        return self._orders.get(order_id)

    def list_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 50,
    ) -> list[Order]:
        """List orders with optional status filter."""
        if self._order_repo is not None:
            try:
                status_str = status.value if status else None
                db_orders = self._order_repo.list_orders(status=status_str, limit=limit)
                return [
                    Order(
                        id=o.id,
                        product_id=o.product_id or "",
                        product_name="",
                        buyer_name=o.buyer_id,
                        quantity_kg=0.0,
                        unit_price=0.0,
                        total_price=float(o.total),
                        status=OrderStatus(o.status) if o.status in [s.value for s in OrderStatus] else OrderStatus.PENDING,
                        created_at=o.created_at,
                    )
                    for o in db_orders
                ]
            except Exception:
                pass
        orders = list(self._orders.values())

        if status:
            orders = [o for o in orders if o.status == status]

        orders.sort(key=lambda x: x.created_at, reverse=True)

        return orders[:limit]

    def confirm_order(self, order_id: str) -> bool:
        """Confirm an order."""
        if self._order_repo is not None:
            try:
                updated = self._order_repo.update_order(order_id, status="confirmed")
                if updated:
                    order = self.get_order(order_id)
                    if order:
                        order.status = OrderStatus.CONFIRMED
                    return True
            except Exception:
                pass
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.confirm()
            return True
        return False

    def ship_order(self, order_id: str) -> bool:
        """Mark order as shipped."""
        if self._order_repo is not None:
            try:
                updated = self._order_repo.update_order(order_id, status="shipped")
                if updated:
                    order = self.get_order(order_id)
                    if order:
                        order.status = OrderStatus.SHIPPED
                    return True
            except Exception:
                pass
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.CONFIRMED:
            order.ship()
            return True
        return False

    def deliver_order(self, order_id: str) -> bool:
        """Mark order as delivered."""
        if self._order_repo is not None:
            try:
                updated = self._order_repo.update_order(order_id, status="delivered")
                if updated:
                    order = self.get_order(order_id)
                    if order:
                        order.status = OrderStatus.DELIVERED
                    return True
            except Exception:
                pass
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.SHIPPED:
            order.deliver()
            return True
        return False

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order and restore quantity."""
        if self._order_repo is not None:
            try:
                updated = self._order_repo.update_order(order_id, status="cancelled")
                if updated:
                    order = self.get_order(order_id)
                    if order:
                        self._catalog.update_quantity(order.product_id, order.quantity_kg)
                    return True
            except Exception:
                pass
        order = self._orders.get(order_id)
        if order and order.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            order.cancel()

            # Restore quantity
            self._catalog.update_quantity(order.product_id, order.quantity_kg)

            return True
        return False

    def get_revenue_stats(self) -> dict:
        """Get revenue statistics."""
        if self._order_repo is not None:
            try:
                db_orders = self._order_repo.list_orders(limit=1000)
                completed = [o for o in db_orders if o.status == "delivered"]
                pending = [o for o in db_orders if o.status in ["pending", "confirmed", "shipped"]]
                return {
                    "total_orders": len(db_orders),
                    "completed_orders": len(completed),
                    "pending_orders": len(pending),
                    "total_revenue": sum(float(o.total) for o in completed),
                    "pending_revenue": sum(float(o.total) for o in pending),
                }
            except Exception:
                pass
        completed = [o for o in self._orders.values() if o.status == OrderStatus.DELIVERED]

        pending = [
            o
            for o in self._orders.values()
            if o.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED]
        ]

        return {
            "total_orders": len(self._orders),
            "completed_orders": len(completed),
            "pending_orders": len(pending),
            "total_revenue": sum(o.total_price for o in completed),
            "pending_revenue": sum(o.total_price for o in pending),
        }


# Singleton for API use
_order_manager: OrderManager | None = None
_order_repo = None


def get_order_manager() -> OrderManager:
    """Get singleton order manager."""
    global _order_manager, _order_repo
    if _order_manager is None:
        _order_manager = OrderManager(order_repo=_order_repo)
    return _order_manager


def init_order_manager(order_repo=None) -> None:
    """Initialize order manager with database repository."""
    global _order_manager, _order_repo
    _order_repo = order_repo
    _order_manager = None  # Force re-creation
