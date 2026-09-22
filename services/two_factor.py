"""Two-Factor Authentication (TOTP) module.

Uses pyotp for TOTP generation and verification.
Secret keys are stored per-user in the settings table.
"""

import logging
import secrets

import pyotp

logger = logging.getLogger("econojin.twofa")


def generate_totp_secret() -> str:
    """Generate a new TOTP secret key (base32)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "Eco Nojin") -> str:
    """Generate otpauth URI for QR code provisioning."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer,
    )


def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
    """Verify a TOTP code against the secret."""
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)
    except Exception as exc:
        logger.warning("TOTP verification error: %s", exc)
        return False


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate one-time recovery codes."""
    return [secrets.token_urlsafe(6).upper() for _ in range(count)]


def hash_recovery_code(code: str) -> str:
    """Hash a recovery code for storage."""
    import hashlib

    return hashlib.sha256(code.encode()).hexdigest()
