"""Align the users table with the current auth model."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260924_010000"
down_revision: str | Sequence[str] | None = "20260924_000000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _user_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("users")}


def upgrade() -> None:
    columns = _user_columns()
    if not columns:
        return
    additions = (
        ("role", sa.String(length=50), False, "regular"),
        ("two_factor_enabled", sa.Boolean(), False, sa.text("false")),
        ("two_factor_secret", sa.String(), True, None),
        ("avatar_url", sa.String(), True, None),
        ("is_active", sa.Boolean(), False, sa.text("true")),
        ("created_at", sa.DateTime(timezone=True), True, sa.func.now()),
    )
    for name, column_type, nullable, default in additions:
        if name in columns:
            continue
        kwargs = {"nullable": nullable}
        if default is not None:
            kwargs["server_default"] = default
        op.add_column("users", sa.Column(name, column_type, **kwargs))


def downgrade() -> None:
    columns = _user_columns()
    if not columns:
        return
    for name in (
        "created_at",
        "is_active",
        "avatar_url",
        "two_factor_secret",
        "two_factor_enabled",
        "role",
    ):
        if name in columns:
            op.drop_column("users", name)
