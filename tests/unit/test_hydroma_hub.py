"""Tests for the HyDroMa data hub (isolated in-memory database)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import ModelRun  # noqa: F401 — registers the model
from services.api_gateway.routers import hydroma_hub

USER = "test-client-1234"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    app = FastAPI()
    app.include_router(hydroma_hub.router)
    app.dependency_overrides[hydroma_hub.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, testing_session


def _create(test_client, model_id="horton-infiltration", outputs=None):
    return test_client.post(
        "/api/v1/hub/runs",
        json={
            "user_key": USER,
            "model_id": model_id,
            "title": "Horton run",
            "inputs": {"f0": 130, "fc": 40, "k": 0.5},
            "outputs": outputs or {"cum6": 412},
        },
    )


class TestHubRuns:
    def test_create_and_list(self, client):
        test_client, _session_factory = client
        response = _create(test_client)
        assert response.status_code == 200
        assert response.json()["ok"] is True

        listing = test_client.get("/api/v1/hub/runs", params={"user_key": USER})
        assert listing.status_code == 200
        assert listing.json()["count"] == 1
        assert listing.json()["runs"][0]["model_id"] == "horton-infiltration"

    def test_share_toggle_and_shared_feed(self, client):
        test_client, _session_factory = client
        run_id = _create(test_client).json()["id"]

        shared_on = test_client.post(
            f"/api/v1/hub/runs/{run_id}/share",
            params={"user_key": USER},
            json={"shared": True},
        )
        assert shared_on.status_code == 200
        assert shared_on.json()["shared"] is True

        feed = test_client.get("/api/v1/hub/shared")
        assert feed.json()["count"] == 1

        shared_off = test_client.post(
            f"/api/v1/hub/runs/{run_id}/share",
            params={"user_key": USER},
            json={"shared": False},
        )
        assert shared_off.json()["shared"] is False
        feed_after = test_client.get("/api/v1/hub/shared")
        assert feed_after.json()["count"] == 0

    def test_user_isolation(self, client):
        test_client, _session_factory = client
        _create(test_client)
        other = test_client.get("/api/v1/hub/runs", params={"user_key": "other-client-99"})
        assert other.json()["count"] == 0

    def test_invalid_user_key_rejected(self, client):
        test_client, _ = client
        _create(test_client)
        bad = test_client.post(
            "/api/v1/hub/runs",
            json={"user_key": "short", "model_id": "m", "inputs": {}, "outputs": {}},
        )
        assert bad.status_code == 422

    def test_oversized_payload_rejected(self, client):
        test_client, _ = client
        big = {"data": "x" * 9000}
        response = test_client.post(
            "/api/v1/hub/runs",
            json={"user_key": USER, "model_id": "m", "inputs": big, "outputs": {}},
        )
        assert response.status_code == 422

    def test_share_of_foreign_run_is_404(self, client):
        test_client, _ = client
        _create(test_client)
        response = test_client.post(
            "/api/v1/hub/runs/does-not-exist/share",
            params={"user_key": USER},
            json={"shared": True},
        )
        assert response.status_code == 404
