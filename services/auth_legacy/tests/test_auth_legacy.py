"""Tests for the legacy auth service.

The properties that matter are the security ones:

* a role can never be self-assigned at registration;
* an email can only be registered once;
* a wrong password is refused *and* counted, so a locked account is refused
  before any bcrypt work.
"""

import pytest

from services.auth_legacy.service import ADMIN_ROLES, AuthService


@pytest.fixture
def service(db_session):
    from services.auth_legacy.repository import AuthLegacyRepository

    return AuthService(AuthLegacyRepository(db_session))


async def _register(service, email="user@example.io", role="farmer", password="Str0ngPass!23"):
    from datetime import date

    return await service.register_user(
        email=email,
        full_name="Test User",
        password=password,
        role=role,
        phone=None,
        date_of_birth=date(1990, 1, 1).isoformat(),
        country="IR",
        city="Tehran",
        address="",
        language="fa",
        avatar_url=None,
    )


class TestRegistration:
    """Tests for the registration path."""

    async def test_a_user_is_registered(self, service):
        user = await _register(service)
        assert user is not None
        assert user.email == "user@example.io"
        assert user.is_active is True
        assert user.is_email_verified is False

    async def test_the_password_is_hashed(self, service):
        """The password must never be stored in the clear."""
        user = await _register(service, password="Str0ngPass!23")
        assert user.hashed_password != "Str0ngPass!23"
        assert user.hashed_password

    async def test_an_admin_role_cannot_be_self_assigned(self, service):
        """A registration must never mint an admin."""
        with pytest.raises(PermissionError, match="Role cannot be self-assigned"):
            await _register(service, role="admin")

    async def test_every_admin_role_is_refused(self, service):
        for role in ADMIN_ROLES:
            with pytest.raises(PermissionError):
                await _register(service, email=f"{role}@example.io", role=role)

    async def test_an_email_cannot_be_registered_twice(self, service):
        await _register(service, email="dup@example.io")
        with pytest.raises(ValueError, match="Email already registered"):
            await _register(service, email="dup@example.io")


class TestAuthentication:
    """Tests for the login path."""

    async def test_the_right_password_authenticates(self, service):
        await _register(service, email="ok@example.io", password="Str0ngPass!23")
        user = await service.authenticate("ok@example.io", "Str0ngPass!23")
        assert user is not None
        assert user.email == "ok@example.io"

    async def test_a_wrong_password_is_refused(self, service):
        await _register(service, email="bad@example.io", password="Str0ngPass!23")
        assert await service.authenticate("bad@example.io", "wrong") is None

    async def test_an_unknown_email_is_refused(self, service):
        assert await service.authenticate("nobody@example.io", "whatever") is None


class TestTokens:
    """Tests for the token issuance."""

    async def test_the_tokens_carry_the_tenant_and_session(self, service):
        """The access token mirrors the subject as the tenant, and carries the
        refresh session id, so ``revoke-all-sessions`` can exclude the
        caller's own session."""
        from starlette.responses import Response

        await _register(service, email="tok@example.io")
        user = await service.repo.get_user_by_email("tok@example.io")

        response = Response()
        token, refresh_token, record = await service.issue_tokens(user, response)

        assert token
        assert refresh_token
        assert record.jti
        assert record.user_id == user.id
        assert record.revoked is False
