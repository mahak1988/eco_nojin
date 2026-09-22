"""Fetch SoilGrids soil property data from ISRIC.

Usage:
    python scripts/fetch_soilgrids.py --bbox 35.5,51.0,36.0,51.5 \
        --properties bdod,clay,soc \
        --depths 0-5cm,5-15cm,15-30cm \
        --out data/raw/soilgrids.json

Provenance: source_url, query params, and fetched_at recorded per property/depth.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from engine.hydroma.data_pipeline.pipeline import SoilGridsConnector


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch SoilGrids soil data")
    ap.add_argument("--bbox", required=True, help="minx,miny,maxx,maxy")
    ap.add_argument(
        "--properties",
        default="bdod,cec,clay,sand,silt,phh2o,soc,nitrogen",
        help="Comma-separated soil properties",
    )
    ap.add_argument(
        "--depths",
        default="0-5cm,5-15cm,15-30cm,30-60cm,60-100cm,100-200cm",
        help="Comma-separated depth intervals",
    )
    ap.add_argument("--out", default="data/raw/soilgrids.json", help="Output JSON path")
    ap.add_argument("--cache-dir", default="data/cache/soilgrids", help="Cache directory")
    args = ap.parse_args()

    bbox = [float(x) for x in args.bbox.split(",")]
    if len(bbox) != 4:
        print("ERROR: --bbox must be minx,miny,maxx,maxy", file=sys.stderr)
        return 1

    properties = [p.strip() for p in args.properties.split(",") if p.strip()]
    depths = [d.strip() for d in args.depths.split(",") if d.strip()]

    connector = SoilGridsConnector(cache_dir=Path(args.cache_dir))
    assets = connector.fetch(
        {
            "bbox": bbox,
            "properties": properties,
            "depths": depths,
        }
    )

    if not assets:
        print("ERROR: No data fetched", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source_id": "soilgrids",
        "name": "ISRIC SoilGrids v2.0",
        "bbox": bbox,
        "properties": properties,
        "depths": depths,
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
        "fetched_by": "scripts/fetch_soilgrids.py",
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"OK: wrote {out_path} ({len(assets)} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())