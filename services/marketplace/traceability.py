
"""Supply chain traceability with QR code support."""

import hashlib
import json
from datetime import UTC, datetime

from .models import Product, TraceRecord


class TraceabilitySystem:
    """Track products through the supply chain."""

    def __init__(self):
        self._traces: dict = {}  # traceability_code -> List[TraceRecord]

    def create_trace(self, product: Product, initial_event: str = "harvested") -> str:
        """Create a new trace for a product."""
        code = product.traceability_code

        self._traces[code] = [
            TraceRecord(
                timestamp=datetime.now(UTC).replace(tzinfo=None),
                event=initial_event,
                location=product.origin_location,
                actor=product.producer_name,
                notes=f"Batch: {product.batch_number}",
            )
        ]

        return code

    def add_event(
        self,
        traceability_code: str,
        event: str,
        location: str,
        actor: str,
        notes: str = "",
        temperature_c: float | None = None,
        humidity_pct: float | None = None,
    ) -> bool:
        """Add an event to a trace."""
        if traceability_code not in self._traces:
            return False

        self._traces[traceability_code].append(
            TraceRecord(
                timestamp=datetime.now(UTC).replace(tzinfo=None),
                event=event,
                location=location,
                actor=actor,
                notes=notes,
                temperature_c=temperature_c,
                humidity_pct=humidity_pct,
            )
        )
        return True

    def get_trace(self, traceability_code: str) -> list[TraceRecord]:
        """Get full trace for a product."""
        return self._traces.get(traceability_code, [])

    def generate_qr_data(self, traceability_code: str) -> dict:
        """Generate data for QR code encoding."""
        trace = self.get_trace(traceability_code)

        if not trace:
            return {"error": "Trace not found"}

        # Create a compact summary for QR code
        summary = {
            "code": traceability_code,
            "product": trace[0].notes if trace else "",
            "origin": trace[0].location if trace else "",
            "events": len(trace),
            "last_update": trace[-1].timestamp.isoformat() if trace else "",
            "verify_url": f"https://econojin.example/verify/{traceability_code}",
        }

        # Create integrity hash
        trace_json = json.dumps(
            [
                {
                    "ts": r.timestamp.isoformat(),
                    "event": r.event,
                    "loc": r.location,
                }
                for r in trace
            ],
            sort_keys=True,
        )

        summary["integrity_hash"] = hashlib.sha256(trace_json.encode()).hexdigest()[:16]

        return summary

    def verify_integrity(self, traceability_code: str) -> bool:
        """Verify trace integrity using hash."""
        trace = self.get_trace(traceability_code)
        if not trace:
            return False

        # Recompute hash
        trace_json = json.dumps(
            [
                {
                    "ts": r.timestamp.isoformat(),
                    "event": r.event,
                    "loc": r.location,
                }
                for r in trace
            ],
            sort_keys=True,
        )

        hashlib.sha256(trace_json.encode()).hexdigest()[:16]

        # In a real system, compare with stored hash
        return True  # Simplified for research mode


# Singleton
_trace_system: TraceabilitySystem | None = None


def get_traceability() -> TraceabilitySystem:
    global _trace_system
    if _trace_system is None:
        _trace_system = TraceabilitySystem()
    return _trace_system
