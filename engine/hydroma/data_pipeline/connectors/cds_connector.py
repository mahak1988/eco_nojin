"""Copernicus Data Space Ecosystem (CDSE) connector — Sentinel-1/2 imagery.

Source
------
* STAC catalogue (search, verified live): ``https://stac.dataspace.copernicus.eu/v1``
* OData catalogue (product resolution + asset download):
  ``https://catalogue.dataspace.copernicus.eu/odata/v1``
* Identity (OAuth2 client-credentials):
  ``https://identity.dataspace.copernicus.eu/auth/realms/cdse/protocol/openid-connect/token``

Credentials
-----------
``CDS_CLIENT_ID`` and ``CDS_CLIENT_SECRET`` (environment variables). Without
both, every method that needs a token raises ``ConnectorUnavailable`` naming
the missing variables — this connector never falls back to anonymous
downloads, because CDSE asset downloads require authentication and an
anonymous attempt would fail after a long download anyway.

What was verified against the live service (2026-10-10)
-------------------------------------------------------
* ``GET /v1`` returns the CDSE STAC catalog document.
* ``POST /v1/search`` returns Sentinel-2 L2A items; the ``datetime`` field
  must be RFC 3339 (``2021-01-01/2021-01-31`` is rejected with HTTP 400
  "invalid datetime separator, expected ``T``"), so date-only input is
  normalised here.
* Item assets carry ``s3://eodata/...`` hrefs; the product UUID is resolved
  anonymously through ``Products?$filter=startswith(Name,'<item id>')``,
  and ``Products(<id>)/$value`` answers HTTP 401 without a bearer token —
  the shape is right, authentication is genuinely required.
* The identity token endpoint answers HTTP 401 ``invalid_client`` without
  credentials, which is the expected failure mode.

Download of an individual file uses the documented OData node path::

    GET /odata/v1/Products(<id>)/Nodes('<dir>')/.../Nodes('<file>')/$value

built from the ``s3://eodata/<path>`` asset href, streamed to
``data/cache/cds/``.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource

logger = logging.getLogger(__name__)

#: STAC catalogue root (verified live).
STAC_CATALOG_URL = "https://stac.dataspace.copernicus.eu/v1"
#: Identity server issuing CDSE access tokens.
IDENTITY_URL = "https://identity.dataspace.copernicus.eu"
#: Classic OData catalogue (product lookup + asset download).
ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
#: Keycloak token path on the identity server.
_TOKEN_PATH = "/auth/realms/cdse/protocol/openid-connect/token"

#: Environment variables holding the OAuth2 client credentials.
CLIENT_ID_ENV = "CDS_CLIENT_ID"
CLIENT_SECRET_ENV = "CDS_CLIENT_SECRET"

#: Default asset key requested per item: Sentinel-2 L2A true-colour 10 m
#: composite — the smallest full-resolution raster band set that still
#: carries usable surface information.
DEFAULT_ASSET_KEY = "TCI_10m"

#: Magic bytes accepted by :meth:`CDSEConnector.validate`.
_JP2_MAGIC = b"\x00\x00\x00\x0cjP  \r\n\x87\n"
_TIFF_MAGICS = (b"II*\x00", b"MM\x00*")


class CDSEConnector(DataConnector):
    """Sentinel-1/2 imagery from the Copernicus Data Space Ecosystem.

    The connector searches the CDSE STAC catalogue, resolves each item's
    product UUID through the OData catalogue, and downloads one asset per
    item to the cache directory. It is registered in
    ``engine.hydroma.data_pipeline.pipeline`` under the source id
    ``cdse_sentinel`` — the generic metadata-only STAC connector already
    registered there as ``cdse`` is left in place and untouched.

    Args:
        cache_dir: Where downloaded assets are written.
        client_id: OAuth2 client id. Defaults to ``$CDS_CLIENT_ID``.
        client_secret: OAuth2 client secret. Defaults to ``$CDS_CLIENT_SECRET``.
        timeout: Per-request timeout in seconds (downloads use 5x).
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/cds"),
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="cdse_sentinel",
            name="Copernicus Data Space Ecosystem (Sentinel download)",
            description=(
                "Sentinel-1/2 imagery via the CDSE STAC catalogue and OData "
                "asset download. Requires CDS_CLIENT_ID / CDS_CLIENT_SECRET."
            ),
            base_url=STAC_CATALOG_URL,
            auth_type="oauth2",
            format="geotiff",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client_id = client_id
        self._client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries

    # ── credentials ──────────────────────────────────────────────

    def _credentials(self) -> tuple[str, str]:
        """Return ``(client_id, client_secret)`` or raise.

        Raises:
            ConnectorUnavailable: when either credential is missing. The
                message names both environment variables so the operator
                knows exactly what to set.
        """
        client_id = self._client_id or os.environ.get(CLIENT_ID_ENV, "")
        client_secret = self._client_secret or os.environ.get(CLIENT_SECRET_ENV, "")
        if not client_id or not client_secret:
            missing = []
            if not client_id:
                missing.append(CLIENT_ID_ENV)
            if not client_secret:
                missing.append(CLIENT_SECRET_ENV)
            raise ConnectorUnavailable(
                f"CDSE requires OAuth2 client credentials; missing "
                f"{', '.join(missing)}. Register an application at "
                f"https://shapps.dataspace.copernicus.eu/ and set the "
                f"environment variables {CLIENT_ID_ENV} and {CLIENT_SECRET_ENV}."
            )
        return client_id, client_secret

    # ── request plumbing ─────────────────────────────────────────

    def _retry(self, fn):
        """Wrap *fn* with the shared retry helper (network errors only)."""
        import requests

        from engine.resilience import with_retry

        return with_retry(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            exceptions=(requests.RequestException,),
        )(fn)

    def _token(self) -> str:
        """Fetch a CDSE access token via the client-credentials grant.

        Raises:
            ConnectorUnavailable: when credentials are missing, the identity
                server rejects them, or the token endpoint is unreachable.
        """
        client_id, client_secret = self._credentials()

        def _post() -> Any:
            import requests

            response = requests.post(
                f"{IDENTITY_URL}{_TOKEN_PATH}",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            payload: dict[str, Any] = self._retry(_post)()
        except Exception as exc:
            raise ConnectorUnavailable(
                f"CDSE token request failed ({type(exc).__name__}: {exc}). The "
                f"identity server {IDENTITY_URL} either rejected the "
                f"{CLIENT_ID_ENV}/{CLIENT_SECRET_ENV} credentials or was "
                f"unreachable from this host."
            ) from exc

        token = payload.get("access_token")
        if not token:
            raise ConnectorUnavailable(
                f"CDSE identity server returned no access_token (response keys: "
                f"{sorted(payload)})."
            )
        return str(token)

    # ── STAC search ──────────────────────────────────────────────

    @staticmethod
    def normalize_datetime(value: str) -> str:
        """Normalise a date range to the RFC 3339 form the CDSE API requires.

        ``"2021-01-01/2021-03-31"`` becomes
        ``"2021-01-01T00:00:00Z/2021-03-31T23:59:59Z"``; a single date
        becomes that day (00:00:00 to 23:59:59 UTC); values that already
        carry a ``T`` are passed through unchanged. The live API rejects
        date-only input with HTTP 400, so this normalisation is part of the
        contract, not cosmetics.
        """
        parts = value.split("/")
        if len(parts) == 1:
            parts = [parts[0], parts[0]]
        normalised = []
        for index, part in enumerate(parts):
            if part in ("", ".."):
                normalised.append(part)
            elif "T" in part:
                normalised.append(part)
            elif len(part) == 10:  # YYYY-MM-DD
                suffix = "T00:00:00Z" if index == 0 else "T23:59:59Z"
                normalised.append(f"{part}{suffix}")
            else:
                normalised.append(part)
        return "/".join(normalised)

    @staticmethod
    def _build_search_payload(
        bbox: list[float],
        datetime_range: str,
        collections: list[str],
        limit: int,
    ) -> dict[str, Any]:
        """Build the ``POST /v1/search`` payload (pure, network-free)."""
        return {
            "bbox": bbox,
            "datetime": CDSEConnector.normalize_datetime(datetime_range),
            "collections": collections,
            "limit": limit,
        }

    def _search(self, payload: dict[str, Any], token: str) -> list[dict]:
        """Run a STAC search and return the item list."""

        def _post() -> Any:
            import requests

            response = requests.post(
                f"{STAC_CATALOG_URL}/search",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            body: dict[str, Any] = self._retry(_post)()
            features: list[dict] = body.get("features", [])
            return features
        except Exception as exc:
            raise ConnectorUnavailable(
                f"CDSE STAC search failed ({type(exc).__name__}: {exc}) for "
                f"{STAC_CATALOG_URL}/search. The catalogue was unreachable or "
                f"rejected the request."
            ) from exc

    # ── OData product resolution and download ────────────────────

    @staticmethod
    def _build_product_filter(item_name: str) -> dict[str, str]:
        """Build the OData query that resolves an item id to a product UUID.

        The STAC item id *is* the product name in the OData catalogue; an
        exact ``Name eq`` match is unreliable (it returned an empty result
        set for a live item on 2026-10-10), while ``startswith`` returned
        the product, so that is what is used here.
        """
        return {"$filter": f"startswith(Name,'{item_name}')", "$top": "1"}

    def _find_product_id(self, item_name: str, token: str) -> str:
        """Resolve a STAC item id to its OData product UUID."""
        import requests

        params = self._build_product_filter(item_name)

        def _get() -> Any:
            response = requests.get(
                f"{ODATA_URL}/Products",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            values = self._retry(_get)().get("value", [])
        except Exception as exc:
            raise ConnectorUnavailable(
                f"CDSE OData product lookup failed for {item_name!r} "
                f"({type(exc).__name__}: {exc})."
            ) from exc

        if not values:
            raise ConnectorUnavailable(
                f"CDSE OData catalogue has no product matching "
                f"startswith(Name,'{item_name}'). The item may have been "
                f"withdrawn from the catalogue."
            )
        return str(values[0]["Id"])

    @staticmethod
    def _build_asset_download_url(product_id: str, asset_href: str) -> str:
        """Build the OData ``$value`` download URL for one asset.

        Accepts the ``s3://eodata/<path>`` hrefs the STAC catalogue returns
        and converts them to::

            <ODATA_URL>/Products(<id>)/Nodes('<seg>')/.../Nodes('<file>')/$value

        An href that is already an ``http(s)`` URL is returned unchanged.
        """
        if asset_href.startswith("http://") or asset_href.startswith("https://"):
            return asset_href
        prefix = "s3://eodata/"
        if not asset_href.startswith(prefix):
            raise ConnectorUnavailable(
                f"CDSE asset href {asset_href!r} is neither an http(s) URL nor "
                f"an {prefix!r} key; cannot build a download URL for it."
            )
        segments = [seg for seg in asset_href[len(prefix) :].split("/") if seg]
        if not segments:
            raise ConnectorUnavailable(
                f"CDSE asset href {asset_href!r} carries no path segments."
            )
        path = "/".join(f"Nodes('{seg}')" for seg in segments)
        return f"{ODATA_URL}/Products({product_id})/{path}/$value"

    def _download(self, url: str, target: Path, token: str) -> Path:
        """Stream one asset to *target* and return its path."""
        import requests

        def _get() -> Any:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout * 5,
                stream=True,
            )
            response.raise_for_status()
            return response

        try:
            with self._retry(_get)() as response:
                with target.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        handle.write(chunk)
        except Exception as exc:
            target.unlink(missing_ok=True)
            raise ConnectorUnavailable(
                f"CDSE asset download failed for {url} "
                f"({type(exc).__name__}: {exc})."
            ) from exc
        return target

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Search the CDSE catalogue and download one asset per item.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "datetime": "2021-01-01/2021-03-31",  # or RFC 3339
            "collections": ["sentinel-2-l2a"],
            "limit": 10,           # STAC search page size
            "asset_key": "TCI_10m",
            "max_items": 5,        # cap on downloaded items
        }

        Raises:
            ConnectorUnavailable: credentials missing, token refused,
                catalogue unreachable, or (per item) product not found.
                Individual asset downloads that fail are logged and
                skipped, so a partly-available scene still yields assets.
        """
        bbox = query.get("bbox", [51.0, 35.0, 52.0, 36.0])
        datetime_range = query.get("datetime", "2021-01-01/2021-03-31")
        collections = query.get("collections", ["sentinel-2-l2a"])
        limit = query.get("limit", 10)
        asset_key = query.get("asset_key", DEFAULT_ASSET_KEY)
        max_items = query.get("max_items", 5)

        token = self._token()
        payload = self._build_search_payload(bbox, datetime_range, collections, limit)
        items = self._search(payload, token)
        logger.info("CDSE search returned %d items for %s", len(items), collections)

        assets: list[DataAsset] = []
        for item in items[:max_items]:
            item_id = item.get("id", "")
            assets_map = item.get("assets", {})
            asset = assets_map.get(asset_key)
            if asset is None:
                logger.warning(
                    "CDSE item %s has no asset %r (available: %s); skipping",
                    item_id,
                    asset_key,
                    ", ".join(sorted(assets_map)[:8]),
                )
                continue

            try:
                product_id = self._find_product_id(item_id, token)
                download_url = self._build_asset_download_url(
                    product_id, asset.get("href", "")
                )
            except ConnectorUnavailable as exc:
                logger.warning("CDSE item %s skipped: %s", item_id, exc)
                continue

            asset_id = f"cdse_{item_id}_{asset_key}"
            file_path = self.cache_dir / f"{asset_id}.jp2"
            self._download(download_url, file_path, token)

            assets.append(
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"CDSE {item_id} {asset_key}",
                    description=(
                        f"Copernicus Data Space Ecosystem {asset_key} from "
                        f"{item.get('collection', collections[0])}"
                    ),
                    file_path=file_path,
                    format="geotiff",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "bbox": bbox,
                        "datetime": payload["datetime"],
                        "collections": collections,
                        "item_id": item_id,
                        "collection": item.get("collection"),
                        "asset_key": asset_key,
                        "media_type": asset.get("type"),
                        "product_id": product_id,
                    },
                    provenance={
                        "source_url": download_url,
                        "stac_item_id": item_id,
                        "stac_catalog": STAC_CATALOG_URL,
                        "query_params": payload,
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": "Copernicus Data Space Ecosystem (ESA)",
                    },
                )
            )

        return assets

    def validate(self, asset: DataAsset) -> bool:
        """Validate a downloaded CDSE asset by its container magic bytes."""
        if not asset.file_path.exists() or asset.file_path.stat().st_size == 0:
            return False
        head = asset.file_path.read_bytes()[:16]
        return head.startswith(_JP2_MAGIC) or head[:4] in _TIFF_MAGICS
