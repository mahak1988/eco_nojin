"""Tests for the mobile-monitoring ingestion service."""

from datetime import UTC, datetime

import pytest

from services.mobile_monitoring.service import (
    MobileMonitoringReport,
    MobileMonitoringService,
    MobileReportType,
)


def _report(**overrides):
    payload = {
        "project_id": "proj-1",
        "location": {"lat": 35.0, "lon": 51.0},
        "report_timestamp": datetime.now(UTC),
        "report_type": MobileReportType.CITIZEN_REPORT,
        "user_id": "user-1",
        "photo_urls": [],
        "text_description": "A general observation",
        "geo_verification_confirmed": True,
        "quality_flag": "ok",
    }
    payload.update(overrides)
    return MobileMonitoringReport(**payload)


class TestReportTypes:
    """Tests for the report-type vocabulary."""

    def test_every_type_has_a_value(self):
        for report_type in MobileReportType:
            assert report_type.value

    def test_the_photo_types_are_distinguishable(self):
        photo_types = {
            MobileReportType.CROP_CONDITION_PHOTO,
            MobileReportType.SOIL_CONDITION_PHOTO,
            MobileReportType.WATER_SOURCE_PHOTO,
            MobileReportType.INFRASTRUCTURE_PHOTO,
        }
        assert len(photo_types) == 4


class TestValidation:
    """Tests for the report validation."""

    @pytest.fixture
    def service(self):
        return MobileMonitoringService()

    def test_a_well_formed_report_is_valid(self, service):
        assert service._validate_report(_report()) is True

    def test_a_report_without_a_location_is_refused(self, service):
        assert service._validate_report(_report(location=None)) is False

    def test_a_location_without_a_latitude_is_refused(self, service):
        assert service._validate_report(_report(location={"lon": 51.0})) is False

    def test_a_location_that_is_not_a_mapping_is_refused(self, service):
        assert service._validate_report(_report(location="35,51")) is False

    def test_a_report_without_a_user_is_refused(self, service):
        assert service._validate_report(_report(user_id="")) is False

    def test_a_photo_type_needs_a_photo(self, service):
        """A photo report without a photo is not a photo report."""
        assert (
            service._validate_report(
                _report(report_type=MobileReportType.CROP_CONDITION_PHOTO, photo_urls=[])
            )
            is False
        )

    def test_a_photo_type_with_a_photo_is_valid(self, service):
        assert (
            service._validate_report(
                _report(
                    report_type=MobileReportType.CROP_CONDITION_PHOTO,
                    photo_urls=["https://example.com/p.jpg"],
                )
            )
            is True
        )

    def test_a_general_report_needs_no_photo(self, service):
        assert (
            service._validate_report(
                _report(report_type=MobileReportType.CITIZEN_REPORT, photo_urls=[])
            )
            is True
        )


class TestQualityScoring:
    """Tests for the quality-flag scoring."""

    @pytest.fixture
    def service(self):
        return MobileMonitoringService()

    def test_an_ok_report_scores_full_when_verified(self, service):
        assert service._score_quality("ok", True) == 1.0

    def test_a_suspect_report_scores_lower(self, service):
        assert service._score_quality("suspect", True) < 1.0

    def test_an_unverified_report_scores_lower_still(self, service):
        assert service._score_quality("unverified", True) < service._score_quality(
            "suspect", True
        )

    def test_a_missing_location_lowers_the_score(self, service):
        """A report whose location was not confirmed is weaker evidence.

        The geo bonus only raises a sub-full score, so the effect is visible
        on a flag that is not already at 1.0.
        """
        confirmed = service._score_quality("suspect", True)
        unconfirmed = service._score_quality("suspect", False)
        assert unconfirmed < confirmed

    def test_an_ok_report_is_full_either_way(self, service):
        """An ``ok`` report is good evidence whether or not the geo was locked."""
        assert service._score_quality("ok", True) == 1.0
        assert service._score_quality("ok", False) == 1.0

    def test_the_score_never_exceeds_one(self, service):
        for flag in ("ok", "suspect", "unverified", "something-else"):
            for geo in (True, False):
                assert service._score_quality(flag, geo) <= 1.0

    def test_an_unknown_flag_is_not_treated_as_good_data(self, service):
        assert service._score_quality("something-else", True) < 1.0


class TestProcessing:
    """Tests for the data processing step."""

    @pytest.fixture
    def service(self):
        return MobileMonitoringService()

    def test_the_photo_urls_are_hashed(self, service):
        """Photo URLs are hashed so the raw URL is not the stored identity."""
        processed = service._process_data(
            _report(photo_urls=["https://example.com/a.jpg"])
        )
        assert len(processed["photo_hashes"]) == 1
        assert len(processed["photo_hashes"][0]) == 64

    def test_the_hash_is_stable(self, service):
        report = _report(photo_urls=["https://example.com/a.jpg"])
        first = service._process_data(report)["photo_hashes"][0]
        second = service._process_data(report)["photo_hashes"][0]
        assert first == second

    def test_the_submitter_is_recorded(self, service):
        processed = service._process_data(_report(user_id="user-7"))
        assert processed["submitted_by_user_id"] == "user-7"


class TestIngestion:
    """Tests for the ingestion path."""

    @pytest.fixture
    def service(self):
        return MobileMonitoringService()

    def test_an_invalid_report_is_not_stored(self, service, monkeypatch):
        import services.mobile_monitoring.service as module

        added = {}

        class FakeDb:
            def add(self, entry):
                added["entry"] = entry

            def commit(self):
                added["committed"] = True

            def rollback(self):
                added["rolled_back"] = True

            def close(self):
                pass

        monkeypatch.setattr(module, "SessionLocal", lambda: FakeDb())
        assert service.ingest_report(_report(location=None)) is False
        assert "entry" not in added

    def test_a_valid_report_is_stored(self, service, monkeypatch):
        import services.mobile_monitoring.service as module

        added = {}

        class FakeDb:
            def add(self, entry):
                added["entry"] = entry

            def commit(self):
                added["committed"] = True

            def rollback(self):
                added["rolled_back"] = True

            def close(self):
                pass

        monkeypatch.setattr(module, "SessionLocal", lambda: FakeDb())
        assert service.ingest_report(_report()) is True
        assert added["committed"] is True
        assert added["entry"].project_id == "proj-1"

    def test_a_store_failure_is_reported_as_false(self, service, monkeypatch):
        """A database failure must not propagate as an exception."""
        import services.mobile_monitoring.service as module

        class BrokenDb:
            def add(self, entry):
                raise RuntimeError("database is down")

            def commit(self):
                pass

            def rollback(self):
                pass

            def close(self):
                pass

        monkeypatch.setattr(module, "SessionLocal", lambda: BrokenDb())
        assert service.ingest_report(_report()) is False

    def test_a_session_failure_does_not_mask_the_error(self, service, monkeypatch):
        """The failure path must not raise ``UnboundLocalError`` on ``db``.

        ``db`` was assigned inside the ``try``, so a failure in
        ``SessionLocal()`` made the ``except`` block raise a *different*
        error and hide the real cause.
        """
        import services.mobile_monitoring.service as module

        def boom():
            raise RuntimeError("cannot open a session")

        monkeypatch.setattr(module, "SessionLocal", boom)
        # Must return False, not raise UnboundLocalError.
        assert service.ingest_report(_report()) is False
