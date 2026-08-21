"""phase6 content versions and translations

Revision ID: e5f1a2b3c4d5
Revises: d4e9f0a3b2c5
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f1a2b3c4d5"
down_revision = "d4e9f0a3b2c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_items", sa.Column("generated_by_ai", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("content_items", sa.Column("rag_synced", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("content_items", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.create_table(
        "content_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "content_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("language", sa.String(10), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("content_translations")
    op.drop_table("content_versions")
    op.drop_column("content_items", "published_at")
    op.drop_column("content_items", "rag_synced")
    op.drop_column("content_items", "generated_by_ai")
