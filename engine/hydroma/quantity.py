from dataclasses import dataclass


@dataclass
class Quantity:
    """Stub for engine.hydroma.quantity.Quantity."""

    value: float
    unit: str = "unit"
    uncertainty: float | None = None
