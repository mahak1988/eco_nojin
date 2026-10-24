"""Tasmimyar decision assistant — router mount + real decision/explain routes.

The decision router calls ``EngineGateway.make_decision`` in-process, so

``POST /api/v1/tasmimyar/decide`` returns a real, traced decision without any

external service.

"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from services.api_gateway.auth import require_user
from services.tasmimyar import decision_service as ds


def test_decision_router_declares_decide_and_explain():

    assert ds.HAS_ROUTER is True

    paths = {getattr(route, "path", "") for route in ds.router.routes}

    assert "/api/v1/tasmimyar/decide" in paths

    assert "/api/v1/tasmimyar/explain/{decision_id}" in paths

    assert "/api/v1/tasmimyar/advice" in paths

def test_advice_endpoint_reaches_the_p11_builder(client):

    """The P11 contract is reachable in production, not only by its own test."""

    created = client.post(

        "/api/v1/tasmimyar/advice",

        json={

            "goal": "planting window for wheat",

            "recommendation": "plant on day 280",

            "model_id": "CANON-004",

            "accountable_user_id": "farmer-1",

            "criteria": [{"name": "soil_moisture", "weight": 1.0}],

            "scenarios": [{"name": "day_280", "predicted": 3.2}],

            "assumptions": ["no irrigation before planting"],

            "uncertainty": "±3 days",

            "limits": "validated for the Caspian plain only",

        },

    )

    assert created.status_code == 200

    advice = created.json()["data"]["advice"]

    assert advice["goal"] == "planting window for wheat"

    assert advice["accountable_user_id"] == "test-user"

    assert advice["criteria_weight_total"] == 1.0

def test_advice_is_refused_when_limits_are_missing(client):

    refused = client.post(

        "/api/v1/tasmimyar/advice",

        json={

            "goal": "irrigation window",

            "recommendation": "irrigate",

            "model_id": "CANON-004",

            "accountable_user_id": "farmer-1",

            "criteria": [{"name": "soil_moisture", "weight": 1.0}],

            "scenarios": [{"name": "now", "predicted": 3.2}],

            "assumptions": ["no rain forecast"],

            "uncertainty": "unknown",

            "limits": "",

        },

    )

    assert refused.status_code == 200

    body = refused.json()

    assert body["success"] is False

    assert body["error_code"] == "ADVICE_REFUSED"

@pytest.fixture(scope="module")
def client():
    from services.api_gateway.main import app

    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id="test-user")
    with TestClient(app, raise_server_exceptions=False) as c:
        c.get("/health")
        yield c
    app.dependency_overrides.pop(require_user, None)


def test_tasmimyar_requires_authentication(client):
    from services.api_gateway.main import app

    override = app.dependency_overrides.pop(require_user)
    try:
        response = client.post(
            "/api/v1/tasmimyar/decide",
            json={"claim_id": "unauthenticated"},
        )
    finally:
        app.dependency_overrides[require_user] = override
    assert response.status_code == 401

def test_decide_returns_success_then_unknown_explain_is_404(client):

    created = client.post(

        "/api/v1/tasmimyar/decide",

        json={
            "claim_id": "c1",
            "supporting_facts": [
                {
                    "id": "f",
                    "statement": "Measured field moisture is within the target range",
                    "source_id": "user-submitted",
                    "confidence": 0.6,
                }
            ],
        },

    )

    assert created.status_code == 200

    body = created.json()

    assert body["success"] is True

    # Results-only contract: the engine's internal scoring trace stays on
    # the server. ``/decide`` returns the decision surface, never the
    # criterion scores, evidence weights or aggregate score the engine used.
    assert set(body["data"]) == {
        "decision_id",
        "outcome",
        "confidence",
        "rationale",
        "recommendations",
        "caveats",
    }
    assert "trace" not in body["data"]
    assert body["data"]["confidence"] == pytest.approx(0.6)

    missing = client.get("/api/v1/tasmimyar/explain/does-not-exist")

    assert missing.status_code == 404

    assert isinstance(missing.json(), dict)
