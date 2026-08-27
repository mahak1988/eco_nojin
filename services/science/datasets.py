"""
Dataset catalog (Phase 9 kickoff) — honest availability report.

Lists the platform's real data assets with their actual status:
- source, coverage, credentials required, live/offline flag.
No fake "available" claims: offline datasets are marked clearly.
"""
from __future__ import annotations

import os
from typing import Any


def dataset_catalog() -> dict[str, Any]:
    cds_configured = bool(os.environ.get("CDS_API_KEY"))
    cdse_configured = bool(
        os.environ.get("CDSE_CLIENT_ID") or os.environ.get("CDSE_USERNAME")
    )
    datasets: list[dict[str, Any]] = [
        {
            "id": "era5-cds",
            "name": "ERA5 Reanalysis (CDS)",
            "domain": "climate",
            "source": "Copernicus Climate Data Store",
            "status": "live" if cds_configured else "offline",
            "requires": "CDS_API_KEY + dataset licence",
            "license": "Copernicus licence (free)",
        },
        {
            "id": "sentinel2-cdse",
            "name": "Sentinel-2 L2A (CDSE)",
            "domain": "vegetation",
            "source": "Copernicus Data Space",
            "status": "live" if cdse_configured else "offline",
            "requires": "CDSE credentials",
            "license": "Copernicus licence (free)",
        },
        {
            "id": "nasa-power",
            "name": "NASA POWER meteorology",
            "domain": "climate",
            "source": "NASA POWER API",
            "status": "live",
            "requires": "none (free API)",
            "license": "NASA open data",
        },
        {
            "id": "open-meteo-era5",
            "name": "Open-Meteo ERA5 (ET0)",
            "domain": "water",
            "source": "Open-Meteo",
            "status": "live",
            "requires": "none (free API)",
            "license": "CC-BY 4.0",
        },
        {
            "id": "farms",
            "name": "Farm registry",
            "domain": "agriculture",
            "source": "platform database",
            "status": "live",
            "requires": "auth",
            "license": "platform",
        },
        {
            "id": "content-rag",
            "name": "Content corpus (RAG)",
            "domain": "knowledge",
            "source": "platform database",
            "status": "live",
            "requires": "auth",
            "license": "platform (CC-BY-NC)",
        },
    ]
    return {
        "count": len(datasets),
        "live": sum(1 for d in datasets if d["status"] == "live"),
        "datasets": datasets,
        "note": "وضعیت صادقانه؛ دیتاست‌های آفلاین فقط با اعتبارنامه فعال می‌شوند",
    }
