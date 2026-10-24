"""Guards for ``CGLSConnector.fetch`` in ``engine.hydroma.data_pipeline.pipeline``.

Two defects lived on the same download line:

1. ``requests`` was never imported in this method (every other ``fetch`` in this
   file does import it locally), so ``requests.get`` raised ``NameError``.
2. That ``NameError`` was raised inside ``except Exception``, so it was caught,
   downgraded to ``logger.warning``, and the tile was skipped. ``fetch()``
   therefore returned ``[]`` on every call, silently, forever -- a caller could
   not distinguish "no CGLS data published yet" from "this connector is broken".

The first test pins the import. The second pins the narrowing: a programming
error must escape rather than be reported as "no data".
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.pipeline import CGLSConnector

_TILE = "x015"
_KEY = "cgls_lwq300_2016_2024/x015/y015/Rw620_rep.tif"


def _stub_s3(monkeypatch, keys: list[str]) -> None:
    """Replace boto3's client so no network call is made."""
    import boto3

    paginator = MagicMock()
    paginator.paginate.return_value = [{"Contents": [{"Key": k} for k in keys]}]
    client = MagicMock()
    client.get_paginator.return_value = paginator
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)


def _stub_download(monkeypatch, payload: bytes = b"II*\x00fake-tiff") -> list[str]:
    """Record every URL the connector downloads."""
    urls: list[str] = []

    def fake_get(url, **kwargs):
        urls.append(url)
        response = MagicMock()
        response.iter_content.return_value = [payload]
        return response

    monkeypatch.setattr(requests, "get", fake_get)
    return urls


def _connector(tmp_path: Path) -> CGLSConnector:
    return CGLSConnector(cache_dir=tmp_path / "cgls")


def test_fetch_downloads_tiles_instead_of_returning_nothing(tmp_path, monkeypatch):
    """The missing ``import requests`` made this return ``[]`` on every call."""
    connector = _connector(tmp_path)
    _stub_s3(monkeypatch, [_KEY])
    urls = _stub_download(monkeypatch)
    monkeypatch.setattr(connector, "_list_tiles", lambda prefix: [_TILE])

    assets = connector.fetch({"product": "lwq300_2016_2024"})

    assert len(assets) == 1, f"expected one asset, got {assets!r}"
    assert assets[0].format == "geotiff"
    assert assets[0].metadata["variable"] == "Rw620_rep"
    assert assets[0].metadata["tile"] == "y015"
    assert len(urls) == 1
    assert urls[0].endswith(_KEY)
    assert assets[0].file_path.exists()


def test_network_failure_still_degrades_to_a_skipped_tile(tmp_path, monkeypatch):
    """The narrowed ``except`` must keep tolerating a real download failure."""
    connector = _connector(tmp_path)
    _stub_s3(monkeypatch, [_KEY])

    def boom(url, **kwargs):
        raise requests.ConnectionError("network unreachable")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(connector, "_list_tiles", lambda prefix: [_TILE])

    assert connector.fetch({"product": "lwq300_2016_2024"}) == []


def test_programming_errors_are_not_reported_as_no_data(tmp_path, monkeypatch):
    """The observable-behaviour guard for the narrowed ``except``.

    ``except Exception`` caught a ``TypeError`` from the connector's own code and
    returned ``[]`` -- the caller was told there was no data when the connector
    was simply wrong.
    """
    connector = _connector(tmp_path)
    _stub_s3(monkeypatch, [_KEY])

    def boom(url, **kwargs):
        raise TypeError("connector called requests.get with the wrong signature")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(connector, "_list_tiles", lambda prefix: [_TILE])

    with pytest.raises(TypeError, match="wrong signature"):
        connector.fetch({"product": "lwq300_2016_2024"})
