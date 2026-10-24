"""Complete authentication router - Phase 0 rewrite (Async version).

S-STRUCT compliant (2026-10-07 remediation): all DB access is delegated to
``services.auth_legacy.AuthService`` and its ``AuthLegacyRepository``. The router
only parses requests, delegates to the service, and shapes responses.

Week 2 fix: converted all endpoints to async to fix SQLite thread-safety
issues when used with async FastAPI test clients and production deployments.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database.hub import hub
from database.models import RefreshToken
from engine.hydroma.config.settings import get_settings
from services.api_gateway.auth import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    role_of,
    set_auth_cookies,
)
from services.auth.lockout import AccountLockedError
from services.auth_legacy.service import AuthService, get_auth_service

logger = structlog.get_logger()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_settings = get_settings()


async def get_async_db():
    """Async DB session dependency — re-exported for other routers that import it."""
    async with hub.get_async_session() as session:
        yield session


def _resolve_user_id(user) -> str:
    return str(getattr(user, "id", user.get("sub", user.get("user_id"))))


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    role: str = Field(
        default="regular",
        pattern="^(farmer|advisor|researcher|organization|tourist|regular)$",
    )
    phone: str | None = None
    date_of_birth: str | None = None
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


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: dict | None = None


def user_to_response(u) -> UserResponse:
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
# Rate limiting
# ============================================================================
from services.api_gateway.errors import domain_detail
from services.api_gateway.security import RateLimitMiddleware


def _auth_rate_limit_enabled() -> bool:
    """Read HYDROMA_AUTH_RATE_LIMIT_ENABLED for the route-level auth limiters.

    The global token-bucket middleware (services.api_gateway.middleware.rate_limit)
    reads this same var; these in-router limiters must agree, otherwise the
    contract test suite sleeps its way through the 60s window after 5 registrations.
    """
    raw = os.getenv("HYDROMA_AUTH_RATE_LIMIT_ENABLED")
    if raw is None or not raw.strip():
        return True
    return raw.strip().lower() not in {"false", "0", "no", "off"}


_register_limiter = RateLimitMiddleware(
    None, redis_client=None, limit=5, window=60,
    enabled=_auth_rate_limit_enabled(),
)
_forgot_limiter = RateLimitMiddleware(
    None, redis_client=None, limit=3, window=60,
    enabled=_auth_rate_limit_enabled(),
)


async def _check_register_rate_limit(request: Request) -> None:
    allowed, _remaining, _reset = _register_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Try again later.",
            headers={"Retry-After": str(_register_limiter.window_seconds)},
        )


async def _check_forgot_rate_limit(request: Request) -> None:
    allowed, _remaining, _reset = _forgot_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset attempts. Try again later.",
            headers={"Retry-After": str(_forgot_limiter.window_seconds)},
        )


# ============================================================================
# REGISTER
# ============================================================================
@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    req: RegisterRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(_check_register_rate_limit)],
):
    """Register a new user with full profile info."""
    if not req.accept_tos or not req.accept_privacy:
        raise HTTPException(status_code=400, detail="accept_tos and accept_privacy must be true")

    try:
        user = await service.register_user(
            email=req.email,
            full_name=req.full_name,
            password=req.password,
            role=req.role,
            phone=req.phone,
            date_of_birth=req.date_of_birth,
            country=req.country,
            city=req.city,
            address=req.address,
            language=req.language,
            avatar_url=req.avatar_url,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Role cannot be self-assigned")
    except ValueError:
        raise HTTPException(status_code=400, detail="Email already registered")

    token, refresh_token, _ = await service.issue_tokens(user, response)
    await service.publish_register_event(user, request)

    logger.info(f"Registered: {user.email} role={user.role} lang={user.language}")
    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user=user_to_response(user),
    )


class BootstrapAdminRequest(BaseModel):
    email: EmailStr


@router.post("/bootstrap-admin")
async def bootstrap_first_admin(
    request: Request,
    req: BootstrapAdminRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Local, explicitly enabled first-admin bootstrap for development."""
    client_host = request.client.host if request.client else ""
    if os.getenv("ECO_NOJIN_ENABLE_ADMIN_BOOTSTRAP") != "1":
        raise HTTPException(status_code=404, detail="Not found")
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=403, detail="Local access required")
    if not await service.bootstrap_first_admin(str(req.email).lower()):
        raise HTTPException(
            status_code=409,
            detail="Account not found or an administrator is already configured",
        )
    return {"message": "Initial administrator configured"}


