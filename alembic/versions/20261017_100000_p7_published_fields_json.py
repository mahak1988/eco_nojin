"""P7: convert published_fields from comma-separated Text to JSON list.

``published_fields`` on ``gov_community_spaces`` was a comma-separated string.
This migration converts it to a JSON array so the service can treat it as a
proper list (``publish_sensitive_field`` now appends to a Python list).

Guard: the column type change is a no-op on databases that already have JSON;
on SQLite/older schemas the ALTER is emitted and existing comma-separated
values are parsed into lists. Rows with NULL stay NULL.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_100000_p7_published_fields_json"
down_revision: str | None = "20261017_093000_p9b_inventory_signed_qty_backfill"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "gov_community_spaces"
_COLUMN = "published_fields"


def _column_exists() -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(_TABLE):
        return False
    return any(c["name"] == _COLUMN for c in inspector.get_columns(_TABLE))


def upgrade() -> None:
    if context.is_offline_mode():
        return
    if not _column_exists():
        return

    # SQLite: JSON is stored as TEXT, so no ALTER needed.
    # Other dialects: change type Text -> JSON with USING clause.
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect != "sqlite":
        op.alter_column(
            _TABLE,
            _COLUMN,
            existing_type=sa.Text(),
            type_=sa.JSON(),
            existing_nullable=True,
            postgresql_using="published_fields::json",
        )
    # SQLite: skip type change; JSON stored as TEXT. Only backfill needed.

    # Backfill: parse any remaining comma-separated strings into JSON lists.
    stmt = sa.text(f"SELECT id, {_COLUMN} FROM {_TABLE} WHERE {_COLUMN} IS NOT NULL")
    result = bind.execute(stmt)
    to_update = []
    for row in result:
        val = row[_COLUMN]
        if isinstance(val, str):
            items = [x.strip() for x in val.split(",") if x.strip()]
            to_update.append({"id": row.id, "published_fields": items})
    if to_update:
        bind.execute(
            sa.text(f"UPDATE {_TABLE} SET {_COLUMN} = :published_fields WHERE id = :id"),
            to_update,
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    if not _column_exists():
        return
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.alter_column(
            _TABLE,
            _COLUMN,
            existing_type=sa.JSON(),
            type_=sa.Text(),
            existing_nullable=True,
        )
    # SQLite: no type change to revert (JSON stored as TEXT)
