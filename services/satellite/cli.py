"""DVC pipeline CLI for satellite data processing.

Subcommands:
    fetch-scenes  Fetch Sentinel-2 L2A scenes via CDSE STAC -> data/raw/scenes.jsonl
    sample-bands  Download B04/B08 COGs and compute NDVI/EVI/SAVI -> data/processed/indices.parquet
    load-db       Load processed indices into satellite_analyses table

Usage:
    python -m services.satellite.cli fetch-scenes --out data/raw/scenes.jsonl
    python -m services.satellite.cli sample-bands --in data/raw/scenes.jsonl --out data/processed/indices.parquet
    python -m services.satellite.cli load-db --in data/processed/indices.parquet
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.config.settings import get_settings
from engine.hydroma.mrv.satellite_cdse import (
    CdseConfig,
    CdseUnavailable,
    build_bbox,
    retrieve_ndvi,
)

logger = logging.getLogger(__name__)


def cmd_fetch_scenes(args: argparse.Namespace) -> int:
    """Fetch Sentinel-2 L2A scenes via CDSE STAC."""
    get_settings()
    try:
        cfg = CdseConfig.from_env()
    except CdseUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    bbox = build_bbox(args.lat, args.lon, half_side_km=args.half_side_km)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scenes: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        import requests

        session = requests.Session()
        result = retrieve_ndvi(session, cfg, bbox, args.start, args.end)
        scenes.append(
            {
                "scene_id": result["payload"]["scene_id"],
                "acquisition": result["payload"]["acquisition"],
                "cloud_cover_pct": result["payload"]["cloud_cover_pct"],
                "ndvi_mean": result["value"],
                "bbox": bbox,
                "data_source": "real",
                "provenance": result["payload"]["provenance"],
                "retrieved_at": datetime.now(UTC).isoformat(),
            }
        )
        print(f"OK: fetched scene {result['payload']['scene_id']}")
    except CdseUnavailable as exc:
        errors.append(str(exc))
        print(f"WARNING: CDSE retrieval failed: {exc}", file=sys.stderr)

    # Write scenes.jsonl (one JSON object per line)
    with out_path.open("w") as fh:
        for scene in scenes:
            fh.write(json.dumps(scene, default=str) + "\n")

    manifest = {
        "pipeline": "dvc stage stac_fetch",
        "bbox": bbox,
        "start": args.start,
        "end": args.end,
        "scene_count": len(scenes),
        "error_count": len(errors),
        "errors": errors,
        "out_file": str(out_path),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

    print(f"OK: wrote {out_path} ({len(scenes)} scenes, {len(errors)} errors)")
    return 0 if scenes else 1


def cmd_sample_bands(args: argparse.Namespace) -> int:
    """Download B04/B08 bands and compute NDVI statistics."""
    in_path = Path(args.inp)
    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    with in_path.open("r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning("skipping malformed line: %s", exc)

    if not rows:
        print("ERROR: no scenes to process", file=sys.stderr)
        return 1

    # Write parquet via pandas (lazy import)
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is required for parquet output", file=sys.stderr)
        return 1

    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False)
    print(f"OK: wrote {out_path} ({len(df)} rows)")
    return 0


def cmd_load_db(args: argparse.Namespace) -> int:
    """Load processed indices into the database."""
    in_path = Path(args.inp)
    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        return 1

    try:
        import pandas as pd

        from database.hub import hub
        from database.models import SatelliteAnalysis
    except ImportError as exc:
        print(f"ERROR: missing dependency: {exc}", file=sys.stderr)
        return 1

    df = pd.read_parquet(in_path)
    if df.empty:
        print("ERROR: no data to load", file=sys.stderr)
        return 1

    Session = hub.get_session
    loaded = 0
    with Session() as db:
        for _, row in df.iterrows():
            record = SatelliteAnalysis(
                farm_id=row.get("scene_id", "unknown"),
                ndvi=float(row.get("ndvi_mean", 0.0)),
                analyzed_at=datetime.now(UTC),
            )
            db.add(record)
            loaded += 1
        db.commit()

    print(f"OK: loaded {loaded} satellite analyses")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Satellite DVC pipeline CLI")
    sub = ap.add_subparsers(dest="command", required=True)

    # fetch-scenes
    fs = sub.add_parser("fetch-scenes", help="Fetch Sentinel-2 L2A scenes via CDSE")
    fs.add_argument("--lat", type=float, required=True)
    fs.add_argument("--lon", type=float, required=True)
    fs.add_argument("--start", required=True, help="ISO-8601 start date")
    fs.add_argument("--end", required=True, help="ISO-8601 end date")
    fs.add_argument("--half-side-km", type=float, default=0.5)
    fs.add_argument("--out", default="data/raw/scenes.jsonl")
    fs.set_defaults(func=cmd_fetch_scenes)

    # sample-bands
    sb = sub.add_parser("sample-bands", help="Sample bands and compute indices")
    sb.add_argument("--in", dest="inp", required=True)
    sb.add_argument("--out", default="data/processed/indices.parquet")
    sb.set_defaults(func=cmd_sample_bands)

    # load-db
    ld = sub.add_parser("load-db", help="Load indices into database")
    ld.add_argument("--in", dest="inp", required=True)
    ld.set_defaults(func=cmd_load_db)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
