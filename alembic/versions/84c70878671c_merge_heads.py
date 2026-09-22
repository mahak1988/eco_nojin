"""merge_heads

Revision ID: 84c70878671c
Revises: 4a6f9c2e1b03, phase5_audit_complete
Create Date: 2026-09-15 05:38:43.450136

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "84c70878671c"
down_revision: Union[str, Sequence[str], None] = ("4a6f9c2e1b03", "phase5_audit_complete")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
