"""Fetch Sentinel-2 NDVI via Copernicus Data Space Ecosystem (CDSE).

Usage:
    python scripts/fetch_cdse.py --lat 35.6892 --lon 51.3890 \
        --start 2024-07-01 --end 2024-08-01 \
        --half-side-km 0.5 \
        --out data/raw/cdse_ndvi.json

Requires env vars: CDSE_BASE_URL, CDSE_IDENTITY_URL, CDSE_CLIENT_ID, CDSE_CLIENT_SECRET
Provenance: scene_id, acquisition, cloud_cover_pct, ndvi stats, and provenance string.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from engine.hydroma.mrv.satellite_cdse import (
    CdseConfig,
    CdseUnavailable,
    build_bbox,
    retrieve_ndvi,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch Sentinel-2 NDVI via CDSE")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--start", required=True, help="ISO-8601 start date")
    ap.add_argument("--end", required=True, help="ISO-8601 end date")
    ap.add_argument("--half-side-km", type=float, default=0.5)
    ap.add_argument("--out", default="data/raw/cdse_ndvi.json")
    args = ap.parse_args()

    try:
        cfg = CdseConfig.from_env()
    except CdseUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    bbox = build_bbox(args.lat, args.lon, half_side_km=args.half_side_km)

    try:
        import requests

        session = requests.Session()
        result = retrieve_ndvi(session, cfg, bbox, args.start, args.end)
    except CdseUnavailable as exc:
        print(f"ERROR: CDSE retrieval failed: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "index": result["index"],
        "value": result["value"],
        "ts": result["ts"],
        "data_source": result["data_source"],
        "payload": result["payload"],
        "bbox": bbox,
        "lat": args.lat,
        "lon": args.lon,
        "fetched_by": "scripts/fetch_cdse.py",
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(
        f"OK: wrote {out_path} (NDVI={result['value']:.4f}, scene={result['payload']['scene_id']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
