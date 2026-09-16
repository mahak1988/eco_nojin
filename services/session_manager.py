"""Session management with Redis-backed storage.

Provides:
- Create session with device fingerprint
- Validate session
- Revoke session
- List active sessions
- Auto-expiry (configurable TTL)
"""
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("econojin.sessions")

DEFAULT_TTL = 86400 * 7  # 7 days


class SessionManager:
    """Redis-backed session manager with fallback to in-memory."""

    def __init__(self, redis_client: Any | None = None, ttl: int = DEFAULT_TTL) -> None:
        self._redis = redis_client
        self._ttl = ttl
        self._fallback: dict[str, dict] = {}
        self._fallback_lock = __import__("threading").Lock()

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def create(self, user_id: str, device: str = "", ip: str = "", user_agent: str = "") -> dict:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "device": device or "unknown",
            "ip": ip or "unknown",
            "user_agent": (user_agent or "")[:200],
            "created_at": now.isoformat(),
            "last_active": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self._ttl)).isoformat(),
            "current": True,
        }
        if self._redis is not None:
            try:
                import json
                self._redis.setex(
                    self._key(session_id),
                    self._ttl,
                    json.dumps(session_data),
                )
                return session_data
            except Exception as exc:
                logger.warning("Redis session store unavailable, using memory: %s", exc)
                self._redis = None
        with self._fallback_lock:
            self._fallback[session_id] = session_data
        return session_data

    def get(self, session_id: str) -> dict | None:
        """Retrieve and validate a session."""
        if self._redis is not None:
            try:
                import json
                raw = self._redis.get(self._key(session_id))
                if raw:
                    data = json.loads(raw)
                    data["current"] = True
                    return data
                return None
            except Exception:
                self._redis = None
        with self._fallback_lock:
            data = self._fallback.get(session_id)
            if data:
                expires = datetime.fromisoformat(data["expires_at"])
                if datetime.now(UTC) > expires:
                    del self._fallback[session_id]
                    return None
                data["current"] = True
                return data
        return None

    def revoke(self, session_id: str) -> bool:
        """Revoke a session."""
        if self._redis is not None:
            try:
                return bool(self._redis.delete(self._key(session_id)))
            except Exception:
                self._redis = None
        with self._fallback_lock:
            return self._fallback.pop(session_id, None) is not None

    def revoke_all_for_user(self, user_id: str, except_session: str | None = None) -> int:
        """Revoke all sessions for a user. Returns count revoked."""
        count = 0
        if self._redis is not None:
            try:
                keys = self._redis.keys(f"session:*")
                for key in keys:
                    raw = self._redis.get(key)
                    if raw:
                        import json
                        data = json.loads(raw)
                        if data.get("user_id") == user_id and key != self._key(except_session):
                            self._redis.delete(key)
                            count += 1
                return count
            except Exception:
                self._redis = None
        with self._fallback_lock:
            to_remove = []
            for sid, data in self._fallback.items():
                if data.get("user_id") == user_id and sid != except_session:
                    to_remove.append(sid)
                    count += 1
            for sid in to_remove:
                del self._fallback[sid]
            return count

    def refresh(self, session_id: str) -> bool:
        """Extend session TTL."""
        data = self.get(session_id)
        if not data:
            return False
        now = datetime.now(UTC)
        data["last_active"] = now.isoformat()
        data["expires_at"] = (now + timedelta(seconds=self._ttl)).isoformat()
        if self._redis is not None:
            try:
                import json
                self._redis.setex(self._key(session_id), self._ttl, json.dumps(data))
            except Exception:
                self._redis = None
                with self._fallback_lock:
                    self._fallback[session_id] = data
        return True


session_manager = SessionManager()
