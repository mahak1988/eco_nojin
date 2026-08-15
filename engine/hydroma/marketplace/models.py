"""Data models for marketplace functionality."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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


class OrderStatus(Enum):
    """Order lifecycle status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
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


@dataclass
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


@dataclass
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
        self.updated_at = datetime.utcnow()

    def ship(self) -> None:
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.utcnow()

    def deliver(self) -> None:
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.utcnow()


@dataclass
class TraceRecord:
    """A single record in the supply chain trace."""

    timestamp: datetime
    event: str  # harvested, processed, packaged, shipped, delivered
    location: str
    actor: str
    notes: str = ""
    temperature_c: float | None = None
    humidity_pct: float | None = None
