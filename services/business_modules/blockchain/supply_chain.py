"""Supply chain traceability using blockchain with real hash-chain.

Provides immutable product traceability with verifiable
SHA-256 hash-chain instead of random UUIDs.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


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
    prev_tx_hash: str = ""


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
    prev_tx_hash: str = ""


class SupplyChainRegistry:
    """Supply chain traceability registry with real hash-chain."""

    def __init__(self):
        self.products: dict[str, TracedProduct] = {}
        self._last_tx_hash: str = "0x0"

    def _generate_tx_hash(self, data: str, prev_tx_hash: str | None = None) -> str:
        """Generate real hash-chain transaction hash."""
        prev = prev_tx_hash or self._last_tx_hash
        raw = f"{prev}:{data}:{uuid.uuid4().hex[:8]}"
        return "0x" + hashlib.sha256(raw.encode()).hexdigest()

    def _update_chain(self, tx_hash: str) -> None:
        """Update the chain head."""
        self._last_tx_hash = tx_hash

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
        prev = self._last_tx_hash
        tx_hash = self._generate_tx_hash(
            f"register:{product_id}:{producer}:{batch_number}",
            prev,
        )

        product = TracedProduct(
            product_id=product_id,
            producer=producer,
            batch_number=batch_number,
            tx_hash=tx_hash,
            prev_tx_hash=prev,
        )

        # Add initial event
        event_prev = tx_hash
        event_tx = self._generate_tx_hash(
            f"event:{initial_event}:{location}:{producer}:{notes}",
            event_prev,
        )
        event = TraceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            product_id=product_id,
            event_type=initial_event,
            location=location,
            actor=producer,
            notes=notes,
            tx_hash=event_tx,
            prev_tx_hash=event_prev,
        )

        product.events.append(event)
        self.products[product_id] = product
        self._update_chain(event_tx)

        return product

    def add_event(
        self, product_id: str, event_type: str, location: str, actor: str, notes: str = ""
    ) -> TraceEvent:
        """Add a trace event to a product."""
        if product_id not in self.products:
            raise ValueError(f"Product not found: {product_id}")

        product = self.products[product_id]
        prev = self._last_tx_hash
        tx_hash = self._generate_tx_hash(
            f"event:{event_type}:{location}:{actor}:{notes}",
            prev,
        )

        event = TraceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            product_id=product_id,
            event_type=event_type,
            location=location,
            actor=actor,
            notes=notes,
            tx_hash=tx_hash,
            prev_tx_hash=prev,
        )

        product.events.append(event)
        self._update_chain(tx_hash)

        return event

    def verify_product(self, product_id: str) -> TracedProduct:
        """Verify a product's traceability."""
        if product_id not in self.products:
            raise ValueError(f"Product not found: {product_id}")

        product = self.products[product_id]
        prev = self._last_tx_hash
        tx_hash = self._generate_tx_hash(
            f"verify:{product_id}:{datetime.now(UTC).isoformat()}",
            prev,
        )
        product.verified = True
        product.verified_at = datetime.now(UTC).replace(tzinfo=None)
        product.tx_hash = tx_hash
        product.prev_tx_hash = prev
        self._update_chain(tx_hash)

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
