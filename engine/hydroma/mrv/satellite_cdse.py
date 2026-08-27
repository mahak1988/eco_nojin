"""Copernicus Data Space Ecosystem (CDSE) Sentinel-2 L2A client (MRV level 1).

Fetches a real NDVI (B04/B08, 10 m) through the CDSE STAC catalogue and
computes the index locally with rasterio. Provenance discipline: a result
carries ``data_source="real"`` only when an actual scene was retrieved;
every failure raises :class:`CdseUnavailable` so the caller chooses the
fallback explicitly (never a silent downgrade to simulated data).

Temporary band files live inside a ``tempfile.TemporaryDirectory`` whose
cleanup is handled by the standard library (no manual file removal here).

Environment keys (see .env):
    CDSE_BASE_URL       STAC catalogue root, e.g. https://catalogue.dataspace.copernicus.eu
    CDSE_IDENTITY_URL   OAuth2 identity root, e.g. https://identity.dataspace.copernicus.eu
    CDSE_CLIENT_ID      OAuth2 client id
    CDSE_CLIENT_SECRET  OAuth2 client secret
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any

import numpy as np
import rasterio
import requests

# Sentinel-2 L2A asset keys in the CDSE STAC catalogue (10 m bands).
ASSET_RED = "B04"
ASSET_NIR = "B08"


class CdseUnavailable(RuntimeError):
    """Raised when a real CDSE retrieval cannot be completed."""


@dataclass(frozen=True)
class CdseConfig:
    """Connection settings for the CDSE STAC + identity endpoints."""

    base_url: str
    identity_url: str
    client_id: str
    client_secret: str
    max_cloud_cover: float = 20.0
    limit: int = 5
    timeout: tuple[float, float] = (10.0, 60.0)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> CdseConfig:
        """Build config from the environment; missing keys raise CdseUnavailable."""
        env = env if env is not None else os.environ
        missing = [
            key
            for key in ("CDSE_BASE_URL", "CDSE_IDENTITY_URL", "CDSE_CLIENT_ID", "CDSE_CLIENT_SECRET")
            if not env.get(key)
        ]
        if missing:
            raise CdseUnavailable(f"CDSE credentials missing in environment: {', '.join(missing)}")
        return cls(
            base_url=env["CDSE_BASE_URL"].rstrip("/"),
            identity_url=env["CDSE_IDENTITY_URL"].rstrip("/"),
            client_id=env["CDSE_CLIENT_ID"],
            client_secret=env["CDSE_CLIENT_SECRET"],
        )


def get_token(session: requests.Session, cfg: CdseConfig) -> str:
    """Request an OAuth2 access token (client credentials grant)."""
    resp = session.post(
        f"{cfg.identity_url}/auth/realms/cdse/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
        },
        timeout=cfg.timeout,
    )
    if resp.status_code != 200:
        raise CdseUnavailable(f"CDSE token request failed: HTTP {resp.status_code}")
    token = resp.json().get("access_token")
    if not token:
        raise CdseUnavailable("CDSE token response missing access_token")
    return token


def search_l2a(
    session: requests.Session,
    cfg: CdseConfig,
    token: str,
    bbox: list[float],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    """Search Sentinel-2 L2A scenes; return newest scenes under the cloud cap."""
    body = {
        "collections": ["SENTINEL-2"],
        "datetime": f"{start}/{end}",
        "bbox": bbox,
        "limit": cfg.limit,
        "query": {"eo:cloud_cover": {"lt": cfg.max_cloud_cover}},
    }
    resp = session.post(
        f"{cfg.base_url}/api/stac/search",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=cfg.timeout,
    )
    if resp.status_code != 200:
        raise CdseUnavailable(f"CDSE STAC search failed: HTTP {resp.status_code}")
    features = resp.json().get("features", [])
    scenes: list[dict[str, Any]] = []
    for feat in features:
        assets = feat.get("assets", {})
        if ASSET_RED in assets and ASSET_NIR in assets:
            scenes.append(
                {
                    "scene_id": feat.get("id"),
                    "acquisition": feat.get("properties", {}).get("datetime"),
                    "cloud_cover": feat.get("properties", {}).get("eo:cloud_cover"),
                    "b04_url": assets[ASSET_RED].get("href"),
                    "b08_url": assets[ASSET_NIR].get("href"),
                }
            )
    return scenes


def compute_ndvi(b04_path: str, b08_path: str) -> dict[str, float]:
    """Compute NDVI statistics from the two 10 m band GeoTIFFs.

    Returns mean/median/min/max NDVI plus the share of valid pixels.
    Raises CdseUnavailable when the scene has no valid pixels.
    """
    with rasterio.open(b04_path) as ds_red, rasterio.open(b08_path) as ds_nir:
        red = ds_red.read(1).astype("float64")
        nir = ds_nir.read(1).astype("float64")
        mask = np.isfinite(red) & np.isfinite(nir)
        for arr, ds in ((red, ds_red), (nir, ds_nir)):
            nodata = ds.nodata
            if nodata is not None:
                mask &= arr != nodata
        total = mask.size
        red, nir = red[mask], nir[mask]

    denom = red + nir
    valid = denom != 0
    ndvi = np.where(valid, (nir - red) / np.where(valid, denom, 1.0), np.nan)
    ndvi = ndvi[np.isfinite(ndvi)]
    if ndvi.size == 0:
        raise CdseUnavailable("Sentinel-2 scene has no valid NDVI pixels")
    return {
        "ndvi_mean": float(np.mean(ndvi)),
        "ndvi_median": float(np.median(ndvi)),
        "ndvi_min": float(np.min(ndvi)),
        "ndvi_max": float(np.max(ndvi)),
        "pct_valid_pixels": round(100.0 * ndvi.size / total, 2),
    }


def _download(session: requests.Session, url: str, dest: str, cfg: CdseConfig) -> None:
    """Stream a CDSE asset into dest; raises CdseUnavailable on failure."""
    with session.get(url, stream=True, timeout=cfg.timeout) as resp:
        if resp.status_code != 200:
            raise CdseUnavailable(f"CDSE asset download failed: HTTP {resp.status_code}")
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                if chunk:
                    fh.write(chunk)


def build_bbox(lat: float, lon: float, half_side_km: float = 0.5) -> list[float]:
    """Build a [west, south, east, north] bbox around a site (default ~1 km)."""
    d_lat = half_side_km / 111.32
    d_lon = half_side_km / (111.32 * max(np.cos(np.radians(lat)), 0.01))
    return [lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat]


def retrieve_ndvi(
    session: requests.Session,
    cfg: CdseConfig,
    bbox: list[float],
    start: str,
    end: str,
) -> dict[str, Any]:
    """Full pipeline: token -> search -> download bands -> NDVI statistics.

    Band files are written inside a standard-library TemporaryDirectory
    (cleanup is automatic). Returns a dict ready to be stored as an MRV
    satellite observation with ``data_source="real"``. Raises
    CdseUnavailable on any failure.
    """
    token = get_token(session, cfg)
    scenes = search_l2a(session, cfg, token, bbox, start, end)
    if not scenes:
        raise CdseUnavailable("No Sentinel-2 L2A scene found for the site/time window")
    scene = scenes[0]
    with tempfile.TemporaryDirectory(prefix="cdse_") as tmp_dir:
        b04 = os.path.join(tmp_dir, "B04.tif")
        b08 = os.path.join(tmp_dir, "B08.tif")
        _download(session, scene["b04_url"], b04, cfg)
        _download(session, scene["b08_url"], b08, cfg)
        stats = compute_ndvi(b04, b08)
    return {
        "index": "NDVI",
        "value": stats["ndvi_mean"],
        "ts": scene["acquisition"],
        "data_source": "real",
        "payload": {
            "scene_id": scene["scene_id"],
            "cloud_cover_pct": scene["cloud_cover"],
            "acquisition": scene["acquisition"],
            "provenance": "CDSE Sentinel-2 L2A (10 m)",
            **{key: value for key, value in stats.items() if key != "ndvi_mean"},
        },
    }
