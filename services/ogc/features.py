"""OGC API — Features (Part 1: Core) implementation.

Free and open standard (OGC 17-069r3). Serves the platform's landscape
points as GeoJSON through the standard resource tree:
  /ogc/features/v1/                      landing page
  /ogc/features/v1/conformance           conformance classes
  /ogc/features/v1/collections           collection list
  /ogc/features/v1/collections/{id}/items  features (GeoJSON)

Data source: live Supabase `geo_points` (public select policy added in
migration 0007). If Supabase env is missing the API honestly returns 503.
"""
import os
from typing import Any, Dict, List, Optional

import httpx

COLLECTION_ID = "landscape-points"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cpncggavcfplewlhvvnw.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_LANDING = {
    "title": "Eco Nojin — OGC API Features",
    "description": "نقاط منظره و پروژه‌های احیای زمین (داده واقعی، استاندارد باز OGC).",
    "links": [
        {"href": "/ogc/features/v1/", "rel": "self", "type": "application/json", "title": "Landing page"},
        {"href": "/ogc/features/v1/conformance", "rel": "conformance", "type": "application/json"},
        {"href": "/ogc/features/v1/collections", "rel": "data", "type": "application/json"},
    ],
}

_CONFORMANCE = {
    "conformsTo": [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    ]
}

_COLLECTIONS = {
    "collections": [
        {
            "id": COLLECTION_ID,
            "title": "Landscape points (نقاط منظره)",
            "description": "نقاط واقعی بازدید/احیای زمین با مختصات.",
            "extent": {"spatial": {"bbox": [[-180, -90, 180, 90]]}},
            "itemType": "feature",
            "crs": ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"],
            "links": [
                {"href": f"/ogc/features/v1/collections/{COLLECTION_ID}/items", "rel": "items", "type": "application/geo+json"},
            ],
        }
    ]
}


def _items_from_supabase(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch real landscape points from Supabase (anon, public read via
    the ogc_landscape_points view created in migration 0007)."""
    url = f"{SUPABASE_URL}/rest/v1/ogc_landscape_points?select=id,name,lon,lat&limit={limit}"
    resp = httpx.get(url, headers={"apikey": SUPABASE_ANON_KEY}, timeout=8)
    resp.raise_for_status()
    features = []
    for row in resp.json():
        features.append({
            "type": "Feature",
            "id": row.get("id"),
            "geometry": {"type": "Point", "coordinates": [row.get("lon"), row.get("lat")]},
            "properties": {"name": row.get("name")},
        })
    return features


def items(limit: int = 100, bbox: Optional[str] = None) -> Dict[str, Any]:
    """GeoJSON FeatureCollection. 503 with honest detail when DB unreachable."""
    try:
        features = _items_from_supabase(limit)
    except Exception as exc:
        return {
            "type": "FeatureCollection",
            "status": "error",
            "code": "NoApplicableCode",
            "detail": f"supabase unreachable: {exc}",
        }
    if bbox:
        try:
            b = [float(x) for x in bbox.split(",")]
            if len(b) == 4:
                features = [f for f in features if b[0] <= f["geometry"]["coordinates"][0] <= b[2] and b[1] <= f["geometry"]["coordinates"][1] <= b[3]]
        except ValueError:
            pass
    return {"type": "FeatureCollection", "features": features}
