"""Complete authentication router - Phase 0 rewrite (Async version).

Week 2 fix: converted all endpoints to async to fix SQLite thread-safety
issues when used with async FastAPI test clients and production deployments.
"""

import structlog
import logging
import os
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from engine.hydroma.config.settings import get_settings
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database.hub import hub
from database.models import AuditLog, EcoWallet, PasswordResetToken, User, OAuthConnection, ApiKey
from services.api_gateway.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    role_of,
    verify_password,
)

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
async def _write_auth_audit(db: AsyncSession, *, email: str, action: str, result: str,
                      ip_address: str = "unknown", user_agent: str = "unknown",
                      actor_id: str = None):
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
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(
        default="regular", pattern="^(farmer|researcher|organization|tourist|regular)$"
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
    new_password: str = Field(min_length=6, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=100)


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
@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
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

    # Auto-login
    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    return TokenResponse(
        access_token=token,
        refresh_token=create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        user=user_to_response(user),
    )


# ============================================================================
# LOGIN
# ============================================================================
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
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
    return TokenResponse(
        access_token=token,
        refresh_token=create_refresh_token({}, subject=str(user.id), role=role_of(user)),
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
async def forgot_password(req: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
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
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == req.token))
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
async def refresh_token_endpoint(req: RefreshRequest, db: AsyncSession = Depends(get_async_db)):
    """Refresh access token via a valid refresh token (rotation)."""
    payload = decode_refresh_token(req.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    try:
        user_id = payload["sub"]
    except (KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token = create_access_token({"type": "access"}, subject=str(user.id), role=role_of(user))
    return TokenResponse(
        access_token=access_token,
        refresh_token=create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        user=user_to_response(user),
    )


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
            "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
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
            "type": log.action.split('.')[-1] if log.action else "unknown",
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
            OAuthConnection.revoked == False if hasattr(OAuthConnection, 'revoked') else None,
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
    """Connect an OAuth provider to the current user."""
    existing = await db.execute(
        select(OAuthConnection).where(
            OAuthConnection.user_id == current_user.id,
            OAuthConnection.provider == req.provider,
        )
    )
    conn = existing.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = req.auth_code
        conn.updated_at = datetime.now(UTC)
    else:
        conn = OAuthConnection(
            user_id=current_user.id,
            provider=req.provider,
            access_token_encrypted=req.auth_code,
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
    import secrets
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
    two_fa_enabled = bool(getattr(current_user, 'two_factor_enabled', False))
    return {
        "status": "success",
        "data": {
            "enabled": two_fa_enabled,
            "method": getattr(current_user, 'two_factor_method', None),
        },
    }


@router.post("/2fa/toggle")
async def toggle_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Toggle 2FA for the current user (stored in user preferences)."""
    import uuid
    pref_key = f"2fa_enabled_{current_user.id}"
    try:
        from database.hub import hub as _hub
        conn = _hub.get_sqlite("manual")
        from sqlalchemy import text
        existing = conn.execute(text(f"SELECT value FROM settings WHERE key = '{pref_key}'")).fetchone()
        current_val = existing[0] if existing else "false"
        new_val = "false" if current_val == "true" else "true"
        if existing:
            conn.execute(text(f"UPDATE settings SET value = '{new_val}' WHERE key = '{pref_key}'"))
        else:
            conn.execute(text(f"INSERT INTO settings (key, value, category) VALUES ('{pref_key}', '{new_val}', 'security')"))
        conn.commit()
        enabled = new_val == "true"
        return {"status": "success", "data": {"enabled": enabled, "message": f"2FA {'enabled' if enabled else 'disabled'}"}}
    except Exception as e:
        logger.warning(f"2FA toggle failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle 2FA")
