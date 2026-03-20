"""add password auth

Revision ID: 20260320_000002
Revises: 20260320_000001
Create Date: 2026-03-20 00:00:02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260320_000002"
down_revision = "20260320_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "clerk_user_id", nullable=True)
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
    op.alter_column("users", "clerk_user_id", nullable=False)
