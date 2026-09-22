"""Persistent data provenance tracking for the Eco Nojin pipeline.

Records every fetch/transform/load event with:
- source identity (who provided the data)
- temporal coverage (when the data was collected)
- spatial coverage (where)
- processing chain (what transformations were applied)
- quality flags (how good is the data)
- lineage (where did this data come from, what was used to produce it)

Storage: JSON Lines in data/provenance/provenance.jsonl
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Default provenance store location
DEFAULT_STORE_PATH = Path("data/provenance/provenance.jsonl")


@dataclass
class ProvenanceRecord:
    """A single provenance event in the data lineage."""

    record_id: str
    event_type: str  # fetch | transform | load | validate | derive
    asset_id: str
    source_id: str
    source_url: str
    captured_at: str
    temporal_start: Optional[str] = None
    temporal_end: Optional[str] = None
    spatial_bbox: Optional[list[float]] = None
    processing_steps: list[str] = field(default_factory=list)
    quality_status: str = "unknown"  # ok | suspect | rejected | unknown
    quality_score: Optional[float] = None  # 0.0 to 1.0
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    format: Optional[str] = None
    data_mode: str = "real"  # real | simulated | modelled_estimate
    lineage: list[str] = field(default_factory=list)  # parent record_ids
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ProvenanceTracker:
    """Append-only JSONL provenance store.

    Every record is immutable once written. The store supports:
    - Recording new events
    - Querying by asset, source, time range, quality
    - Building lineage graphs
    """

    def __init__(self, store_path: Path = DEFAULT_STORE_PATH):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("")

    def record(self, record: ProvenanceRecord) -> str:
        """Append a provenance record. Returns the record_id."""
        line = record.to_json() + "\n"
        with self.store_path.open("a") as fh:
            fh.write(line)
        logger.debug("provenance recorded: %s (%s)", record.record_id, record.event_type)
        return record.record_id

    def record_fetch(
        self,
        asset_id: str,
        source_id: str,
        source_url: str,
        **kwargs: Any,
    ) -> str:
        """Convenience: record a fetch event."""
        record = ProvenanceRecord(
            record_id=f"prov-{uuid4().hex[:12]}",
            event_type="fetch",
            asset_id=asset_id,
            source_id=source_id,
            source_url=source_url,
            captured_at=datetime.now(UTC).isoformat(),
            **kwargs,
        )
        return self.record(record)

    def record_transform(
        self,
        asset_id: str,
        source_id: str,
        processing_steps: list[str],
        parent_ids: list[str],
        **kwargs: Any,
    ) -> str:
        """Convenience: record a transform event."""
        record = ProvenanceRecord(
            record_id=f"prov-{uuid4().hex[:12]}",
            event_type="transform",
            asset_id=asset_id,
            source_id=source_id,
            source_url=kwargs.pop("source_url", ""),
            captured_at=datetime.now(UTC).isoformat(),
            processing_steps=processing_steps,
            lineage=parent_ids,
            **kwargs,
        )
        return self.record(record)

    def query(
        self,
        asset_id: Optional[str] = None,
        source_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[ProvenanceRecord]:
        """Query provenance records with optional filters."""
        results: list[ProvenanceRecord] = []
        if not self.store_path.exists():
            return results

        with self.store_path.open("r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if asset_id and data.get("asset_id") != asset_id:
                    continue
                if source_id and data.get("source_id") != source_id:
                    continue
                if event_type and data.get("event_type") != event_type:
                    continue
                results.append(ProvenanceRecord(**data))
                if len(results) >= limit:
                    break

        return results

    def get_lineage(self, asset_id: str) -> list[ProvenanceRecord]:
        """Build the full lineage chain for an asset (recursive)."""
        visited: set[str] = set()
        chain: list[ProvenanceRecord] = []

        def _walk(id_: str) -> None:
            if id_ in visited:
                return
            visited.add(id_)
            for record in self.query(asset_id=id_):
                chain.append(record)
                for parent_id in record.lineage:
                    _walk(parent_id)

        _walk(asset_id)
        return chain

    def count(self) -> int:
        """Total number of records in the store."""
        if not self.store_path.exists():
            return 0
        count = 0
        with self.store_path.open("r") as fh:
            for line in fh:
                if line.strip():
                    count += 1
        return count


# Global tracker instance
_tracker: Optional[ProvenanceTracker] = None


def get_tracker(store_path: Path = DEFAULT_STORE_PATH) -> ProvenanceTracker:
    """Get the global provenance tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker(store_path)
    return _tracker


def reset_tracker() -> None:
    """Reset the global tracker (for testing)."""
    global _tracker
    _tracker = None