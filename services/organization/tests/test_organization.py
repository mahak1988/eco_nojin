"""Tests for the organization service (tenancy + membership roles)."""

import pytest

from services.organization.service import OrganizationService


@pytest.fixture
def service(sync_db_session):
    return OrganizationService(sync_db_session)


def _create(service, slug="acme", user_id="owner-1"):
    return service.create_organization(
        slug=slug,
        name="Acme Ltd",
        country="IR",
        description="A test organization",
        user_id=user_id,
    )


class TestCreateOrganization:
    """Tests for creating an organization."""

    def test_an_organization_is_created(self, service):
        org = _create(service)
        assert org["slug"] == "acme"
        assert org["name"] == "Acme Ltd"
        assert org["country"] == "IR"

    def test_the_creator_becomes_an_admin_member(self, service):
        _create(service)
        listed = service.list_organizations("owner-1")
        assert len(listed) == 1
        assert listed[0]["role"] == "admin"

    def test_a_duplicate_slug_is_refused(self, service):
        _create(service)
        with pytest.raises(ValueError, match="slug already exists"):
            _create(service)


class TestScoping:
    """Tests that an organization is scoped to its members."""

    def test_a_stranger_sees_nothing(self, service):
        _create(service)
        assert service.list_organizations("stranger") == []

    def test_a_stranger_cannot_read_the_organization(self, service):
        org = _create(service)
        with pytest.raises(LookupError):
            service.get_organization(org["id"], "stranger")

    def test_a_member_sees_their_role(self, service):
        org = _create(service)
        found = service.get_organization(org["id"], "owner-1")
        assert found["user_role"] == "admin"

    def test_an_unknown_organization_raises(self, service):
        with pytest.raises(LookupError):
            service.get_organization("no-such-org", "owner-1")


class TestInvitations:
    """Tests for inviting and removing members."""

    def test_an_admin_can_invite(self, service):
        org = _create(service)
        member = service.invite_member(
            org["id"], slug_email="member@acme.io", role="member", user_id="owner-1"
        )
        assert member["role"] == "member"

    def test_a_non_admin_cannot_invite(self, service):
        org = _create(service)
        service.invite_member(
            org["id"], slug_email="member@acme.io", role="member", user_id="owner-1"
        )
        with pytest.raises(PermissionError, match="Only admins"):
            service.invite_member(
                org["id"], slug_email="other@acme.io", role="member", user_id="someone-else"
            )

    def test_a_stranger_cannot_invite(self, service):
        org = _create(service)
        with pytest.raises(PermissionError):
            service.invite_member(
                org["id"], slug_email="x@acme.io", role="member", user_id="stranger"
            )

    def test_a_member_can_be_removed(self, service):
        org = _create(service)
        member = service.invite_member(
            org["id"], slug_email="member@acme.io", role="member", user_id="owner-1"
        )
        service.remove_member(org["id"], member["id"], user_id="owner-1")
        assert service.list_organizations("member@acme.io") == []
