"""Authentication router - Production grade (Phase 0 rewrite).

Handles user registration, login, password reset, profile updates, and
demo seed endpoints. All sensitive actions are audit-logged via AuditLog
model using the canonical schema (actor_id, action, resource_type,
resource_id, details JSON, ip_address).

Contract stability: Public API (paths, request/response shapes) is
backward compatible. Internal refactoring includes:
- Structured logging with extra fields
- IP address capture for audit trail
- Environment guard on /seed-demo
- Defensive None safety throughout
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import EcoWallet, PasswordResetToken, User
from services.admin.models import AuditLog
from services.api_gateway.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    role_of,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# Request / Response Schemas
# ============================================================================
class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(
        default="regular",
        pattern=r"^(farmer|researcher|organization|tourist|regular)$",
    )
    phone: str | None = None
    date_of_birth: str | None = None  # YYYY-MM-DD
    country: str | None = None
    city: str | None = None
    address: str | None = None
    language: str = Field(default="fa", pattern=r"^(fa|en|ar|tr)$")
    avatar_url: str | None = None
    accept_tos: bool = False
    accept_privacy: bool = False


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Password reset request payload."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset payload (token + new password)."""

    token: str
    new_password: str = Field(min_length=6, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Change password payload (authenticated)."""

    current_password: str
    new_password: str = Field(min_length=6, max_length=100)


class ProfileUpdateRequest(BaseModel):
    """Partial profile update payload."""

    full_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = None
    date_of_birth: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    language: str | None = Field(None, pattern=r"^(fa|en|ar|tr)$")
    avatar_url: str | None = None


class UserResponse(BaseModel):
    """Public user representation.

    NOTE on field types:
    - `id` is str because User.id is a UUID column (serialized as string)
    - Optional string fields default to None to tolerate legacy rows
      where these columns were nullable in the User table.
    """

    id: str
    email: str
    full_name: str | None = None
    role: str | None = None
    language: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    is_email_verified: bool = False
    is_active: bool = True
    created_at: datetime


class TokenResponse(BaseModel):
    """Auth token response with embedded user profile."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    """Refresh token payload."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True
    data: dict[str, Any] | None = None


# ============================================================================
# Helpers
# ============================================================================
def _user_to_response(user: User) -> UserResponse:
    """Convert User ORM instance to UserResponse DTO.

    Defensive: uses getattr with defaults to tolerate None values in
    optional columns and ensures id is always a string.
    """
    return UserResponse(
        id=str(getattr(user, "id", "")),
        email=getattr(user, "email", "") or "",
        full_name=getattr(user, "full_name", None),
        role=getattr(user, "role", None),
        language=getattr(user, "language", None),
        phone=getattr(user, "phone", None),
        country=getattr(user, "country", None),
        city=getattr(user, "city", None),
        avatar_url=getattr(user, "avatar_url", None),
        is_email_verified=bool(getattr(user, "is_email_verified", False)),
        is_active=bool(getattr(user, "is_active", True)),
        created_at=getattr(user, "created_at", None) or datetime.now(timezone.utc),
    )


def _parse_date_of_birth(raw: str | None):
    """Parse YYYY-MM-DD string to date or raise ValueError."""
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _extract_client_ip(request: Request | None) -> str | None:
    """Safely extract client IP from request, with proxy awareness."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is None:
        return None
    return request.client.host


def _write_audit_log(
    db: Session,
    *,
    action: str,
    actor_id: Any | None = None,
    actor_email: str | None = None,
    target: str | None = None,
    result: str = "ok",
    ip_address: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Persist an AuditLog entry using the canonical schema.

    The AuditLog model exposes: id, actor_id (String 100), action,
    resource_type, resource_id, details (JSON), ip_address, created_at.
    Auxiliary metadata (actor_email, login_method, result) is stored
    inside the JSON `details` column to keep the schema stable.
    """
    details: dict[str, Any] = {
        "actor_email": actor_email,
        "result": result,
    }
    if extra:
        details.update(extra)

    resource_type: str | None = None
    resource_id: str | None = None
    if target and ":" in target:
        resource_type, resource_id = target.split(":", 1)

    db.add(
        AuditLog(
            actor_id=str(actor_id) if actor_id is not None else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
    )


# ============================================================================
# REGISTER
# ============================================================================
@router.post("/register", response_model=TokenResponse)
def register(
    req: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new user with full profile information.

    Legal compliance: accept_tos and accept_privacy must both be true.
    On success an EcoWallet is provisioned automatically and the user
    is logged in immediately (auto-login).
    """
    if not req.accept_tos or not req.accept_privacy:
        raise HTTPException(
            status_code=400,
            detail="accept_tos and accept_privacy must be true",
        )

    if db.query(User).filter(User.email == req.email).first() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        dob = _parse_date_of_birth(req.date_of_birth)
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid date_of_birth format (use YYYY-MM-DD)",
        ) from err

    user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
        phone=req.phone,
        date_of_birth=dob,
        country=req.country,
        city=req.city,
        address=req.address,
        language=req.language,
        avatar_url=req.avatar_url,
        is_email_verified=False,  # In production: send verification email
        is_active=True,
        accept_tos=True,
        accept_privacy=True,
    )
    db.add(user)
    db.flush()

    wallet = EcoWallet(
        user_id=user.id,
        balance=0.0,
        total_earned=0.0,
        total_redeemed=0.0,
    )
    db.add(wallet)
    db.commit()
    db.refresh(user)

    logger.info(
        "user.registered",
        extra={"email": user.email, "role": user.role, "language": user.language},
    )

    _write_audit_log(
        db,
        action="auth.register",
        actor_id=user.id,
        actor_email=user.email,
        target=f"user:{user.id}",
        result="ok",
        ip_address=_extract_client_ip(request),
    )
    db.commit()

    access_token = create_access_token(
        {"user_id": str(user.id)}, subject=str(user.id), role=user.role or "farmer"
    )
    refresh_token = create_refresh_token(
        {}, subject=str(user.id), role=role_of(user)
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


# ============================================================================
# LOGIN
# ============================================================================
@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with email + password and issue JWT pair."""
    client_ip = _extract_client_ip(request)
    user = db.query(User).filter(User.email == req.email).first()

    if user is None or not verify_password(req.password, user.hashed_password):
        logger.warning(
            "user.login.failed",
            extra={"email": req.email, "reason": "bad_credentials"},
        )
        _write_audit_log(
            db,
            action="auth.login",
            actor_email=req.email,
            target=f"user:{req.email}",
            result="failed",
            ip_address=client_ip,
            extra={"reason": "bad_credentials"},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        logger.warning(
            "user.login.failed",
            extra={"email": req.email, "reason": "disabled"},
        )
        _write_audit_log(
            db,
            action="auth.login",
            actor_id=user.id,
            actor_email=req.email,
            target=f"user:{user.id}",
            result="failed",
            ip_address=client_ip,
            extra={"reason": "account_disabled"},
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Account disabled")

    logger.info(
        "user.login.success",
        extra={"email": user.email, "role": user.role},
    )
    _write_audit_log(
        db,
        action="auth.login",
        actor_id=user.id,
        actor_email=user.email,
        target=f"user:{user.id}",
        result="ok",
        ip_address=client_ip,
        extra={"role": user.role or "farmer"},
    )
    db.commit()

    access_token = create_access_token(
        {"user_id": str(user.id)}, subject=str(user.id), role=user.role or "farmer"
    )
    refresh_token = create_refresh_token(
        {}, subject=str(user.id), role=role_of(user)
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


# ============================================================================
# ME
# ============================================================================
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return _user_to_response(current_user)


# ============================================================================
# FORGOT PASSWORD
# ============================================================================
@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Request a password reset link.

    Always returns a generic message to prevent email enumeration.
    In development environments the reset URL is included in the
    response data for testing convenience.
    """
    user = db.query(User).filter(User.email == req.email).first()
    generic_msg = "If an account exists with this email, a reset link has been sent."

    if user is None:
        return MessageResponse(message=generic_msg)

    # Invalidate any outstanding tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,  # noqa: E712 (SQLAlchemy idiom)
    ).update({"used": True})

    reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
    db.add(reset_token)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    is_dev = "127.0.0.1" in base_url or "localhost" in base_url
    frontend_url = "http://localhost:3000" if is_dev else base_url
    reset_url = f"{frontend_url}/reset-password?token={reset_token.token}"

    logger.info("user.password_reset.requested", extra={"email": user.email})

    _write_audit_log(
        db,
        action="auth.password_reset.request",
        actor_id=user.id,
        actor_email=user.email,
        target=f"user:{user.id}",
        result="ok",
        ip_address=_extract_client_ip(request),
    )
    db.commit()

    return MessageResponse(
        message=generic_msg,
        data={"reset_url": reset_url, "token": reset_token.token} if is_dev else None,
    )


# ============================================================================
# RESET PASSWORD
# ============================================================================
@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    req: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Set a new password using a valid, unexpired reset token."""
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == req.token)
        .first()
    )
    if reset_token is None or not reset_token.is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    reset_token.used = True
    db.commit()

    logger.info("user.password_reset.completed", extra={"email": user.email})
    _write_audit_log(
        db,
        action="auth.password_reset.complete",
        actor_id=user.id,
        actor_email=user.email,
        target=f"user:{user.id}",
        result="ok",
        ip_address=_extract_client_ip(request),
    )
    db.commit()

    return MessageResponse(message="Password has been reset successfully")


# ============================================================================
# CHANGE PASSWORD
# ============================================================================
@router.post("/change-password", response_model=MessageResponse)
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Change password for the currently authenticated user."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()

    logger.info("user.password.changed", extra={"email": current_user.email})
    _write_audit_log(
        db,
        action="auth.password.change",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target=f"user:{current_user.id}",
        result="ok",
        ip_address=_extract_client_ip(request),
    )
    db.commit()

    return MessageResponse(message="Password changed successfully")


# ============================================================================
# UPDATE PROFILE
# ============================================================================
@router.put("/profile", response_model=UserResponse)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's profile (partial update)."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.date_of_birth is not None:
        try:
            current_user.date_of_birth = _parse_date_of_birth(req.date_of_birth)
        except ValueError as err:
            raise HTTPException(
                status_code=400, detail="Invalid date_of_birth format"
            ) from err
    if req.country is not None:
        current_user.country = req.country
    if req.city is not None:
        current_user.city = req.city
    if req.address is not None:
        current_user.address = req.address
    if req.language is not None:
        current_user.language = req.language
    if req.avatar_url is not None:
        if len(req.avatar_url) > 2_000_000:
            raise HTTPException(
                status_code=400, detail="Avatar image too large (max 2MB encoded)"
            )
        current_user.avatar_url = req.avatar_url

    db.commit()
    db.refresh(current_user)
    return _user_to_response(current_user)


# ============================================================================
# REFRESH TOKEN
# ============================================================================
@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    req: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rotate a valid refresh token for a new access/refresh pair."""
    payload = decode_refresh_token(req.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    try:
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except (KeyError, TypeError, ValueError) as err:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from err

    # Support both integer and UUID user IDs (model uses UUID)
    from sqlalchemy import select

    user = db.query(User).filter(User.id == user_id_str).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(
        {"type": "access", "user_id": str(user.id)},
        subject=str(user.id),
        role=role_of(user),
    )
    refresh_token = create_refresh_token(
        {}, subject=str(user.id), role=role_of(user)
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


# ============================================================================
# SEED DEMO USERS (development only)
# ============================================================================
_DEMO_SEEDS: list[dict[str, str]] = [
    {"email": "test@demo.com", "password": "demo123", "name": "Test Demo User", "role": "regular", "lang": "en"},
    {"email": "farmer@test.com", "password": "farmer123", "name": "Demo Farmer", "role": "farmer", "lang": "fa"},
    {"email": "researcher@test.com", "password": "research123", "name": "Demo Researcher", "role": "researcher", "lang": "fa"},
    {"email": "org@test.com", "password": "org123", "name": "Demo Organization", "role": "organization", "lang": "en"},
    {"email": "admin@test.com", "password": "admin123", "name": "Admin User", "role": "regular", "lang": "en"},
]


@router.post("/seed-demo", response_model=MessageResponse)
def seed_demo_users(db: Session = Depends(get_db)) -> MessageResponse:
    """Create/update demo users for testing.

    Gated by ECO_NOJIN_ALLOW_SEED=1 environment variable to prevent
    accidental execution in production.
    """
    if os.getenv("ECO_NOJIN_ALLOW_SEED", "0") != "1":
        raise HTTPException(
            status_code=403,
            detail="Demo seeding is disabled. Set ECO_NOJIN_ALLOW_SEED=1 to enable.",
        )

    created: list[str] = []
    updated: list[str] = []

    for seed in _DEMO_SEEDS:
        existing = db.query(User).filter(User.email == seed["email"]).first()
        if existing is not None:
            existing.hashed_password = hash_password(seed["password"])
            existing.role = seed["role"]
            existing.language = seed["lang"]
            updated.append(seed["email"])
            continue

        user = User(
            email=seed["email"],
            full_name=seed["name"],
            hashed_password=hash_password(seed["password"]),
            role=seed["role"],
            language=seed["lang"],
            is_active=True,
            accept_tos=True,
            accept_privacy=True,
        )
        db.add(user)
        db.flush()
        wallet = EcoWallet(user_id=user.id, balance=100.0)
        db.add(wallet)
        created.append(seed["email"])

    db.commit()
    logger.info(
        "demo.seed.completed",
        extra={"created": len(created), "updated": len(updated)},
    )
    return MessageResponse(
        message=f"Created: {len(created)}, Updated: {len(updated)}",
        data={"created": created, "updated": updated, "credentials": _DEMO_SEEDS},
    )