"""The published tool-registry contract must match what the router serialises.

`ToolResponse` and `ToolListResponse` were added so a client can type the 57
catalogue surfaces behind `/api/v1/tool-registry`. A model that drifts from
`_to_response` is worse than no model: it would publish fields the route does
not return, or silently drop fields it does. These tests pin the two together,
and pin the published schema to a real declaration rather than a permissive
object.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from database.models import ToolRegistryEntry
from services.api_gateway.main import app
from services.api_gateway.routers.tool_registry import (
    ToolListResponse,
    ToolResponse,
    _to_response,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _schema() -> None:
    """Ensure the route's table exists before each test in this module.

    This module previously declared no fixture at all, so it ran against
    whatever schema happened to be in ``data/econojin.db`` and reported
    ``no such table: tool_registry`` whenever an earlier test had reset the
    database. A contract test for a route must not depend on ambient state.

    Function-scoped rather than module-scoped on purpose: other modules in
    this session call ``reset_database()``, which drops every table. A
    module-scoped setup would be undone part-way through the run.
    """
    from database.config import init_db

    init_db()


EXPECTED_FIELDS = {
    "id",
    "tool_id",
    "name_fa",
    "name_en",
    "domain",
    "category",
    "fidelity",
    "reference",
    "description",
    "formula",
    "service_slug",
    "endpoint_path",
    "phase",
    "is_active",
    "created_at",
    "updated_at",
}


def _entry() -> ToolRegistryEntry:
    return ToolRegistryEntry(
        id=1,
        tool_id="soil-water-balance",
        name_fa="تعادل آب خاک",
        name_en="Soil water balance",
        domain="hydrology",
        category="water",
        fidelity="research",
        reference="FAO-56",
        description="A reference entry used only by this contract test.",
        formula="theta = ...",
        service_slug="soil",
        endpoint_path="/api/v1/analyses/soil-water",
        phase=2,
        is_active=True,
    )


def test_model_fields_match_the_serialiser() -> None:
    """A field the serialiser emits must exist on the model, and vice versa."""
    assert set(_to_response(_entry())) == EXPECTED_FIELDS
    assert set(ToolResponse.model_fields) == EXPECTED_FIELDS


def test_model_accepts_what_the_serialiser_produces() -> None:
    """The declared model must validate the real payload, not a guessed one."""
    payload = _to_response(_entry())
    model = ToolResponse.model_validate(payload)
    assert model.tool_id == "soil-water-balance"
    assert model.phase == 2
    assert model.created_at is None


def test_list_envelope_matches_the_list_route() -> None:
    """`GET ""` returns `count` plus `tools`; the published operation says so."""
    operation = app.openapi()["paths"]["/api/v1/tool-registry"]["get"]
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/ToolListResponse"
    assert set(ToolListResponse.model_fields) == {"count", "tools"}


def test_published_schema_declares_fields() -> None:
    """The OpenAPI document must describe the entry, not `additionalProperties`."""
    schema = app.openapi()
    entry = schema["components"]["schemas"]["ToolResponse"]
    assert "properties" in entry, "ToolResponse publishes no fields"
    assert set(entry["properties"]) == EXPECTED_FIELDS
    assert entry.get("additionalProperties") is not True

    envelope = schema["components"]["schemas"]["ToolListResponse"]
    assert set(envelope["properties"]) == {"count", "tools"}


def test_route_still_answers_under_the_declared_model() -> None:
    """A live request must pass response validation."""
    response = client.get("/api/v1/tool-registry")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"count", "tools"}
    for tool in body["tools"]:
        assert set(tool) == EXPECTED_FIELDS
