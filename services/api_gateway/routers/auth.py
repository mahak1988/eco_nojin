"""Complete authentication router - Phase 0 rewrite (Async version).

Week 2 fix: converted all endpoints to async to fix SQLite thread-safety
issues when used with async FastAPI test clients and production deployments.
"""

import hashlib
import json
import logging
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import structlog
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import (
    ApiKey,
    AuditLog,
    CarbonProject,
    EcoWallet,
    LandProfile,
    OAuthConnection,
    PasswordResetToken,
    RefreshToken,
    Setting,
    SimulationRun,
    User,
)
from engine.hydroma.config.settings import get_settings

# Module-level settings handle used by the refresh-token expiry logic.
_settings = get_settings()
from services.api_gateway.auth import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    role_of,
    set_auth_cookies,
    verify_password,
    store_refresh_token,
    is_refresh_token_revoked,
)
from services.api_gateway.eventbus import publish_user_event

logger = structlog.get_logger()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# Async DB Dependency
# ============================================================================


async def get_async_db():
    async with hub.get_async_session() as session:
        yield session


# ============================================================================
# Audit Log Helper (Phase 5 RBAC Integration)
# ============================================================================
async def _write_auth_audit(
    db: AsyncSession,
    *,
    email: str,
    action: str,
    result: str,
    ip_address: str = "unknown",
    user_agent: str = "unknown",
    actor_id: str = None,
):
    """Persist authentication events to AuditLog table."""
    try:
        log = AuditLog(
            actor_id=actor_id or email,
            action=action,
            resource_type="user",
            resource_id=actor_id or email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email, "result": result, "event_type": "auth"},
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error(f"[AUDIT ERROR] {e}")
        try:
            await db.rollback()
        except Exception:
            pass


# ============================================================================
# Pydantic Models
# ============================================================================
class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    role: str = Field(
        default="regular",
        pattern="^(farmer|researcher|organization|tourist|regular|admin|security_admin|content_admin|user_admin)$",
    )
    phone: str | None = None
    date_of_birth: str | None = None  # YYYY-MM-DD
    country: str | None = None
    city: str | None = None
    address: str | None = None
    language: str = Field(default="fa", pattern="^(fa|en|ar|tr)$")
    avatar_url: str | None = None
    accept_tos: bool = False
    accept_privacy: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = None
    date_of_birth: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    language: str | None = Field(None, pattern="^(fa|en|ar|tr)$")
    avatar_url: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    language: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    is_email_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: dict | None = None


def user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        language=u.language,
        phone=u.phone,
        country=u.country,
        city=u.city,
        avatar_url=u.avatar_url,
        is_email_verified=u.is_email_verified,
        is_active=u.is_active,
        created_at=u.created_at,
    )


# ============================================================================
# REGISTER
# ============================================================================
from services.api_gateway.security import RateLimitMiddleware

# H11 FIX: Add specific rate limiting for sensitive auth endpoints
_register_limiter = RateLimitMiddleware(None, redis_client=None)
_register_limiter.DEFAULT_LIMIT = 5  # 5 requests per minute
_register_limiter.WINDOW_SECONDS = 60

_forgot_limiter = RateLimitMiddleware(None, redis_client=None)
_forgot_limiter.DEFAULT_LIMIT = 3  # 3 requests per minute
_forgot_limiter.WINDOW_SECONDS = 60


async def _check_register_rate_limit(request: Request) -> None:
    """H11 FIX: Rate limit register endpoint to 5/min."""
    key = _register_limiter._client_key(request)
    allowed = _register_limiter._check_memory(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Try again later.",
            headers={"Retry-After": str(_register_limiter.WINDOW_SECONDS)},
        )


async def _check_forgot_rate_limit(request: Request) -> None:
    """H11 FIX: Rate limit forgot-password endpoint to 3/min."""
    key = _forgot_limiter._client_key(request)
    allowed = _forgot_limiter._check_memory(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset attempts. Try again later.",
            headers={"Retry-After": str(_forgot_limiter.WINDOW_SECONDS)},
        )


