"""ProvenanceStamp: attaches source/timestamp metadata to financial numbers in API responses.

Every financial number in API responses is wrapped with a ProvenanceStamp so consumers
can audit its origin and the moment it was computed, per the Scientific Engine
provenance requirements.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ProvenanceStamp(BaseModel):
    """Audit stamp attached to every financial value surfaced through the API.

    Fields (per AGENTS.md requirement: every financial number gets source/timestamp):
    - source:      system/service that produced the value
    - timestamp:   UTC moment the value was computed
    - method:      optional computation method (e.g. 'realtime', 'aggregated')
    """

    value: Decimal | float | int | str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    method: str | None = None

    def model_dump(self, **kwargs):  # type: ignore[override]
        data = super().model_dump(**kwargs)
        ts = data.get("timestamp")
        if isinstance(ts, datetime):
            data["timestamp"] = ts.isoformat()
        val = data.get("value")
        if isinstance(val, Decimal):
            data["value"] = str(val)
        return data


def stamp_value(
    value: Decimal | float | int | str,
    source: str,
    method: str | None = None,
    timestamp: datetime | None = None,
) -> ProvenanceStamp:
    """Wrap a financial value with a provenance stamp.

    Usage in financial API responses:
        amount = stamp_value(Decimal("150000"), source="ledger:balance", method="realtime")
        return {"amount": amount.model_dump()}
    """
    return ProvenanceStamp(
        value=value,
        source=source,
        timestamp=timestamp or datetime.now(UTC),
        method=method,
    )


def stamp_balance(
    amount: Decimal | float | int,
    account_id: str,
    method: str = "realtime",
) -> dict[str, Any]:
    """Convenience wrapper returning a JSON-serializable balance dict with stamp."""
    stamped = stamp_value(
        value=amount,
        source=f"ledger:{account_id}",
        method=method,
    )
    return stamped.model_dump()
