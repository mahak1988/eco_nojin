"""AuthService"""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models import AuthUser
from services.auth.repository import AuthRepository
from services.auth.schemas import TokenResponse, UserInfo, UserLogin, UserRegister


class AuthService:
    ACCESS_TOKEN_TTL = 3600
    REFRESH_TOKEN_TTL = 86400 * 30
    MAX_FAILED_ATTEMPTS = 5

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    def _hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return f"{salt}:{hashed}", salt

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, _ = stored_hash.split(":", 1)
            computed, _ = self._hash_password(password, salt)
            return secrets.compare_digest(computed, stored_hash)
        except Exception:
            return False

    def _generate_token(self, user_id: str, ttl: int) -> str:
        payload = f"{user_id}:{int(datetime.now(UTC).timestamp())}:{ttl}"
        return f"{payload}:{secrets.token_urlsafe(32)}"

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
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            raise ValueError("Account locked")
        if not self._verify_password(data.password, user.password_hash):
            await self.repo.increment_failed_attempts(user.id)
            raise ValueError("Invalid credentials")
        access = self._generate_token(user.id, self.ACCESS_TOKEN_TTL)
        refresh = self._generate_token(user.id, self.REFRESH_TOKEN_TTL)
        await self.repo.save_refresh_token(
            user.id, hashlib.sha256(refresh.encode()).hexdigest(),
            datetime.now(UTC) + timedelta(seconds=self.REFRESH_TOKEN_TTL),
        )
        await self.repo.update_last_login(user.id)
        return TokenResponse(
            access_token=access, refresh_token=refresh,
            expires_in=self.ACCESS_TOKEN_TTL,
        )

    async def get_user_info(self, user_id: str) -> UserInfo:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return UserInfo(
            id=user.id, email=user.email, username=user.username,
            is_active=user.is_active, is_verified=user.is_verified,
            created_at=user.created_at,
        )
