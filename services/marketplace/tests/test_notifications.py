"""Tests for in-app notifications (plan v2.2)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import services.notification.models_db  # noqa: F401
from database.base import Base
from services.notification.db_service import NotificationDbService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_notify_and_list(db_session):
    svc = NotificationDbService(db_session)
    svc.notify("u-1", "پرداخت تأیید شد", ntype="payment")
    svc.notify("u-1", "شکایت جدید", ntype="dispute")
    svc.notify("u-2", "for other user", ntype="system")
    items = svc.list_for("u-1")
    assert len(items) == 2
    assert all(n.user_id == "u-1" for n in items)


def test_mark_read_owner_scoped(db_session):
    svc = NotificationDbService(db_session)
    n = svc.notify("u-1", "hello", ntype="system")
    with pytest.raises(LookupError):
        svc.mark_read(n.id, "u-2")
    out = svc.mark_read(n.id, "u-1")
    assert out.is_read is True
    assert len(svc.list_for("u-1", unread_only=True)) == 0


def test_invalid_type_rejected(db_session):
    with pytest.raises(ValueError):
        NotificationDbService(db_session).notify("u-1", "x", ntype="bogus")
