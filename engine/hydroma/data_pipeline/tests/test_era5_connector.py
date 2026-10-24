"""Guards for the ERA5 (Climate Data Store) connector.

Covers, without any network call:

1. credential discovery — ``CDS_KEY``, ``CDSAPI_KEY``, then ``~/.cdsapirc``
   (relocated with ``CDSAPI_RC`` for the test) — and the typed
   ``ConnectorUnavailable`` that names all three when none is present;
2. the request document builder, including the bbox → ``[N, W, S, E]``
   area conversion the CDS API expects (the reverse of the bbox convention
   used everywhere else in this pipeline);
3. the submit → poll → download protocol with ``requests`` faked in.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.era5_connector import (
    CDS_API_URL,
    ERA5Connector,
)

_NETCDF = b"CDF\x01" + b"netcdf-payload"


def _fake_response(*, status: int = 200, payload: dict | None = None, chunks=None) -> MagicMock:
    """A ``requests`` response double wired for both with-blocks and .json()."""
    response = MagicMock()
    response.status_code = status
    if payload is not None:
        response.json.return_value = payload
    if chunks is not None:
        response.iter_content.return_value = chunks
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.raise_for_status.return_value = None
    return response


def _connector(tmp_path: Path, **kwargs) -> ERA5Connector:
    kwargs.setdefault("api_key", "12345:abcdef")
    kwargs.setdefault("cache_dir", tmp_path / "era5")
    return ERA5Connector(**kwargs)


def _no_key_anywhere(monkeypatch, tmp_path: Path) -> None:
    """Point credential discovery at an environment with no key at all."""
    monkeypatch.delenv("CDS_KEY", raising=False)
    monkeypatch.delenv("CDSAPI_KEY", raising=False)
    monkeypatch.setenv("CDSAPI_RC", str(tmp_path / "definitely-absent.cdsapirc"))


# ── credentials ────────────────────────────────────────────────────


def test_missing_key_names_every_source(tmp_path, monkeypatch):
    _no_key_anywhere(monkeypatch, tmp_path)
    connector = ERA5Connector(cache_dir=tmp_path / "era5")

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector._credentials()

    message = str(excinfo.value)
    assert "CDS_KEY" in message
    assert "CDSAPI_KEY" in message
    assert ".cdsapirc" in message


def test_key_is_read_from_the_cds_key_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("CDS_KEY", "111:222")
    monkeypatch.delenv("CDSAPI_KEY", raising=False)
    monkeypatch.setenv("CDSAPI_RC", str(tmp_path / "absent.cdsapirc"))

    url, key = ERA5Connector(cache_dir=tmp_path / "era5")._credentials()
    assert key == "111:222"
    assert url == CDS_API_URL


def test_key_falls_back_to_cdsapirc_file(tmp_path, monkeypatch):
    rc = tmp_path / ".cdsapirc"
    rc.write_text(
        "url: https://cds.climate.copernicus.eu/api\nkey: 999:888\n", encoding="utf-8"
    )
    monkeypatch.delenv("CDS_KEY", raising=False)
    monkeypatch.delenv("CDSAPI_KEY", raising=False)
    monkeypatch.setenv("CDSAPI_RC", str(rc))

    url, key = ERA5Connector(cache_dir=tmp_path / "era5")._credentials()
    assert key == "999:888"
    assert url == CDS_API_URL


def test_malformed_key_is_rejected_with_the_expected_format(tmp_path, monkeypatch):
    connector = ERA5Connector(cache_dir=tmp_path / "era5", api_key="no-colon-here")

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector._credentials()

    assert "UID" in str(excinfo.value) and "API" in str(excinfo.value)


# ── request builder ────────────────────────────────────────────────


def test_build_request_converts_bbox_to_cds_area_order(tmp_path):
    connector = _connector(tmp_path)
    request = connector.build_request(
        {
            "dataset": "reanalysis-era5-land",
            "variables": ["2m_temperature"],
            "bbox": [51.0, 35.0, 52.0, 36.0],
            "start_date": "2021-01-01",
            "end_date": "2021-01-02",
        }
    )

    # CDS wants [North, West, South, East] — the reverse of the bbox order.
    assert request["area"] == [36.0, 51.0, 35.0, 52.0]
    assert request["variable"] == ["2m_temperature"]
    assert request["year"] == ["2021"]
    assert request["month"] == ["01"]
    assert request["day"] == ["01", "02"]
    assert request["data_format"] == "netcdf"
    assert request["download_format"] == "unarchived"


def test_build_request_merges_extra_dataset_keys(tmp_path):
    connector = _connector(tmp_path)
    request = connector.build_request(
        {
            "dataset": "reanalysis-era5-single-levels",
            "bbox": [0, 0, 1, 1],
            "start_date": "2021-05-01",
            "end_date": "2021-05-01",
            "extra": {"product_type": ["reanalysis"]},
        }
    )
    assert request["product_type"] == ["reanalysis"]


def test_build_request_rejects_reversed_date_range(tmp_path):
    connector = _connector(tmp_path)
    with pytest.raises(ValueError):
        connector.build_request({"start_date": "2021-06-01", "end_date": "2021-01-01"})


def test_build_request_rejects_bad_bbox(tmp_path):
    connector = _connector(tmp_path)
    with pytest.raises(ValueError):
        connector.build_request({"bbox": [0, 0, 1]})


# ── submit / poll / download ───────────────────────────────────────


def _stub_cds(monkeypatch, task_state: str = "completed", **extra) -> dict:
    """Fake the CDS REST protocol: submit, poll and result download."""
    calls: dict[str, list] = {"post": [], "get": []}

    def fake_post(url, **kwargs):
        calls["post"].append((url, kwargs.get("json")))
        assert kwargs.get("auth") == ("12345", "abcdef")
        return _fake_response(status=202, payload={"state": "queued", "request_id": "task-1"})

    def fake_get(url, **kwargs):
        calls["get"].append(url)
        if "/tasks/" in url:
            return _fake_response(
                payload={
                    "state": task_state,
                    "location": "https://cds.example.org/result.nc",
                    "content_length": len(_NETCDF),
                    **extra,
                }
            )
        return _fake_response(chunks=[_NETCDF])

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def test_fetch_submits_polls_and_downloads(tmp_path, monkeypatch):
    connector = _connector(tmp_path, max_wait=1)
    calls = _stub_cds(monkeypatch)

    assets = connector.fetch(
        {
            "dataset": "reanalysis-era5-land",
            "variables": ["2m_temperature"],
            "bbox": [51.0, 35.0, 52.0, 36.0],
            "start_date": "2021-01-01",
            "end_date": "2021-01-01",
        }
    )

    assert len(assets) == 1
    asset = assets[0]
    assert asset.format == "netcdf"
    assert asset.file_path.exists() and asset.file_path.stat().st_size > 0
    assert asset.metadata["request_id"] == "task-1"
    assert asset.provenance["source_url"] == "https://cds.example.org/result.nc"

    submit_url, payload = calls["post"][0]
    assert submit_url == f"{CDS_API_URL}/resources/reanalysis-era5-land"
    assert payload["area"] == [36.0, 51.0, 35.0, 52.0]
    assert calls["get"][0] == f"{CDS_API_URL}/tasks/task-1"
    assert calls["get"][-1] == "https://cds.example.org/result.nc"


def test_fetch_reports_failed_tasks(tmp_path, monkeypatch):
    connector = _connector(tmp_path, max_wait=1)
    _stub_cds(monkeypatch, task_state="failed", message="licence terms not accepted")

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector.fetch({"start_date": "2021-01-01", "end_date": "2021-01-01"})

    assert "licence terms not accepted" in str(excinfo.value)


def test_fetch_reports_submission_failures(tmp_path, monkeypatch):
    connector = _connector(tmp_path)

    def boom(url, **kwargs):
        raise requests.ConnectionError("cds unreachable")

    monkeypatch.setattr(requests, "post", boom)

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector.fetch({})

    assert "cds unreachable" in str(excinfo.value)


def test_validate_accepts_netcdf_magic_only(tmp_path):
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    connector = _connector(tmp_path)

    def make(payload: bytes) -> DataAsset:
        path = tmp_path / "probe.nc"
        path.write_bytes(payload)
        return DataAsset(
            asset_id="x",
            source_id="era5",
            name="x",
            description="x",
            file_path=path,
            format="netcdf",
            size_bytes=len(payload),
            checksum="0" * 32,
        )

    assert connector.validate(make(_NETCDF)) is True
    assert connector.validate(make(b"\x89HDF\r\n\x1a\nrest")) is True
    assert connector.validate(make(b"garbage")) is False
    assert connector.validate(make(b"")) is False
