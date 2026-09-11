"""Auth backward-compatible wrapper.

Provides drop-in replacements for the legacy auth service so that
both old and new routers produce compatible JWTs and bcrypt password hashes.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from services.api_gateway.auth import (
    decode_token,
    hash_password as bcrypt_hash_password,
    verify_password as bcrypt_verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

from services.auth.models import AuthUser, RefreshToken


class PasswordHasher:
    """Unified password hasher with lazy migration from legacy pbkdf2."""

    LEGACY_PREFIX = "pbkdf2:"
    BCRYPT_PREFIX = "$2b$"

    def hash(self, password: str) -> str:
        return bcrypt_hash_password(password)

    def verify(self, password: str, stored_hash: str) -> bool:
        if stored_hash.startswith(self.BCRYPT_PREFIX):
            return bcrypt_verify_password(password, stored_hash)
        if stored_hash.startswith(self.LEGACY_PREFIX):
            return self._verify_legacy(password, stored_hash)
        return secrets.compare_digest(password.encode(), stored_hash.encode())

    def needs_migration(self, stored_hash: str) -> bool:
        return not stored_hash.startswith(self.BCRYPT_PREFIX)

    def _verify_legacy(self, password: str, stored_hash: str) -> bool:
        try:
            _, salt, hashed = stored_hash.split(":", 2)
            computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
            return secrets.compare_digest(computed, hashed)
        except Exception:
            return False


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hasher.verify(password, stored_hash)


def create_access_token_compat(
    data: dict,
    expires_delta: timedelta | None = None,
    subject: str | None = None,
    role: str = "farmer",
) -> str:
    return create_access_token(
        data=data,
        expires_delta=expires_delta,
        subject=subject,
        role=role,
    )


def create_refresh_token_compat(
    data: dict,
    subject: str | None = None,
    role: str = "farmer",
) -> str:
    return create_refresh_token(
        data=data,
        subject=subject,
        role=role,
    )


def decode_refresh_token_compat(token: str) -> dict | None:
    return decode_refresh_token(token)


def generate_token(user_id: str, ttl: int) -> str:
    payload = f"{user_id}:{int(datetime.now(UTC).timestamp())}:{ttl}"
    return f"{payload}:{secrets.token_urlsafe(32)}"
