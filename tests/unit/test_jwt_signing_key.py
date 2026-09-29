"""Regression tests for the JWT signing key.

Before the fix, ``create_access_token`` and ``decode_token`` signed with
``Settings.secret_key`` while ``Settings.jwt_secret`` was the value audited by
``validate_production_settings`` CHECK 3. A strong ``JWT_SECRET`` was therefore
inert, and a deployment that kept ``SECRET_KEY`` at the public
``"dev-secret-key"`` literal minted tokens anyone with the source could forge.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from unittest.mock import patch

import jwt as pyjwt
import pytest

from engine.hydroma.config.settings import Settings

STRONG_JWT = "J9" + "y" * 70
OTHER_STRONG = "S8" + "q" * 70


@contextmanager
def _env(**overrides: str):
    with patch.dict(os.environ, overrides, clear=False):
        yield


def test_jwt_signing_key_prefers_jwt_secret():
    """JWT_SECRET must win, because that is the audited value."""
    s = Settings(
        _env_file=None,
        environment="development",
        jwt_secret=STRONG_JWT,
        secret_key=OTHER_STRONG,
    )

    assert s.jwt_signing_key == STRONG_JWT


def test_jwt_signing_key_falls_back_to_secret_key():
    """Existing development setups with no JWT_SECRET keep working."""
    s = Settings(_env_file=None, environment="development", secret_key=OTHER_STRONG)

    assert s.jwt_signing_key == OTHER_STRONG


def test_jwt_signing_key_never_returns_empty():
    s = Settings(_env_file=None, environment="development")

    assert s.jwt_signing_key  # falls back through app_secret_key


def test_jwt_secret_secure_rejects_public_literal():
    s = Settings(
        _env_file=None,
        environment="development",
        jwt_secret="dev-jwt-secret",
        secret_key="dev-secret-key",
    )

    assert s.jwt_secret_secure is False


def test_jwt_secret_secure_accepts_strong_value():
    s = Settings(_env_file=None, environment="development", jwt_secret=STRONG_JWT)

    assert s.jwt_secret_secure is True


# --------------------------------------------------------------------------
# Token issuance refuses a weak key
# --------------------------------------------------------------------------


def test_token_creation_rejects_dev_literal_key():
    """A public literal signing key must raise instead of minting a token."""
    from services.api_gateway import auth as gw_auth

    with _env(ENVIRONMENT="development", APP_ENV="development"):
        s = Settings(_env_file=None, environment="development")
        assert s.jwt_signing_key in gw_auth._WEAK_SIGNING_KEYS

        with patch.object(gw_auth, "_settings", s):
            with pytest.raises(RuntimeError, match="signing key"):
                gw_auth.create_access_token({"sub": "attacker", "role": "admin"})


def test_token_roundtrip_uses_the_resolved_key():
    """Sign and verify must agree, and the key must be the resolved one."""
    from services.api_gateway import auth as gw_auth

    s = Settings(
        _env_file=None,
        environment="development",
        jwt_secret=STRONG_JWT,
        secret_key=OTHER_STRONG,
    )
    with patch.object(gw_auth, "_settings", s):
        token = gw_auth.create_access_token({"sub": "u1"}, role="advisor")
        payload = gw_auth.decode_token(token)

    assert payload is not None
    assert payload["sub"] == "u1"
    assert payload["role"] == "advisor"

    # A token signed with the *other* configured key must not validate.
    forged = pyjwt.encode(
        {"sub": "attacker", "role": "admin", "exp": 4102444800},
        OTHER_STRONG,
        algorithm="HS256",
    )
    with patch.object(gw_auth, "_settings", s):
        assert gw_auth.decode_token(forged) is None
