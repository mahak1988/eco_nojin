"""Auth service — OIDC-style JWT authentication & authorization.

Implements the real auth backend used by the API gateway:
- User registration / login with bcrypt password hashing
- Role-aware JWT tokens (farmer / advisor / admin / cooperative / ngo)
- ``get_current_user`` (strict 401) and ``require_user`` / ``require_admin`` dependencies
- API-key guard for telco webhooks (USSD/SMS/Voice)

Password hashing uses the shared :mod:`services.auth.compat` hasher
(bcrypt + verified legacy PBKDF2-HMAC-SHA256 migration), not ``passlib``:
passlib 1.7.4 is broken on Python 3.12 (``passlib/context.py`` contains a
mid-file ``from __future__ import with_statement``), so importing
``passlib.context`` raises ``SyntaxError``.

Security posture (SEC-01/02/27, 2026-10-12): the request body can no longer
choose the account's role, login is rate-bounded per account via
:mod:`services.auth.lockout`, the API-key comparison is constant-time, and the
settings field names match the live ``Settings`` schema (the previous
``jwt_secret_key`` / ``jwt_access_token_minutes`` spellings raised
``AttributeError`` on every login and register call).
"""
import hmac
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from engine.hydroma.config.settings import get_settings
from services.auth.compat import password_hasher
from services.auth.lockout import (
    AccountLockedError,
    check_locked,
    register_failure,
    register_success,
)

logger = logging.getLogger(__name__)
_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

#: The only role a self-registration may hold. Everything else (admin,
#: cooperative-admin, …) is granted out-of-band by an existing administrator.
#: SEC-01: the previous schema accepted ``role`` from the request body, which
#: let any caller mint an admin account.
DEFAULT_SELF_REGISTRATION_ROLE = "farmer"


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a stored hash.

    Accepts both bcrypt hashes produced by this service and the legacy
    ``pbkdf2:<salt>:<hex>`` format written by older deployments (see
    :class:`services.auth.compat.PasswordHasher`).
    """
    return password_hasher.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def _access_token_ttl() -> timedelta:
    return timedelta(minutes=_settings.access_token_expire_minutes)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or _access_token_ttl())
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.jwt_signing_key, algorithm=_settings.jwt_algorithm)


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Strict authentication — returns the authenticated User or raises 401."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, _settings.jwt_signing_key, algorithms=[_settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def verify_api_key(
    api_key: str | None = Depends(api_key_header),
) -> dict:
    """Verify telco webhook API key (constant-time comparison, SEC-27).

    Compared as bytes: FastAPI decodes headers as latin-1, so a non-ASCII
    ``X-API-Key`` would raise ``TypeError`` in ``compare_digest`` and turn an
    unauthenticated call into a 500 instead of a 401.
    """
    expected = _settings.api_key
    if (
        not api_key
        or not expected
        or not hmac.compare_digest(api_key.encode("utf-8"), expected.encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"service": "telco"}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    # Pre-check the email: ``users.email`` carries a unique constraint, and a
    # duplicate would otherwise surface as an IntegrityError -> 500. The
    # message is deliberately distinct from the username one so a legitimate
    # retry can tell which field collided.
    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=DEFAULT_SELF_REGISTRATION_ROLE,
        is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    # ``tenant_id`` mirrors the subject: in this deployment each account is its
    # own platform/tenant. IdentityMiddleware publishes it on
    # ``request.state`` and the IoT router derives a device's ``platform_id``
    # from it — without the claim the derivation yields None and devices lose
    # their attribution (2026-10-12 review finding 4).
    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "tenant_id": str(user.id)}
    )
    return TokenResponse(access_token=token, expires_in=int(_access_token_ttl().total_seconds()))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: TokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    try:
        # Locked accounts are refused before any bcrypt work (SEC-02). The row
        # was loaded at the start of this request, so the lock state is current
        # as of that load.
        check_locked(user)
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=423,
            detail="Account temporarily locked after too many failed attempts",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    if not verify_password(body.password, user.hashed_password):
        # Atomic increment + threshold lock in one statement (SEC-02): under
        # concurrent guesses a Python-level counter would lose increments.
        await register_failure(db, user.id)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await register_success(db, user.id)
    await db.commit()
    # ``tenant_id`` mirrors the subject: each account is its own platform/tenant
    # (see the register path). IdentityMiddleware publishes it on
    # ``request.state`` for the IoT router's tenant derivation.
    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "tenant_id": str(user.id)}
    )
    return TokenResponse(access_token=token, expires_in=int(_access_token_ttl().total_seconds()))


@router.get("/me")
async def me(user: Annotated[User, Depends(require_user)]):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


def main() -> None:
    """Run the auth service (loopback by default — SEC-21).

    The port comes from ``HYDROMA_BIND_PORT`` so a manual run matches the
    supervised deployment (``runtime/services.yaml`` runs the auth service on
    8101).
    """
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HYDROMA_BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("HYDROMA_BIND_PORT", "8101")),
    )


# Create the standalone FastAPI app for this microservice

app = FastAPI(title="Eco Nojin Auth Service", version="1.0.0")
app.include_router(router)


if __name__ == "__main__":
    main()
