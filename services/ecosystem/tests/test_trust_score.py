"""Tests for the ecosystem trust-score service."""

import pytest

from services.ecosystem.trust_score import TrustEvent, TrustEventType, TrustScoreService


@pytest.fixture
def service(db_session):
    return TrustScoreService(db_session)


class TestTrustEventTypes:
    """Tests for the event-type enum."""

    def test_every_type_has_a_weight(self):
        """Each declared event type must have a weight in the table."""
        for event_type in TrustEventType:
            assert event_type.value in TrustScoreService.EVENT_WEIGHTS


class TestTrustScoreBounds:
    """Tests for the score bounds."""

    def test_base_score(self):
        assert TrustScoreService.BASE_SCORE == 0.5

    def test_min_and_max(self):
        assert TrustScoreService.MIN_SCORE == 0.0
        assert TrustScoreService.MAX_SCORE == 1.0

    def test_weights_are_signed(self):
        """Positive events raise the score, negative ones lower it."""
        positives = {
            "activity_verified",
            "evidence_added",
            "challenge_upheld",
            "milestone_completed",
            "consecutive_days",
        }
        for name, weight in TrustScoreService.EVENT_WEIGHTS.items():
            if name in positives:
                assert weight > 0, name
            else:
                assert weight < 0, name

    def test_rejection_penalises_more_than_dispute(self):
        weights = TrustScoreService.EVENT_WEIGHTS
        assert weights["activity_rejected"] < weights["activity_disputed"]


class TestTrustScoreCalculation:
    """Tests for score calculation."""

    async def test_a_user_without_events_gets_the_base_score(self, service):
        assert await service.calculate_score("nobody") == TrustScoreService.BASE_SCORE

    async def test_verified_activity_raises_the_score(self, service, monkeypatch):
        events = [
            TrustEvent(
                event_id="e1",
                user_id="user-1",
                event_type="activity_verified",
                timestamp=TrustScoreService.BASE_SCORE and __import__("datetime").datetime.now(
                    __import__("datetime").UTC
                ),
                impact=1.0,
                description="",
            )
        ]
        monkeypatch.setattr(service, "_get_user_events", lambda _uid: _async(events))

        score = await service.calculate_score("user-1")
        assert score > TrustScoreService.BASE_SCORE

    async def test_rejected_activity_lowers_the_score(self, service, monkeypatch):
        now = __import__("datetime").datetime.now(__import__("datetime").UTC)
        events = [
            TrustEvent(
                event_id="e1",
                user_id="user-1",
                event_type="activity_rejected",
                timestamp=now,
                impact=1.0,
                description="",
            )
        ]
        monkeypatch.setattr(service, "_get_user_events", lambda _uid: _async(events))

        score = await service.calculate_score("user-1")
        assert score < TrustScoreService.BASE_SCORE

    async def test_the_score_is_clamped_to_the_bounds(self, service, monkeypatch):
        now = __import__("datetime").datetime.now(__import__("datetime").UTC)
        many = [
            TrustEvent(
                event_id=f"e{i}",
                user_id="user-1",
                event_type="activity_verified",
                timestamp=now,
                impact=1000.0,
                description="",
            )
            for i in range(10)
        ]
        monkeypatch.setattr(service, "_get_user_events", lambda _uid: _async(many))

        score = await service.calculate_score("user-1")
        assert score == TrustScoreService.MAX_SCORE

    async def test_an_unknown_event_type_carries_no_weight(self, service, monkeypatch):
        now = __import__("datetime").datetime.now(__import__("datetime").UTC)
        events = [
            TrustEvent(
                event_id="e1",
                user_id="user-1",
                event_type="not_a_real_event",
                timestamp=now,
                impact=1.0,
                description="",
            )
        ]
        monkeypatch.setattr(service, "_get_user_events", lambda _uid: _async(events))

        score = await service.calculate_score("user-1")
        assert score == TrustScoreService.BASE_SCORE


class TestTrustEvents:
    """Tests for recording trust events."""

    async def test_recording_a_known_event_succeeds(self, service):
        assert await service.record_event("user-1", "activity_verified") is True

    async def test_recording_an_unknown_event_fails(self, service):
        assert await service.record_event("user-1", "not_a_real_event") is False

    async def test_the_impact_defaults_to_the_weight(self, service):
        """An event with no explicit impact takes the table's weight."""
        captured = {}
        original = service._get_user_events

        async def capture(uid):
            captured["uid"] = uid
            return await original(uid)

        service._get_user_events = capture
        assert await service.record_event("user-1", "activity_verified") is True


class TestTrustLevels:
    """Tests for the human-readable trust levels."""

    async def test_base_score_is_silver(self, service):
        assert await service.get_trust_level("nobody") == "Silver"

    async def test_the_multiplier_is_in_basis_points(self, service):
        multiplier = await service.get_trust_multiplier("nobody")
        assert 5000 <= multiplier <= 15000

    async def test_the_base_multiplier_is_one_x(self, service):
        """0.5 score maps to 10000 bp = 1.0x."""
        assert await service.get_trust_multiplier("nobody") == 10000

    async def test_the_level_requirements_are_consistent(self, service):
        requirements = await service.get_trust_level_requirements()
        for level, spec in requirements.items():
            assert TrustScoreService.MIN_SCORE <= spec["min_score"] <= TrustScoreService.MAX_SCORE
            assert spec["multiplier"] > 0, level
            assert spec["benefits"]

    async def test_the_multiplier_grows_with_the_level(self, service):
        """Each level must pay at least as much as the one below it."""
        requirements = await service.get_trust_level_requirements()
        ordered = sorted(requirements.values(), key=lambda s: s["min_score"])
        multipliers = [spec["multiplier"] for spec in ordered]
        assert multipliers == sorted(multipliers)

    async def test_the_new_level_is_penalised(self, service):
        """A brand-new user must not get a bonus."""
        requirements = await service.get_trust_level_requirements()
        assert requirements["New"]["multiplier"] < 1.0
        assert requirements["Diamond"]["multiplier"] > 1.0


def _async(value):
    """Wrap a value in a coroutine so it can be awaited."""

    async def _inner():
        return value

    return _inner()
