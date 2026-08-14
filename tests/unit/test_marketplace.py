"""Tests for Marketplace module with dependency injection."""
import pytest
from datetime import datetime

from engine.hydroma.marketplace.models import (
    Product, Producer, Order, ProductCategory,
    CertificationType, OrderStatus
)
from engine.hydroma.marketplace.product_catalog import (
    ProductCatalog, get_catalog
)
from engine.hydroma.marketplace.traceability import (
    TraceabilitySystem, get_traceability
)
from engine.hydroma.marketplace.order_management import (
    OrderManager, get_order_manager
)


class TestModels:
    """Test data models."""
    
    def test_product_creation(self):
        """Verify product can be created."""
        product = Product(
            name="Test Wheat",
            category=ProductCategory.GRAINS,
            price_per_kg=0.30,
            quantity_available_kg=1000,
        )
        
        assert product.name == "Test Wheat"
        assert product.traceability_code.startswith("ECO-")
    
    def test_product_can_fulfill_order(self):
        """Verify order fulfillment logic."""
        product = Product(
            name="Test",
            price_per_kg=1.0,
            quantity_available_kg=100,
            minimum_order_kg=10,
        )
        
        assert product.can_fulfill_order(50) == True
        assert product.can_fulfill_order(5) == False   # Below minimum
        assert product.can_fulfill_order(150) == False  # Above available
    
    def test_producer_rating_update(self):
        """Verify rating update with moving average."""
        producer = Producer(name="Test Farmer")
        
        producer.update_rating(5.0)
        assert producer.rating == 5.0
        
        producer.total_sales = 10
        producer.update_rating(4.0)
        assert 4.0 < producer.rating < 5.0
    
    def test_order_lifecycle(self):
        """Verify order status transitions."""
        order = Order(product_id="test", quantity_kg=10, total_price=100)
        
        assert order.status == OrderStatus.PENDING
        
        order.confirm()
        assert order.status == OrderStatus.CONFIRMED
        
        order.ship()
        assert order.status == OrderStatus.SHIPPED
        
        order.deliver()
        assert order.status == OrderStatus.DELIVERED


class TestProductCatalog:
    """Test product catalog."""
    
    def test_catalog_has_demo_products(self):
        """Verify catalog initializes with demo data."""
        catalog = ProductCatalog()
        products = catalog.list_products()
        
        assert len(products) > 0
    
    def test_filter_by_category(self):
        """Verify category filtering."""
        catalog = ProductCatalog()
        grains = catalog.list_products(category=ProductCategory.GRAINS)
        
        assert all(p.category == ProductCategory.GRAINS for p in grains)
    
    def test_filter_organic_only(self):
        """Verify organic filtering."""
        catalog = ProductCatalog()
        organic = catalog.list_products(organic_only=True)
        
        assert all(p.organic_certified for p in organic)
    
    def test_filter_by_price_range(self):
        """Verify price range filtering."""
        catalog = ProductCatalog()
        expensive = catalog.list_products(min_price=10.0)
        
        assert all(p.price_per_kg >= 10.0 for p in expensive)
    
    def test_search_products(self):
        """Verify search functionality."""
        catalog = ProductCatalog()
        results = catalog.search_products("saffron")
        
        assert len(results) > 0
        assert any("saffron" in p.name.lower() for p in results)
    
    def test_get_product_by_id(self):
        """Verify product retrieval by ID."""
        catalog = ProductCatalog()
        products = catalog.list_products()
        
        if products:
            product_id = products[0].id
            retrieved = catalog.get_product(product_id)
            assert retrieved is not None
            assert retrieved.id == product_id


