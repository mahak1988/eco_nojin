"""JWT authentication & authorization (Phase 0 rewrite).

Fixes W-016: real auth with roles. Secret key comes from settings
(env/.env), never hard-coded. Adds:
- role-aware JWT (farmer / advisor / admin)
- ``get_current_user`` (strict 401) and ``get_current_user_optional``
- ``require_roles`` RBAC dependency
- API-key guard for telco webhooks (USSD/SMS/Voice)
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import User
from engine.hydroma.config.settings import get_settings

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Well-known roles
ROLE_FARMER = "farmer"
ROLE_ADVISOR = "advisor"
ROLE_ADMIN = "admin"
ALL_ROLES = {ROLE_FARMER, ROLE_ADVISOR, ROLE_ADMIN}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    subject: str | None = None,
    role: str = ROLE_FARMER,
) -> str:
    """Create signed JWT. ``data`` may carry extra claims."""
    to_encode = data.copy()
    if subject is not None:
        to_encode["sub"] = str(subject)
    to_encode["role"] = role
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=_settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.secret_key, algorithm=_settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """Decode + validate signature/expiry. Returns payload or None."""
    try:
        return jwt.decode(token, _settings.secret_key, algorithms=[_settings.jwt_algorithm])
    except JWTError:
        return None


def create_refresh_token(
    data: dict,
    subject: str | None = None,
    role: str = ROLE_FARMER,
) -> str:
    """Create a refresh JWT (long-lived, ``type=refresh`` claim).

    Separate lifetime from access tokens so short-lived access tokens can be
    re-issued without re-authentication (token rotation on each refresh).
    """
    to_encode = data.copy()
    if subject is not None:
        to_encode["sub"] = str(subject)
    to_encode["role"] = role
    to_encode["type"] = "refresh"
    expire = datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.secret_key, algorithm=_settings.jwt_algorithm)


def decode_refresh_token(token: str) -> dict | None:
    """Decode + validate a refresh token (signature, expiry, type claim)."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None
    return payload


def _user_from_payload(payload: dict, db: Session) -> User | None:
    sub = payload.get("sub")
    if sub is None:
        return None
    # Handle both UUID strings and integer IDs
    return db.query(User).filter(User.id == sub).first()


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return user for valid token, else None (public endpoints)."""
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    return _user_from_payload(payload, db)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Strict auth: 401 when missing/invalid token or unknown user."""
    user = await get_current_user_optional(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: str):
    """RBAC guard: current user must hold at least one of ``roles``."""

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role!r} not allowed. Required: {list(roles)}",
            )
        return user

    return _dependency


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Guard telco webhook endpoints with a shared secret (if configured)."""
    expected = _settings.telco_webhook_key
    if not expected:
        # Webhook auth disabled — only acceptable outside production.
        if _settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook auth not configured",
            )
        return x_api_key or ""
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


def role_of(user: User) -> str:
    return user.role if user.role in ALL_ROLES else ROLE_FARMER


# Backward-compatible alias: existing routers import `require_user`
require_user = get_current_user
