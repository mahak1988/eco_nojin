"""merge heads

Revision ID: 152cf86214af
Revises: 20260918_140000_village_hub_extended, 20260920_000000_add_supabase_sync_fields, eco_coin_ecosystem_001, p2_phase2_legal_tool_registry
Create Date: 2026-09-24 08:26:21.780312

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "152cf86214af"
down_revision: str | Sequence[str] | None = (
    "20260918_140000_village_hub_extended",
    "20260920_000000_add_supabase_sync_fields",
    "eco_coin_ecosystem_001",
    "p2_phase2_legal_tool_registry",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
