"""AuthService - backward compatible with unified auth backend.

Per-account brute-force lockout (SEC-02) is NOT implemented here: it lives
once, in :mod:`services.auth.lockout`, and it is wired into the *mounted*
login paths (``services/auth_legacy`` and ``services/api_gateway/routers/auth``),
both of which authenticate ``database.models.User`` rows. This plane keeps its
own ``auth_users`` store for backward compatibility and carries no HTTP
surface; a second lockout implementation here used to raise a *permanent*
``ValueError("Account locked")`` that the success path could never clear
(the counter reset only ran after a password verify the pre-check blocked),
which was both an unrecoverable denial of service and a second source of
truth for the threshold. It has been deleted; if this plane is ever mounted
again it must call the shared module rather than re-implement it.
"""

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.compat import (
    create_access_token_compat,
    create_refresh_token_compat,
    generate_token,
    hash_password,
    password_hasher,
    verify_password,
)
from services.auth.models import AuthUser
from services.auth.repository import AuthRepository
from services.auth.schemas import TokenResponse, UserInfo, UserLogin, UserRegister


class AuthService:
    ACCESS_TOKEN_TTL = 3600
    REFRESH_TOKEN_TTL = 86400 * 30

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    def _hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        return hash_password(password), ""

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        return verify_password(password, stored_hash)

    def _generate_token(self, user_id: str, ttl: int) -> str:
        return generate_token(user_id, ttl)

    async def register(self, data: UserRegister) -> AuthUser:
        if not data.validate_password_strength():
            raise ValueError("Password must be 8+ chars with uppercase and digit")
        if await self.repo.get_user_by_email(data.email):
            raise ValueError("Email already registered")
        password_hash, _ = self._hash_password(data.password)
        return await self.repo.create_user(data.email, data.username, password_hash)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.repo.get_user_by_email(data.email)
        if not user:
            raise ValueError("Invalid credentials")
        if not self._verify_password(data.password, user.password_hash):
            raise ValueError("Invalid credentials")
        if password_hasher.needs_migration(user.password_hash):
            user.password_hash = hash_password(data.password)
            await self.db.commit()
            await self.db.refresh(user)
        access = create_access_token_compat(
            {"user_id": user.id}, subject=str(user.id), role="farmer"
        )
        refresh = create_refresh_token_compat({}, subject=str(user.id), role="farmer")
        await self.repo.save_refresh_token(
            user.id,
            hashlib.sha256(refresh.encode()).hexdigest(),
            datetime.now(UTC) + timedelta(seconds=self.REFRESH_TOKEN_TTL),
        )
        await self.repo.update_last_login(user.id)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=self.ACCESS_TOKEN_TTL,
        )

    async def get_user_info(self, user_id: str) -> UserInfo:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return UserInfo(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
