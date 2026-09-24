"""merge heads

Revision ID: 152cf86214af
Revises: 20260918_140000_village_hub_extended, 20260920_000000_add_supabase_sync_fields, eco_coin_ecosystem_001, p2_phase2_legal_tool_registry
Create Date: 2026-09-24 08:26:21.780312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '152cf86214af'
down_revision: Union[str, Sequence[str], None] = ('20260918_140000_village_hub_extended', '20260920_000000_add_supabase_sync_fields', 'eco_coin_ecosystem_001', 'p2_phase2_legal_tool_registry')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
