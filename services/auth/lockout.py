"""SEC-02: per-account brute-force lockout — shared by both mounted login paths.

``AuthRateLimitMiddleware`` bounds *requests per IP*; it cannot stop credential
stuffing aimed at one account from a rotating pool of IPs. This module is the
per-account ceiling, and it reads and writes the ``User`` row both mounted login
paths use (``services/auth_legacy/service.py`` on the gateway router and
``services/auth/main.py`` on the supervisor's auth service).

Semantics
---------
* A failed login increments ``user.failed_login_attempts`` **atomically** — one
  conditional ``UPDATE`` — and at ``max_attempts`` the same statement sets
  ``locked_until = now + lockout_seconds``. While locked, authentication is
  refused **before** the password is checked, so a locked account costs no
  bcrypt work.
* A successful login clears the counter and the lock; a completed password
  reset does too.
* The lock is time-based, not permanent: after ``locked_until`` passes the
  counter is still armed, so the next failure re-locks immediately.

Why the increment is SQL, not Python (2026-10-12 review finding 2)
-------------------------------------------------------------------
The first version read ``user.failed_login_attempts`` in Python and wrote
``attempts + 1``. Under the concurrency this module exists for — one account,
many guesses — every request read the same pre-commit value and wrote
``stale + 1``, so the counter could be pinned below the threshold forever (and
on SQLite the colliding writers raised ``database is locked``). The increment
and the lock decision are now a single statement:

    UPDATE users
       SET failed_login_attempts = failed_login_attempts + 1,
           locked_until = CASE
               WHEN failed_login_attempts + 1 >= :threshold THEN :until
               ELSE locked_until END
     WHERE id = :user_id

so N concurrent failures advance the counter by exactly N.

Configuration (environment, read at call time so tests can toggle it):

* ``HYDROMA_AUTH_LOCKOUT_ENABLED`` — ``false``/``0``/``no``/``off`` disables
  the layer (test escape hatch; the suite must never enable it by accident);
* ``HYDROMA_AUTH_LOCKOUT_MAX_ATTEMPTS`` — failures before the lock;
* ``HYDROMA_AUTH_LOCKOUT_SECONDS`` — lock duration.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_SECONDS = 900  # 15 minutes: long enough to break a stuffing run

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    return value if value > 0 else default


def is_enabled() -> bool:
    raw = os.getenv("HYDROMA_AUTH_LOCKOUT_ENABLED", "1")
    return raw.strip().lower() in _TRUTHY


def max_attempts() -> int:
    return _env_int("HYDROMA_AUTH_LOCKOUT_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS)


def lockout_seconds() -> int:
    return _env_int("HYDROMA_AUTH_LOCKOUT_SECONDS", DEFAULT_LOCKOUT_SECONDS)


class AccountLockedError(Exception):
    """Raised when a locked account attempts to authenticate."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = max(int(retry_after_seconds), 1)
        super().__init__("Account temporarily locked after too many failed attempts")


def is_locked(user, now: datetime | None = None) -> bool:
    """True when the account is inside its lock window right now.

    Object-level and synchronous: both login paths check the row they loaded at
    the start of the request, which is current as of that load.
    """
    if not is_enabled():
        return False
    locked_until = getattr(user, "locked_until", None)
    if locked_until is None:
        return False
    now = now or datetime.now(UTC)
    # Naive timestamps come from SQLite DateTime columns; compare in UTC.
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return locked_until > now


def check_locked(user, now: datetime | None = None) -> None:
    """Raise :class:`AccountLockedError` when the account is locked."""
    if not is_locked(user, now):
        return
    locked_until = user.locked_until
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    retry_after = int((locked_until - now).total_seconds()) + 1
    raise AccountLockedError(retry_after)


async def register_failure(db: AsyncSession, user_id: str, now: datetime | None = None) -> None:
    """Count one failed login and engage the lock at the threshold.

    The increment and the lock are one conditional statement, so concurrent
    failures each advance the counter by exactly one (see the module docstring
    for the threat). The caller commits — this module never touches a session
    transaction boundary.
    """
    if not is_enabled():
        return
    now = now or datetime.now(UTC)
    until = now + timedelta(seconds=lockout_seconds())
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            failed_login_attempts=User.failed_login_attempts + 1,
            locked_until=case(
                (User.failed_login_attempts + 1 >= max_attempts(), until),
                else_=User.locked_until,
            ),
        )
        .execution_options(synchronize_session=False)
    )


async def register_success(db: AsyncSession, user_id: str) -> None:
    """Clear the counter and the lock after a successful authentication."""
    if not is_enabled():
        return
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(failed_login_attempts=0, locked_until=None)
        .execution_options(synchronize_session=False)
    )
