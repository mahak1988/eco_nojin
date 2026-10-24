"""Repository layer for legacy auth router DB operations.

All database access from services/api_gateway/routers/auth.py is centralized
here. The repository receives an AsyncSession and exposes typed async methods.
The service layer and router are pure of direct DB calls.

Created by S-STRUCT remediation on 2026-10-07.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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


class AuthLegacyRepository:
    """All DB access for the legacy auth router lives here."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- users ----
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def merge(self, obj):
        """Attach an instance loaded by a *different* session to this one.

        ``get_current_user`` resolves the caller in its own request-scoped
        session, while the auth service (and therefore the repository) gets
        another one. Mutating a detached instance and committing here used
        to raise ``InvalidRequestError: Instance '<User>' is not persistent
        within this Session`` — an HTTP 500 on every profile update.
        ``Session.merge`` copies the state onto this session's copy, which is
        the documented way to move an object between sessions.
        """
        return await self.db.merge(obj)

    async def check_email_exists(self, email: str) -> bool:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def bootstrap_first_admin(self, email: str, admin_roles: tuple[str, ...]) -> bool:
        has_admin = select(User.id).where(User.role.in_(admin_roles)).exists()
        result = await self.db.execute(
            update(User)
            .where(User.email == email, ~has_admin)
            .values(role="admin")
        )
        if result.rowcount != 1:
            await self.db.rollback()
            return False
        self.db.add(
            AuditLog(
                actor_id="local-bootstrap",
                action="bootstrap_first_admin",
                resource_type="user",
                resource_id=email,
                details={"role": "admin", "method": "loopback_development_bootstrap"},
            )
        )
        await self.db.commit()
        return True

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        wallet = EcoWallet(user_id=user.id, balance=Decimal("0"))
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_demo_user(self, email: str, name: str, password_hash: str,
                               role: str, lang: str) -> User:
        user = User(
            email=email,
            full_name=name,
            hashed_password=password_hash,
            role=role,
            language=lang,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        wallet = EcoWallet(user_id=user.id, balance=Decimal("100"))
        self.db.add(wallet)
        return user

    async def commit(self):
        await self.db.commit()

    async def refresh(self, obj):
        await self.db.refresh(obj)

    # ---- refresh tokens ----
    async def get_refresh_token_by_jti(self, token_jti: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == token_jti).with_for_update()
        )
        return result.scalar_one_or_none()

    async def save_refresh_token(self, refresh_record: RefreshToken):
        self.db.add(refresh_record)
        await self.db.commit()

    async def revoke_refresh_token_by_jti(self, token_jti: str):
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == token_jti, RefreshToken.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(UTC))
        )
        await self.db.commit()

    # ---- password reset tokens ----
    async def get_reset_token(self, token: str) -> PasswordResetToken | None:
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        return result.scalar_one_or_none()

    async def invalidate_old_reset_tokens(self, user_id: str):
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .values(used=True)
        )

    async def create_reset_token(self, reset_token: PasswordResetToken):
        self.db.add(reset_token)
        await self.db.commit()

    async def mark_reset_token_used(self, reset_token: PasswordResetToken):
        reset_token.used = True
        await self.db.commit()

    # ---- audit logs ----
    async def write_audit_log(self, log: AuditLog):
        try:
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            from services.api_gateway.logging import logger as db_logger
            db_logger.error(f"[AUDIT ERROR] {e}")
            with contextlib.suppress(Exception):
                await self.db.rollback()

    async def get_audit_logs(self, actor_id: str, limit: int = 20,
                            offset: int = 0) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_audit_log_count(self, actor_id: str) -> int:
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.actor_id == actor_id)
        )
        return len(result.scalars().all())

    async def get_user_activity_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.actor_id == user_id)
        )
        return len(result.scalars().all())

    # ---- OAuth connections ----
    async def get_oauth_connections(self, user_id: str) -> list[OAuthConnection]:
        result = await self.db.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == user_id,
            )
        )
        return result.scalars().all()

    async def get_oauth_connection(self, user_id: str, provider: str) -> OAuthConnection | None:
        result = await self.db.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == user_id,
                OAuthConnection.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def save_oauth_connection(self, conn: OAuthConnection):
        self.db.add(conn)
        await self.db.commit()

    async def delete_oauth_connection(self, conn: OAuthConnection):
        await self.db.delete(conn)
        await self.db.commit()

    # ---- API keys ----
    async def get_api_keys(self, user_id: str) -> list[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ~ApiKey.revoked,
            )
        )
        return result.scalars().all()

    async def save_api_key(self, key: ApiKey):
        self.db.add(key)
        await self.db.commit()

    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.id == key_id,
            )
        )
        key = result.scalar_one_or_none()
        if not key:
            return False
        key.revoked = True
        key.revoked_at = datetime.now(UTC)
        await self.db.commit()
        return True

    # ---- settings ----
    async def get_setting(self, key: str) -> Setting | None:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        return result.scalar_one_or_none()

    async def save_setting(self, setting: Setting):
        self.db.add(setting)
        await self.db.commit()

    async def update_setting_value(self, key: str, value: str):
        await self.db.execute(
            update(Setting)
            .where(Setting.key == key)
            .values(value=value)
        )
        await self.db.commit()

    async def get_sensor_settings(self) -> list[Setting]:
        result = await self.db.execute(
            select(Setting).where(Setting.key.like("sensor_%"))
        )
        return result.scalars().all()

    async def get_preferences_settings(self, keys: list[str]) -> list[Setting]:
        result = await self.db.execute(
            select(Setting).where(Setting.key.in_(keys))
        )
        return result.scalars().all()

    async def upsert_setting(self, key: str, value: str, category: str):
        existing = await self.get_setting(key)
        if existing:
            existing.value = value
            existing.updated_at = datetime.now(UTC)
        else:
            new_setting = Setting(
                id=f"{key}_{datetime.now(UTC).timestamp()}",
                key=key,
                value=value,
                category=category,
            )
            self.db.add(new_setting)
        await self.db.commit()

    # ---- carbon projects ----
    async def get_user_carbon_projects(self, user_id: str) -> list[CarbonProject]:
        result = await self.db.execute(
            select(CarbonProject).where(
                CarbonProject.user_id == user_id,
                CarbonProject.status == "active",
            )
        )
        return result.scalars().all()

    async def get_user_all_carbon_projects(self, user_id: str) -> list[CarbonProject]:
        result = await self.db.execute(
            select(CarbonProject).where(CarbonProject.user_id == user_id)
        )
        return result.scalars().all()

    # ---- land profiles ----
    async def get_user_lands(self, user_id: str) -> list[LandProfile]:
        result = await self.db.execute(
            select(LandProfile).where(LandProfile.user_id == user_id)
        )
        return result.scalars().all()

    # ---- wallets ----
    async def get_user_wallet(self, user_id: str) -> EcoWallet | None:
        result = await self.db.execute(
            select(EcoWallet).where(EcoWallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # ---- simulation runs ----
    async def get_latest_simulation_run(self, site_id: str) -> SimulationRun | None:
        result = await self.db.execute(
            select(SimulationRun)
            .where(SimulationRun.site_id == site_id)
            .order_by(SimulationRun.executed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ---- sessions (refresh tokens) ----
    async def list_active_sessions(self, user_id: str) -> list[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .order_by(RefreshToken.created_at.desc())
        )
        return result.scalars().all()

    async def get_session_by_jti(self, session_jti: str, user_id: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.jti == session_jti,
                RefreshToken.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session: RefreshToken) -> None:
        session.revoked = True
        session.revoked_at = datetime.now(UTC)
        await self.db.commit()

    async def revoke_all_sessions_except_current(self, user_id: str, current_jti: str | None) -> int:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True, revoked_at=datetime.now(UTC))
        )
        if current_jti:
            stmt = stmt.where(RefreshToken.jti != current_jti)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    # ---- notification settings ----
    async def get_notification_settings(self, user_id: str) -> dict:
        keys = [
            f"notif_email_{user_id}",
            f"notif_push_{user_id}",
            f"notif_sms_{user_id}",
            f"notif_marketing_{user_id}",
        ]
        result = await self.db.execute(select(Setting).where(Setting.key.in_(keys)))
        rows = {row.key: row.value for row in result.scalars().all()}
        return {
            "email": rows.get(f"notif_email_{user_id}", "true") == "true",
            "push": rows.get(f"notif_push_{user_id}", "true") == "true",
            "sms": rows.get(f"notif_sms_{user_id}", "false") == "true",
            "marketing": rows.get(f"notif_marketing_{user_id}", "false") == "true",
        }

    async def upsert_notification_setting(self, key: str, value: bool, category: str) -> None:
        str_val = "true" if value else "false"
        existing = await self.get_setting(key)
        if existing:
            existing.value = str_val
            existing.updated_at = datetime.now(UTC)
        else:
            new_setting = Setting(
                id=f"{key}_{datetime.now(UTC).timestamp()}",
                key=key,
                value=str_val,
                category=category,
            )
            self.db.add(new_setting)
        await self.db.commit()

    # ---- email change tokens ----
    async def create_email_change_token(self, user_id: str, new_email: str) -> str:
        token = PasswordResetToken.create_for_user(user_id, hours_valid=24)
        self.db.add(token)
        await self.db.commit()
        return token.token

    async def get_email_change_token(self, token: str) -> PasswordResetToken | None:
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        return result.scalar_one_or_none()