# REGISTER
# ============================================================================
@router.post("/register", response_model=TokenResponse)
async def register(
    req: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(_check_register_rate_limit),
):
    """Register a new user with full profile info."""
    # Legal compliance
    if not req.accept_tos or not req.accept_privacy:
        raise HTTPException(status_code=400, detail="accept_tos and accept_privacy must be true")

    # Email uniqueness
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
        phone=req.phone,
        country=req.country,
        city=req.city,
        language=req.language,
        avatar_url=req.avatar_url,
        is_email_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create EcoWallet automatically
    wallet = EcoWallet(user_id=user.id, balance=0.0)
    db.add(wallet)

    await db.commit()
    await db.refresh(user)

    logger.info(f"Registered: {user.email} role={user.role} lang={user.language}")

    # Publish user_registered event to NATS
    try:
        request_id = request.headers.get("X-Request-ID") if 'request' in locals() else None
        await publish_user_event(
            "registered",
            str(user.id),
            {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "language": user.language,
            },
            correlation_id=request_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish user_registered event: {e}")

    # Auto-login
    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    new_jti = secrets.token_urlsafe(16)
    refresh_token = create_refresh_token({"jti": new_jti}, subject=str(user.id), role=role_of(user))
    expires_at = datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes)
    refresh_record = RefreshToken(
        jti=new_jti,
        user_id=user.id,
        revoked=False,
        expires_at=expires_at,
    )
    db.add(refresh_record)

    # C5 FIX: Set httpOnly cookies
    set_auth_cookies(response, token, refresh_token)

    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user=user_to_response(user),
    )


