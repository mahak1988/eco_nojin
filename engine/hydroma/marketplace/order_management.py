"""Order management with dependency injection support."""
from typing import Dict, List, Optional
from datetime import datetime

from .models import Order, OrderStatus, Product
from .product_catalog import ProductCatalog, get_catalog


class OrderManager:
    """Manage marketplace orders with injectable catalog dependency."""
    
    def __init__(self, catalog: ProductCatalog = None):
        """Initialize with optional catalog injection.
        
        Args:
            catalog: ProductCatalog instance. If None, uses singleton.
        """
        self._catalog = catalog if catalog is not None else get_catalog()
        self._orders: Dict[str, Order] = {}
    
    def create_order(
        self,
        product_id: str,
        buyer_name: str,
        quantity_kg: float,
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
            quantity_kg=quantity_kg,
            unit_price=product.price_per_kg,
            total_price=product.calculate_total_value(quantity_kg),
            traceability_code=product.traceability_code,
        )
        
        self._orders[order.id] = order
        
        # Reserve quantity
        self._catalog.update_quantity(product_id, -quantity_kg)
        
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def list_orders(
        self,
        status: Optional[OrderStatus] = None,
        limit: int = 50,
    ) -> List[Order]:
        """List orders with optional status filter."""
        orders = list(self._orders.values())
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders[:limit]
    
    def confirm_order(self, order_id: str) -> bool:
        """Confirm an order."""
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.confirm()
            return True
        return False
    
    def ship_order(self, order_id: str) -> bool:
        """Mark order as shipped."""
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.CONFIRMED:
            order.ship()
            return True
        return False
    
    def deliver_order(self, order_id: str) -> bool:
        """Mark order as delivered."""
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.SHIPPED:
            order.deliver()
            return True
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order and restore quantity."""
        order = self._orders.get(order_id)
        if order and order.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            order.cancel()
            
            # Restore quantity
            self._catalog.update_quantity(order.product_id, order.quantity_kg)
            
            return True
        return False
    
    def get_revenue_stats(self) -> dict:
        """Get revenue statistics."""
        completed = [
            o for o in self._orders.values()
            if o.status == OrderStatus.DELIVERED
        ]
        
        pending = [
            o for o in self._orders.values()
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
_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    """Get singleton order manager."""
    global _order_manager
    if _order_manager is None:
        _order_manager = OrderManager()
    return _order_manager
