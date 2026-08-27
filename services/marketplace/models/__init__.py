import uuid

"""
مدل‌های داده بازارچه روستایی
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.models import Base


class MarketplaceProductStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class MarketplaceOrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class MarketplaceSeller(Base):
    __tablename__ = "marketplace_sellers"
    __table_args__ = (
        Index("idx_seller_village", "village_id"),
        Index("idx_seller_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    village_id = Column(String(100), nullable=False)
    shop_name = Column(String(200), nullable=False)
    shop_description = Column(Text)
    status = Column(String(20), default="pending", index=True)
    is_verified = Column(Boolean, default=False)
    certifications = Column(JSON, default=list)
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=Decimal("0.00"))
    rating = Column(Numeric(3, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    products = relationship("MarketplaceProduct", back_populates="seller")


class MarketplaceProduct(Base):
    __tablename__ = "marketplace_products"
    __table_args__ = (
        Index("idx_product_seller", "seller_id"),
        Index("idx_product_village", "village_id"),
        Index("idx_product_status", "status"),
        Index("idx_product_category", "category"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), ForeignKey("marketplace_sellers.id"), nullable=False)
    name = Column(String(300), nullable=False)
    slug = Column(String(300), nullable=False, unique=True, index=True)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    stock = Column(Integer, default=0)
    unit = Column(String(50), default="piece")
    village_id = Column(String(100), nullable=False, index=True)
    uses_village_brand = Column(Boolean, default=True)
    status = Column(SQLEnum(MarketplaceProductStatus), default=MarketplaceProductStatus.DRAFT, index=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    images = Column(JSON, default=list)
    pgs_certified = Column(Boolean, default=False)
    organic = Column(Boolean, default=False)
    story = Column(Text)
    metadata_json = Column(JSON, default=dict)
    sales_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    seller = relationship("MarketplaceSeller", back_populates="products")


class MarketplaceOrder(Base):
    __tablename__ = "marketplace_orders"
    __table_args__ = (
        Index("idx_order_buyer", "buyer_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_village", "village_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    buyer_id = Column(String(36), nullable=False, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    subtotal = Column(Numeric(15, 2), nullable=False)
    platform_fee = Column(Numeric(15, 2), default=Decimal("0.00"))
    landscape_fee = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    status = Column(SQLEnum(MarketplaceOrderStatus), default=MarketplaceOrderStatus.PENDING, index=True)
    payment_status = Column(String(20), default="pending")
    shipping_address = Column(JSON)
    blockchain_tx_hash = Column(String(100), nullable=True)
    settlement_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class MarketplaceCommissionRule(Base):
    __tablename__ = "marketplace_commission_rules"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True)
    platform_fee_bps = Column(Integer, default=300)
    landscape_fee_bps = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# Merged from models_legacy.py
class ProductCategory(Enum):
    """Product categories for the marketplace."""

    GRAINS = "grains"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    HERBS_MEDICINAL = "herbs_medicinal"
    DAIRY = "dairy"
    HONEY = "honey"
    HANDICRAFTS = "handicrafts"
    SEEDS = "seeds"
    FERTILIZER_ORGANIC = "fertilizer_organic"
    OTHER = "other"

# Merged from models_legacy.py
class CertificationType(Enum):
    """Available certifications for products and sellers."""

    ORGANIC = "organic"
    FAIR_TRADE = "fair_trade"
    GLOBAL_GAP = "global_gap"
    CARBON_NEUTRAL = "carbon_neutral"
    WATER_SAVING = "water_saving"
    LOCAL_HERITAGE = "local_heritage"
    WOMEN_PRODUCED = "women_produced"
    NOMADIC_PRODUCT = "nomadic_product"

# Merged from models_legacy.py
class OrderStatus(Enum):
    """Order lifecycle status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Merged from models_legacy.py
class Producer:
    """A product producer (farmer, pastoralist, cooperative)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    location: str = ""
    lat: float = 0.0
    lon: float = 0.0
    producer_type: str = "individual"  # individual, cooperative, nomadic
    verification_status: str = "unverified"  # unverified, pending, verified
    rating: float = 0.0
    total_sales: int = 0
    certifications: list[CertificationType] = field(default_factory=list)
    joined_date: datetime = field(default_factory=datetime.utcnow)

    def add_certification(self, cert: CertificationType) -> None:
        if cert not in self.certifications:
            self.certifications.append(cert)

    def update_rating(self, new_rating: float) -> None:
        """Update rating with exponential moving average."""
        if self.total_sales == 0:
            self.rating = new_rating
        else:
            alpha = 0.3  # Weight for new rating
            self.rating = alpha * new_rating + (1 - alpha) * self.rating

# Merged from models_legacy.py
class Product:
    """A product listed in the marketplace."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    category: ProductCategory = ProductCategory.OTHER
    description: str = ""

    # Producer info
    producer_id: str = ""
    producer_name: str = ""
    origin_location: str = ""

    # Pricing and quantity
    price_per_kg: float = 0.0
    quantity_available_kg: float = 0.0
    minimum_order_kg: float = 1.0

    # Sustainability metrics
    organic_certified: bool = False
    carbon_footprint_kg_co2: float = 0.0
    water_footprint_liters: float = 0.0

    # Traceability
    harvest_date: datetime | None = None
    expiry_date: datetime | None = None
    batch_number: str = ""
    traceability_code: str = field(default_factory=lambda: f"ECO-{uuid.uuid4().hex[:12].upper()}")

    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def calculate_total_value(self, quantity_kg: float) -> float:
        """Calculate total value for a given quantity."""
        return quantity_kg * self.price_per_kg

    def can_fulfill_order(self, quantity_kg: float) -> bool:
        """Check if product can fulfill an order."""
        return (
            self.is_active
            and quantity_kg >= self.minimum_order_kg
            and quantity_kg <= self.quantity_available_kg
        )

# Merged from models_legacy.py
class Order:
    """A marketplace order."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    product_id: str = ""
    product_name: str = ""
    buyer_name: str = ""
    quantity_kg: float = 0.0
    unit_price: float = 0.0
    total_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    traceability_code: str = ""

    def confirm(self) -> None:
        self.status = OrderStatus.CONFIRMED
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)

    def ship(self) -> None:
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)

    def deliver(self) -> None:
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)

# Merged from models_legacy.py
class TraceRecord:
    """A single record in the supply chain trace."""

    timestamp: datetime
    event: str  # harvested, processed, packaged, shipped, delivered
    location: str
    actor: str
    notes: str = ""
    temperature_c: float | None = None
    humidity_pct: float | None = None
