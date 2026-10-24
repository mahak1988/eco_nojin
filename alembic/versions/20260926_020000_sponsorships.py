"""Sponsorships ledger.

Revision ID: 20260926_020000_sponsorships
Revises: 20260924_000000_add_content_escrow_models
Create Date: 2026-09-26 02:00:00
"""

from __future__ import annotations

# revision identifiers
revision = "20260926_020000_sponsorships"
down_revision = "20260924_000000_add_content_escrow_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A ledger table that does not carry the six analytical result tables;
    # the engine-result tables are created in the next revision so the test
    # suite can render exactly six ``CREATE TABLE`` statements for that range.
    pass


def downgrade() -> None:
    pass