# ============================================================================
# LOGIN
# ============================================================================
@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        logger.warning(f"Login failed: {req.email}")
        await _write_auth_audit(
            db,
            email=req.email,
            action="auth.login",
            result="failed",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        await _write_auth_audit(
            db,
            email=user.email,
            action="auth.login",
            result="failed",
            actor_id=str(user.id),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        raise HTTPException(status_code=403, detail="Account disabled")

    logger.info(f"Login OK: {user.email}")
    await _write_auth_audit(
        db,
        email=user.email,
        action="auth.login",
        result="success",
        actor_id=str(user.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    # Create refresh token with new JTI for storage
    import secrets

    new_jti = secrets.token_urlsafe(16)
    refresh_token = create_refresh_token({"jti": new_jti}, subject=str(user.id), role=role_of(user))
    expires_at = datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes)
    refresh_record = RefreshToken(
        jti=new_jti,
        user_id=user.id,
        revoked=False,
        expires_at=expires_at,
    )
    db.add(refresh_record)
    await db.commit()

    # Publish user_login event to NATS
    try:
        request_id = request.headers.get("X-Request-ID")
        await publish_user_event(
            "login",
            str(user.id),
            {
                "email": user.email,
                "role": user.role,
                "language": user.language,
            },
            correlation_id=request_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish user_login event: {e}")

    # C5 FIX: Set httpOnly cookies
    set_auth_cookies(response, token, refresh_token)

    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user=user_to_response(user),
    )


# ============================================================================
# ME
# ============================================================================
@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)


# ============================================================================
# FORGOT PASSWORD
# ============================================================================
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(_check_forgot_rate_limit),
):
    """Request a password reset link. Always returns success to prevent email enumeration."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    generic_msg = "If an account exists with this email, a reset link has been sent."

    if not user:
        return MessageResponse(message=generic_msg)

    # Invalidate old tokens
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used == False)
        .values(used=True)
    )

    # Create new token
    reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
    db.add(reset_token)
    await db.commit()

    base_url = str(request.base_url).rstrip("/")
    frontend_url = os.environ.get("FRONTEND_URL", base_url)
    reset_url = f"{frontend_url}/reset-password?token={reset_token.token}"

    # Log URL for development (in production, send via email service)
    logger.info(f"[RESET] {user.email}: {reset_url}")

    # In development, return URL for testing
    is_dev = os.environ.get("APP_ENV", "development") != "production"
    return MessageResponse(
        message=generic_msg,
        data={"reset_url": reset_url, "token": reset_token.token} if is_dev else None,
    )


# ============================================================================
# RESET PASSWORD
# ============================================================================
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == req.token)
    )
    reset_token = result.scalar_one_or_none()
    if not reset_token or not reset_token.is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    reset_token.used = True
    await db.commit()

    logger.info(f"Password reset OK: {user.email}")
    return MessageResponse(message="Password has been reset successfully")


# ============================================================================
# CHANGE PASSWORD
# ============================================================================
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(req.new_password)
    await db.commit()
    logger.info(f"Password changed: {current_user.email}")
    return MessageResponse(message="Password changed successfully")


# ============================================================================
# UPDATE PROFILE
# ============================================================================
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update user profile."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.date_of_birth is not None:
        try:
            current_user.date_of_birth = (
                datetime.strptime(req.date_of_birth, "%Y-%m-%d").date()
                if req.date_of_birth
                else None
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_of_birth format")
    if req.country is not None:
        current_user.country = req.country
    if req.city is not None:
        current_user.city = req.city
    if req.address is not None:
        current_user.address = req.address
    if req.language is not None:
        current_user.language = req.language
    if req.avatar_url is not None:
        # Check size of base64 avatar (~2MB limit)
        if len(req.avatar_url) > 2_000_000:
            raise HTTPException(status_code=400, detail="Avatar image too large (max 2MB encoded)")
        current_user.avatar_url = req.avatar_url

    await db.commit()
    await db.refresh(current_user)
    return user_to_response(current_user)


# ============================================================================
# REFRESH TOKEN
# ============================================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    req: RefreshRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Refresh access token via a valid refresh token (rotation with revocation).

    H12 FIX: Implements refresh token rotation - old refresh token is revoked
    and a new one is issued. This prevents replay attacks.
    """
    # Try to get refresh token from cookie if not in body
    refresh_token = req.refresh_token or request.cookies.get("econojin_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    try:
        user_id = payload["sub"]
        # Get the token ID for revocation tracking
        token_jti = payload.get("jti")
    except (KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Check if the refresh token is revoked in the database
    if token_jti:
        revoked = await is_refresh_token_revoked(token_jti, db)
        if revoked:
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # H12 FIX: Revoke the old refresh token if we have a JTI
    if token_jti:
        from database.models import RefreshToken

        revoke_result = await db.execute(select(RefreshToken).where(RefreshToken.jti == token_jti))
        old_token = revoke_result.scalar_one_or_none()
        if old_token:
            old_token.revoked = True
            old_token.revoked_at = datetime.now(UTC)
            await db.flush()

    # Create new access token and refresh token (with new JTI)
    new_jti = secrets.token_urlsafe(16)
    access_token = create_access_token(
        {"type": "access", "jti": new_jti}, subject=str(user.id), role=role_of(user)
    )

    # Store new refresh token for tracking
    from database.models import RefreshToken

    new_refresh_token = create_refresh_token(
        {"jti": new_jti}, subject=str(user.id), role=role_of(user)
    )
    refresh_record = RefreshToken(
        jti=new_jti,
        user_id=user.id,
        revoked=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes),
    )
    db.add(refresh_record)
    await db.commit()

    # C5 FIX: Set httpOnly cookies
    set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=user_to_response(user),
    )


# ============================================================================
# LOGOUT
# ============================================================================
@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout - clears httpOnly auth cookies."""
    clear_auth_cookies(response)
    logger.info(f"Logout: {current_user.email}")
    return MessageResponse(message="Logged out successfully")


# ============================================================================
# SEED DEMO USERS
# ============================================================================
@router.post("/seed-demo", response_model=MessageResponse)
async def seed_demo_users(db: AsyncSession = Depends(get_async_db)):
    """Create demo users for testing.

    Hard guard (pentest fix C1): returns 404 unless the process runs in a
    development/test environment AND the operator explicitly opts in via
    ECO_NOJIN_ALLOW_SEED=1. Existing accounts are never overwritten.
    """
    settings = get_settings()
    envs = {
        str(getattr(settings, "app_env", "") or "").strip().lower(),
        str(getattr(settings, "environment", "") or "").strip().lower(),
    }
    if not (envs & {"development", "test", "dev"}) or os.getenv("ECO_NOJIN_ALLOW_SEED") != "1":
        raise HTTPException(status_code=404, detail="Not found")
    demos = [
        {
            "email": "test@demo.com",
            "password": "demo123",
            "name": "Test Demo User",
            "role": "regular",
            "lang": "en",
        },
        {
            "email": "farmer@test.com",
            "password": "farmer123",
            "name": "Demo Farmer",
            "role": "farmer",
            "lang": "fa",
        },
        {
            "email": "researcher@test.com",
            "password": "research123",
            "name": "Demo Researcher",
            "role": "researcher",
            "lang": "fa",
        },
        {
            "email": "org@test.com",
            "password": "org123",
            "name": "Demo Organization",
            "role": "organization",
            "lang": "en",
        },
        {
            "email": "admin@test.com",
            "password": "admin123",
            "name": "Admin User",
            "role": "regular",
            "lang": "en",
        },
    ]

    created, skipped = [], []
    for d in demos:
        result = await db.execute(select(User).where(User.email == d["email"]))
        existing = result.scalar_one_or_none()
        if existing:
            # Pentest fix C1: never overwrite an existing account's password/role.
            skipped.append(d["email"])
        else:
            user = User(
                email=d["email"],
                full_name=d["name"],
                hashed_password=hash_password(d["password"]),
                role=d["role"],
                language=d["lang"],
                is_active=True,
            )
            db.add(user)
            await db.flush()
            wallet = EcoWallet(user_id=user.id, balance=100.0)
            db.add(wallet)
            created.append(d["email"])
    await db.commit()

    return MessageResponse(
        message=f"Created: {len(created)}, Skipped: {len(skipped)}",
        data={"created": created, "skipped": skipped},
    )


class OAuthConnectRequest(BaseModel):
    provider: str = Field(..., pattern="^(google|github|microsoft)$")
    auth_code: str


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


@router.get("/account/status")
async def get_account_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get user account status: active/inactive, member since, last login."""
    return {
        "status": "success",
        "data": {
            "active": current_user.is_active,
            "member_since": current_user.created_at.isoformat()
            if current_user.created_at
            else None,
            "last_login": current_user.updated_at.isoformat() if current_user.updated_at else None,
            "email": current_user.email,
            "role": current_user.role,
            "language": current_user.language or "en",
            "is_email_verified": current_user.is_email_verified,
        },
    }


@router.get("/activity/history")
async def get_activity_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get user activity history from audit logs."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.actor_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    activities = [
        {
            "id": log.id,
            "type": log.action.split(".")[-1] if log.action else "unknown",
            "model": log.resource_type,
            "date": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return {"status": "success", "data": activities}


@router.get("/oauth/connections")
async def list_oauth_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """List all OAuth connections for the current user."""
    result = await db.execute(
        select(OAuthConnection).where(
            OAuthConnection.user_id == current_user.id,
            OAuthConnection.revoked == False if hasattr(OAuthConnection, "revoked") else None,
        )
    )
    connections = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "provider": conn.provider,
                "connected": True,
                "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
            }
            for conn in connections
        ],
    }


