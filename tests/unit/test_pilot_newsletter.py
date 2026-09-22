"""Tests for the public pilot and newsletter endpoints (isolated DB)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import (  # noqa: F401 — registers the models
    NewsletterSubscriber,
    PilotApplication,
)
from services.api_gateway.routers import newsletter, pilot


@pytest.fixture()
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
    app.include_router(pilot.router)
    app.include_router(newsletter.router)
    app.dependency_overrides[pilot.get_db] = override_get_db
    app.dependency_overrides[newsletter.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, testing_session


VALID_PILOT = {
    "name": "Ali Rezaei",
    "phone": "09121234567",
    "province": "Khuzestan",
    "land_hectares": 4.5,
    "main_crop": "wheat",
    "preferred_channel": "USSD",
    "consent": True,
    "locale": "en",
}


class TestPilotEndpoint:
    def test_roundtrip(self, client):
        test_client, session_factory = client
        response = test_client.post("/api/v1/pilot/apply", json=VALID_PILOT)
        assert response.status_code == 200
        assert response.json()["ok"] is True
        with session_factory() as session:
            stored = session.query(PilotApplication).filter_by(phone="09121234567").one()
            assert stored.province == "Khuzestan"
            assert stored.consent is True

    def test_consent_required(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/pilot/apply", json=dict(VALID_PILOT, consent=False))
        assert response.status_code == 422

    def test_blank_province_rejected(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/pilot/apply", json=dict(VALID_PILOT, province="  "))
        assert response.status_code == 422

    def test_negative_hectares_rejected(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/pilot/apply", json=dict(VALID_PILOT, land_hectares=-1))
        assert response.status_code == 422


class TestNewsletterEndpoint:
    def test_subscribe_roundtrip(self, client):
        test_client, session_factory = client
        response = test_client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "Reader@Example.COM", "locale": "fa"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True, "already": False}
        with session_factory() as session:
            stored = session.query(NewsletterSubscriber).one()
            assert stored.email == "reader@example.com"

    def test_duplicate_subscribe_is_graceful(self, client):
        test_client, session_factory = client
        payload = {"email": "dup@example.com", "locale": "en"}
        first = test_client.post("/api/v1/newsletter/subscribe", json=payload)
        second = test_client.post("/api/v1/newsletter/subscribe", json=payload)
        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json() == {"ok": True, "already": True}
        with session_factory() as session:
            assert session.query(NewsletterSubscriber).count() == 1

    def test_invalid_email_rejected(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/newsletter/subscribe", json={"email": "broken"})
        assert response.status_code == 422
