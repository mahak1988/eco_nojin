"""P8: multi-language fields on village_brands and village_destinations.

Adds English-language variants of the primary text fields so village
branding and destination pages can be served in multiple languages.
Each ``_en`` column falls back to the primary field when absent.

Guarded and re-run-safe: each column is added only when absent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_080000_p8_village_multilanguage"
down_revision: str | None = "20261017_073000_p5_inventory_user_id"
branch_labels: str | None = None
depends_on: str | None = None


def _column_exists(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    if context.is_offline_mode():
        return
    if not _column_exists("village_brands", "story_en"):
        op.add_column(
            "village_brands", sa.Column("story_en", sa.Text(), nullable=True)
        )
    if not _column_exists("village_brands", "vision_en"):
        op.add_column(
            "village_brands", sa.Column("vision_en", sa.Text(), nullable=True)
        )
    if not _column_exists("village_brands", "heritage_en"):
        op.add_column(
            "village_brands", sa.Column("heritage_en", sa.Text(), nullable=True)
        )
    if not _column_exists("village_destinations", "tagline_en"):
        op.add_column(
            "village_destinations",
            sa.Column("tagline_en", sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    for table, column in [
        ("village_brands", "story_en"),
        ("village_brands", "vision_en"),
        ("village_brands", "heritage_en"),
        ("village_destinations", "tagline_en"),
    ]:
        if _column_exists(table, column):
            try:
                op.drop_column(table, column)
            except Exception:
                pass
