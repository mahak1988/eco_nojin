"""Fetch STAC items from a STAC API endpoint.

Usage:
    python scripts/fetch_stac.py --catalog https://planetarycomputer.microsoft.com/api/stac/v1 \
        --collections sentinel-2-l2a \
        --bbox 35.5,51.0,36.0,51.5 \
        --datetime 2024-01-01/2024-12-31 \
        --limit 10 \
        --out data/raw/stac_items.json

Supports: Planetary Computer, AWS Earth Search, CDSE, any STAC 1.0 API.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from engine.hydroma.data_pipeline.pipeline import STACConnector


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch STAC items")
    ap.add_argument("--catalog", required=True, help="STAC API base URL")
    ap.add_argument("--source-id", default="stac_custom", help="Source identifier")
    ap.add_argument("--name", default="STAC Catalog", help="Human-readable name")
    ap.add_argument(
        "--collections", default="sentinel-2-l2a", help="Comma-separated collection IDs"
    )
    ap.add_argument("--bbox", required=True, help="minx,miny,maxx,maxy")
    ap.add_argument(
        "--datetime", required=True, help="ISO-8601 datetime range, e.g. 2024-01-01/2024-12-31"
    )
    ap.add_argument("--limit", type=int, default=10, help="Max items to fetch")
    ap.add_argument("--out", default="data/raw/stac_items.json", help="Output JSON path")
    ap.add_argument("--cache-dir", default="data/cache/stac", help="Cache directory")
    args = ap.parse_args()

    bbox = [float(x) for x in args.bbox.split(",")]
    if len(bbox) != 4:
        print("ERROR: --bbox must be minx,miny,maxx,maxy", file=sys.stderr)
        return 1

    collections = [c.strip() for c in args.collections.split(",") if c.strip()]

    connector = STACConnector(
        catalog_url=args.catalog,
        source_id=args.source_id,
        name=args.name,
        cache_dir=Path(args.cache_dir),
    )
    assets = connector.fetch(
        {
            "bbox": bbox,
            "datetime": args.datetime,
            "collections": collections,
            "limit": args.limit,
        }
    )

    if not assets:
        print("ERROR: No STAC items fetched", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source_id": args.source_id,
        "name": args.name,
        "catalog_url": args.catalog,
        "collections": collections,
        "bbox": bbox,
        "datetime_range": args.datetime,
        "asset_count": len(assets),
        "assets": [
            {
                "asset_id": a.asset_id,
                "name": a.name,
                "file_path": str(a.file_path),
                "format": a.format,
                "size_bytes": a.size_bytes,
                "checksum": a.checksum,
                "provenance": a.provenance,
            }
            for a in assets
        ],
        "fetched_by": "scripts/fetch_stac.py",
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"OK: wrote {out_path} ({len(assets)} STAC items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
