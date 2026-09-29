"""Regression tests for production configuration resolution.

These tests pin the source-precedence contract of ``Settings``. Before the fix,
``Settings.__init__`` injected insecure defaults into the *init kwargs*, which
under pydantic-settings precedence (``init_settings`` outranks ``env_settings``
and ``dotenv_settings``) silently overrode a real ``ENVIRONMENT=production`` and
a real ``SECRET_KEY`` read from the environment. The application therefore ran
with ``debug=True`` and the public literal ``"dev-secret-key"`` as the JWT
signing key, and ``validate_production_settings`` returned early on every boot.

The fix applies the insecure test defaults *after* ``super().__init__()`` and
gates them on the explicit ``_env_file=None`` call, so a production environment
now reaches the validator instead of being bypassed.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from engine.hydroma.config.settings import Settings

#: 72-char values so they clear the 64-character production length checks.
STRONG_SECRET = "K9" + "x" * 70
STRONG_JWT = "J9" + "y" * 70

#: A complete, valid production environment: every one of the 15 checks in
#: ``validate_production_settings`` satisfied. Used as the baseline that must
#: resolve to ``is_production is True`` instead of being downgraded.
VALID_PRODUCTION_ENV = {
    "ENVIRONMENT": "production",
    "APP_ENV": "production",
    "SECRET_KEY": STRONG_SECRET,
    "JWT_SECRET": STRONG_JWT,
    "APP_SECRET_KEY": STRONG_SECRET,
    "AGENT_TOKEN": "A9" + "z" * 70,
    "DEBUG": "false",
    "APP_DEBUG": "false",
    "ENABLE_SIMULATED_DATA": "false",
    "ENABLE_DEBUG_ROUTES": "false",
    "TELEGRAM_BOT_TOKEN": "1234567890:AAHtestTokenForValidationOnly",
    "DATABASE_URL": "postgresql+psycopg://user:pw@db.internal:5432/econojin",
    "REDIS_URL": "redis://redis.internal:6379/0",
    "CORS_ORIGINS": '["https://app.econojin.io"]',
    "ENABLE_SUPABASE_SYNC": "false",
    "ENABLE_BLOCKCHAIN": "false",
    "ENABLE_EVENT_BUS": "false",
    "SENTRY_DSN": "https://public@sentry.invalid/1",
}


@contextmanager
def _env(**overrides: str):
    """Patch environment variables for the duration of the block."""
    with patch.dict(os.environ, overrides, clear=False):
        yield


# --------------------------------------------------------------------------
# The production environment must survive resolution (the core regression)
# --------------------------------------------------------------------------


def test_production_from_env_var_is_not_downgraded():
    """ENVIRONMENT=production in the environment must survive resolution."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings()

    assert s.environment == "production", (
        f"environment was downgraded to {s.environment!r}; init kwargs must not "
        "outrank the environment"
    )
    assert s.app_env == "production"
    assert s.is_production is True


def test_production_preserves_real_secret():
    """A real SECRET_KEY must not be replaced by the public dev literal."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings()

    assert s.secret_key == STRONG_SECRET
    assert s.secret_key != "dev-secret-key"
    assert s.jwt_secret == STRONG_JWT


def test_production_does_not_force_debug_true():
    """debug must stay False in production regardless of the test-mode branch."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings()

    assert s.debug is False, "debug was forced True in production"
    assert s.app_debug is False


