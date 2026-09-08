
"""Product catalog management for the marketplace."""

from datetime import UTC, datetime, timedelta
from typing import Optional

from .models import CertificationType, Producer, Product, ProductCategory


class ProductCatalog:
    """Product catalog with optional DB-backed persistence."""

    def __init__(
        self,
        seller_repo=None,
        product_repo=None,
    ):
        self._products: dict[str, Product] = {}
        self._producers: dict[str, Producer] = {}
        self._seller_repo = seller_repo
        self._product_repo = product_repo
        self._initialize_demo_data()

    def _initialize_demo_data(self) -> None:
        """Initialize with demo products for testing."""

        # Demo producers
        producers = [
            Producer(
                name="Golestan Organic Farm",
                location="Golestan Province, Iran",
                lat=36.8,
                lon=54.4,
                producer_type="cooperative",
                verification_status="verified",
                rating=4.8,
                total_sales=156,
                certifications=[CertificationType.ORGANIC, CertificationType.GLOBAL_GAP],
            ),
            Producer(
                name="Qashqai Nomadic Cooperative",
                location="Fars Province, Iran",
                lat=29.6,
                lon=52.5,
                producer_type="nomadic",
                verification_status="verified",
                rating=4.9,
                total_sales=89,
                certifications=[
                    CertificationType.NOMADIC_PRODUCT,
                    CertificationType.LOCAL_HERITAGE,
                ],
            ),
            Producer(
                name="Khorasan Saffron Collective",
                location="Khorasan Province, Iran",
                lat=36.3,
                lon=59.6,
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
                harvest_date=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30),
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
                harvest_date=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2),
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
                harvest_date=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=60),
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
                harvest_date=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=15),
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
                harvest_date=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=45),
                batch_number="GLS-2025-002",
            ),
        ]

        for p in products:
            self._products[p.id] = p

    def add_product(self, product: Product) -> str:
        """Add a product to the catalog."""
        self._products[product.id] = product

        if self._product_repo is not None:
            try:
                seller = self._seller_repo.get_seller_by_user(product.producer_id) if self._seller_repo else None
                seller_id = seller.id if seller else None
                self._product_repo.create_product(
                    seller_id=seller_id or product.producer_id,
                    name=product.name,
                    category=product.category.value if hasattr(product.category, 'value') else str(product.category),
                    price=product.price_per_kg,
                    village_id="default",
                    description=product.description,
                    stock=int(product.quantity_available_kg),
                    unit="kg",
                    status="active" if product.is_active else "draft",
                    organic=product.organic_certified,
                )
            except Exception:
                pass

        return product.id

    def get_product(self, product_id: str) -> Product | None:
        """Get product by ID."""
        if self._product_repo is not None:
            try:
                db_product = self._product_repo.get_product(product_id)
                if db_product is not None:
                    return Product(
                        id=db_product.id,
                        name=db_product.name,
                        category=ProductCategory(db_product.category) if db_product.category in [c.value for c in ProductCategory] else ProductCategory.OTHER,
                        description=db_product.description or "",
                        producer_id=db_product.seller_id,
                        producer_name=db_product.seller.shop_name if db_product.seller else "",
                        origin_location="",
                        price_per_kg=float(db_product.price),
                        quantity_available_kg=float(db_product.stock),
                        minimum_order_kg=1.0,
                        organic_certified=db_product.organic,
                        carbon_footprint_kg_co2=0.0,
                        water_footprint_liters=0.0,
                        is_active=db_product.status == "active",
                    )
            except Exception:
                pass
        return self._products.get(product_id)

    def list_products(
        self,
        category: ProductCategory | None = None,
        organic_only: bool = False,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 50,
    ) -> list[Product]:
        """List products with optional filters."""
        if self._product_repo is not None:
            try:
                category_str = category.value if category else None
                db_products = self._product_repo.list_products(
                    category=category_str,
                    organic_only=organic_only,
                    limit=limit,
                )
                results = []
                for db_product in db_products:
                    try:
                        cat = ProductCategory(db_product.category) if db_product.category in [c.value for c in ProductCategory] else ProductCategory.OTHER
                    except ValueError:
                        cat = ProductCategory.OTHER
                    results.append(Product(
                        id=db_product.id,
                        name=db_product.name,
                        category=cat,
                        description=db_product.description or "",
                        producer_id=db_product.seller_id,
                        producer_name=db_product.seller.shop_name if db_product.seller else "",
                        origin_location="",
                        price_per_kg=float(db_product.price),
                        quantity_available_kg=float(db_product.stock),
                        minimum_order_kg=1.0,
                        organic_certified=db_product.organic,
                        carbon_footprint_kg_co2=0.0,
                        water_footprint_liters=0.0,
                        is_active=db_product.status == "active",
                    ))
                return results
            except Exception:
                pass

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

    def search_products(self, query: str) -> list[Product]:
        """Search products by name or description."""
        query_lower = query.lower()
        return [
            p
            for p in self._products.values()
            if p.is_active
            and (query_lower in p.name.lower() or query_lower in p.description.lower())
        ]

    def get_producer(self, producer_id: str) -> Producer | None:
        """Get producer by ID."""
        if self._seller_repo is not None:
            try:
                db_seller = self._seller_repo.get_seller(producer_id)
                if db_seller is not None:
                    return Producer(
                        id=db_seller.id,
                        name=db_seller.shop_name,
                        location="",
                        lat=0.0,
                        lon=0.0,
                        producer_type="individual",
                        verification_status="verified" if db_seller.is_verified else "unverified",
                        rating=float(db_seller.rating),
                        total_sales=db_seller.total_sales,
                    )
            except Exception:
                pass
        return self._producers.get(producer_id)

    def list_producers(self) -> list[Producer]:
        """List all producers."""
        if self._seller_repo is not None:
            try:
                db_sellers = self._seller_repo.list_sellers()
                return [
                    Producer(
                        id=s.id,
                        name=s.shop_name,
                        location="",
                        lat=0.0,
                        lon=0.0,
                        producer_type="individual",
                        verification_status="verified" if s.is_verified else "unverified",
                        rating=float(s.rating),
                        total_sales=s.total_sales,
                    )
                    for s in db_sellers
                ]
            except Exception:
                pass
        return list(self._producers.values())

    def get_products_by_producer(self, producer_id: str) -> list[Product]:
        """Get all products from a specific producer."""
        if self._product_repo is not None:
            try:
                db_products = self._product_repo.list_products()
                return [p for p in db_products if p.seller_id == producer_id]
            except Exception:
                pass
        return [p for p in self._products.values() if p.producer_id == producer_id]

    def update_quantity(self, product_id: str, quantity_change: float) -> bool:
        """Update product quantity (positive or negative)."""
        if self._product_repo is not None:
            try:
                return self._product_repo.update_stock(product_id, int(quantity_change))
            except Exception:
                pass
        product = self._products.get(product_id)
        if product:
            product.quantity_available_kg += quantity_change
            if product.quantity_available_kg < 0:
                product.quantity_available_kg = 0
            return True
        return False


# Singleton instance
_catalog: ProductCatalog | None = None
_seller_repo = None
_product_repo = None


def get_catalog() -> ProductCatalog:
    """Get or create the singleton catalog."""
    global _catalog, _seller_repo, _product_repo
    if _catalog is None:
        _catalog = ProductCatalog(seller_repo=_seller_repo, product_repo=_product_repo)
    return _catalog


def init_catalog(seller_repo=None, product_repo=None) -> None:
    """Initialize catalog with database repositories."""
    global _catalog, _seller_repo, _product_repo
    _seller_repo = seller_repo
    _product_repo = product_repo
    _catalog = None  # Force re-creation
