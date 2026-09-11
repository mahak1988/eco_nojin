"""Auth service — OIDC-style JWT authentication & authorization.

Implements the real auth backend used by the API gateway:
- User registration / login with bcrypt password hashing
- Role-aware JWT tokens (farmer / advisor / admin / cooperative / ngo)
- ``get_current_user`` (strict 401) and ``require_user`` / ``require_admin`` dependencies
- API-key guard for telco webhooks (USSD/SMS/Voice)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import User
from engine.hydroma.config.settings import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


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
    role: str = "farmer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=_settings.jwt_access_token_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.jwt_secret_key, algorithm=_settings.jwt_algorithm)


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Strict authentication — returns the authenticated User or raises 401."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, _settings.jwt_secret_key, algorithms=[_settings.jwt_algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
) -> dict:
    """Verify telco webhook API key."""
    if not api_key or api_key != _settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"service": "telco"}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, expires_in=_settings.jwt_access_token_minutes * 60)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: TokenRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, expires_in=_settings.jwt_access_token_minutes * 60)


@router.get("/me")
async def me(user: User = Depends(require_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


def main() -> None:
    """Run the auth service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)


# Create the standalone FastAPI app for this microservice
from fastapi import FastAPI

app = FastAPI(title="Eco Nojin Auth Service", version="1.0.0")
app.include_router(router)


if __name__ == "__main__":
    main()