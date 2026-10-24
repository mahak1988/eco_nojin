"""Guards for the IGRAC GGIS (global groundwater) connector.

No network call is made: ``requests.get`` is faked out. The fixtures follow
the shapes of responses captured live on 2026-10-10 — the GeoNode v2 dataset
document for "GGMN Levels Data" (pk 2689), its GeoServer WFS GeoJSON
features, and its per-well level series at
``/groundwater/record/<id>/measurements/WellLevelMeasurement/data``. The
measurement *numbers* are arbitrary test values; the field names are the
documented ones.

What is pinned:

1. the WFS parameter builder (``outputFormat=application/json``, the
   ``CQL_FILTER=id=…`` restriction, the bbox filter and its validation);
2. the documented per-well measurement URL;
3. the honest typed failure paths — portal unreachable, dataset without a
   workspace/layer pair, WFS answering an OGC ServiceExceptionReport
   instead of a feature collection, and a level series with no ``data`` key;
4. the level-series parser and the station-metadata mapping onto asset
   metadata, with the source's parameter name and unit carried verbatim.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.igrac_connector import (
    DEFAULT_DATASET_PK,
    GGIS_BASE_URL,
    IGRACGroundwaterConnector,
)

# Epoch seconds for 2026-04-08T00:00:00Z / 2026-04-09T00:00:00Z.
_EPOCH_2026_04_08 = 1775606400.0
_EPOCH_2026_04_09 = 1775692800.0

_LEVEL_PARAMETER = "Water depth [from the top of the well]"


def _dataset_document() -> dict:
    """A GeoNode v2 dataset document, shaped like the live GGIS response."""
    return {
        "pk": DEFAULT_DATASET_PK,
        "uuid": "8340ad99-af22-4e66-afe4-e87be3a4e8e0",
        "name": "GGMN_Levels_Data",
        "title": "GGMN Levels Data",
        "workspace": "groundwater",
        "store": "groundwater",
        "subtype": "vector",
        "detail_url": f"{GGIS_BASE_URL}/catalogue/#/dataset/2689",
        "download_url": (
            f"{GGIS_BASE_URL}/datasets/groundwater:GGMN_Levels_Data/dataset_download"
        ),
        "attribute_set": [
            {"pk": 54025, "attribute": "id", "attribute_type": "xsd:int"},
            {"pk": 54026, "attribute": "ggis_uid", "attribute_type": "xsd:string"},
            {"pk": 54027, "attribute": "name", "attribute_type": "xsd:string"},
            {"pk": 54034, "attribute": "country", "attribute_type": "xsd:string"},
            {"pk": 54056, "attribute": "first_recorded_measurement", "attribute_type": "xsd:dateTime"},
        ],
        "extent": {
            "coords": [-169.589706420898, -43.8792610168457, 167.91960144043, 60.0],
            "srid": "EPSG:4326",
        },
    }


def _feature(well_id: str = "831568") -> dict:
    """One WFS GeoJSON well feature, shaped like the live GGIS response."""
    return {
        "type": "Feature",
        "id": f"GGMN_Levels_Data.fid-{well_id}",
        "geometry": {"type": "Point", "coordinates": [43.66982, 3.16987]},
        "properties": {
            "id": int(well_id),
            "ggis_uid": "Somalia - Ministry of Energy and Water Resources (MoEWR)-GW69",
            "original_id": "GW69",
            "name": "Bangiyaamo_3",
            "feature_type": "Water well",
            "purpose": "Observation / monitoring",
            "status": "Active",
            "organisation": "Somalia - Ministry of Energy and Water Resources (MoEWR)",
            "groundwater_level_data": 164,
            "groundwater_quality_data": 0,
            "country": "Somalia",
            "year_of_drilling": None,
            "aquifer_name": None,
            "aquifer_type": None,
            "detail": f'<a href="/groundwater/record/{well_id}">Full Data Record</a>',
            "first_recorded_measurement": "2025-10-27T00:00:00Z",
            "last_recorded_measurement": "2026-04-08T00:00:00Z",
            "groundwater_level": "yes",
            "groundwater_quality": "no",
            "ground_surface_elevation": None,
            "dem_elevation": 474.25,
            "dem_elevation_unit": "m",
        },
    }


def _levels_payload() -> dict:
    """A per-well level series, shaped like the live GGIS response."""
    return {
        "data": [
            {"dt": _EPOCH_2026_04_08, "par": _LEVEL_PARAMETER, "u": "m", "v": 23.4},
            {"dt": _EPOCH_2026_04_09, "par": _LEVEL_PARAMETER, "u": "m", "v": 12.67},
        ]
    }


def _fake_response(*, status: int = 200, payload: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.text = text or (json.dumps(payload) if payload is not None else "")
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def _stub_ggis(monkeypatch, *, features: list[dict] | None = None) -> dict:
    """Fake the GGIS endpoints: catalogue, WFS and the level series."""
    calls: dict[str, list] = {"datasets": [], "wfs": [], "measurements": []}

    def fake_get(url, **kwargs):
        if "measurements" in url:
            calls["measurements"].append(url)
            return _fake_response(payload=_levels_payload())
        if "/geoserver/" in url:
            calls["wfs"].append((url, kwargs.get("params")))
            return _fake_response(
                payload={
                    "type": "FeatureCollection",
                    "features": features if features is not None else [_feature()],
                }
            )
        calls["datasets"].append((url, kwargs.get("params")))
        if url.rstrip("/").endswith(str(DEFAULT_DATASET_PK)):
            return _fake_response(payload={"dataset": _dataset_document()})
        return _fake_response(payload={"datasets": [_dataset_document()]})

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def _connector(tmp_path: Path, **kwargs) -> IGRACGroundwaterConnector:
    kwargs.setdefault("cache_dir", tmp_path / "igrac")
    return IGRACGroundwaterConnector(**kwargs)


# ── request builders (pure) ─────────────────────────────────────────────


def test_wfs_params_carry_the_documented_json_output_format():
    params = IGRACGroundwaterConnector._build_wfs_params("groundwater:GGMN_Levels_Data", 50)
    assert params["service"] == "WFS"
    assert params["version"] == "1.0.0"
    assert params["request"] == "GetFeature"
    assert params["outputFormat"] == "application/json"
    assert params["typeName"] == "groundwater:GGMN_Levels_Data"
    assert params["maxFeatures"] == "50"
    assert params["maxFeatures"] == str(50)
    assert "CQL_FILTER" not in params
    assert "bbox" not in params


def test_wfs_params_add_a_cql_filter_for_a_single_well():
    params = IGRACGroundwaterConnector._build_wfs_params(
        "groundwater:GGMN_Levels_Data", cql_filter="id=831568"
    )
    assert params["CQL_FILTER"] == "id=831568"


def test_wfs_params_add_a_bbox_and_reject_a_malformed_one():
    params = IGRACGroundwaterConnector._build_wfs_params(
        "groundwater:GGMN_Levels_Data", bbox=[43.0, 3.0, 43.8, 3.3]
    )
    assert params["bbox"] == "43.0,3.0,43.8,3.3"

    with pytest.raises(ValueError):
        IGRACGroundwaterConnector._build_wfs_params(
            "groundwater:GGMN_Levels_Data", bbox=[43.0, 3.0]
        )


def test_measurements_use_the_documented_gwml2_path(tmp_path):
    connector = _connector(tmp_path)
    assert connector.measurements_url("831568") == (
        f"{GGIS_BASE_URL}/groundwater/record/831568/measurements/WellLevelMeasurement/data"
    )


def test_layer_for_dataset_reads_workspace_and_name_from_the_document():
    assert IGRACGroundwaterConnector.layer_for_dataset(_dataset_document()) == (
        "groundwater:GGMN_Levels_Data"
    )


def test_layer_for_dataset_fails_typed_without_a_workspace_layer_pair():
    with pytest.raises(ConnectorUnavailable) as excinfo:
        IGRACGroundwaterConnector.layer_for_dataset({"pk": 1, "title": "no workspace"})
    assert "workspace" in str(excinfo.value)


# ── catalogue + station metadata ────────────────────────────────────────


def test_dataset_document_is_read_from_the_geonode_api(tmp_path, monkeypatch):
    calls = _stub_ggis(monkeypatch)
    document = _connector(tmp_path).dataset()

    url, params = calls["datasets"][0]
    assert url == f"{GGIS_BASE_URL}/api/v2/datasets/{DEFAULT_DATASET_PK}/"
    assert document["name"] == "GGMN_Levels_Data"
    assert params == {}


def test_search_datasets_reads_the_documented_catalogue_endpoint(tmp_path, monkeypatch):
    calls = _stub_ggis(monkeypatch)

    datasets = _connector(tmp_path).search_datasets("groundwater")

    url, params = calls["datasets"][0]
    assert url == f"{GGIS_BASE_URL}/api/v2/datasets/"
    assert params == {"search": "groundwater", "page_size": 20}
    assert datasets[0]["title"] == "GGMN Levels Data"


def test_list_wells_maps_station_metadata_from_the_wfs_feature(tmp_path, monkeypatch):
    calls = _stub_ggis(monkeypatch)
    features = _connector(tmp_path).list_wells("831568")

    url, params = calls["wfs"][0]
    assert url == f"{GGIS_BASE_URL}/geoserver/groundwater/wfs"
    assert params["typeName"] == "groundwater:GGMN_Levels_Data"
    assert params["CQL_FILTER"] == "id=831568"
    assert len(features) == 1

    properties = features[0]["properties"]
    assert properties["name"] == "Bangiyaamo_3"
    assert properties["country"] == "Somalia"
    assert properties["dem_elevation"] == 474.25
    assert properties["dem_elevation_unit"] == "m"
    assert features[0]["geometry"]["coordinates"] == [43.66982, 3.16987]


def test_list_wells_passes_the_bbox_filter(tmp_path, monkeypatch):
    calls = _stub_ggis(monkeypatch)
    _connector(tmp_path).list_wells(bbox=[43.0, 3.0, 43.8, 3.3])
    assert calls["wfs"][0][1]["bbox"] == "43.0,3.0,43.8,3.3"


def test_list_wells_reports_an_ogc_service_exception_as_missing_data(tmp_path, monkeypatch):
    """GeoServer answers unknown layers with HTTP 200 + ServiceExceptionReport."""
    dataset_url = f"{GGIS_BASE_URL}/api/v2/datasets/{DEFAULT_DATASET_PK}/"

    def ogc_error(url, **kwargs):
        if "/geoserver/" in url:
            return _fake_response(
                status=200,
                text=(
                    '<?xml version="1.0" ?>'
                    '<ServiceExceptionReport version="1.2.0">'
                    "<ServiceException>No such feature type</ServiceException>"
                    "</ServiceExceptionReport>"
                ),
            )
        if url == dataset_url:
            return _fake_response(payload={"dataset": _dataset_document()})
        return _fake_response(payload={"datasets": [_dataset_document()]})

    monkeypatch.setattr(requests, "get", ogc_error)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).list_wells("831568")
    message = str(excinfo.value)
    assert "service exception" in message
    assert "No such feature type" in message
    assert "GGMN_Levels_Data" in message


# ── level series ────────────────────────────────────────────────────────


def test_parse_level_series_maps_epoch_parameter_and_unit(tmp_path):
    records = IGRACGroundwaterConnector.parse_level_series(_levels_payload())
    assert len(records) == 2
    assert records[0]["dt"] == _EPOCH_2026_04_08
    assert records[0]["datetime"].startswith("2026-04-08")
    assert records[0]["parameter"] == _LEVEL_PARAMETER
    assert records[0]["unit"] == "m"
    assert records[0]["value"] == 23.4


@pytest.mark.parametrize("payload", [None, {}, {"records": []}, [1, 2, 3]])
def test_parse_level_series_rejects_a_body_without_the_data_key(payload):
    with pytest.raises(ConnectorUnavailable):
        IGRACGroundwaterConnector.parse_level_series(payload)


def test_parse_level_series_accepts_an_empty_series_as_no_records():
    """A well with no published levels answers ``{"data": []}`` — zero rows."""
    assert IGRACGroundwaterConnector.parse_level_series({"data": []}) == []


def test_fetch_level_series_hits_the_documented_endpoint(tmp_path, monkeypatch):
    calls = _stub_ggis(monkeypatch)
    records = _connector(tmp_path).fetch_level_series("831568")

    assert calls["measurements"][0] == (
        f"{GGIS_BASE_URL}/groundwater/record/831568/measurements/WellLevelMeasurement/data"
    )
    assert len(records) == 2


def test_fetch_level_series_filters_on_date(tmp_path, monkeypatch):
    _stub_ggis(monkeypatch)
    records = _connector(tmp_path).fetch_level_series(
        "831568", start_date="2026-04-09", end_date="2026-04-09"
    )
    assert [record["value"] for record in records] == [12.67]


# ── fetch ───────────────────────────────────────────────────────────────


def test_fetch_builds_a_unit_carrying_csv_and_maps_station_metadata(tmp_path, monkeypatch):
    _stub_ggis(monkeypatch)
    assets = _connector(tmp_path).fetch({"station_id": "831568"})

    assert len(assets) == 1
    asset = assets[0]
    assert asset.source_id == "igrac_groundwater"
    assert asset.format == "csv"
    assert asset.file_path.exists() and asset.file_path.stat().st_size > 0

    station = asset.metadata["station"]
    assert station["station_id"] == "831568"
    assert station["name"] == "Bangiyaamo_3"
    assert station["country"] == "Somalia"
    assert station["aquifer_name"] is None
    assert station["latitude"] == 3.16987
    assert station["longitude"] == 43.66982
    assert station["dem_elevation"] == 474.25
    assert station["dem_elevation_unit"] == "m"
    assert station["status"] == "Active"
    assert station["organisation"].endswith("(MoEWR)")

    metadata = asset.metadata
    # The unit and parameter are carried verbatim from the source, so a
    # caller can see this is a depth to water and not a head elevation.
    assert metadata["unit"] == "m"
    assert metadata["parameter"] == _LEVEL_PARAMETER
    assert metadata["observation_count"] == 2
    assert metadata["first_observation"].startswith("2026-04-08")

    lines = asset.file_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "station_id,datetime,value,unit,parameter"
    assert lines[1] == f"831568,2026-04-08T00:00:00+00:00,23.4,m,{_LEVEL_PARAMETER}"
    assert "/groundwater/record/831568/measurements/WellLevelMeasurement/data" in (
        asset.provenance["source_url"]
    )
    assert _connector(tmp_path).validate(asset) is True


def test_fetch_requires_a_station_id(tmp_path, monkeypatch):
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({})
    assert "well id" in str(excinfo.value)


def test_fetch_surfaces_network_failures(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("ggis unreachable")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"station_id": "831568", "with_station_metadata": False})
    assert "unreachable" in str(excinfo.value)


def test_fetch_surfaces_an_error_status(tmp_path, monkeypatch):
    def denied(url, **kwargs):
        return _fake_response(status=503, text="service unavailable")

    monkeypatch.setattr(requests, "get", denied)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"station_id": "831568", "with_station_metadata": False})
    assert "503" in str(excinfo.value)


def test_fetch_reports_a_body_that_is_not_json(tmp_path, monkeypatch):
    def html(url, **kwargs):
        return _fake_response(status=200, text="<html>GeoNode maintenance page</html>")

    monkeypatch.setattr(requests, "get", html)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"station_id": "831568", "with_station_metadata": False})
    assert "not JSON" in str(excinfo.value)


def test_fetch_reports_a_well_with_no_published_level_series(tmp_path, monkeypatch):
    def no_records(url, **kwargs):
        return _fake_response(payload={"data": []})

    monkeypatch.setattr(requests, "get", no_records)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"station_id": "999999", "with_station_metadata": False})
    assert "no WellLevelMeasurement records" in str(excinfo.value)


def test_validate_rejects_a_table_without_a_usable_header(tmp_path):
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    connector = _connector(tmp_path)

    def make(payload: str) -> DataAsset:
        path = tmp_path / "probe.csv"
        path.write_text(payload, encoding="utf-8")
        return DataAsset(
            asset_id="x",
            source_id="igrac_groundwater",
            name="x",
            description="x",
            file_path=path,
            format="csv",
            size_bytes=len(payload),
            checksum="0" * 32,
        )

    header = "station_id,datetime,value,unit,parameter"
    assert connector.validate(make(header + "\n")) is False
    assert (
        connector.validate(make(f"{header}\n831568,2026-04-08T00:00:00+00:00,23.4,m,Depth\n"))
        is True
    )
    assert connector.validate(make("")) is False
