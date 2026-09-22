"""JWT authentication & authorization (Phase 0 rewrite).

Fixes W-016: real auth with roles. Secret key comes from settings
(env/.env), never hard-coded. Adds:
- role-aware JWT (farmer / advisor / admin)
- ``get_current_user`` (strict 401) and ``get_current_user_optional``
- ``require_roles`` RBAC dependency
- API-key guard for telco webhooks (USSD/SMS/Voice)
- Tenant-aware authentication for multi-tenant SaaS
- httpOnly cookie support for secure token storage (C5 fix)

Async version (Week 2 fix): uses async SQLAlchemy sessions to avoid
thread-safety issues with SQLite in async FastAPI endpoints.
"""

from datetime import UTC, datetime, timedelta
from typing import NamedTuple

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from engine.hydroma.config.settings import get_settings

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Cookie names
ACCESS_TOKEN_COOKIE = "econojin_access_token"
REFRESH_TOKEN_COOKIE = "econojin_refresh_token"


async def _get_async_db():
    """Dependency wrapper for async database session."""
    async with hub.get_async_session() as session:
        yield session


# Well-known roles
ROLE_FARMER = "farmer"
ROLE_ADVISOR = "advisor"
ROLE_ADMIN = "admin"
ROLE_SECURITY_ADMIN = "security_admin"
ROLE_CONTENT_ADMIN = "content_admin"
ROLE_USER_ADMIN = "user_admin"
ALL_ROLES = {
    ROLE_FARMER,
    ROLE_ADVISOR,
    ROLE_ADMIN,
    ROLE_SECURITY_ADMIN,
    ROLE_CONTENT_ADMIN,
    ROLE_USER_ADMIN,
}

ADMIN_ROLES = {ROLE_ADMIN, ROLE_SECURITY_ADMIN, ROLE_CONTENT_ADMIN, ROLE_USER_ADMIN}


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
    tenant_id: str | None = None,
) -> str:
    """Create signed JWT. ``data`` may carry extra claims."""
    to_encode = data.copy()
    if subject is not None:
        to_encode["sub"] = str(subject)
    to_encode["role"] = role
    if tenant_id is not None:
        to_encode["platform_id"] = tenant_id
        to_encode["tenant_id"] = tenant_id
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
    tenant_id: str | None = None,
) -> str:
    """Create a refresh JWT (long-lived, ``type=refresh`` claim).

    Separate lifetime from access tokens so short-lived access tokens can be
    re-issued without re-authentication (token rotation on each refresh).

    H12 FIX: Includes JTI (JWT ID) claim for refresh token tracking and rotation.
    """
    import secrets

    to_encode = data.copy()
    if subject is not None:
        to_encode["sub"] = str(subject)
    to_encode["role"] = role
    to_encode["type"] = "refresh"
    # H12 FIX: Add JTI for refresh token tracking and rotation
    to_encode["jti"] = secrets.token_urlsafe(16)
    if tenant_id is not None:
        to_encode["platform_id"] = tenant_id
        to_encode["tenant_id"] = tenant_id
    expire = datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.secret_key, algorithm=_settings.jwt_algorithm)


async def store_refresh_token(
    jti: str, user_id: str, expires_at: datetime, db: AsyncSession
) -> None:
    """Store a refresh token JTI in the database for revocation tracking."""
    from database.models import RefreshToken

    refresh_record = RefreshToken(
        jti=jti,
        user_id=user_id,
        revoked=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes),
    )
    db.add(
        RefreshToken(
            jti=jti,
            user_id=user_id,
            revoked=False,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=_settings.refresh_token_expire_minutes),
        )
    )
    # Note: caller must commit the session


async def is_refresh_token_revoked(jti: str, db: AsyncSession) -> bool:
    """Check if a refresh token JTI is revoked in the database."""
    from database.models import RefreshToken

    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    token = result.scalar_one_or_none()
    if token is None:
        # Token not found in DB - treat as revoked for security
        return True
    return token.revoked


def decode_refresh_token(token: str) -> dict | None:
    """Decode + validate a refresh token (signature, expiry, type claim)."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None
    return payload


async def _user_from_payload(payload: dict, db: AsyncSession) -> User | None:
    sub = payload.get("sub")
    if sub is None:
        return None
    result = await db.execute(select(User).where(User.id == sub))
    return result.scalar_one_or_none()


async def get_current_user_optional(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(_get_async_db),
) -> User | None:
    """Return user for valid token, else None (public endpoints).

    Checks both Authorization header and httpOnly cookies.
    """
    # Try header first, then cookie
    if not token:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    return await _user_from_payload(payload, db)


async def get_current_user(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(_get_async_db),
) -> User:
    """Strict auth: 401 when missing/invalid token or unknown user.

    Checks both Authorization header and httpOnly cookies.
    """
    user = await get_current_user_optional(request, response, token, db)
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


def require_admin(user: User = Depends(require_roles(ROLE_ADMIN))) -> User:
    return user


def require_security_admin(
    user: User = Depends(require_roles(ROLE_ADMIN, ROLE_SECURITY_ADMIN)),
) -> User:
    return user


def require_content_admin(
    user: User = Depends(require_roles(ROLE_ADMIN, ROLE_CONTENT_ADMIN)),
) -> User:
    return user


def require_user_admin(user: User = Depends(require_roles(ROLE_ADMIN, ROLE_USER_ADMIN))) -> User:
    return user


async def require_admin_with_mfa(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(_get_async_db),
) -> User:
    """Require admin role AND MFA enabled. Returns user if both conditions met."""
    user = await get_current_user(request, response, token, db)

    if user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin role required. Current role: {user.role}",
        )

    # Check MFA enabled - look in user settings or dedicated field
    # For now, check if user has two_factor_enabled attribute or check settings table
    mfa_enabled = getattr(user, "two_factor_enabled", False)

    # Also check in settings table for backward compatibility
    if not mfa_enabled:
        try:
            from database.models import Setting

            setting = db.query(Setting).filter(Setting.key == f"2fa_enabled_{user.id}").first()
            if setting and setting.value == "true":
                mfa_enabled = True
        except Exception:
            pass

    if not mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA required for admin access. Enable 2FA in settings.",
        )

    return user


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


class UserWithTenant(NamedTuple):
    """Container for user and their tenant context."""

    user: User
    tenant_id: str | None


async def get_current_user_with_tenant(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(_get_async_db),
) -> UserWithTenant:
    """Strict auth with tenant context: returns User and tenant_id from JWT only.

    Extracts tenant_id from JWT payload (platform_id or tenant_id claim).
    Does NOT fall back to X-Tenant-Id header for authenticated users.

    Returns UserWithTenant(user, tenant_id) where tenant_id may be None if not in JWT.
    """
    user = await get_current_user(request, response, token, db)

    tenant_id: str | None = None
    payload = decode_token(token) if token else None
    if payload:
        tenant_id = payload.get("platform_id") or payload.get("tenant_id")

    return UserWithTenant(user=user, tenant_id=tenant_id)


# Backward-compatible alias: existing routers import `require_user`
require_user = get_current_user


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly secure cookies for access and refresh tokens.

    C5 FIX: Moves JWT storage from localStorage to httpOnly cookies
    to prevent XSS token theft.
    """
    is_production = _settings.is_production

    # Access token - short lived
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=_settings.access_token_expire_minutes * 60,
        path="/",
    )

    # Refresh token - long lived
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=_settings.refresh_token_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies on logout."""
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")
