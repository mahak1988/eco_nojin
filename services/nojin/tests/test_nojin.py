"""Tests for the Nojin biofertilizer service.

The Nojin repository is a **stub**: it returns empty catalogues because the
``NojinMaterial`` / ``NojinSoilType`` / ``NojinFormulationRecipe`` records are
plain classes in the gateway facade, not table-backed models. The contract
these tests pin is the *honest* one: the service must refuse rather than
fabricate, and the health check must not claim a healthy catalogue it does
not have.
"""

import pytest

from services.nojin.repository import NojinRepository
from services.nojin.service import NojinService


@pytest.fixture
def service(sync_db_session):
    return NojinService(NojinRepository(sync_db_session))


class TestHealth:
    """Tests for the health check."""

    def test_an_empty_catalogue_is_not_reported_as_healthy(self, service):
        """A reachable database with no catalogue is not a healthy service."""
        health = service.health_check()
        assert health["status"] != "healthy"
        assert health["status"] == "no_data"

    def test_the_database_connection_is_reported(self, service):
        health = service.health_check()
        assert health["database_connected"] is True

    def test_the_catalogue_availability_is_explicit(self, service):
        health = service.health_check()
        assert health["catalogue_available"] is False
        assert health["materials_count"] == 0
        assert health["recipes_count"] == 0


class TestStatistics:
    """Tests for the statistics view."""

    def test_the_statistics_report_the_system_status(self, service):
        stats = service.get_statistics()
        assert "system_status" in stats

    def test_the_statistics_never_claim_a_catalogue(self, service):
        stats = service.get_statistics()
        assert stats["materials_count"] == 0
        assert stats["recipes_count"] == 0


class TestHonestRefusal:
    """The data endpoints must refuse rather than return an empty success.

    An empty list is a success-shaped answer that a caller would read as
    "there are no materials", which is a different claim from "the catalogue
    is not loaded". The router turns this refusal into a 503.
    """

    def test_listing_materials_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.list_materials()

    def test_getting_a_material_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.get_material("MIN-011")

    def test_listing_the_arid_priority_materials_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.get_arid_priority_materials()

    def test_listing_soil_types_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.list_soil_types()

    def test_getting_a_soil_type_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.get_soil_type("LOAM")

    def test_listing_recipes_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.list_recipes()

    def test_getting_a_recipe_refuses(self, service):
        with pytest.raises(RuntimeError, match="not available"):
            service.get_recipe("REC-001")


class TestRepository:
    """The repository is a stub; these tests keep that explicit."""

    def test_the_repository_returns_no_materials(self, sync_db_session):
        repo = NojinRepository(sync_db_session)
        assert repo.list_materials() == []

    def test_the_repository_returns_no_recipes(self, sync_db_session):
        repo = NojinRepository(sync_db_session)
        assert repo.list_recipes() == []

    def test_the_repository_finds_nothing_by_code(self, sync_db_session):
        repo = NojinRepository(sync_db_session)
        assert repo.get_material_by_code("MIN-011") is None
        assert repo.get_soil_type_by_code("LOAM") is None
        assert repo.get_recipe_by_code("REC-001") is None
