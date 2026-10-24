"""Tests for the field-monitoring ingestion service."""

from datetime import UTC, datetime

from services.field_monitoring.service import (
    FieldDataType,
    FieldMonitoringReport,
    FieldMonitoringService,
)


def _report(**overrides):
    payload = {
        "project_id": "proj-1",
        "location": {"lat": 35.0, "lon": 51.0},
        "report_date": datetime.now(UTC),
        "data_type": FieldDataType.SOIL_MOISTURE,
        "data_payload": {"value": 22.5},
        "reporter_id": "sensor-1",
    }
    payload.update(overrides)
    return FieldMonitoringReport(**payload)


class TestValidation:
    """Tests for the report validation."""

    def test_a_well_formed_report_is_valid(self):
        service = FieldMonitoringService()
        assert service._validate_report(_report()) is True

    def test_a_missing_location_is_refused(self):
        service = FieldMonitoringService()
        assert service._validate_report(_report(location=None)) is False

    def test_a_location_without_a_latitude_is_refused(self):
        service = FieldMonitoringService()
        assert service._validate_report(_report(location={"lon": 51.0})) is False

    def test_a_location_that_is_not_a_mapping_is_refused(self):
        service = FieldMonitoringService()
        assert service._validate_report(_report(location="35,51")) is False

    def test_a_missing_payload_is_refused(self):
        service = FieldMonitoringService()
        assert service._validate_report(_report(data_payload=None)) is False


class TestQualityScoring:
    """Tests for the quality-flag mapping."""

    def test_the_ok_flag_scores_full(self):
        service = FieldMonitoringService()
        assert service._score_quality("ok") == 1.0

    def test_a_suspect_flag_scores_lower(self):
        service = FieldMonitoringService()
        assert service._score_quality("suspect") < 1.0

    def test_an_error_flag_scores_zero(self):
        service = FieldMonitoringService()
        assert service._score_quality("error") == 0.0

    def test_an_unknown_flag_is_not_treated_as_good_data(self):
        """An unrecognised flag must not score as good data.

        It is scored like a *suspect* sample (0.5), which is the honest
        reading: the quality is unknown, so it is neither trusted nor
        declared an error.
        """
        service = FieldMonitoringService()
        assert service._score_quality("something-else") == 0.5
        assert service._score_quality("something-else") < 1.0


class TestIngestion:
    """Tests for the ingestion path."""

    def test_an_invalid_report_is_not_stored(self):
        """A report that fails validation must be refused, not persisted."""
        service = FieldMonitoringService()
        assert service.ingest_report(_report(location=None)) is False

    def test_a_valid_report_is_stored(self, monkeypatch):
        """A valid report reaches the database and is committed."""
        import services.field_monitoring.service as module

        added = {}

        class FakeDb:
            def add(self, entry):
                added["entry"] = entry

            def commit(self):
                added["committed"] = True

            def rollback(self):
                added["rolled_back"] = True

            def close(self):
                added["closed"] = True

        monkeypatch.setattr(module, "SessionLocal", lambda: FakeDb())

        service = FieldMonitoringService()
        assert service.ingest_report(_report()) is True
        assert added["committed"] is True
        assert added["entry"].project_id == "proj-1"

    def test_a_store_failure_is_reported_as_false(self, monkeypatch):
        """A database failure must not propagate as an exception."""
        import services.field_monitoring.service as module

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

        service = FieldMonitoringService()
        assert service.ingest_report(_report()) is False

    def test_a_session_failure_does_not_mask_the_error(self, monkeypatch):
        """The failure path must not raise ``UnboundLocalError`` on ``db``.

        ``db`` was assigned inside the ``try``, so a failure in
        ``SessionLocal()`` made the ``except`` block raise a *different*
        error and hide the real cause.
        """
        import services.field_monitoring.service as module

        def boom():
            raise RuntimeError("cannot open a session")

        monkeypatch.setattr(module, "SessionLocal", boom)

        service = FieldMonitoringService()
        # Must return False, not raise UnboundLocalError.
        assert service.ingest_report(_report()) is False