class TestTraceability:
    """Test traceability system."""
    
    def test_create_trace(self):
        """Verify trace creation."""
        system = TraceabilitySystem()
        product = Product(
            name="Test",
            origin_location="Test Farm",
            producer_name="Test Producer",
            batch_number="TEST-001",
        )
        
        code = system.create_trace(product)
        
        assert code.startswith("ECO-")
        assert len(system.get_trace(code)) == 1
    
    def test_add_event(self):
        """Verify adding events to trace."""
        system = TraceabilitySystem()
        product = Product(name="Test", origin_location="Farm")
        code = system.create_trace(product)
        
        system.add_event(
            traceability_code=code,
            event="processed",
            location="Processing Center",
            actor="Cooperative",
        )
        
        trace = system.get_trace(code)
        assert len(trace) == 2
    
    def test_generate_qr_data(self):
        """Verify QR code data generation."""
        system = TraceabilitySystem()
        product = Product(name="Test", origin_location="Farm")
        code = system.create_trace(product)
        
        qr_data = system.generate_qr_data(code)
        
        assert "code" in qr_data
        assert "integrity_hash" in qr_data
        assert "verify_url" in qr_data


class TestOrderManagement:
    """Test order management with dependency injection."""
    
    def test_create_order(self):
        """Verify order creation with injected catalog."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)  # Dependency injection
        
        products = catalog.list_products()
        assert len(products) > 0, "Catalog should have products"
        
        product = products[0]
        
        order = manager.create_order(
            product_id=product.id,
            buyer_name="Test Buyer",
            quantity_kg=product.minimum_order_kg,
        )
        
        assert order.product_id == product.id
        assert order.status == OrderStatus.PENDING
    
    def test_order_reduces_quantity(self):
        """Verify ordering reduces available quantity."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)  # Dependency injection
        
        products = catalog.list_products()
        assert len(products) > 0
        
        product = products[0]
        initial_qty = product.quantity_available_kg
        order_qty = product.minimum_order_kg
        
        manager.create_order(
            product_id=product.id,
            buyer_name="Test",
            quantity_kg=order_qty,
        )
        
        updated = catalog.get_product(product.id)
        assert updated.quantity_available_kg == initial_qty - order_qty
    
    def test_cancel_order_restores_quantity(self):
        """Verify cancelling restores quantity."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)  # Dependency injection
        
        products = catalog.list_products()
        assert len(products) > 0
        
        product = products[0]
        initial_qty = product.quantity_available_kg
        
        order = manager.create_order(
            product_id=product.id,
            buyer_name="Test",
            quantity_kg=product.minimum_order_kg,
        )
        
        manager.cancel_order(order.id)
        
        updated = catalog.get_product(product.id)
        assert updated.quantity_available_kg == initial_qty
    
    def test_order_with_invalid_product(self):
        """Verify error handling for invalid product."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)
        
        with pytest.raises(ValueError, match="Product not found"):
            manager.create_order(
                product_id="nonexistent-id",
                buyer_name="Test",
                quantity_kg=10,
            )
    
    def test_order_below_minimum(self):
        """Verify error for order below minimum quantity."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)
        
        products = catalog.list_products()
        assert len(products) > 0
        
        product = products[0]
        
        with pytest.raises(ValueError, match="Cannot fulfill order"):
            manager.create_order(
                product_id=product.id,
                buyer_name="Test",
                quantity_kg=0.001,  # Below minimum
            )
    
    def test_revenue_stats(self):
        """Verify revenue statistics."""
        catalog = ProductCatalog()
        manager = OrderManager(catalog=catalog)
        
        stats = manager.get_revenue_stats()
        
        assert "total_orders" in stats
        assert "total_revenue" in stats


class TestOrderManagerSingleton:
    """Test singleton behavior for API use."""
    
    def test_singleton_returns_same_instance(self):
        """Verify get_order_manager returns singleton."""
        manager1 = get_order_manager()
        manager2 = get_order_manager()
        
        assert manager1 is manager2
    
    def test_singleton_uses_global_catalog(self):
        """Verify singleton uses global catalog."""
        manager = get_order_manager()
        catalog = get_catalog()
        
        products = catalog.list_products()
        if products:
            product = products[0]
            
            # Should be able to create order via singleton
            order = manager.create_order(
                product_id=product.id,
                buyer_name="Singleton Test",
                quantity_kg=product.minimum_order_kg,
            )
            
            assert order.product_id == product.id