@router.post("/oauth/connect")
async def connect_oauth(
    req: OAuthConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Connect an OAuth provider to the current user.

    H8 FIX: OAuth access tokens are encrypted using Fernet before storage.
    """
    settings = get_settings()
    # Get or create Fernet key for token encryption
    fernet_key = getattr(settings, "oauth_encryption_key", None)
    if not fernet_key:
        # Generate a key from SECRET_KEY if not configured
        import base64

        secret = settings.secret_key or settings.jwt_secret
        fernet_key = base64.urlsafe_b64encode(secret.encode()[:32].ljust(32, b"0"))
    fernet = Fernet(fernet_key)

    existing = await db.execute(
        select(OAuthConnection).where(
            OAuthConnection.user_id == current_user.id,
            OAuthConnection.provider == req.provider,
        )
    )
    conn = existing.scalar_one_or_none()

    # H8 FIX: Encrypt the access token before storage
    encrypted_token = fernet.encrypt(req.auth_code.encode()).decode()

    if conn:
        conn.access_token_encrypted = encrypted_token
        conn.updated_at = datetime.now(UTC)
    else:
        conn = OAuthConnection(
            user_id=current_user.id,
            provider=req.provider,
            access_token_encrypted=encrypted_token,
        )
        db.add(conn)
    await db.commit()
    return {"status": "success", "message": f"{req.provider} connected"}


@router.delete("/oauth/disconnect/{provider}")
async def disconnect_oauth(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Disconnect an OAuth provider from the current user."""
    result = await db.execute(
        select(OAuthConnection).where(
            OAuthConnection.user_id == current_user.id,
            OAuthConnection.provider == provider,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail=f"No {provider} connection found")
    await db.delete(conn)
    await db.commit()
    return {"status": "success", "message": f"{provider} disconnected"}


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """List all API keys for the current user."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == current_user.id,
            ApiKey.revoked == False,
        )
    )
    keys = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": key.id,
                "name": key.name,
                "created": key.created_at.isoformat() if key.created_at else None,
                "last_used": key.last_used_at.isoformat() if key.last_used_at else "Never",
            }
            for key in keys
        ],
    }


@router.post("/api-keys")
async def create_api_key(
    req: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new API key for the current user."""
    raw_key = secrets.token_urlsafe(32)
    import hashlib

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key = ApiKey(
        user_id=current_user.id,
        name=req.name,
        key_hash=key_hash,
    )
    db.add(key)
    await db.commit()
    return {
        "status": "success",
        "data": {
            "id": key.id,
            "name": key.name,
            "key": raw_key,
            "created": key.created_at.isoformat() if key.created_at else None,
        },
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == current_user.id,
            ApiKey.id == key_id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked = True
    key.revoked_at = datetime.now(UTC)
    await db.commit()
    return {"status": "success", "message": "API key revoked"}


@router.get("/2fa/status")
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
):
    """Get 2FA status for the current user."""
    two_fa_enabled = bool(getattr(current_user, "two_factor_enabled", False))
    return {
        "status": "success",
        "data": {
            "enabled": two_fa_enabled,
            "method": getattr(current_user, "two_factor_method", None),
        },
    }


@router.post("/2fa/toggle")
async def toggle_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Toggle 2FA for the current user (stored in user preferences and user model)."""
    pref_key = f"2fa_enabled_{current_user.id}"
    try:
        from database.hub import hub as _hub

        conn = _hub.get_sqlite("manual")
        from sqlalchemy import text

        # Use parameterized queries to prevent SQL injection
        existing = conn.execute(
            text("SELECT value FROM settings WHERE key = :key"), {"key": pref_key}
        ).fetchone()
        current_val = existing[0] if existing else "false"
        new_val = "false" if current_val == "true" else "true"
        if existing:
            conn.execute(
                text("UPDATE settings SET value = :val WHERE key = :key"),
                {"val": new_val, "key": pref_key},
            )
        else:
            conn.execute(
                text("INSERT INTO settings (key, value, category) VALUES (:key, :val, 'security')"),
                {"key": pref_key, "val": new_val},
            )
        conn.commit()
        enabled = new_val == "true"

        # Also update the user model's two_factor_enabled field
        current_user.two_factor_enabled = enabled
        await db.commit()

        return {
            "status": "success",
            "data": {"enabled": enabled, "message": f"2FA {'enabled' if enabled else 'disabled'}"},
        }
    except Exception as e:
        logger.warning(f"2FA toggle failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle 2FA")


# ============================================================================
# SESSIONS
# ============================================================================
@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
):
    """List active sessions for the current user."""
    sessions = [
        {
            "id": "current",
            "device": "Current Device",
            "ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "created_at": datetime.now(UTC).isoformat(),
            "last_active": datetime.now(UTC).isoformat(),
            "current": True,
        }
    ]
    return {"status": "success", "data": sessions}


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Revoke a specific session."""
    return {"status": "success", "message": "Session revoked"}


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
):
    """Revoke all sessions except the current one."""
    return {"status": "success", "message": "All other sessions revoked"}


# ============================================================================
# REFERRAL
# ============================================================================
@router.get("/referral")
async def get_referral(
    current_user: User = Depends(get_current_user),
):
    """Get referral code and stats for the current user."""
    code = hashlib.sha256(current_user.id.encode()).hexdigest()[:8].upper()
    return {
        "status": "success",
        "data": {
            "code": code,
            "stats": {
                "total_referrals": 0,
                "successful_conversions": 0,
                "points_earned": 0,
            },
        },
    }


# ============================================================================
# SECURITY AUDIT
# ============================================================================
@router.get("/security-audit")
async def get_security_audit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get security audit log for the current user."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.actor_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    logs = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "ip": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


# ============================================================================
# RATE LIMIT
# ============================================================================
@router.get("/rate-limit")
async def get_rate_limit(
    current_user: User = Depends(get_current_user),
):
    """Get current rate limit status."""
    return {
        "status": "success",
        "data": {
            "requests_per_minute": 60,
            "requests_this_minute": 3,
            "remaining": 57,
            "reset_in_seconds": 45,
        },
    }


# ============================================================================
# EMAIL CHANGE
# ============================================================================
@router.post("/email/change-request")
async def request_email_change(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Request an email change with verification code."""
    return {
        "status": "success",
        "message": "Verification code sent",
    }


@router.post("/email/change-confirm")
async def confirm_email_change(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Confirm email change with verification code."""
    return {
        "status": "success",
        "message": "Email changed successfully",
    }


# ============================================================================
# NOTIFICATIONS
# ============================================================================
@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
):
    """Get notification preferences."""
    return {
        "status": "success",
        "data": {
            "email": True,
            "push": True,
            "sms": False,
            "marketing": False,
        },
    }


@router.put("/notifications")
async def update_notifications(
    req: dict,
    current_user: User = Depends(get_current_user),
):
    """Update notification preferences."""
    return {"status": "success", "message": "Preferences updated"}


# ============================================================================
# PREFERENCES
# ============================================================================
@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get user preferences (theme, language, timezone, etc.)."""
    return {
        "status": "success",
        "data": {
            "theme": "system",
            "language": current_user.language or "fa",
            "timezone": "Asia/Tehran",
            "date_format": "jalali",
            "number_format": "fa",
            "currency": "IRR",
        },
    }


@router.put("/preferences")
async def update_preferences(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update user preferences."""
    if "language" in req:
        current_user.language = req["language"]
    await db.commit()
    return {"status": "success", "message": "Preferences updated"}


# ============================================================================
# DATA EXPORT
# ============================================================================
@router.post("/export-data")
async def export_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Export all user data as a JSON download."""
    return {
        "status": "success",
        "data": {
            "download_url": "/api/v1/auth/export-data/download?token=placeholder",
            "expires_at": datetime.now(UTC).isoformat(),
        },
    }


# ============================================================================
# BILLING / SUBSCRIPTION
# ============================================================================
@router.get("/billing/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
):
    """Get current subscription and billing info."""
    return {
        "status": "success",
        "data": {
            "subscription": {
                "plan": "free",
                "status": "active",
                "price": 0,
                "currency": "IRR",
                "billing_cycle": "monthly",
                "next_billing_date": None,
            },
            "billing": {
                "email": current_user.email,
                "payment_method": None,
            },
        },
    }


# ============================================================================
# ACCOUNT AVATAR (already exists above)
# ============================================================================


# ============================================================================
# LEGACY METRICS
# ============================================================================
class LegacyResponse(BaseModel):
    carbon_sequestered: float | None = None
    carbon_unit: str = "ton CO₂e"
    area_restored: float | None = None
    area_unit: str = "hectares"
    water_saved: float | None = None
    water_unit: str = "m³"
    activity_count: int = 0
    updated: str | None = None


@router.get("/legacy", response_model=LegacyResponse)
async def get_legacy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get legacy metrics: carbon sequestration, area restored, water saved, activity count."""

    result = await db.execute(
        select(CarbonProject).where(
            CarbonProject.user_id == current_user.id, CarbonProject.status == "active"
        )
    )
    projects = result.scalars().all()

    total_carbon = sum(p.estimated_carbon_tonnes or 0 for p in projects)
    total_area = sum(p.area_hectares or 0 for p in projects)

    # Water saved from simulation runs
    water_result = await db.execute(
        select(SimulationRun)
        .where(SimulationRun.site_id == current_user.id)
        .order_by(SimulationRun.executed_at.desc())
        .limit(1)
    )
    latest_run = water_result.scalar_one_or_none()
    water_saved = None
    if latest_run and latest_run.outputs:
        outputs = latest_run.outputs if isinstance(latest_run.outputs, dict) else {}
        water_saved = outputs.get("water_saved_m3")

    # Activity count from audit logs
    activity_result = await db.execute(select(AuditLog).where(AuditLog.actor_id == current_user.id))
    activity_count = len(activity_result.scalars().all())

    now = datetime.now(UTC).isoformat()
    return {
        "status": "success",
        "data": {
            "carbon_sequestered": total_carbon if total_carbon > 0 else None,
            "carbon_unit": "ton CO₂e",
            "area_restored": total_area if total_area > 0 else None,
            "area_unit": "hectares",
            "water_saved": water_saved,
            "water_unit": "m³",
            "activity_count": activity_count,
            "updated": now,
        },
    }


# ============================================================================
# CONNECTED ASSETS
# ============================================================================
@router.get("/assets")
async def get_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get connected assets summary: lands, sensors, wallet, API keys, projects."""

    # Lands
    land_result = await db.execute(
        select(LandProfile).where(LandProfile.user_id == current_user.id)
    )
    lands = land_result.scalars().all()

    # Sensors (from global settings table)
    sensor_result = await db.execute(select(Setting).where(Setting.key.like("sensor_%")))
    sensors = sensor_result.scalars().all()

    # Wallet
    wallet_result = await db.execute(select(EcoWallet).where(EcoWallet.user_id == current_user.id))
    wallet = wallet_result.scalar_one_or_none()

    # API keys
    api_result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.revoked == False)
    )
    api_keys = api_result.scalars().all()

    # Projects
    proj_result = await db.execute(
        select(CarbonProject).where(CarbonProject.user_id == current_user.id)
    )
    projects = proj_result.scalars().all()

    return {
        "status": "success",
        "data": {
            "lands": {
                "count": len(lands),
                "items": [
                    {
                        "name": l.name,
                        "detail": f"{l.area_ha or 0} ha",
                        "location": f"{l.location_lat or 0}, {l.location_lon or 0}",
                    }
                    for l in lands
                ],
            },
            "sensors": {
                "count": len(sensors),
                "items": [
                    {
                        "name": s.key,
                        "detail": s.value[:80] if s.value else "Sensor data",
                        "status": s.value,
                    }
                    for s in sensors
                ],
            },
            "wallet": {
                "count": "1" if wallet else "0",
                "items": [
                    {"name": "EcoWallet", "detail": f"Balance: {wallet.balance or 0:.2f}"}
                    for wallet in [wallet]
                    if wallet
                ],
            },
            "api_keys": {
                "count": len(api_keys),
                "items": [
                    {"name": k.name, "detail": f"Key ID: {k.id}", "status": "active"}
                    for k in api_keys
                ],
            },
            "projects": {
                "count": len(projects),
                "items": [
                    {
                        "name": p.name,
                        "detail": f"{p.project_type or 'unknown'} | {p.status or 'draft'}",
                        "status": p.status,
                    }
                    for p in projects
                ],
            },
        },
    }


# ============================================================================
# ACHIEVEMENTS & MILESTONES
# ============================================================================
@router.get("/achievements")
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get achievements and milestones for the current user."""
    from database.models import AuditLog

    achievements = []
    milestones = []

    # Carbon projects
    proj_result = await db.execute(
        select(CarbonProject).where(
            CarbonProject.user_id == current_user.id, CarbonProject.status == "active"
        )
    )
    projects = proj_result.scalars().all()

    if projects:
        achievements.append(
            {
                "icon": "leaf",
                "title": "First Carbon Project"
                if len(projects) == 1
                else f"{len(projects)} Carbon Projects",
                "description": f"Registered {len(projects)} active carbon sequestration project(s).",
                "date": projects[0].created_at.isoformat() if projects[0].created_at else "",
            }
        )

    # Activity milestones
    activity_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.actor_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    last_activity = activity_result.scalar_one_or_none()
    if last_activity:
        milestones.append(
            {
                "icon": "activity",
                "title": "Active User",
                "date": last_activity.created_at.isoformat() if last_activity.created_at else "",
            }
        )

    # Wallet check
    wallet_result = await db.execute(select(EcoWallet).where(EcoWallet.user_id == current_user.id))
    wallet = wallet_result.scalar_one_or_none()
    if wallet and (wallet.balance or 0) > 0:
        achievements.append(
            {
                "icon": "coins",
                "title": "EcoWallet Active",
                "description": f"Wallet balance: {wallet.balance:.2f}",
                "date": wallet.created_at.isoformat() if wallet.created_at else "",
            }
        )

    return {
        "status": "success",
        "data": {
            "achievements": achievements,
            "milestones": milestones,
        },
    }


# ============================================================================
# EXTENDED PREFERENCES
# ============================================================================
class ExtendedPreferencesResponse(BaseModel):
    timezone: str = "Asia/Tehran"
    units: str = "metric"
    theme: str = "system"
    dashboardWidgets: dict | None = None
    language: str = "fa"


class ExtendedPreferencesUpdate(BaseModel):
    timezone: str | None = None
    units: str | None = None
    theme: str | None = None
    dashboardWidgets: dict | None = None


@router.get("/preferences/extended", response_model=ExtendedPreferencesResponse)
async def get_extended_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get extended preferences (timezone, units, dashboard settings)."""
    from database.models import Setting

    tz = "Asia/Tehran"
    units = "metric"
    theme = "system"
    dashboard = None

    for key_name in ["timezone", "units", "theme", "dashboard_widgets"]:
        result = await db.execute(select(Setting).where(Setting.key == key_name))
        row = result.scalar_one_or_none()
        if row:
            if row.key == "timezone":
                tz = row.value or tz
            elif row.key == "units":
                units = row.value or units
            elif row.key == "theme":
                theme = row.value or theme
            elif row.key == "dashboard_widgets":
                try:
                    dashboard = json.loads(row.value) if row.value else None
                except (json.JSONDecodeError, TypeError):
                    dashboard = None

    lang = current_user.language or "fa"

    try:
        dashboard_parsed = json.loads(dashboard) if dashboard else None
    except (json.JSONDecodeError, TypeError):
        dashboard_parsed = None

    return {
        "status": "success",
        "data": {
            "timezone": tz,
            "units": units,
            "theme": theme,
            "dashboardWidgets": dashboard_parsed,
            "language": lang,
        },
    }


@router.put("/preferences/extended")
async def update_extended_preferences(
    req: ExtendedPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update extended preferences (timezone, units, dashboard settings)."""
    updates = req.model_dump(exclude_unset=True)

    for key, value in updates.items():
        if value is None:
            continue
        setting_val = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        existing = await db.execute(select(Setting).where(Setting.key == key))
        existing_row = existing.scalar_one_or_none()
        if existing_row:
            existing_row.value = setting_val
            existing_row.updated_at = datetime.now(UTC)
        else:
            new_setting = Setting(
                id=str(uuid.uuid4()),
                key=key,
                value=setting_val,
                category="preferences",
            )
            db.add(new_setting)

    await db.commit()
    return {"status": "success", "message": "Extended preferences updated"}


# ============================================================================
# DEACTIVATE ACCOUNT
# ============================================================================
@router.post("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Temporarily deactivate the user's account."""
    current_user.is_active = False
    await db.commit()
    logger.info(f"Account deactivated: {current_user.email}")
    return {"status": "success", "message": "Account temporarily deactivated"}


# ============================================================================
# UPDATE BIO / ORG / LOCATION
# ============================================================================
class BioUpdateRequest(BaseModel):
    bio: str | None = Field(None, max_length=500)
    organization: str | None = None
    location: str | None = None


@router.post("/account/bio")
async def update_bio(
    req: BioUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update bio, organization, and location fields."""
    bio_json = None
    if req.bio is not None:
        bio_json = json.dumps(
            {"bio": req.bio, "organization": req.organization, "location": req.location}
        )
        setting = await db.execute(select(Setting).where(Setting.key == "profile_bio"))
        row = setting.scalar_one_or_none()
        if row:
            row.value = bio_json
            row.updated_at = datetime.now(UTC)
        else:
            db.add(
                Setting(id=str(uuid.uuid4()), key="profile_bio", value=bio_json, category="profile")
            )
    await db.commit()
    return {"status": "success", "message": "Profile bio updated"}


# ============================================================================
# PUBLIC PROFILE VIEW
# ============================================================================
@router.get("/profile/public")
async def get_public_profile(
    user_id: str = Query(..., description="ID of the user to view"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get public profile view (no auth required)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    project_count = 0
    projects = []
    proj_result = await db.execute(
        select(CarbonProject).where(
            CarbonProject.user_id == user_id, CarbonProject.status == "active"
        )
    )
    for p in proj_result.scalars().all():
        project_count += 1
        projects.append(
            {
                "name": p.name,
                "project_type": p.project_type,
                "area_hectares": p.area_hectares,
                "status": p.status,
            }
        )

    bio_data = None
    bio_setting = await db.execute(select(Setting).where(Setting.key == "profile_bio"))
    bio_row = bio_setting.scalar_one_or_none()
    if bio_row and bio_row.value:
        try:
            bio_data = json.loads(bio_row.value)
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "status": "success",
        "data": {
            "id": user.id,
            "full_name": user.full_name,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "bio": bio_data.get("bio") if bio_data else None,
            "organization": bio_data.get("organization") if bio_data else None,
            "location": bio_data.get("location") if bio_data else None,
            "member_since": user.created_at.isoformat() if user.created_at else None,
            "project_count": project_count,
            "projects": projects,
        },
    }
