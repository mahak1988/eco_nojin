"""Tests for the quality-assurance inspection service."""

import pytest

from services.quality_assurance.service import PASS_THRESHOLD, QualityService


@pytest.fixture
def service(sync_db_session):
    return QualityService(sync_db_session)


class TestCreateInspection:
    """Tests for creating an inspection."""

    def test_a_harvest_inspection_is_created(self, service):
        insp = service.create_inspection("product-1", "harvest")
        assert insp.id is not None
        assert insp.product_id == "product-1"
        assert insp.inspection_type == "harvest"
        assert insp.status == "pending"

    def test_every_documented_type_is_accepted(self, service):
        for inspection_type in ("harvest", "packaging", "delivery"):
            insp = service.create_inspection(f"p-{inspection_type}", inspection_type)
            assert insp.inspection_type == inspection_type

    def test_an_unknown_type_is_refused(self, service):
        with pytest.raises(ValueError, match="unknown inspection type"):
            service.create_inspection("product-1", "not-a-type")

    def test_the_inspector_is_recorded(self, service):
        insp = service.create_inspection("product-1", "harvest", inspector_id="u-1")
        assert insp.inspector_id == "u-1"


class TestRecordResult:
    """Tests for recording an inspection result."""

    def _inspection(self, service, product_id="product-1"):
        return service.create_inspection(product_id, "harvest")

    def test_a_high_score_passes(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=95.0)
        assert result["inspection"].status == "passed"

    def test_a_low_score_fails(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=10.0)
        assert result["inspection"].status == "failed"

    def test_the_threshold_decides_the_outcome(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=float(PASS_THRESHOLD))
        assert result["inspection"].status == "passed"

    def test_a_score_above_the_range_is_refused(self, service):
        insp = self._inspection(service)
        with pytest.raises(ValueError, match=r"\[0, 100\]"):
            service.record_result(insp.id, score=101.0)

    def test_a_negative_score_is_refused(self, service):
        insp = self._inspection(service)
        with pytest.raises(ValueError, match=r"\[0, 100\]"):
            service.record_result(insp.id, score=-1.0)

    def test_a_missing_inspection_raises(self, service):
        with pytest.raises(LookupError):
            service.record_result("no-such-inspection", score=50.0)

    def test_the_notes_are_recorded(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=80.0, notes="looks good")
        assert result["inspection"].notes == "looks good"

    def test_a_passing_inspection_above_the_certificate_bar_gets_a_certificate(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=95.0)
        assert result["certificate_id"] is not None

    def test_a_failing_inspection_gets_no_certificate(self, service):
        insp = self._inspection(service)
        result = service.record_result(insp.id, score=10.0)
        assert result["certificate_id"] is None


class TestListing:
    """Tests for the listing helpers."""

    def test_a_new_inspection_is_listed(self, service):
        service.create_inspection("product-1", "harvest")
        listed = service.list()
        assert len(listed) == 1

    def test_the_list_can_be_filtered_by_product(self, service):
        service.create_inspection("product-1", "harvest")
        service.create_inspection("product-2", "harvest")
        assert len(service.list(product_id="product-1")) == 1

    def test_an_unknown_inspection_raises(self, service):
        with pytest.raises(LookupError):
            service.get("no-such-inspection")
