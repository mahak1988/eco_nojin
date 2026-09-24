"""merge_phase5_heads

Revision ID: 300c2f07b568
Revises: 20260824_135612_marketplace_tourism_landscape
Create Date: 2026-08-28 00:17:56.360047

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "300c2f07b568"
down_revision: str | Sequence[str] | None = "20260824_135612_marketplace_tourism_landscape"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
