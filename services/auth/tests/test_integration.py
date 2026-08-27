"""Integration tests for Auth"""
import pytest

from services.auth.schemas import UserLogin, UserRegister


@pytest.mark.asyncio
class TestAuthIntegration:
    async def test_register_and_login(self, auth_service):
        user = await auth_service.register(UserRegister(
            email="test@example.com", username="testuser", password="StrongPass1",
        ))
        assert user.email == "test@example.com"
        tokens = await auth_service.login(UserLogin(
            email="test@example.com", password="StrongPass1",
        ))
        assert tokens.access_token
        assert tokens.refresh_token

    async def test_duplicate_email(self, auth_service):
        data = UserRegister(email="dup@example.com", username="dupuser", password="StrongPass1")
        await auth_service.register(data)
        with pytest.raises(ValueError, match="already registered"):
            await auth_service.register(data)
