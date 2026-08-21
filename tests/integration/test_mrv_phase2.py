"""Integration tests for the MRV (EM-01) API endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def _site() -> str:
    """Return a unique site id so repeated runs never collide."""
    return f"mrv-test-{uuid4().hex[:12]}"


class TestIotReadings:
    """Level 2: IoT sensor readings with QA/QC."""

    def test_store_iot_reading_and_list(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/iot-reading",
            json={
                "site_id": site,
                "sensor_type": "soil_moisture",
                "value": 34.5,
                "unit": "%",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["qa_status"] == "ok"
        assert data["level"] == 2
        assert data["source"] == "iot"
        assert data["data_source"] == "real"

        listing = client.get(f"/api/v1/mrv/observations?site_id={site}").json()
        assert listing["count"] == 1
        assert listing["observations"][0]["sensor_type"] == "soil_moisture"

    def test_iot_reading_out_of_range_is_rejected_but_persisted(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/iot-reading",
            json={"site_id": site, "sensor_type": "ec", "value": 95.0, "unit": "dS/m"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["qa_status"] == "rejected"
        assert data["qa"]["message"]
        # rejected rows stay visible for the audit trail
        assert client.get(f"/api/v1/mrv/observations?site_id={site}").json()["count"] == 1

    def test_invalid_sensor_type_rejected_by_schema(self):
        response = client.post(
            "/api/v1/mrv/iot-reading",
            json={"site_id": _site(), "sensor_type": "ph", "value": 7.0, "unit": "-"},
        )
        assert response.status_code == 422


class TestCitizenReports:
    """Level 3: citizen field reports."""

    def test_store_citizen_report_and_filter_by_level(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/citizen-report",
            json={
                "site_id": site,
                "observer": "farmer-42",
                "category": "pest",
                "note": "Aphids observed on young leaves.",
                "lat": 36.85,
                "lon": 54.42,
                "photos_urls": ["https://example.com/photos/1.jpg"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == 3
        assert data["category"] == "pest"
        assert data["payload"]["observer"] == "farmer-42"
        assert data["payload"]["lat"] == 36.85

        listing = client.get(f"/api/v1/mrv/observations?site_id={site}&level=3").json()
        assert listing["count"] == 1
        assert listing["observations"][0]["source"] == "citizen"


class TestSatelliteIndex:
    """Level 1: satellite indices with provenance."""

    def test_store_satellite_index_simulated(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/satellite-index",
            json={
                "site_id": site,
                "index": "NDVI",
                "value": 0.72,
                "data_source": "simulated",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == 1
        assert data["data_source"] == "simulated"
        assert data["qa_status"] == "ok"


class TestDashboardMetrics:
    """Transparency dashboard with provenance badges."""

    def test_dashboard_without_data_returns_none_metrics(self):
        site = _site()
        response = client.get(f"/api/v1/mrv/dashboard-metrics?site_id={site}")
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == site
        assert all(v is None for v in data["metrics"].values())
        assert data["observation_counts"] == {"satellite": 0, "iot": 0, "citizen": 0}

    def test_dashboard_real_data_computes_co2e(self):
        site = _site()
        client.post(
            "/api/v1/mrv/iot-reading",
            json={"site_id": site, "sensor_type": "soil_moisture", "value": 30.0, "unit": "%"},
        )
        response = client.get(
            f"/api/v1/mrv/dashboard-metrics?site_id={site}"
            "&area_ha=4&soc_before_pct=1.0&soc_after_pct=1.5"
            "&rusle_before_tha=12&rusle_after_tha=3"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["observation_counts"]["iot"] == 1
        assert data["data_sources_observed"] == ["real"]
        soc = data["metrics"]["soc_change_pct"]
        assert soc["data_source"] == "real"
        assert soc.get("warning") is None
        assert soc["soc_change_pct"] == 50.0
        # delta SOC = 0.5% * 1.3 * 0.3 * 10000 = 19.5 t/ha; 4 ha * 19.5 * 3.67
        co2e = data["metrics"]["co2e_sequestered_t"]["co2e_sequestered_t"]
        assert abs(co2e - 19.5 * 4.0 * 3.67) < 0.1
        erosion = data["metrics"]["erosion_reduction_t_yr"]
        assert erosion["erosion_reduction_t_yr"] == 36.0  # (12-3) * 4

    def test_dashboard_simulated_observation_downgrades_badge(self):
        site = _site()
        client.post(
            "/api/v1/mrv/satellite-index",
            json={"site_id": site, "index": "LAI", "value": 3.5, "data_source": "simulated"},
        )
        response = client.get(
            f"/api/v1/mrv/dashboard-metrics?site_id={site}"
            "&area_ha=2&soc_before_pct=1.2&soc_after_pct=1.4"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data_sources_observed"] == ["simulated"]
        soc = data["metrics"]["soc_change_pct"]
        assert soc["data_source"] == "simulated"
        assert soc["warning"], "simulated badge must warn the reader"
        assert data["metrics"]["restored_area_ha"]["data_source"] == "simulated"