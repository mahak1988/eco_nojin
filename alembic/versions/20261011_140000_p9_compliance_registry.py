"""P9: the compliance-registry tables (sources, jurisdictions, requirements,
credentials, verifications, assessments, exceptions, audit log).

P7's guarded pattern, reused: the definitions come from the registry
(``Base.metadata``), tables are created only when missing, offline ``--sql``
renders every create, and the downgrade drops exactly these tables.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers every declared table on the shared Base)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261011_140000_p9_compliance_registry"
down_revision: str | None = "20261011_130000_p7_governance_tables"
branch_labels: str | None = None
depends_on: str | None = None

_TABLES: tuple[str, ...] = (
    "com_jurisdictions",
    "com_regulatory_sources",
    "com_requirements",
    "com_activity_classifications",
    "com_credentials",
    "com_credential_verifications",
    "com_assessments",
    "com_exceptions",
    "com_audit_log",
)


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _create_table(name: str) -> None:
    """Create one table from the registry definition.

    Indexes are column-level here, so they ride along with the table; passing
    registry ``Index`` objects into ``create_table`` is refused by SQLAlchemy
    (an index already knows its table). Foreign keys and unique constraints
    pass through as well, so a migrated table cannot diverge from
    ``create_all`` or admit orphan rows (a requirement is meaningless without
    its jurisdiction and source).
    """
    table = Base.metadata.tables[name]
    columns = [column.copy() for column in table.columns]
    constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(
            constraint,
            (
                sa.PrimaryKeyConstraint,
                sa.ForeignKeyConstraint,
                sa.UniqueConstraint,
                sa.CheckConstraint,
            ),
        )
    ]
    op.create_table(name, *columns, *constraints)


def upgrade() -> None:
    if context.is_offline_mode():
        for name in _TABLES:
            _create_table(name)
        return

    for name in _TABLES:
        if not _inspector().has_table(name):
            _create_table(name)


def downgrade() -> None:
    if context.is_offline_mode():
        return
    for name in reversed(_TABLES):
        if _inspector().has_table(name):
            op.drop_table(name)