def test_production_validator_runs_and_passes_for_a_valid_environment():
    """With the fix, a complete production config must pass all 15 checks."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings()
        assert s.validate_production_settings() is s


@pytest.mark.parametrize("env_field", ["ENVIRONMENT", "APP_ENV"])
def test_production_detected_from_either_field(env_field: str):
    """Both ``environment`` and the legacy ``app_env`` field must be honoured."""
    env = dict(VALID_PRODUCTION_ENV)
    env.pop("ENVIRONMENT", None)
    env.pop("APP_ENV", None)
    env[env_field] = "production"
    with _env(**env):
        s = Settings()

    assert s.is_production is True
    assert s.debug is False


def test_production_from_init_kwarg_still_works():
    """The pre-existing contract: environment passed to the constructor."""
    env = dict(VALID_PRODUCTION_ENV)
    env.pop("ENVIRONMENT")
    env.pop("APP_ENV")
    with _env(**env):
        s = Settings(environment="production")

    assert s.is_production is True
    assert s.secret_key == STRONG_SECRET
    assert s.debug is False


# --------------------------------------------------------------------------
# The guards that were dormant must now actually fire
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("override", "expected_fragment"),
    [
        ({"SECRET_KEY": "short"}, "strong, non-default secret"),
        ({"JWT_SECRET": "short"}, "strong, non-default JWT secret"),
        ({"DEBUG": "true"}, "debug=False"),
        ({"ENABLE_SIMULATED_DATA": "true"}, "simulated"),
        ({"ENABLE_DEBUG_ROUTES": "true"}, "debug_routes"),
        ({"TELEGRAM_BOT_TOKEN": ""}, "TELEGRAM_BOT_TOKEN"),
        ({"DATABASE_URL": "sqlite:///./data/econojin.db"}, "PostgreSQL"),
        ({"REDIS_URL": "redis://localhost:6379/0"}, "REDIS_URL"),
        ({"CORS_ORIGINS": '["*"]'}, "CORS"),
    ],
)
def test_production_guards_now_enforce(override: dict, expected_fragment: str):
    """Each dormant production check must raise once the env is honoured.

    Before the fix every one of these returned early because ``is_production``
    was always ``False``. ``validate_production_settings`` is a
    ``model_validator(mode="after")``, so the failure surfaces at construction.
    """
    env = dict(VALID_PRODUCTION_ENV)
    env.update(override)
    with _env(**env):
        with pytest.raises(RuntimeError) as exc:
            Settings()

    assert expected_fragment.lower() in str(exc.value).lower()


def test_development_literal_secret_is_rejected_in_production():
    """The public dev literal must never satisfy the production secret check."""
    env = dict(VALID_PRODUCTION_ENV)
    env["SECRET_KEY"] = "dev-secret-key"
    env["JWT_SECRET"] = "dev-jwt-secret"
    with _env(**env):
        with pytest.raises(RuntimeError):
            Settings()


# --------------------------------------------------------------------------
# The documented test-mode behaviour must be preserved
# --------------------------------------------------------------------------


def test_explicit_test_mode_still_yields_insecure_defaults():
    """Settings(_env_file=None) must keep forcing insecure defaults.

    Unit tests rely on this branch to get fail-closed, triggerable guards. Note
    the deliberate asymmetry: ``_env_file=None`` excludes the dotenv *file*, and
    the branch only engages for a non-production environment. If the ambient
    environment itself declares production, production wins -- otherwise this
    branch would be the downgrade path the fix removes.
    """
    with _env(ENVIRONMENT="development", APP_ENV="development"):
        s = Settings(_env_file=None)

    assert s.environment == "development"
    assert s.secret_key == "dev-secret-key"
    assert s.debug is True
    assert s.is_production is False


def test_explicit_test_mode_does_not_override_ambient_production():
    """A production environment must never be downgraded, even in test mode."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings(_env_file=None)

    assert s.is_production is True
    assert s.secret_key == STRONG_SECRET


def test_plain_construction_outside_test_mode_is_not_forced():
    """Plain Settings() with no _env_file argument must not force dev defaults."""
    with _env(**VALID_PRODUCTION_ENV):
        s = Settings()

    assert s.is_production is True
    assert s.secret_key == STRONG_SECRET


def test_is_secure_secret_rejects_public_literal():
    with _env(ENVIRONMENT="development"):
        s = Settings(_env_file=None)

    assert s.is_secure_secret is False
