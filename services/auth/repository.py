"""Auth repository"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from services.auth.models import AuthUser, RefreshToken

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        result = await self.db.execute(select(AuthUser).where(AuthUser.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        result = await self.db.execute(select(AuthUser).where(AuthUser.id == user_id))
        return result.scalar_one_or_none()
    
    async def create_user(self, email: str, username: str, password_hash: str) -> AuthUser:
        user = AuthUser(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_last_login(self, user_id: str):
        stmt = (
            update(AuthUser).where(AuthUser.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc), failed_login_attempts=0)
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def increment_failed_attempts(self, user_id: str):
        user = await self.get_user_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            await self.db.commit()
    
    async def save_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        await self.db.commit()
        return token
    
    async def revoke_refresh_token(self, token_hash: str):
        stmt = update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
        await self.db.execute(stmt)
        await self.db.commit()
    