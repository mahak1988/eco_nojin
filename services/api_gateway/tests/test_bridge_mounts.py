"""The Daneshyar (knowledge) and Tasmimyar (decision) bridges, the stable
API-v1 motor surface, and the nine never-wired gateway routers must be mounted.

This is the regression guard for the wiring that was missing: these routers
existed as importable modules with no ``include_router``, so every path they
declared was unreachable.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from services.api_gateway.api.v1 import router as api_v1_router
from services.api_gateway.auth import require_user
from services.api_gateway.routers import (
    ai_advice_router,
    climate,
    community,
    culture,
    economy,
    ecosystem,
    lab,
    nature,
    water,
)
from services.knowledge.router import router as knowledge_router
from services.tasmimyar.decision_service import router as tasmimyar_router

_PRE_EXISTING_FLOOR = 568  # openapi paths present before this wiring


def _openapi_paths() -> set[str]:
    from services.api_gateway.main import app

    return set(app.openapi()["paths"].keys())


def _router_paths(router) -> set[str]:
    return {getattr(route, "path", "") for route in getattr(router, "routes", [])}


def _assert_all_mounted(router) -> None:
    missing = _router_paths(router) - _openapi_paths()
    assert not missing, f"routes not mounted: {sorted(missing)}"


def test_knowledge_router_is_mounted():
    _assert_all_mounted(knowledge_router)
    assert "/api/v1/knowledge/search" in _openapi_paths()


def test_tasmimyar_router_is_mounted():
    _assert_all_mounted(tasmimyar_router)
    assert "/api/tasmimyar/decide" in _openapi_paths()
    assert "/api/tasmimyar/explain/{decision_id}" in _openapi_paths()


def test_api_v1_motors_surface_is_mounted():
    _assert_all_mounted(api_v1_router)
    paths = _openapi_paths()
    assert "/api/v1/motors" in paths
    assert "/api/v1/motors/{motor_type}" in paths


@pytest.mark.parametrize(
    "router,expected_path",
    [
        (ecosystem, "/api/v1/ecosystem/health"),
        (climate, "/api/v1/motors/drought"),
        (lab, "/api/mrv/lab/samples"),
        (community, "/api/v1/community/participants"),
        (culture, "/api/v1/culture/events"),
        (economy, "/api/motors/economy/"),
        (nature, "/api/v1/nature/ecosystems"),
        (water, "/api/v1/water-signature/summary"),
        (ai_advice_router, "/api/v1/ai/advice/advise"),
    ],
)
def test_never_wired_gateway_routers_are_mounted(router, expected_path):
    _assert_all_mounted(router)
    assert expected_path in _openapi_paths()


def test_total_endpoint_count_grew():
    total = len(_openapi_paths())
    assert total > _PRE_EXISTING_FLOOR, f"expected endpoints to grow past {_PRE_EXISTING_FLOOR}"


@pytest.fixture(scope="module")
def client():
    from services.api_gateway.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        c.get("/health")  # materialise the lazily-built middleware stack
        yield c


def test_motors_endpoint_returns_real_inventory(client):
    response = client.get("/api/v1/motors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10, "the API must report the real motor inventory"
    types = {m["motor_type"] for m in data}
    assert "erosion_rusle" in types
    for motor in data:
        assert motor["display_name"]


def test_tasmimyar_decide_returns_a_real_decision(client):
    from services.api_gateway.main import app

    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id="test-user")
    try:
        response = client.post(
            "/api/tasmimyar/decide",
            json={
                "claim_id": "irrigate-today",
                "supporting_facts": [
                    {
                        "id": "f1",
                        "statement": "Measured field moisture is within the target range",
                        "source_id": "user-submitted",
                        "confidence": 0.9,
                    }
                ],
                "contradicting_facts": [],
            },
        )
    finally:
        app.dependency_overrides.pop(require_user, None)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    decision = body["data"]
    assert isinstance(decision["outcome"], str) and decision["outcome"]
    # Results-only contract: the decision surface reaches the client, the
    # engine's internal scoring trace does not.
    assert "trace" not in decision
    assert set(decision) == {
        "decision_id",
        "outcome",
        "confidence",
        "rationale",
        "recommendations",
        "caveats",
    }


def test_api_v1_health_stays_the_rich_payload(client):
    # api/v1/router.py also declares GET /api/v1/health (terse). It is mounted
    # after main.py's rich handler so the rich one stays authoritative.
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "checks" in response.json()
