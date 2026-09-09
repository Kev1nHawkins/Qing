"""add user phone

Revision ID: 20260909_0002
Revises: 20260723_0001
Create Date: 2026-09-09
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260909_0002"
down_revision: str | None = "20260723_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "phone")
