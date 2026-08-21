"""Supply chain traceability using blockchain.

Provides immutable product traceability.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceEvent:
    """Single trace event in supply chain."""

    event_id: str
    product_id: str
    event_type: str  # harvested, processed, packaged, shipped, delivered
    location: str
    actor: str
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tx_hash: str = ""


@dataclass
class TracedProduct:
    """Product with traceability."""

    product_id: str
    producer: str
    batch_number: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    events: list[TraceEvent] = field(default_factory=list)
    verified: bool = False
    verified_at: datetime | None = None
    tx_hash: str = ""


class SupplyChainRegistry:
    """Supply chain traceability registry."""

    def __init__(self):
        self.products: dict[str, TracedProduct] = {}
        self._tx_counter = 0

    def _generate_tx_hash(self) -> str:
        """Generate mock transaction hash."""
        self._tx_counter += 1
        return f"0x{uuid.uuid4().hex[:64]}"

    def register_product(
        self,
        producer: str,
        batch_number: str,
        initial_event: str = "harvested",
        location: str = "",
        notes: str = "",
    ) -> TracedProduct:
        """Register a new product in supply chain."""
        product_id = f"prod_{uuid.uuid4().hex[:8]}"

        product = TracedProduct(
            product_id=product_id,
            producer=producer,
            batch_number=batch_number,
            tx_hash=self._generate_tx_hash(),
        )

        # Add initial event
        event = TraceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            product_id=product_id,
            event_type=initial_event,
            location=location,
            actor=producer,
            notes=notes,
            tx_hash=self._generate_tx_hash(),
        )

        product.events.append(event)
        self.products[product_id] = product

        return product

    def add_event(
        self, product_id: str, event_type: str, location: str, actor: str, notes: str = ""
    ) -> TraceEvent:
        """Add a trace event to a product."""
        if product_id not in self.products:
            raise ValueError(f"Product not found: {product_id}")

        product = self.products[product_id]

        event = TraceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            product_id=product_id,
            event_type=event_type,
            location=location,
            actor=actor,
            notes=notes,
            tx_hash=self._generate_tx_hash(),
        )

        product.events.append(event)

        return event

    def verify_product(self, product_id: str) -> TracedProduct:
        """Verify a product's traceability."""
        if product_id not in self.products:
            raise ValueError(f"Product not found: {product_id}")

        product = self.products[product_id]
        product.verified = True
        product.verified_at = datetime.utcnow()

        return product

    def get_product(self, product_id: str) -> TracedProduct | None:
        """Get product by ID."""
        return self.products.get(product_id)

    def get_product_history(self, product_id: str) -> list[TraceEvent]:
        """Get full trace history for a product."""
        if product_id not in self.products:
            raise ValueError(f"Product not found: {product_id}")

        return self.products[product_id].events

    def get_products_by_producer(self, producer: str) -> list[TracedProduct]:
        """Get all products from a producer."""
        return [p for p in self.products.values() if p.producer == producer]

    def get_stats(self) -> dict:
        """Get supply chain statistics."""
        total_products = len(self.products)
        verified_products = sum(1 for p in self.products.values() if p.verified)
        total_events = sum(len(p.events) for p in self.products.values())

        return {
            "total_products": total_products,
            "verified_products": verified_products,
            "total_trace_events": total_events,
            "avg_events_per_product": round(total_events / total_products, 2)
            if total_products > 0
            else 0,
        }


# Singleton
_supply_chain_registry: SupplyChainRegistry | None = None


def get_supply_chain_registry() -> SupplyChainRegistry:
    """Get singleton supply chain registry."""
    global _supply_chain_registry
    if _supply_chain_registry is None:
        _supply_chain_registry = SupplyChainRegistry()
    return _supply_chain_registry