# ============================================================================
# LOGIN
# ============================================================================
@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Login with email and password."""
    try:
        user = await service.authenticate(req.email, req.password)
    except AccountLockedError as exc:
        # SEC-02: per-account lockout — distinct from a wrong password so the
        # client knows to back off, with Retry-After for well-behaved callers.
        await service.write_audit(
            email=req.email,
            action="auth.login",
            result="locked",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        raise HTTPException(
            status_code=423,
            detail="Account temporarily locked after too many failed attempts",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    if not user or not user.is_active:
        await service.write_audit(
            email=req.email,
            action="auth.login",
            result="failed",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info(f"Login OK: {user.email}")
    await service.write_audit(
        email=user.email,
        action="auth.login",
        result="success",
        actor_id=str(user.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    token, refresh_token, _ = await service.issue_tokens(user, response)
    await service.publish_login_event(user, request)

    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user=user_to_response(user),
    )


# ============================================================================
# ME
# ============================================================================
@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[Any, Depends(get_current_user)]):
    return user_to_response(current_user)


# ============================================================================
# FORGOT PASSWORD
# ============================================================================
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(_check_forgot_rate_limit)],
):
    """Request a password reset link. Always returns success to prevent email enumeration."""
    generic_msg = "If an account exists with this email, a reset link has been sent."

    user_exists, reset_url, token = await service.request_reset(req.email)
    if not user_exists:
        return MessageResponse(message=generic_msg)

    is_dev = os.environ.get("APP_ENV", "development") != "production"
    return MessageResponse(
        message=generic_msg,
        data={"reset_url": reset_url, "token": token} if is_dev else None,
    )


# ============================================================================
# RESET PASSWORD
# ============================================================================
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    req: ResetPasswordRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        user = await service.reset_password(req.token, req.new_password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    except LookupError:
        raise HTTPException(status_code=400, detail="User not found")

    logger.info(f"Password reset OK: {user.email}")
    return MessageResponse(message="Password has been reset successfully")


# ============================================================================
# CHANGE PASSWORD
# ============================================================================
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        await service.change_password(current_user, req.current_password, req.new_password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    logger.info(f"Password changed: {current_user.email}")
    return MessageResponse(message="Password changed successfully")


# ============================================================================
# UPDATE PROFILE
# ============================================================================
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        user = await service.update_profile(current_user, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=domain_detail(e, 400))
    return user_to_response(user)


# ============================================================================
# REFRESH TOKEN
# ============================================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    req: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Refresh access token via a valid refresh token (rotation with revocation).

    H12 FIX: Implements refresh token rotation - old refresh token is revoked
    and a new one is issued. This prevents replay attacks.
    """
    refresh_token = req.refresh_token or request.cookies.get("econojin_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    try:
        user_id = payload["sub"]
        token_jti = payload.get("jti")
    except (KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        user = await service.refresh_tokens(refresh_token, user_id, token_jti)
    except ValueError:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    new_jti = secrets.token_urlsafe(16)
    access_token = create_access_token(
        {"type": "access", "jti": new_jti}, subject=str(user.id), role=role_of(user)
    )
    new_refresh_token = create_refresh_token(
        {"jti": new_jti}, subject=str(user.id), role=role_of(user)
    )
    new_refresh_record = RefreshToken(
        jti=new_jti,
        user_id=user.id,
        revoked=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=_settings.refresh_token_expire_minutes),
    )
    await service.repo.save_refresh_token(new_refresh_record)
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
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[Any, Depends(get_current_user)],
    req: LogoutRequest | None = None,
    service: Annotated[AuthService, Depends(get_auth_service)] = None,
):
    """Logout - revokes the active refresh token and clears auth cookies."""
    refresh_token = req.refresh_token if req else request.cookies.get("econojin_refresh_token")
    await service.logout(refresh_token, current_user)
    clear_auth_cookies(response)
    logger.info(f"Logout: {current_user.email}")
    return MessageResponse(message="Logged out successfully")


