"""Tests for the public contact endpoint (isolated in-memory database)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import ContactMessage  # noqa: F401 — registers the model
from services.api_gateway.routers import contact


VALID_PAYLOAD = {
    "name": "Hassan Sadeghi",
    "email": "hassan@example.com",
    "role": "Researcher",
    "message": "We would like to join the pilot program this season.",
    "locale": "en",
}


@pytest.fixture()
def client():
    # Shared in-memory database: StaticPool keeps one connection for all sessions.
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
    app.include_router(contact.router)
    app.dependency_overrides[contact.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, testing_session


class TestContactEndpoint:
    def test_roundtrip_stores_message(self, client):
        test_client, session_factory = client
        response = test_client.post("/api/v1/contact", json=VALID_PAYLOAD)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["id"]
        with session_factory() as session:
            stored = session.query(ContactMessage).filter_by(email="hassan@example.com").one()
            assert stored.name == "Hassan Sadeghi"
            assert stored.role == "Researcher"

    def test_invalid_email_rejected(self, client):
        test_client, _ = client
        payload = dict(VALID_PAYLOAD, email="not-an-email")
        response = test_client.post("/api/v1/contact", json=payload)
        assert response.status_code == 422

    def test_short_message_rejected(self, client):
        test_client, _ = client
        payload = dict(VALID_PAYLOAD, message="hi")
        response = test_client.post("/api/v1/contact", json=payload)
        assert response.status_code == 422

    def test_blank_name_rejected(self, client):
        test_client, _ = client
        payload = dict(VALID_PAYLOAD, name="   ")
        response = test_client.post("/api/v1/contact", json=payload)
        assert response.status_code == 422

    def test_honeypot_accepts_but_stores_nothing(self, client):
        test_client, session_factory = client
        payload = dict(VALID_PAYLOAD, website="http://spam.example")
        response = test_client.post("/api/v1/contact", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True
        with session_factory() as session:
            assert session.query(ContactMessage).count() == 0

    def test_email_is_normalized(self, client):
        test_client, session_factory = client
        payload = dict(VALID_PAYLOAD, email="  User+Tag@Example.COM ")
        response = test_client.post("/api/v1/contact", json=payload)
        assert response.status_code == 200
        with session_factory() as session:
            stored = session.query(ContactMessage).first()
            assert stored.email == "user+tag@example.com"
