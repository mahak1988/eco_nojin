"""Fetch ERA5 reanalysis data from Open-Meteo API.

Usage:
    python scripts/fetch_open_meteo.py --bbox 35.5,51.0,36.0,51.5 \
        --start 2024-01-01 --end 2024-12-31 \
        --variables temperature_2m,precipitation \
        --out data/raw/open_meteo_era5.json

Provenance: every record carries source_url, query_params, and fetched_at.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from engine.hydroma.data_pipeline.pipeline import OpenMeteoConnector


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch ERA5 data from Open-Meteo")
    ap.add_argument("--bbox", required=True, help="minx,miny,maxx,maxy")
    ap.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    ap.add_argument(
        "--variables",
        default="temperature_2m,precipitation",
        help="Comma-separated variable names",
    )
    ap.add_argument("--out", default="data/raw/open_meteo_era5.json", help="Output JSON path")
    ap.add_argument("--cache-dir", default="data/cache/open_meteo", help="Cache directory")
    args = ap.parse_args()

    bbox = [float(x) for x in args.bbox.split(",")]
    if len(bbox) != 4:
        print("ERROR: --bbox must be minx,miny,maxx,maxy", file=sys.stderr)
        return 1

    variables = [v.strip() for v in args.variables.split(",") if v.strip()]

    connector = OpenMeteoConnector(cache_dir=Path(args.cache_dir))
    assets = connector.fetch(
        {
            "bbox": bbox,
            "start_date": args.start,
            "end_date": args.end,
            "variables": variables,
        }
    )

    if not assets:
        print("ERROR: No data fetched", file=sys.stderr)
        return 1

    asset = assets[0]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest with provenance
    manifest = {
        "asset_id": asset.asset_id,
        "source_id": asset.source_id,
        "name": asset.name,
        "file_path": str(asset.file_path),
        "format": asset.format,
        "size_bytes": asset.size_bytes,
        "checksum": asset.checksum,
        "metadata": asset.metadata,
        "provenance": asset.provenance,
        "created_at": asset.created_at,
        "fetched_by": "scripts/fetch_open_meteo.py",
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"OK: wrote {out_path} ({asset.size_bytes} bytes, checksum={asset.checksum[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
