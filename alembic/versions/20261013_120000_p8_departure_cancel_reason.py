"""P8: record why a departure was cancelled.

The cancellation reason used to be discarded by
``services/tourism/departure_service.py`` (the ``reason`` argument was accepted
and then dropped, leaving a no-op self-assignment), so the only audit trail of
*why* a departure disappeared was lost. The column is added to the model and,
guarded and re-run-safe, to migrated databases — SQLite's implicit rebuild
handles the ALTER, and ``create_all`` carries it from now on.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import services.tourism.departures  # noqa: F401  (registers tourism_departures)
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261013_120000_p8_departure_cancel_reason"
down_revision: str | None = "20261012_140000_sec_user_lockout"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "tourism_departures"
_COLUMN = "cancelled_reason"


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _has_column() -> bool:
    if not _inspector().has_table(_TABLE):
        return True  # nothing to repair on a database that lacks the table
    return any(c["name"] == _COLUMN for c in _inspector().get_columns(_TABLE))


def upgrade() -> None:
    if context.is_offline_mode():
        return
    if not _has_column():
        op.add_column(
            _TABLE,
            sa.Column(
                _COLUMN,
                sa.Text(),
                nullable=True,
            ),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    if _inspector().has_table(_TABLE) and _has_column():
        try:
            op.drop_column(_TABLE, _COLUMN)
        except Exception:
            pass  # column already absent — the downgrade stays re-runnable
