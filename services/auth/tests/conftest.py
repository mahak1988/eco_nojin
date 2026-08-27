"""Fixtures for auth integration tests (Phase 6C fix: missing fixture)."""
import pytest

from services.auth.service import AuthService


@pytest.fixture
async def auth_service(db_session) -> AuthService:
    """Real AuthService bound to the shared async DB session."""
    return AuthService(db_session)
