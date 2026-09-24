"""Fetch NASA POWER daily data.

Usage:
    python scripts/fetch_nasa_power.py --lat 35.6892 --lon 51.3890 \
        --start 2024-01-01 --end 2024-12-31 \
        --parameters T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN \
        --out data/raw/nasa_power.json

Provenance: source_url, query params, and fetched_at recorded in manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from engine.hydroma.data_pipeline.pipeline import NASA_POWER_Connector


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch NASA POWER data")
    ap.add_argument("--lat", type=float, required=True, help="Latitude")
    ap.add_argument("--lon", type=float, required=True, help="Longitude")
    ap.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    ap.add_argument(
        "--parameters",
        default="T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
        help="Comma-separated parameter codes",
    )
    ap.add_argument("--out", default="data/raw/nasa_power.json", help="Output JSON path")
    ap.add_argument("--cache-dir", default="data/cache/nasa_power", help="Cache directory")
    args = ap.parse_args()

    params = [p.strip() for p in args.parameters.split(",") if p.strip()]

    connector = NASA_POWER_Connector(cache_dir=Path(args.cache_dir))
    assets = connector.fetch(
        {
            "lat": args.lat,
            "lon": args.lon,
            "start_date": args.start,
            "end_date": args.end,
            "parameters": params,
        }
    )

    if not assets:
        print("ERROR: No data fetched", file=sys.stderr)
        return 1

    asset = assets[0]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "asset_id": asset.asset_id,
        "source_id": asset.source_id,
        "name": asset.name,
        "file_path": str(asset.file_path),
        "format": asset.format,
        "size_bytes": asset.size_bytes,
        "checksum": asset.checksum,
        "metadata": {},
        "provenance": asset.provenance,
        "created_at": asset.created_at,
        "fetched_by": "scripts/fetch_nasa_power.py",
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"OK: wrote {out_path} ({asset.size_bytes} bytes, checksum={asset.checksum[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
