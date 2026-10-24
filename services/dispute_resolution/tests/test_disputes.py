"""Tests for the dispute-resolution lifecycle."""

import pytest

from services.dispute_resolution.models import Dispute, DisputeEvent
from services.dispute_resolution.service import DisputeService


@pytest.fixture
def service(sync_db_session):
    """The dispute service runs on a *sync* session (see routers/disputes.py)."""
    return DisputeService(sync_db_session)


def _open(service, **overrides):
    payload = {
        "order_id": "order-1",
        "complainant_id": "buyer-1",
        "category": "quality",
        "description": "The goods did not match the description.",
    }
    payload.update(overrides)
    return service.create(**payload)


class TestDisputeModels:
    """Tests for the dispute models."""

    def test_dispute_defaults(self):
        dispute = Dispute(
            order_id="o-1",
            complainant_id="c-1",
            category="quality",
            description="d",
        )
        # Column defaults are applied at flush time, not at construction.
        assert dispute.status is None or dispute.status == "open"
        assert dispute.is_active in (None, True)

    def test_dispute_status_default_is_open(self, sync_db_session):
        """A persisted dispute starts open."""
        from services.dispute_resolution.models import Dispute as D

        d = D(
            order_id="o-2",
            complainant_id="c-2",
            category="quality",
            description="d",
        )
        sync_db_session.add(d)
        sync_db_session.commit()
        sync_db_session.refresh(d)
        assert d.status == "open"
        assert d.is_active is True

    def test_dispute_event_defaults(self):
        event = DisputeEvent(dispute_id="d-1", event="opened", actor="c-1")
        assert event.event == "opened"


class TestDisputeCreation:
    """Tests for creating a dispute."""

    def test_create_returns_an_open_dispute(self, service):
        dispute = _open(service)
        assert dispute.id is not None
        assert dispute.status == "open"
        assert dispute.category == "quality"

    def test_create_records_an_opened_event(self, service):
        dispute = _open(service)
        events = service.events(dispute.id)
        assert any(e.event == "opened" for e in events)

    def test_create_accepts_every_documented_category(self, service):
        for category in ("quality", "delivery", "payment", "other"):
            dispute = _open(service, category=category, order_id=f"o-{category}")
            assert dispute.category == category

    def test_create_rejects_an_unknown_category(self, service):
        with pytest.raises(ValueError, match="unknown category"):
            _open(service, category="not-a-category")

    def test_get_missing_dispute_raises(self, service):
        with pytest.raises(LookupError):
            service.get("no-such-dispute")


class TestDisputeEvents:
    """Tests for adding events to a dispute."""

    def test_comment_moves_the_dispute_under_review(self, service):
        dispute = _open(service)
        service.add_event(dispute.id, "comment", actor="buyer-1", note="More detail")
        assert service.get(dispute.id).status == "under_review"

    def test_evidence_moves_the_dispute_under_review(self, service):
        dispute = _open(service)
        service.add_event(dispute.id, "evidence", actor="buyer-1")
        assert service.get(dispute.id).status == "under_review"

    def test_other_events_do_not_change_the_status(self, service):
        dispute = _open(service)
        service.add_event(dispute.id, "note", actor="buyer-1")
        assert service.get(dispute.id).status == "open"

    def test_events_are_recorded(self, service):
        dispute = _open(service)
        service.add_event(dispute.id, "comment", actor="buyer-1", note="x")
        events = service.events(dispute.id)
        assert any(e.event == "comment" for e in events)


class TestDisputeResolution:
    """Tests for resolving and rejecting a dispute."""

    def test_resolve_closes_the_dispute(self, service):
        dispute = _open(service)
        resolved = service.resolve(dispute.id, resolved_by="mod-1", resolution="Refund issued")
        assert resolved.status == "resolved"
        assert resolved.resolution == "Refund issued"
        assert resolved.resolved_by == "mod-1"

    def test_reject_closes_the_dispute(self, service):
        dispute = _open(service)
        rejected = service.resolve(
            dispute.id, resolved_by="mod-1", resolution="No violation", outcome="rejected"
        )
        assert rejected.status == "rejected"

    def test_resolve_rejects_an_invalid_outcome(self, service):
        dispute = _open(service)
        with pytest.raises(ValueError, match="invalid outcome"):
            service.resolve(
                dispute.id, resolved_by="mod-1", resolution="x", outcome="escalated"
            )

    def test_a_closed_dispute_cannot_be_resolved_twice(self, service):
        dispute = _open(service)
        service.resolve(dispute.id, resolved_by="mod-1", resolution="Done")
        with pytest.raises(ValueError, match="already closed"):
            service.resolve(dispute.id, resolved_by="mod-1", resolution="Again")

    def test_a_closed_dispute_rejects_new_events(self, service):
        dispute = _open(service)
        service.resolve(dispute.id, resolved_by="mod-1", resolution="Done")
        with pytest.raises(ValueError, match="dispute is closed"):
            service.add_event(dispute.id, "comment", actor="buyer-1")


class TestDisputeListing:
    """Tests for listing disputes."""

    def test_list_returns_disputes(self, service):
        _open(service)
        disputes = service.list()
        assert len(disputes) >= 1

    def test_list_filters_by_status(self, service):
        dispute = _open(service)
        service.resolve(dispute.id, resolved_by="mod-1", resolution="Done")
        resolved = service.list(status="resolved")
        assert all(d.status == "resolved" for d in resolved)
        assert len(resolved) >= 1

    def test_list_respects_the_limit(self, service):
        for i in range(3):
            _open(service, order_id=f"o-{i}")
        assert len(service.list(limit=2)) <= 2
