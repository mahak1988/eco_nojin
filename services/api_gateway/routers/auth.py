"""Complete authentication router - Phase 0 rewrite."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database.config import get_db
from services.auth.models import AuditLog, EcoWallet, PasswordResetToken
from database.models import User
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
    id: int
    email: str
    full_name: str
    role: str
    language: str
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    is_email_verified: bool
    is_active: bool
    created_at: datetime


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
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with full profile info."""
    # Legal compliance
    if not req.accept_tos or not req.accept_privacy:
        raise HTTPException(status_code=400, detail="accept_tos and accept_privacy must be true")

    # Email uniqueness
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Parse date of birth
    dob = None
    if req.date_of_birth:
        try:
            dob = datetime.strptime(req.date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date_of_birth format (use YYYY-MM-DD)"
            )

    # Create user
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
        is_email_verified=False,  # In production, send verification email
        is_active=True,
        accept_tos=True,
        accept_privacy=True,
    )
    db.add(user)
    db.flush()

    # Create EcoWallet automatically
    wallet = EcoWallet(user_id=user.id, balance=0.0, total_earned=0.0, total_redeemed=0.0)
    db.add(wallet)

    db.commit()
    db.refresh(user)

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
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        logger.warning(f"Login failed: {req.email}")
        db.add(
            AuditLog(
                actor_email=req.email,
                action="auth.login",
                target=f"user:{req.email}",
                detail="failed: bad credentials",
            )
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        db.add(
            AuditLog(
                actor_email=req.email,
                action="auth.login",
                target=f"user:{req.email}",
                detail="failed: account disabled",
            )
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Account disabled")

    logger.info(f"Login OK: {user.email}")
    db.add(
        AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            action="auth.login",
            target=f"user:{user.id}",
            detail=f"ok role={user.role or 'farmer'}",
        )
    )
    db.commit()
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
def me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)


# ============================================================================
# FORGOT PASSWORD
# ============================================================================
@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Request a password reset link. Always returns success to prevent email enumeration."""
    user = db.query(User).filter(User.email == req.email).first()

    generic_msg = "If an account exists with this email, a reset link has been sent."

    if not user:
        return MessageResponse(message=generic_msg)

    # Invalidate old tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        not PasswordResetToken.used,
    ).update({"used": True})

    # Create new token
    reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
    db.add(reset_token)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    frontend_url = (
        "http://localhost:3000"
        if "127.0.0.1:8000" in base_url or "localhost:8000" in base_url
        else base_url
    )
    reset_url = f"{frontend_url}/reset-password?token={reset_token.token}"

    # Log URL for development (in production, send via email service)
    logger.info(f"[RESET] {user.email}: {reset_url}")

    # In development, return URL for testing
    is_dev = "127.0.0.1" in base_url or "localhost" in base_url
    return MessageResponse(
        message=generic_msg,
        data={"reset_url": reset_url, "token": reset_token.token} if is_dev else None,
    )


# ============================================================================
# RESET PASSWORD
# ============================================================================
@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == req.token).first()
    if not reset_token or not reset_token.is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    reset_token.used = True
    db.commit()

    logger.info(f"Password reset OK: {user.email}")
    return MessageResponse(message="Password has been reset successfully")


# ============================================================================
# CHANGE PASSWORD
# ============================================================================
@router.post("/change-password", response_model=MessageResponse)
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    logger.info(f"Password changed: {current_user.email}")
    return MessageResponse(message="Password changed successfully")


# ============================================================================
# UPDATE PROFILE
# ============================================================================
@router.put("/profile", response_model=UserResponse)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


# ============================================================================
# SEED DEMO USERS
# ============================================================================
@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token via a valid refresh token (rotation)."""
    payload = decode_refresh_token(req.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token = create_access_token({"type": "access"}, subject=str(user.id), role=role_of(user))
    return TokenResponse(
        access_token=access_token,
        refresh_token=create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        user=user_to_response(user),
    )


@router.post("/seed-demo", response_model=MessageResponse)
def seed_demo_users(db: Session = Depends(get_db)):
    """Create demo users for testing (development only)."""
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

    created, updated = [], []
    for d in demos:
        existing = db.query(User).filter(User.email == d["email"]).first()
        if existing:
            existing.hashed_password = hash_password(d["password"])
            existing.role = d["role"]
            existing.language = d["lang"]
            updated.append(d["email"])
        else:
            user = User(
                email=d["email"],
                full_name=d["name"],
                hashed_password=hash_password(d["password"]),
                role=d["role"],
                language=d["lang"],
                is_active=True,
                accept_tos=True,
                accept_privacy=True,
            )
            db.add(user)
            db.flush()
            wallet = EcoWallet(user_id=user.id, balance=100.0)
            db.add(wallet)
            created.append(d["email"])
    db.commit()

    return MessageResponse(
        message=f"Created: {len(created)}, Updated: {len(updated)}",
        data={"created": created, "updated": updated, "credentials": demos},
    )
