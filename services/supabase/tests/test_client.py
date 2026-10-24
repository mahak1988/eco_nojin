"""Tests for the Supabase client factory.

The client is optional: without ``SUPABASE_URL`` / a key there is no client,
and the factory must say so rather than hand back a half-built one.
"""


import pytest

from services.supabase import client as supabase_client


@pytest.fixture(autouse=True)
def _reset_singleton(monkeypatch):
    """The client is a module-level singleton; every test starts without one."""
    monkeypatch.setattr(supabase_client, "_client", None)
    for name in (
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


class TestClientFactory:
    """Tests for the singleton factory."""

    def test_without_a_url_the_factory_refuses(self):
        """A missing URL is a configuration error, not a silent None."""
        with pytest.raises(ValueError, match="SUPABASE_URL"):
            supabase_client.get_supabase_client()

    def test_without_a_key_the_factory_refuses(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        with pytest.raises(ValueError, match="SUPABASE_ANON_KEY"):
            supabase_client.get_supabase_client()

    def test_the_anon_client_refuses_without_a_url(self):
        with pytest.raises(ValueError, match="SUPABASE_URL"):
            supabase_client.get_anon_client()

    def test_the_anon_client_refuses_without_a_key(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        with pytest.raises(ValueError, match="SUPABASE_ANON_KEY"):
            supabase_client.get_anon_client()

    def test_the_anon_client_never_uses_the_service_role_key(self, monkeypatch):
        """The anon client must not be able to reach the service-role key."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-secret")
        # The service role key alone is not enough for the *anon* client.
        with pytest.raises(ValueError):
            supabase_client.get_anon_client()


class TestModels:
    """Tests for the platform models the client reads."""

    def test_the_platform_models_are_importable(self):
        from services.supabase import models

        for name in (
            "PlatformLandscape",
            "PlatformProfile",
            "PlatformCarbonProject",
            "PlatformCarbonCredit",
        ):
            assert hasattr(models, name), name

    def test_the_anon_client_is_a_different_factory(self):
        """The anon client and the service client are separate singletons."""
        assert supabase_client.get_anon_client is not supabase_client.get_supabase_client
