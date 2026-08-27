"""Fixtures for admin integration tests (Phase 6C fix: missing fixture)."""
import pytest

from services.admin.service import AdminService


@pytest.fixture
async def admin_service(db_session) -> AdminService:
    """Real AdminService bound to the shared async DB session."""
    return AdminService(db_session)
