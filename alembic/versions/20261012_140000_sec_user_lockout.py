"""SEC-02: per-account login lockout columns on ``users``.

Context
-------
The gateway already carries a per-IP brute-force ceiling
(``AuthRateLimitMiddleware``) and ``services/auth/service.py`` implements a
failed-attempt lockout, but that lockout binds to the ``auth_users`` table of
the *unmounted* microservice, while both live login paths
(``services/auth_legacy/service.py::authenticate`` — the gateway router — and
``services/auth/main.py::login`` — the supervisor's auth service) query
``database.models.User``, which had no counter column at all. Credential
stuffing against one account spread over many IPs therefore had no per-account
ceiling anywhere on the mounted surface.

This revision adds the two columns the runtime needs. It is additive and
backfill-safe: every existing row gets ``failed_login_attempts = 0`` and
``locked_until = NULL`` via the server default, and no data is moved.

Guarded shape (the pattern the earlier revisions established)
-------------------------------------------------------------
* **Re-runnable.** Online, each column is added only when the live table does
  not already carry it, so a fresh ``alembic upgrade head``, an old
  ``create_all`` build (which now includes the columns) and a partially
  migrated database all converge.
* **Offline (``--sql``) renders nothing for the columns.** The offline replay
  starts from an empty database and creates ``users`` from the registry in
  ``20261011_090000_remaining_legacy_tables``; because this revision's columns
  are now part of ``Base.metadata``, that ``CREATE TABLE users`` already
  contains them, and emitting ``ALTER TABLE users ADD COLUMN`` on top would
  fail with a duplicate column. The guarded online branch is what upgrades the
  older shapes (``create_all`` from a pre-lockout registry, partial
  migrations); the offline script needs nothing.

Downgrade
---------
Drops the two columns, each guarded by presence, inside batch mode (SQLite
recreates the table for a drop). Run it on a scratch database, never on
production: the columns carry the lockout state, and a running service writes
them.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261012_140000_sec_user_lockout"
down_revision: str | None = "20261011_170000_p8_refunds_and_incidents"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "users"

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine, bool, str | None], ...] = (
    # (name, type, nullable, server_default)
    ("failed_login_attempts", sa.Integer(), False, "0"),
    ("locked_until", sa.DateTime(timezone=True), True, None),
)


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _live_columns() -> set[str]:
    return {column["name"] for column in _inspector().get_columns(_TABLE)}


def upgrade() -> None:
    if context.is_offline_mode():
        # Nothing to render: the offline replay's ``CREATE TABLE users``
        # (emitted by 20261011_090000 from the registry) already carries both
        # columns. Emitting the ALTERs here would be a duplicate-column error.
        return
    if not _inspector().has_table(_TABLE):
        raise RuntimeError(
            f"{_TABLE} does not exist; run the earlier revisions first. "
            "This revision is additive and refuses to create the table."
        )
    live = _live_columns()
    for name, type_, nullable, server_default in _COLUMNS:
        if name not in live:
            op.add_column(
                _TABLE,
                sa.Column(name, type_, nullable=nullable, server_default=server_default),
            )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    if not _inspector().has_table(_TABLE):
        return
    live = _live_columns()
    with op.batch_alter_table(_TABLE) as batch:
        for name, _type, _nullable, _default in reversed(_COLUMNS):
            if name in live:
                batch.drop_column(name)
