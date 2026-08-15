"""Phase 0 tests: pydantic-settings configuration."""

import pytest
from pydantic import ValidationError

from engine.hydroma.config.settings import Settings, get_settings


class TestSettingsDefaults:
    def test_defaults_sane(self):
        s = Settings(_env_file=None)
        assert s.project_name == "Eco Nojin"
        assert s.environment == "development"
        assert s.rate_limit_requests > 0
        assert s.access_token_expire_minutes > 0
        assert any("localhost:3000" in o for o in s.cors_origins)

    def test_dev_secret_marked_insecure(self):
        s = Settings(_env_file=None)
        assert s.is_secure_secret is False

    def test_cors_allow_all_property(self):
        s = Settings(_env_file=None, cors_origins=["*"])
        assert s.cors_allow_all is True
        s2 = Settings(_env_file=None, cors_origins=["http://x.test"])
        assert s2.cors_allow_all is False

    def test_environment_validation(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, environment="bogus")

    def test_empty_cors_rejected(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, cors_origins=[])


class TestProductionGuards:
    def test_production_default_secret_raises(self):
        with pytest.raises(RuntimeError, match="secret"):
            Settings(_env_file=None, environment="production")

    def test_production_wildcard_credentials_raises(self):
        with pytest.raises(RuntimeError, match="CORS"):
            Settings(
                _env_file=None,
                environment="production",
                secret_key="a" * 64,
                cors_origins=["*"],
                allow_credentials=True,
            )

    def test_production_valid_config_ok(self):
        s = Settings(
            _env_file=None,
            environment="production",
            secret_key="k" * 64,
            cors_origins=["https://app.econojin.org"],
            allow_credentials=True,
        )
        assert s.is_production
        assert s.is_secure_secret


def test_get_settings_cached():
    assert get_settings() is get_settings()
