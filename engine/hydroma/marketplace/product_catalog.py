"""Product catalog management for the marketplace."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

from .models import Product, Producer, ProductCategory, CertificationType


class ProductCatalog:
    """In-memory product catalog for research mode."""
    
    def __init__(self):
        self._products: Dict[str, Product] = {}
        self._producers: Dict[str, Producer] = {}
        self._initialize_demo_data()
    
    def _initialize_demo_data(self) -> None:
        """Initialize with demo products for testing."""
        
        # Demo producers
        producers = [
            Producer(
                name="Golestan Organic Farm",
                location="Golestan Province, Iran",
                lat=36.8, lon=54.4,
                producer_type="cooperative",
                verification_status="verified",
                rating=4.8,
                total_sales=156,
                certifications=[CertificationType.ORGANIC, CertificationType.GLOBAL_GAP],
            ),
            Producer(
                name="Qashqai Nomadic Cooperative",
                location="Fars Province, Iran",
                lat=29.6, lon=52.5,
                producer_type="nomadic",
                verification_status="verified",
                rating=4.9,
                total_sales=89,
                certifications=[CertificationType.NOMADIC_PRODUCT, CertificationType.LOCAL_HERITAGE],
            ),
            Producer(
                name="Khorasan Saffron Collective",
                location="Khorasan Province, Iran",
                lat=36.3, lon=59.6,
                producer_type="cooperative",
                verification_status="verified",
                rating=4.7,
                total_sales=234,
                certifications=[CertificationType.ORGANIC, CertificationType.WOMEN_PRODUCED],
            ),
        ]
        
        for p in producers:
            self._producers[p.id] = p
        
        # Demo products
        products = [
            Product(
                name="Organic Wheat (Golestan)",
                category=ProductCategory.GRAINS,
                description="High-quality organic wheat from Golestan cooperative farms",
                producer_id=producers[0].id,
                producer_name=producers[0].name,
                origin_location=producers[0].location,
                price_per_kg=0.35,
                quantity_available_kg=5000,
                minimum_order_kg=100,
                organic_certified=True,
                carbon_footprint_kg_co2=0.8,
                water_footprint_liters=1200,
                harvest_date=datetime.utcnow() - timedelta(days=30),
                batch_number="GLS-2025-001",
            ),
            Product(
                name="Nomadic Dairy (Qashqai)",
                category=ProductCategory.DAIRY,
                description="Traditional dairy products from Qashqai nomadic herders",
                producer_id=producers[1].id,
                producer_name=producers[1].name,
                origin_location=producers[1].location,
                price_per_kg=8.50,
                quantity_available_kg=200,
                minimum_order_kg=5,
                organic_certified=True,
                carbon_footprint_kg_co2=2.5,
                water_footprint_liters=800,
                harvest_date=datetime.utcnow() - timedelta(days=2),
                batch_number="QSH-2025-042",
            ),
            Product(
                name="Premium Saffron (Khorasan)",
                category=ProductCategory.HERBS_MEDICINAL,
                description="World-famous Khorasan saffron, hand-harvested by women",
                producer_id=producers[2].id,
                producer_name=producers[2].name,
                origin_location=producers[2].location,
                price_per_kg=850.00,
                quantity_available_kg=15,
                minimum_order_kg=0.1,
                organic_certified=True,
                carbon_footprint_kg_co2=0.1,
                water_footprint_liters=50,
                harvest_date=datetime.utcnow() - timedelta(days=60),
                batch_number="KHS-2025-007",
            ),
            Product(
                name="Medicinal Thyme (Zagros)",
                category=ProductCategory.HERBS_MEDICINAL,
                description="Wild-harvested thyme from Zagros mountains",
                producer_id=producers[1].id,
                producer_name=producers[1].name,
                origin_location=producers[1].location,
                price_per_kg=12.00,
                quantity_available_kg=150,
                minimum_order_kg=2,
                organic_certified=True,
                carbon_footprint_kg_co2=0.2,
                water_footprint_liters=100,
                harvest_date=datetime.utcnow() - timedelta(days=15),
                batch_number="ZGR-2025-023",
            ),
            Product(
                name="Organic Barley (Golestan)",
                category=ProductCategory.GRAINS,
                description="Drought-resistant barley variety for arid regions",
                producer_id=producers[0].id,
                producer_name=producers[0].name,
                origin_location=producers[0].location,
                price_per_kg=0.28,
                quantity_available_kg=8000,
                minimum_order_kg=200,
                organic_certified=True,
                carbon_footprint_kg_co2=0.6,
                water_footprint_liters=900,
                harvest_date=datetime.utcnow() - timedelta(days=45),
                batch_number="GLS-2025-002",
            ),
        ]
        
        for p in products:
            self._products[p.id] = p
    
    def add_product(self, product: Product) -> str:
        """Add a product to the catalog."""
        self._products[product.id] = product
        return product.id
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self._products.get(product_id)
    
    def list_products(
        self,
        category: Optional[ProductCategory] = None,
        organic_only: bool = False,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
    ) -> List[Product]:
        """List products with optional filters."""
        results = list(self._products.values())
        
        if category:
            results = [p for p in results if p.category == category]
        
        if organic_only:
            results = [p for p in results if p.organic_certified]
        
        if min_price is not None:
            results = [p for p in results if p.price_per_kg >= min_price]
        
        if max_price is not None:
            results = [p for p in results if p.price_per_kg <= max_price]
        
        # Only active products
        results = [p for p in results if p.is_active]
        
        return results[:limit]
    
    def search_products(self, query: str) -> List[Product]:
        """Search products by name or description."""
        query_lower = query.lower()
        return [
            p for p in self._products.values()
            if p.is_active and (
                query_lower in p.name.lower() or
                query_lower in p.description.lower()
            )
        ]
    
    def get_producer(self, producer_id: str) -> Optional[Producer]:
        """Get producer by ID."""
        return self._producers.get(producer_id)
    
    def list_producers(self) -> List[Producer]:
        """List all producers."""
        return list(self._producers.values())
    
    def get_products_by_producer(self, producer_id: str) -> List[Product]:
        """Get all products from a specific producer."""
        return [
            p for p in self._products.values()
            if p.producer_id == producer_id
        ]
    
    def update_quantity(self, product_id: str, quantity_change: float) -> bool:
        """Update product quantity (positive or negative)."""
        product = self._products.get(product_id)
        if product:
            product.quantity_available_kg += quantity_change
            if product.quantity_available_kg < 0:
                product.quantity_available_kg = 0
            return True
        return False


# Singleton instance
_catalog: Optional[ProductCatalog] = None


def get_catalog() -> ProductCatalog:
    """Get or create the singleton catalog."""
    global _catalog
    if _catalog is None:
        _catalog = ProductCatalog()
    return _catalog
