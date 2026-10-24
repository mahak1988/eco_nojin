"""Tests for the legal-text service (slugs, locales, versions)."""

import pytest

from services.legal.service import VALID_SLUGS, LegalTextService


@pytest.fixture
def service(sync_db_session):
    return LegalTextService(sync_db_session)


def _payload(**overrides):
    payload = {
        "locale": "fa",
        "slug": "terms",
        "title": "شرایط استفاده",
        "body": "متن",
    }
    payload.update(overrides)
    return payload


class TestSlugValidation:
    """Tests for the slug contract."""

    def test_a_valid_slug_is_accepted(self):
        assert LegalTextService.validate_slug("terms") == "terms"

    def test_every_documented_slug_is_valid(self):
        for slug in VALID_SLUGS:
            assert LegalTextService.validate_slug(slug) == slug

    def test_an_unknown_slug_is_refused(self):
        with pytest.raises(ValueError, match="Invalid slug"):
            LegalTextService.validate_slug("not-a-real-slug")

    def test_a_path_traversal_slug_is_refused(self):
        with pytest.raises(ValueError, match="Invalid slug"):
            LegalTextService.validate_slug("../../etc/passwd")

    def test_an_empty_slug_is_refused(self):
        with pytest.raises(ValueError, match="Invalid slug"):
            LegalTextService.validate_slug("")


class TestLegalListing:
    """Tests for the listing helpers."""

    def test_an_empty_registry_lists_nothing(self, service):
        assert service.list() == []
        assert service.list_slugs() == []

    def test_a_created_document_is_listed(self, service):
        service.create(_payload())
        listed = service.list()
        assert listed
        assert listed[0]["slug"] == "terms"
        assert listed[0]["locale"] == "fa"

    def test_the_slug_is_listed(self, service):
        service.create(_payload())
        assert "terms" in service.list_slugs()

    def test_the_versions_are_listed(self, service):
        service.create(_payload())
        service.create(_payload())
        versions = service.list_versions("fa", "terms")
        assert len(versions) == 2
        assert versions[0]["version"] == 2

    def test_an_unknown_slug_has_no_versions(self, service):
        """An unknown slug is an invalid slug, not a missing document."""
        with pytest.raises(ValueError, match="Invalid slug"):
            service.list_versions("fa", "not-a-real-slug")

    def test_a_missing_document_raises(self, service):
        with pytest.raises(LookupError):
            service.get("fa", "terms")

    def test_a_created_document_can_be_read_back(self, service):
        service.create(_payload())
        found = service.get("fa", "terms")
        assert found["slug"] == "terms"
        assert found["title"] == "شرایط استفاده"


class TestVersioning:
    """Tests for the version rules."""

    def test_the_first_version_is_one(self, service):
        created = service.create(_payload())
        assert created["version"] == 1

    def test_the_version_increments(self, service):
        service.create(_payload())
        second = service.create(_payload())
        assert second["version"] == 2

    def test_an_explicit_version_is_refused_when_it_exists(self, service):
        service.create(_payload(version=1))
        with pytest.raises(ValueError, match="already exists"):
            service.create(_payload(version=1))

    def test_an_explicit_version_is_accepted_when_it_is_free(self, service):
        created = service.create(_payload(version=7))
        assert created["version"] == 7

    def test_an_unknown_slug_cannot_be_created(self, service):
        with pytest.raises(ValueError, match="Invalid slug"):
            service.create(_payload(slug="not-a-real-slug"))
