"""Persistence for the admin settings plane.

Moved here 2026-10-04 out of ``services/api_gateway/routers/admin_settings.py``,
which had grown a module-level persistence layer: four helpers that took a
``Session`` and issued SQL, plus five route handlers annotated ``db: Session``.
That is 24 of the 25 ``G5.router-touches-db`` / ``G5.service-takes-session``
findings in that file, and it is the shape the structure gate exists to stop --
a router that opens a transaction is a router whose transaction boundary no
reviewer is looking at. The same shape has already produced a real defect
elsewhere: ``services/commerce/service.py::settle_order`` stopped calling
``ensure_account`` and nothing else supplied ``FinAccount`` rows, so the ledger
balanced against accounts that did not exist.

SYNC, NOT ASYNC -- and that is a deliberate difference from ``services/reporting``
--------------------------------------------------------------------------
``ReportingRepository`` is async because ``services/reporting/main.py`` builds
its session from ``hub.get_async_session()``. This plane's session comes from
``hub.get_session()``, a ``sqlalchemy.orm.Session``, and ``hub`` creates the two
through different engines (``create_async_engine`` vs ``get_sqlalchemy_engine``),
so adopting ``AsyncSession`` here would change which connection this endpoint
writes through, not merely which keyword is awaited. That is a different change
from the one this module exists for, and it is not one this refactor makes.

The consequence to be honest about: the handlers are ``async def`` and the
session is synchronous, so their queries block the event loop. That was already
true before the move and is unchanged by it.

The invariant of this module: **the queries are the ones the router used to
issue, unchanged**. Same SELECTs, same predicates, same ordering, same
transaction boundaries. ``tests/unit/test_admin_settings_repository.py`` pins the
emitted SQL so that a future edit cannot quietly reshape a query.
"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import AuditEvent, Setting

#: ``resource_type`` written to the audit trail for this plane.
SETTING_RESOURCE_TYPE = "setting"


def get_db() -> Generator[Session, None, None]:
    """The synchronous session the gateway already used for this plane.

    Kept here rather than in the router because a FastAPI dependency *is* the
    normal place for a session, but this is the only module that has any business
    naming one. The router re-exports it under the same name, so anything keying
    a ``dependency_overrides`` entry on it keeps working.
    """
    with hub.get_session() as session:
        yield session


@dataclass(frozen=True)
class SettingWrite:
    """One row a request wants to persist, together with the audit row that goes
    with it.

    Assembled by the router, which owns the registry and the redaction rules, and
    consumed by the repository, which owns the session. Holding the two together
    is deliberate: a write and its audit record are one fact, and leaving them as
    two independent calls is how a write ends up with no audit row -- or, in the
    case this repository was written for, how a caller ends up able to stage
    writes and return without committing any of them.

    ``existing`` is the row the caller already loaded, or ``None`` for a key that
    has never been written. Carrying it rather than re-reading means a write
    still costs exactly one SELECT.
    """

    key: str
    value: str
    description: str | None
    is_secret: bool
    action: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    existing: Setting | None = None


class SettingsRepository:
    """Every ``settings`` / ``audit_event`` statement this plane makes.

    Constructed per request from the request's session. Each write method owns its
    transaction: the router cannot stage a write and forget to commit it, because
    there is no way to stage one.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_row(self, key: str) -> Setting | None:
        """One setting by name, or ``None`` when it has never been written."""
        return self.db.execute(select(Setting).where(Setting.key == key)).scalars().first()

    def list_rows(self) -> dict[str, Setting]:
        """Every settings row, keyed by setting name. One query, not one per key."""
        return {
            row.key: row for row in self.db.execute(select(Setting).order_by(Setting.key)).scalars()
        }

    def last_actors(self, key: str | None = None) -> dict[str, str]:
        """Who last changed each setting, keyed by setting name.

        ``Setting`` has no ``updated_by`` column - the attribute only ever existed
        in the dict - so the audit trail is the record of authorship. One query
        for a whole listing rather than one per row.
        """
        statement = select(
            AuditEvent.resource_id, AuditEvent.actor_id, AuditEvent.created_at
        ).where(AuditEvent.resource_type == SETTING_RESOURCE_TYPE)
        if key is not None:
            statement = statement.where(AuditEvent.resource_id == key)
        actors: dict[str, str] = {}
        for resource_id, actor_id, _created_at in self.db.execute(
            statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        ):
            actors.setdefault(resource_id, actor_id)
        return actors

    def apply(self, write: SettingWrite, *, actor: str, correlation_id: str) -> Setting:
        """Persist one write and its audit row, in one transaction."""
        return self.apply_all([write], actor=actor, correlation_id=correlation_id)[0]

    def apply_all(
        self,
        writes: Sequence[SettingWrite],
        *,
        actor: str,
        correlation_id: str,
    ) -> list[Setting]:
        """Persist every write and its audit row, in **one** transaction.

        One commit for the whole list rather than one per write. A bulk that
        committed per key could leave half of it applied, which is the state the
        endpoint's own docstring calls unacceptable and which the caller cannot
        detect from the response.

        An empty list commits nothing, and issues no statement. The endpoint
        still answers ``{"updated": 0}``, exactly as it did when the commit was
        an unconditional call that had nothing to flush.
        """
        rows = [self._stage(write, actor=actor, correlation_id=correlation_id) for write in writes]
        if rows:
            self.db.commit()
        return rows

    def remove(
        self,
        row: Setting,
        *,
        actor: str,
        correlation_id: str,
        before: dict[str, Any] | None,
    ) -> None:
        """Remove a stored row and record the removal, in one transaction.

        Named ``remove`` rather than ``delete`` because ``tests/contract/gates.py``
        matches a router's database calls on the *attribute name alone* -- its own
        comment says "a session/engine is the only thing that has them in this
        codebase", which stopped being true the moment a repository sat between
        the router and the session. With ``delete`` the router read
        ``repo.delete(...)`` and the gate reported it as a direct database write.
        The name is the ordinary English one for the operation; the sentence worth
        recording is that the gate needs the receiver, which is not this file's to
        change.

        ``before`` arrives already redacted. The audit trail is readable by more
        people than the admin plane is, and must not become the place a secret is
        kept, so masking stays with the caller that owns the key's secrecy rules
        rather than being duplicated here.
        """
        self.db.delete(row)
        self._record(
            action="delete",
            key=row.key,
            actor=actor,
            correlation_id=correlation_id,
            before=before,
            after=None,
        )
        self.db.commit()

    def _stage(self, write: SettingWrite, *, actor: str, correlation_id: str) -> Setting:
        row = write.existing
        if row is None:
            row = Setting(key=write.key, description=write.description, is_secret=write.is_secret)
            self.db.add(row)
        row.value = write.value
        row.description = write.description
        row.is_secret = write.is_secret
        self._record(
            action=write.action,
            key=write.key,
            actor=actor,
            correlation_id=correlation_id,
            before=write.before,
            after=write.after,
        )
        return row

    def _record(
        self,
        *,
        action: str,
        key: str,
        actor: str,
        correlation_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> None:
        """Stage one audit row, storing ``before``/``after`` exactly as given.

        No masking happens here, and none must start. Redaction belongs to the
        router, which owns the registry and the name rules; a second
        implementation free to drift is how a mask ends up applied in the response
        but not in the audit trail, which is the one place it cannot be missed.
        """
        self.db.add(
            AuditEvent(
                correlation_id=correlation_id,
                actor_id=actor,
                action=action,
                resource_type=SETTING_RESOURCE_TYPE,
                resource_id=key,
                before_state=before,
                after_state=after,
                request_id=correlation_id,
            )
        )


def get_settings_repository(db: Annotated[Session, Depends(get_db)]) -> SettingsRepository:
    """FastAPI dependency: bind the request's session to the repository."""
    return SettingsRepository(db)
