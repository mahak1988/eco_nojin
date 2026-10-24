"""Tests for the notification service.

The service is a thin wrapper over the notification tables; the contract it
pins is the *shape* of the API the gateway consumes.
"""

import pytest

from services.notification.service import NotificationService


class TestHealth:
    """Tests for the health check."""

    def test_the_service_reports_healthy(self):
        assert NotificationService().health() == "ok"

    def test_the_service_constructs_without_a_session(self):
        """The gateway imports the service before a session exists."""
        service = NotificationService()
        assert service.db is None
        assert service.session is None

    def test_the_service_keeps_the_session_it_was_given(self):
        session = object()
        assert NotificationService(db=session).db is session
        assert NotificationService(session=session).session is session


class TestGatewaySchema:
    """The gateway's notification payload."""

    def test_a_notification_can_be_created(self):
        from services.notification.main import NotificationCreate

        notification = NotificationCreate(
            user_id="user-1",
            channel="in_app",
            message="A message",
        )
        assert notification.user_id == "user-1"
        assert notification.channel == "in_app"
        assert notification.subject is None
        assert notification.metadata is None


class TestDbService:
    """Tests for the database-backed service."""

    @pytest.fixture
    def service(self, sync_db_session):
        from services.notification.db_service import NotificationDbService

        return NotificationDbService(sync_db_session)

    def test_the_service_constructs(self, service):
        assert service is not None

    def test_creating_a_notification_returns_it(self, service):
        created = service.notify("user-1", "Hello", body="A message")
        assert created is not None
        assert created.title == "Hello"
        assert created.is_read is False

    def test_a_notification_can_be_listed_for_a_user(self, service):
        service.notify("user-1", "Hello", body="A message")
        assert len(service.list_for("user-1")) == 1

    def test_another_users_notifications_are_not_listed(self, service):
        service.notify("user-1", "Hello", body="A message")
        assert service.list_for("user-2") == []

    def test_the_unread_filter_works(self, service):
        notification = service.notify("user-1", "Hello", body="A message")
        assert len(service.list_for("user-1", unread_only=True)) == 1
        service.mark_read(notification.id, user_id="user-1")
        assert service.list_for("user-1", unread_only=True) == []

    def test_the_limit_is_respected(self, service):
        for i in range(5):
            service.notify("user-1", f"Hello {i}")
        assert len(service.list_for("user-1", limit=2)) == 2

    def test_marking_a_notification_read(self, service):
        created = service.notify("user-1", "Hello", body="A message")
        updated = service.mark_read(created.id, user_id="user-1")
        assert updated.is_read is True

    def test_another_user_cannot_mark_it_read(self, service):
        created = service.notify("user-1", "Hello", body="A message")
        with pytest.raises(LookupError):
            service.mark_read(created.id, user_id="user-2")

    def test_an_unknown_notification_type_is_refused(self, service):
        with pytest.raises(ValueError, match="unknown notification type"):
            service.notify("user-1", "Hello", ntype="not-a-type")

    def test_a_notification_without_a_user_is_refused(self, service):
        with pytest.raises(ValueError, match="user_id is required"):
            service.notify("", "Hello")