# ============================================================================
# SEED DEMO USERS
# ============================================================================
@router.post("/seed-demo", response_model=MessageResponse)
async def seed_demo_users(service: Annotated[AuthService, Depends(get_auth_service)]):
    """Create demo users for testing.

    Hard guard (pentest fix C1): returns 404 unless the process runs in a
    development/test environment AND the operator explicitly opts in via
    ECO_NOJIN_ALLOW_SEED=1. Existing accounts are never overwritten.
    """
    from engine.hydroma.config.settings import get_settings
    settings = get_settings()
    envs = {
        str(getattr(settings, "app_env", "") or "").strip().lower(),
        str(getattr(settings, "environment", "") or "").strip().lower(),
    }
    if not (envs & {"development", "test", "dev"}) or os.getenv("ECO_NOJIN_ALLOW_SEED") != "1":
        raise HTTPException(status_code=404, detail="Not found")

    created, skipped = await service.seed_demo_users()
    return MessageResponse(
        message=f"Created: {len(created)}, Skipped: {len(skipped)}",
        data={"created": created, "skipped": skipped},
    )


class OAuthConnectRequest(BaseModel):
    provider: str = Field(..., pattern="^(google|github|microsoft)$")
    auth_code: str


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# ACCOUNT STATUS
# ============================================================================
@router.get("/account/status")
async def get_account_status(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.get_account_status(current_user)


# ============================================================================
# ACTIVITY HISTORY
# ============================================================================
@router.get("/activity/history")
async def get_activity_history(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    return await service.get_activity_history(str(current_user.id), limit)


# ============================================================================
# OAUTH CONNECTIONS
# ============================================================================
@router.get("/oauth/connections")
async def list_oauth_connections(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.list_oauth_connections(str(current_user.id))


@router.post("/oauth/connect")
async def connect_oauth(
    req: OAuthConnectRequest,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.connect_oauth(req.provider, req.auth_code, str(current_user.id))


@router.delete("/oauth/disconnect/{provider}")
async def disconnect_oauth(
    provider: str,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        return await service.disconnect_oauth(provider, str(current_user.id))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=domain_detail(e, 404))


# ============================================================================
# API KEYS
# ============================================================================
@router.get("/api-keys")
async def list_api_keys(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.list_api_keys(str(current_user.id))


@router.post("/api-keys")
async def create_api_key(
    req: ApiKeyCreateRequest,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.create_api_key(req.name, str(current_user.id))


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        return await service.revoke_api_key(key_id, str(current_user.id))
    except LookupError:
        raise HTTPException(status_code=404, detail="API key not found")


# ============================================================================
# 2FA
# ============================================================================
@router.get("/2fa/status")
async def get_2fa_status(
    current_user: Annotated[Any, Depends(get_current_user)],
):
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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        result = await service.toggle_2fa(current_user)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=domain_detail(e, 500))
    return {"status": "success", "data": result}


# ============================================================================
# SESSIONS
# ============================================================================
@router.get("/sessions")
async def list_sessions(current_user: Annotated[Any, Depends(get_current_user)]):
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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Revoke a specific session."""
    try:
        return await service.revoke_session(session_id, current_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Revoke all sessions except the current one."""
    token = getattr(current_user, "_request_token_jti", None)
    return await service.revoke_all_sessions(current_user, token)


# ============================================================================
# REFERRAL
# ============================================================================
@router.get("/referral")
async def get_referral(current_user: Annotated[Any, Depends(get_current_user)]):
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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.get_security_audit(str(current_user.id))


# ============================================================================
# RATE LIMIT
# ============================================================================
@router.get("/rate-limit")
async def get_rate_limit(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get current rate limit status."""
    return await service.get_rate_limit(current_user)


# ============================================================================
# EMAIL CHANGE
# ============================================================================
@router.post("/email/change-request")
async def request_email_change(
    req: dict,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Request an email change with verification code."""
    new_email = req.get("email") or req.get("new_email")
    return await service.request_email_change(current_user, new_email)


@router.post("/email/change-confirm")
async def confirm_email_change(
    req: dict,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Confirm email change with verification code."""
    token = req.get("token")
    return await service.confirm_email_change(current_user, token)


# ============================================================================
# NOTIFICATIONS
# ============================================================================
@router.get("/notifications")
async def get_notifications(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get notification preferences."""
    return await service.get_notifications(current_user)


@router.put("/notifications")
async def update_notifications(
    req: dict,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Update notification preferences."""
    return await service.update_notifications(current_user, req)


# ============================================================================
# PREFERENCES
# ============================================================================
@router.get("/preferences")
async def get_preferences(current_user: Annotated[Any, Depends(get_current_user)]):
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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Update user preferences."""
    return await service.update_preferences(current_user, req.get("language"))


# ============================================================================
# DATA EXPORT
# ============================================================================
@router.post("/export-data")
async def export_data(current_user: Annotated[Any, Depends(get_current_user)]):
    """Export all user data as a JSON download.

    Not implemented. An earlier version returned a 200 with a download URL
    pointing at ``/export-data/download?token=placeholder``, an endpoint that
    does not exist. A caller was told the export had worked and received
    nothing, which is the worst possible answer for a data-access request: it
    reads as a completed right of access.

    Refusing honestly is the correct behaviour until the export is built.
    ``S-HONEST`` requires the status envelope to match reality.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "export_not_implemented",
            "message": (
                "Personal data export is not available yet. No data was "
                "exported. This endpoint does not pretend to succeed."
            ),
        },
    )


# ============================================================================
# BILLING / SUBSCRIPTION
# ============================================================================
@router.get("/billing/subscription")
async def get_subscription(current_user: Annotated[Any, Depends(get_current_user)]):
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
            "billing": {"email": current_user.email, "payment_method": None},
        },
    }


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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get legacy metrics: carbon sequestration, area restored, water saved, activity count."""
    return await service.get_legacy_metrics(str(current_user.id))


# ============================================================================
# CONNECTED ASSETS
# ============================================================================
@router.get("/assets")
async def get_assets(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get connected assets summary: lands, sensors, wallet, API keys, projects."""
    return await service.get_assets(str(current_user.id))


# ============================================================================
# ACHIEVEMENTS & MILESTONES
# ============================================================================
@router.get("/achievements")
async def get_achievements(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get achievements and milestones for the current user."""
    return await service.get_achievements(str(current_user.id))


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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get extended preferences (timezone, units, dashboard settings)."""
    return await service.get_extended_preferences(current_user)


@router.put("/preferences/extended")
async def update_extended_preferences(
    req: ExtendedPreferencesUpdate,
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Update extended preferences (timezone, units, dashboard settings)."""
    updates = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
    return await service.update_extended_preferences(str(current_user.id), updates)


# ============================================================================
# DEACTIVATE ACCOUNT
# ============================================================================
@router.post("/deactivate")
async def deactivate_account(
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Temporarily deactivate the user's account."""
    result = await service.deactivate_account(current_user)
    logger.info(f"Account deactivated: {current_user.email}")
    return result


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
    current_user: Annotated[Any, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Update bio, organization, and location fields."""
    return await service.update_bio(
        current_user,
        req.bio,
        req.organization,
        req.location,
    )


# ============================================================================
# PUBLIC PROFILE VIEW
# ============================================================================
@router.get("/profile/public")
async def get_public_profile(
    user_id: Annotated[str, Query(description="ID of the user to view")],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Get public profile view (no auth required)."""
    try:
        return await service.get_public_profile(user_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="User not found")
