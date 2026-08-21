"""ERA5 fetch tests (mocked CDS job + real xarray NetCDF parse)."""
import pathlib

import io

import pytest
import xarray as xr

from services.satellite.cds import DataStoreError
from services.satellite.era5_fetch import (
    Era5Error,
    _parse_netcdf,
    fetch_era5_point,
)


def make_netcdf(vars_=("t2m", "tp")):
    """Synthetic ERA5-like NetCDF bytes for one day, 3x3 grid."""
    import numpy as np

    lat = np.array([36.4, 36.2, 36.0])
    lon = np.array([50.6, 50.8, 51.0])
    t = np.array([0], dtype="datetime64[h]")
    data = {}
    if "t2m" in vars_:
        data["t2m"] = (("time", "y", "x"), np.array([[[290.0, 291.0, 292.0],
                                                       [289.0, 290.0, 291.0],
                                                       [288.0, 289.0, 290.0]]]))
    if "tp" in vars_:
        data["tp"] = (("time", "y", "x"), np.array([[[0.001, 0.002, 0.001],
                                                      [0.000, 0.001, 0.002],
                                                      [0.001, 0.001, 0.001]]]))
    ds = xr.Dataset(
        data,
        coords={
            "latitude": (("y",), lat),
            "longitude": (("x",), lon),
            "valid_time": (("time",), t),
        },
    )
    buf = io.BytesIO()
    ds.to_netcdf(buf, engine="h5netcdf")
    ds.close()
    return buf.getvalue()


class TestParse:
    def test_parse_t2m_and_tp(self):
        out = _parse_netcdf(make_netcdf(), 36.2, 50.8, ["t2m", "tp"])
        assert out["dataset"] == "reanalysis-era5-single-levels"
        assert len(out["daily"]) == 1
        row = out["daily"][0]
        # nearest point (36.2, 50.8) -> t2m 290 K = 16.85 C, tp 1 mm
        assert row["t2m_c"] == pytest.approx(16.85, abs=0.01)
        assert row["tp_mm"] == pytest.approx(1.0, abs=0.001)

    def test_parse_single_variable(self):
        out = _parse_netcdf(make_netcdf(["t2m"]), 36.4, 51.0, ["t2m"])
        assert "tp_mm" not in out["daily"][0]
        assert out["daily"][0]["t2m_c"] == pytest.approx(18.85, abs=0.01)

    def test_bad_bytes(self):
        with pytest.raises(Era5Error):
            _parse_netcdf(b"not netcdf", 36.0, 51.0, ["t2m"])


class TestFetch:
    def test_invalid_coords(self):
        with pytest.raises(Era5Error):
            fetch_era5_point(91.0, 0.0, "2024-06-01", "2024-06-02")

    def test_unknown_variable(self):
        with pytest.raises(Era5Error):
            fetch_era5_point(36.0, 51.0, "2024-06-01", "2024-06-02", variables=["nope"])

    def test_full_pipeline_mocked(self, monkeypatch):
        calls = {}

        class FakeClient:
            def __init__(self, store="cds"):
                calls["store"] = store

            def submit_request(self, params, dataset="reanalysis-era5-single-levels"):
                calls["params"] = params
                calls["dataset"] = dataset
                return "https://cds/task/1"

            def poll_task(self, task_url, max_seconds=600.0):
                calls["poll"] = True
                return "completed"

            def download(self, task_url):
                return make_netcdf(["t2m"])

        monkeypatch.setattr("services.satellite.era5_fetch.DataStoreClient", FakeClient)
        out = fetch_era5_point(36.2, 50.8, "2024-06-01", "2024-06-02", variables=["t2m"])
        assert calls["dataset"] == "reanalysis-era5-single-levels"
        assert "2m_temperature" in calls["params"]["variable"]
        assert calls["params"]["year"] == ["2024"]
        assert out["daily"][0]["t2m_c"] == pytest.approx(16.85, abs=0.01)

    def test_store_error_surfaced(self, monkeypatch):
        class BoomClient:
            def __init__(self, store="cds"):
                pass

            def submit_request(self, params, dataset="x"):
                raise DataStoreError("boom 401 operation not allowed")

        monkeypatch.setattr("services.satellite.era5_fetch.DataStoreClient", BoomClient)
        with pytest.raises(Era5Error) as exc:
            fetch_era5_point(36.0, 51.0, "2024-06-01", "2024-06-02")
        assert "401" in str(exc.value)
