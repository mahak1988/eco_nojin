"""merge webauthn and engine result heads

Revision ID: b3e09e91d6f3
Revises: 20260926_010000, 20260927_010000_engine_result_tables
Create Date: 2026-09-28 03:36:05.561263

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b3e09e91d6f3"
down_revision: str | Sequence[str] | None = (
    "20260926_010000",
    "20260927_010000_engine_result_tables",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
