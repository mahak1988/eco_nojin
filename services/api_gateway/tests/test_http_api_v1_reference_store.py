"""Honest-availability regression guards for the DuckDB reference endpoints.

P0 / KN-43: ``GET /api/v1/rules`` and ``GET /api/v1/units`` previously surfaced a
missing reference store as a ``500`` (``AttributeError: 'Hub' object has no
attribute 'internal_duckdb'``). ``Hub`` now wires to the real
``data/master/eco_nojin_master.duckdb`` file, so the store answers ``200`` with an
empty list when no reference rows exist -- honest, not fabricated.

``GET /dashboard/public/weather`` previously fabricated ``avg_temperature_c:
22.5`` on the no-data path. It must return ``status: "no_data"`` with zeroed
metrics, matching the sibling dashboard fallbacks (dashboard.py:389/439/489/...).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from services.api_gateway.main import app


def test_reference_rules_answers_200_not_500() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/v1/rules")
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_reference_units_answers_200_not_500() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/v1/units")
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_dashboard_weather_does_not_fabricate_temperature() -> None:
    with TestClient(app) as client:
        resp = client.get("/dashboard/public/weather")
    assert resp.status_code == 200, resp.text
    # ``PublicDashboardResponse`` wraps the helper output under ``data`` (the
    # envelope ``status`` is always "success"; the data-level status carries the
    # availability signal).
    data = resp.json()["data"]
    assert data["status"] == "no_data"
    assert data["avg_temperature_c"] != 22.5
