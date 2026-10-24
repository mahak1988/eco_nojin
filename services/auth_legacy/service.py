"""Business logic for the legacy auth router.

S-STRUCT compliant: AuthService receives an AuthLegacyRepository (which wraps
AsyncSession), never a Session directly. All business logic lives here; the
router only parses the request and shapes the response.

Created by S-STRUCT remediation on 2026-10-07.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import structlog
from cryptography.fernet import Fernet
from fastapi import Request

from database.hub import hub
from database.models import (
    AuditLog,
    OAuthConnection,
    PasswordResetToken,
    RefreshToken,
    User,
)
from engine.hydroma.config.settings import get_settings
from services.api_gateway.auth import (
    ADMIN_ROLES,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    role_of,
    set_auth_cookies,
    verify_password,
)
from services.api_gateway.eventbus import publish_user_event
from services.auth.lockout import check_locked, register_failure, register_success
from services.auth_legacy.repository import AuthLegacyRepository

logger = structlog.get_logger()
logger = logging.getLogger(__name__)
_settings = get_settings()


class AuthService:
    """Pure business logic for authentication — no Session dependency."""

    def __init__(self, repo: AuthLegacyRepository):
        self.repo = repo

    # ---- audit ----
    async def write_audit(
        self,
        *,
        email: str,
        action: str,
        result: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        actor_id: str | None = None,
    ):
        log = AuditLog(
            actor_id=actor_id or email,
            action=action,
            resource_type="user",
            resource_id=actor_id or email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email, "result": result, "event_type": "auth"},
        )
        await self.repo.write_audit_log(log)

    # ---- registration ----
    async def register_user(
        self,
        email: str,
        full_name: str,
        password: str,
        role: str,
        phone: str | None,
        date_of_birth: str | None,
        country: str | None,
        city: str | None,
        address: str | None,
        language: str,
        avatar_url: str | None,
    ) -> User:
        """Register a new user + wallet, return the flushed user."""
        if role in ADMIN_ROLES:
            raise PermissionError("Role cannot be self-assigned")
        if await self.repo.check_email_exists(email):
            raise ValueError("Email already registered")

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            phone=phone,
            date_of_birth=datetime.strptime(date_of_birth, "%Y-%m-%d").date() if date_of_birth else None,
            country=country,
            city=city,
            address=address,
            language=language,
            avatar_url=avatar_url,
            is_email_verified=False,
            is_active=True,
        )
        return await self.repo.create_user(user)

    async def bootstrap_first_admin(self, email: str) -> bool:
        """Promote one existing account only when the platform has no admins."""
        return await self.repo.bootstrap_first_admin(email, tuple(ADMIN_ROLES))

    async def seed_demo_users(self) -> tuple[list[str], list[str]]:
        """Create demo users if they don't exist. Returns (created, skipped).

        SEC-24: the passwords are no longer literals in source. Each demo
        account is created only when its ``ECO_NOJIN_DEMO_PASSWORD_<N>``
        variable is set — an unset variable skips that account instead of
        falling back to a well-known credential like ``admin123``. Account 5
        (the admin showcase) additionally requires ``ECO_NOJIN_DEMO_ADMIN=1``;
        the seeding endpoint is dev-only and the ``--seed-demo`` path is gated
        by ``ECO_NOJIN_ALLOW_SEED``.
        """
        demos = [
            ("test@demo.com", "Test Demo User", "ECO_NOJIN_DEMO_PASSWORD_1", "regular", "en"),
            ("farmer@test.com", "Demo Farmer", "ECO_NOJIN_DEMO_PASSWORD_2", "farmer", "fa"),
            ("researcher@test.com", "Demo Researcher", "ECO_NOJIN_DEMO_PASSWORD_3", "researcher", "fa"),
            ("org@test.com", "Demo Organization", "ECO_NOJIN_DEMO_PASSWORD_4", "organization", "en"),
        ]
        if os.getenv("ECO_NOJIN_DEMO_ADMIN", "") == "1":
            demos.append(
                ("admin@test.com", "Admin User", "ECO_NOJIN_DEMO_PASSWORD_5", "regular", "en")
            )
        created, skipped = [], []
        for email, name, password_var, role, lang in demos:
            password = os.getenv(password_var, "")
            if not password:
                # the account's credential was not provisioned for this
                # environment — skip rather than create a guessable one
                skipped.append(email)
                continue
            existing = await self.repo.get_user_by_email(email)
            if existing:
                skipped.append(email)
            else:
                await self.repo.create_demo_user(email, name, hash_password(password), role, lang)
                created.append(email)
        await self.repo.commit()
        return created, skipped

    # ---- login / logout ----
    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.repo.get_user_by_email(email)
        if not user:
            return None
        # SEC-02: the per-account brute-force ceiling. A locked account is
        # refused before any bcrypt work; a failure is counted atomically (one
        # conditional UPDATE — concurrent guesses cannot lose increments);
        # success clears the counter and the lock.
        check_locked(user)
        if not verify_password(password, user.hashed_password):
            await register_failure(self.repo.db, user.id)
            await self.repo.commit()
            return None
        await register_success(self.repo.db, user.id)
        await self.repo.commit()
        return user

    async def issue_tokens(self, user: User, response) -> tuple[str, str, RefreshToken]:
        # ``tenant_id`` mirrors the subject: the account is its own
        # platform/tenant. This is the claim IdentityMiddleware publishes on
        # ``request.state`` and the IoT router derives a device's
        # ``platform_id`` from — without it every device registered
        # ``platform_id=NULL`` (2026-10-12 review finding 4).
        # ``sid`` carries the refresh session id into the access token so
        # ``revoke-all-sessions`` can exclude the caller's own session
        # (SEC-26: without it the attribute was always None and the endpoint
        # revoked the current session too).
        new_jti = secrets.token_urlsafe(16)
        token = create_access_token(
            {"user_id": user.id, "tenant_id": user.id, "sid": new_jti},
            subject=str(user.id),
            role=user.role or "farmer",
        )
        refresh_token = create_refresh_token(
            {"jti": new_jti}, subject=str(user.id), role=role_of(user)
        )
        expires_at = datetime.now(UTC) + timedelta(
            minutes=_settings.refresh_token_expire_minutes
        )
        refresh_record = RefreshToken(
            jti=new_jti, user_id=user.id, revoked=False, expires_at=expires_at
        )
        await self.repo.save_refresh_token(refresh_record)
        set_auth_cookies(response, token, refresh_token)
        return token, refresh_token, refresh_record

    async def publish_login_event(self, user: User, request: Request):
        try:
            request_id = request.headers.get("X-Request-ID")
            await publish_user_event(
                "login",
                str(user.id),
                {
                    "email": user.email,
                    "role": user.role,
                    "language": user.language,
                },
                correlation_id=request_id,
            )
        except Exception as e:
            logger.warning(f"Failed to publish user_login event: {e}")

    async def publish_register_event(self, user: User, request: Request):
        try:
            request_id = request.headers.get("X-Request-ID")
            await publish_user_event(
                "registered",
                str(user.id),
                {
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "language": user.language,
                },
                correlation_id=request_id,
            )
        except Exception as e:
            logger.warning(f"Failed to publish user_registered event: {e}")

    async def logout(self, refresh_token: str | None, current_user: User):
        if refresh_token:
            payload = decode_refresh_token(refresh_token)
            token_jti = payload.get("jti") if payload else None
            if token_jti:
                await self.repo.revoke_refresh_token_by_jti(token_jti)

    # ---- password reset ----
    async def request_reset(self, email: str) -> tuple[bool, str | None, str | None]:
        """Returns (user_exists, reset_url, token_or_none)."""
        user = await self.repo.get_user_by_email(email)
        if not user:
            return False, None, None
        await self.repo.invalidate_old_reset_tokens(user.id)
        reset_token = PasswordResetToken.create_for_user(user.id, hours_valid=1)
        await self.repo.create_reset_token(reset_token)

        from engine.hydroma.config.settings import get_settings
        settings = get_settings()
        link_base = str(getattr(settings, "public_base_url", "")).rstrip("/")
        reset_url = f"{link_base}/reset-password?token={reset_token.token}"
        logger.info(f"[RESET] {user.email}: {reset_url}")
        return True, reset_url, reset_token.token

    async def reset_password(self, token: str, new_password: str):
        reset_token = await self.repo.get_reset_token(token)
        if not reset_token or not reset_token.is_valid:
            raise ValueError("Invalid or expired reset token")
        user = await self.repo.get_user_by_id(reset_token.user_id)
        if not user:
            raise ValueError("User not found")
        user.hashed_password = hash_password(new_password)
        # SEC-02: a completed reset proves credential ownership — clear any
        # brute-force lock so the owner is not locked out of their own reset.
        await register_success(self.repo.db, user.id)
        reset_token.used = True
        await self.repo.commit()
        return user

    async def change_password(self, current_user: User, current_password: str, new_password: str):
        if not verify_password(current_password, current_user.hashed_password):
            raise ValueError("Current password is incorrect")
        current_user.hashed_password = hash_password(new_password)
        await self.repo.commit()

    # ---- profile ----
    async def update_profile(self, user: User, req) -> User:
        # The caller arrives from the authentication dependency's session;
        # this service owns a different one, so merge it before mutating.
        user = await self.repo.merge(user)
        if req.full_name is not None:
            user.full_name = req.full_name
        if req.phone is not None:
            user.phone = req.phone
        if req.date_of_birth is not None:
            try:
                user.date_of_birth = (
                    datetime.strptime(req.date_of_birth, "%Y-%m-%d").date()
                    if req.date_of_birth else None
                )
            except ValueError:
                raise ValueError("Invalid date_of_birth format")
        if req.country is not None:
            user.country = req.country
        if req.city is not None:
            user.city = req.city
        if req.address is not None:
            user.address = req.address
        if req.language is not None:
            user.language = req.language
        if req.avatar_url is not None:
            if len(req.avatar_url) > 2_000_000:
                raise ValueError("Avatar image too large (max 2MB encoded)")
            user.avatar_url = req.avatar_url
        await self.repo.commit()
        await self.repo.refresh(user)
        return user

    # ---- refresh ----
    async def refresh_tokens(self, refresh_token: str, user_sub: str, token_jti: str | None) -> User:
        user = await self.repo.get_user_by_id(user_sub)
        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")
        if token_jti:
            old_token = await self.repo.get_refresh_token_by_jti(token_jti)
            if old_token is None or old_token.revoked:
                raise ValueError("Refresh token has been revoked")
            old_token.revoked = True
            old_token.revoked_at = datetime.now(UTC)
            await self.repo.db.flush()
        return user

    # ---- 2FA ----
    async def get_2fa_status(self, current_user: User) -> dict:
        two_fa_enabled = bool(getattr(current_user, "two_factor_enabled", False))
        return {
            "enabled": two_fa_enabled,
            "method": getattr(current_user, "two_factor_method", None),
        }

    async def toggle_2fa(self, current_user: User) -> dict:
        pref_key = f"2fa_enabled_{current_user.id}"
        try:
            conn = hub.get_sqlite("manual")
            from sqlalchemy import text
            existing = conn.execute(
                text("SELECT value FROM settings WHERE key = :key"), {"key": pref_key}
            ).fetchone()
            current_val = existing[0] if existing else "false"
            new_val = "false" if current_val == "true" else "true"
            if existing:
                conn.execute(
                    text("UPDATE settings SET value = :val WHERE key = :key"),
                    {"val": new_val, "key": pref_key},
                )
            else:
                conn.execute(
                    text(
                        "INSERT INTO settings (key, value, category) "
                        "VALUES (:key, :val, 'security')"
                    ),
                    {"key": pref_key, "val": new_val},
                )
            conn.commit()
            enabled = new_val == "true"
            current_user.two_factor_enabled = enabled
            await self.repo.commit()
            return {"enabled": enabled, "message": f"2FA {'enabled' if enabled else 'disabled'}"}
        except Exception as e:
            logger.warning(f"2FA toggle failed: {e}")
            raise RuntimeError("Failed to toggle 2FA") from e

    # ---- OAuth connections ----
    async def list_oauth_connections(self, user_id: str) -> dict:
        connections = await self.repo.get_oauth_connections(user_id)
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

    async def connect_oauth(self, provider: str, auth_code: str, user_id: str) -> dict:
        settings = get_settings()
        fernet_key = getattr(settings, "oauth_encryption_key", None)
        if not fernet_key:
            secret = settings.secret_key or settings.jwt_secret
            fernet_key = base64.urlsafe_b64encode(secret.encode()[:32].ljust(32, b"0"))
        fernet = Fernet(fernet_key)

        existing = await self.repo.get_oauth_connection(user_id, provider)
        encrypted_token = fernet.encrypt(auth_code.encode()).decode()
        if existing:
            existing.access_token_encrypted = encrypted_token
            existing.updated_at = datetime.now(UTC)
        else:
            conn = OAuthConnection(
                user_id=user_id,
                provider=provider,
                access_token_encrypted=encrypted_token,
            )
            await self.repo.save_oauth_connection(conn)
        return {"status": "success", "message": f"{provider} connected"}

    async def disconnect_oauth(self, provider: str, user_id: str) -> dict:
        conn = await self.repo.get_oauth_connection(user_id, provider)
        if not conn:
            raise LookupError(f"No {provider} connection found")
        await self.repo.delete_oauth_connection(conn)
        return {"status": "success", "message": f"{provider} disconnected"}

    # ---- API keys ----
    async def list_api_keys(self, user_id: str) -> dict:
        keys = await self.repo.get_api_keys(user_id)
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

    async def create_api_key(self, name: str, user_id: str) -> dict:
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        from database.models import ApiKey
        key = ApiKey(user_id=user_id, name=name, key_hash=key_hash)
        await self.repo.save_api_key(key)
        return {
            "status": "success",
            "data": {
                "id": key.id,
                "name": key.name,
                "key": raw_key,
                "created": key.created_at.isoformat() if key.created_at else None,
            },
        }

    async def revoke_api_key(self, key_id: str, user_id: str) -> dict:
        success = await self.repo.revoke_api_key(key_id, user_id)
        if not success:
            raise LookupError("API key not found")
        return {"status": "success", "message": "API key revoked"}

    # ---- account status ----
    async def get_account_status(self, current_user: User) -> dict:
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

    async def get_activity_history(self, user_id: str, limit: int) -> dict:
        logs = await self.repo.get_audit_logs(user_id, limit=limit)
        activities = [
            {
                "id": log.id,
                "type": log.action.split(".")[-1] if log.action else "unknown",
                "model": log.resource_type,
                "date": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
        return {"status": "success", "data": activities}

    async def get_security_audit(self, user_id: str) -> dict:
        logs = await self.repo.get_audit_logs(user_id, limit=20)
        return {
            "status": "success",
            "data": [
                {
                    "id": log.id,
                    "action": log.action,
                    "ip": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        }

    async def update_preferences(self, user: User, language: str | None) -> dict:
        if language is not None:
            user.language = language
        await self.repo.commit()
        return {"status": "success", "message": "Preferences updated"}

    async def update_extended_preferences(self, user_id: str, updates: dict) -> dict:
        for key, value in updates.items():
            if value is None:
                continue
            setting_val = (
                (value if isinstance(value, str) else None)
                or (json.dumps(value) if isinstance(value, (dict, list)) else str(value))
            )
            await self.repo.upsert_setting(key, setting_val, "preferences")
        return {"status": "success", "message": "Extended preferences updated"}

    async def get_extended_preferences(self, user: User) -> dict:
        tz = "Asia/Tehran"
        units = "metric"
        theme = "system"
        dashboard = None

        for key_name in ["timezone", "units", "theme", "dashboard_widgets"]:
            row = await self.repo.get_setting(key_name)
            if row:
                if row.key == "timezone":
                    tz = row.value or tz
                elif row.key == "units":
                    units = row.value or units
                elif row.key == "theme":
                    theme = row.value or theme
                elif row.key == "dashboard_widgets":
                    try:
                        dashboard = json.loads(row.value) if row.value else None
                    except (json.JSONDecodeError, TypeError):
                        dashboard = None

        lang = user.language or "fa"
        try:
            dashboard_parsed = json.loads(dashboard) if dashboard else None
        except (json.JSONDecodeError, TypeError):
            dashboard_parsed = None
        return {
            "status": "success",
            "data": {
                "timezone": tz,
                "units": units,
                "theme": theme,
                "dashboardWidgets": dashboard_parsed,
                "language": lang,
            },
        }

    async def deactivate_account(self, current_user: User) -> dict:
        current_user.is_active = False
        await self.repo.commit()
        return {"status": "success", "message": "Account temporarily deactivated"}

    async def update_bio(self, user: User, bio: str | None, organization: str | None, location: str | None) -> dict:
        bio_json = None
        if bio is not None:
            bio_json = json.dumps(
                {"bio": bio, "organization": organization, "location": location}
            )
            await self.repo.upsert_setting("profile_bio", bio_json, "profile")
        return {"status": "success", "message": "Profile bio updated"}

    async def get_public_profile(self, user_id: str) -> dict:
        user = await self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise LookupError("User not found")

        projects = await self.repo.get_user_all_carbon_projects(user_id)
        project_list = [
            {
                "name": p.name,
                "project_type": p.project_type,
                "area_hectares": p.area_hectares,
                "status": p.status,
            }
            for p in projects
        ]
        project_count = len(projects)

        bio_data = None
        bio_row = await self.repo.get_setting("profile_bio")
        if bio_row and bio_row.value:
            try:
                import contextlib
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    bio_data = json.loads(bio_row.value)
            except Exception:
                bio_data = None

        return {
            "status": "success",
            "data": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
                "avatar_url": user.avatar_url,
                "bio": bio_data.get("bio") if bio_data else None,
                "organization": bio_data.get("organization") if bio_data else None,
                "location": bio_data.get("location") if bio_data else None,
                "member_since": user.created_at.isoformat() if user.created_at else None,
                "project_count": project_count,
                "projects": project_list,
            },
        }

    async def get_legacy_metrics(self, user_id: str) -> dict:
        projects = await self.repo.get_user_carbon_projects(user_id)
        total_carbon = sum(p.estimated_carbon_tonnes or 0 for p in projects)
        total_area = sum(p.area_hectares or 0 for p in projects)

        latest_run = await self.repo.get_latest_simulation_run(user_id)
        water_saved = None
        if latest_run and latest_run.outputs:
            outputs = latest_run.outputs if isinstance(latest_run.outputs, dict) else {}
            water_saved = outputs.get("water_saved_m3")

        activity_count = await self.repo.get_user_activity_count(user_id)
        now = datetime.now(UTC).isoformat()
        return {
            "status": "success",
            "data": {
                "carbon_sequestered": total_carbon if total_carbon > 0 else None,
                "carbon_unit": "ton CO₂e",
                "area_restored": total_area if total_area > 0 else None,
                "area_unit": "hectares",
                "water_saved": water_saved,
                "water_unit": "m³",
                "activity_count": activity_count,
                "updated": now,
            },
        }

    async def get_assets(self, user_id: str) -> dict:
        lands = await self.repo.get_user_lands(user_id)
        sensors = await self.repo.get_sensor_settings()
        wallet = await self.repo.get_user_wallet(user_id)
        api_keys = await self.repo.get_api_keys(user_id)
        projects = await self.repo.get_user_all_carbon_projects(user_id)

        return {
            "status": "success",
            "data": {
                "lands": {
                    "count": len(lands),
                    "items": [
                        {"name": land.name, "detail": f"{land.area_ha or 0} ha",
                         "location": f"{land.location_lat or 0}, {land.location_lon or 0}"}
                        for land in lands
                    ],
                },
                "sensors": {
                    "count": len(sensors),
                    "items": [
                        {"name": s.key, "detail": s.value[:80] if s.value else "Sensor data",
                         "status": s.value}
                        for s in sensors
                    ],
                },
                "wallet": {
                    "count": "1" if wallet else "0",
                    "items": [
                        {"name": "EcoWallet", "detail": f"Balance: {wallet.balance or 0:.2f}"}
                        for w in [wallet] if w
                    ],
                },
                "api_keys": {
                    "count": len(api_keys),
                    "items": [
                        {"name": k.name, "detail": f"Key ID: {k.id}", "status": "active"}
                        for k in api_keys
                    ],
                },
                "projects": {
                    "count": len(projects),
                    "items": [
                        {"name": p.name, "detail": f"{p.project_type or 'unknown'} | {p.status or 'draft'}",
                         "status": p.status}
                        for p in projects
                    ],
                },
            },
        }

    async def get_achievements(self, user_id: str) -> dict:
        achievements = []
        milestones = []

        projects = await self.repo.get_user_carbon_projects(user_id)
        if projects:
            achievements.append({
                "icon": "leaf",
                "title": "First Carbon Project" if len(projects) == 1 else f"{len(projects)} Carbon Projects",
                "description": f"Registered {len(projects)} active carbon sequestration project(s).",
                "date": projects[0].created_at.isoformat() if projects[0].created_at else "",
            })

        last_activity = (await self.repo.get_audit_logs(user_id, limit=1))
        if last_activity:
            log = last_activity[0]
            milestones.append({
                "icon": "activity",
                "title": "Active User",
                "date": log.created_at.isoformat() if log.created_at else "",
            })

        wallet = await self.repo.get_user_wallet(user_id)
        if wallet and (wallet.balance or 0) > 0:
            achievements.append({
                "icon": "coins",
                "title": "EcoWallet Active",
                "description": f"Wallet balance: {wallet.balance:.2f}",
                "date": wallet.created_at.isoformat() if wallet.created_at else "",
            })

        return {
            "status": "success",
            "data": {"achievements": achievements, "milestones": milestones},
        }

    # ---- sessions ----
    async def list_sessions(self, current_user: User) -> dict:
        sessions = await self.repo.list_active_sessions(str(current_user.id))
        return {
            "status": "success",
            "data": [
                {
                    "id": s.jti,
                    "device": "Session",
                    "ip": "unknown",
                    "user_agent": "unknown",
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "last_active": s.expires_at.isoformat() if s.expires_at else None,
                    "current": False,
                }
                for s in sessions
            ],
        }

    async def revoke_session(self, session_id: str, current_user: User) -> dict:
        session = await self.repo.get_session_by_jti(session_id, str(current_user.id))
        if not session or session.revoked:
            raise LookupError("Session not found")
        await self.repo.revoke_session(session)
        return {"status": "success", "message": "Session revoked"}

    async def revoke_all_sessions(self, current_user: User, current_jti: str | None) -> dict:
        count = await self.repo.revoke_all_sessions_except_current(
            str(current_user.id), current_jti
        )
        return {"status": "success", "message": f"All other sessions revoked ({count} sessions)"}

    # ---- rate limit ----
    async def get_rate_limit(self, current_user: User) -> dict:
        from services.api_gateway.routers.auth import _register_limiter
        bucket_key = str(getattr(current_user, "id", "unknown"))
        hits = _register_limiter._hits.get(bucket_key, [])
        now_ts = datetime.now(UTC).timestamp()
        window = _register_limiter.window_seconds
        recent = [t for t in hits if now_ts - t < window]
        remaining = max(_register_limiter.limit - len(recent), 0)
        reset_in = max(int(window - (now_ts - recent[0])) if recent else 0, 0)
        return {
            "status": "success",
            "data": {
                "requests_per_minute": _register_limiter.limit,
                "requests_this_minute": len(recent),
                "remaining": remaining,
                "reset_in_seconds": reset_in,
            },
        }

    # ---- email change ----
    async def request_email_change(self, current_user: User, new_email: str) -> dict:
        if not new_email:
            raise ValueError("new_email is required")
        token = await self.repo.create_email_change_token(str(current_user.id), new_email)
        _settings = get_settings()
        link_base = str(getattr(_settings, "public_base_url", "")).rstrip("/")
        verify_url = f"{link_base}/email-change/confirm?token={token}&new_email={new_email}"
        logger.info(f"[EMAIL-CHANGE] {current_user.email} -> {new_email}: {verify_url}")
        return {"status": "success", "message": "Verification code sent"}

    async def confirm_email_change(self, current_user: User, token: str) -> dict:
        reset_token = await self.repo.get_email_change_token(token)
        if not reset_token or not reset_token.is_valid:
            raise ValueError("Invalid or expired verification code")
        if reset_token.user_id != str(current_user.id):
            raise PermissionError("Token does not belong to this user")
        current_user.email = current_user.email
        reset_token.used = True
        await self.repo.commit()
        return {"status": "success", "message": "Email changed successfully"}

    # ---- notifications ----
    async def get_notifications(self, current_user: User) -> dict:
        prefs = await self.repo.get_notification_settings(str(current_user.id))
        return {"status": "success", "data": prefs}

    async def update_notifications(self, current_user: User, req: dict) -> dict:
        email = req.get("email")
        push = req.get("push")
        sms = req.get("sms")
        marketing = req.get("marketing")
        uid = str(current_user.id)
        if email is not None:
            await self.repo.upsert_notification_setting(f"notif_email_{uid}", email, "notifications")
        if push is not None:
            await self.repo.upsert_notification_setting(f"notif_push_{uid}", push, "notifications")
        if sms is not None:
            await self.repo.upsert_notification_setting(f"notif_sms_{uid}", sms, "notifications")
        if marketing is not None:
            await self.repo.upsert_notification_setting(f"notif_marketing_{uid}", marketing, "notifications")
        return {"status": "success", "message": "Preferences updated"}


async def get_auth_service() -> AsyncIterator[AuthService]:
    """Yield an auth service backed by the shared async database session."""
    async with hub.get_async_session() as db:
        yield AuthService(AuthLegacyRepository(db))
