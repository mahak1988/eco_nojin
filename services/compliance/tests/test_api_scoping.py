"""P9 — the compliance router scopes every read/write to the caller.

P3 established the marketplace matrix; this is the compliance-plane half: a
non-admin caller cannot register a credential for, assess, or read the status of
another subject. Each test fails if the scope check is removed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.api_gateway.auth import require_user
from services.compliance.api import router as compliance_router

pytestmark = pytest.mark.asyncio


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(compliance_router)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="user-a", role="farmer", is_active=True
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_cannot_register_a_credential_for_another_subject(client: AsyncClient):
    response = await client.post(
        "/api/v1/compliance/credentials/seller/user-b",
        json={"kind": "trade_licence", "reference": "X-1"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Cannot register a credential for another subject"


async def test_cannot_assess_another_subject(client: AsyncClient):
    response = await client.post(
        "/api/v1/compliance/assess/seller/user-b",
        json={
            "activity_code": "food.producer",
            "jurisdiction_id": "j-1",
            "outcome": "compliant",
            "evidence_ref": "doc-1",
            "note": "not really",
        },
    )
    assert response.status_code == 403


async def test_cannot_classify_another_subject(client: AsyncClient):
    response = await client.post(
        "/api/v1/compliance/classify/seller/user-b",
        json={
            "activity_code": "food.producer",
            "jurisdiction_id": "j-1",
        },
    )
    assert response.status_code == 403
    assert "another subject" in response.json()["detail"]


async def test_cannot_read_another_subjects_status(client: AsyncClient):
    response = await client.get(
        "/api/v1/compliance/status/seller/user-b", params={"jurisdiction_id": "j-1"}
    )
    assert response.status_code == 403
    assert "another subject" in response.json()["detail"]


async def test_unknown_outcome_is_refused(client: AsyncClient):
    response = await client.post(
        "/api/v1/compliance/assess/seller/user-a",
        json={
            "activity_code": "food.producer",
            "jurisdiction_id": "j-1",
            "outcome": "definitely_fine",
            "evidence_ref": "doc-1",
            "note": "x",
        },
    )
    assert response.status_code == 422
