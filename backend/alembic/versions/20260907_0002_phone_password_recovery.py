"""phone password recovery

Revision ID: 20260907_0002
Revises: 20260723_0001
Create Date: 2026-09-07

Approved by role 1 for the phone and verification challenge schema change.
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0002"
down_revision: str | None = "20260723_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(20), nullable=True))
    op.add_column(
        "users",
        sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_table(
        "phone_verification_challenges",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("phone_hash", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_phone_verification_challenges_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_phone_verification_challenges"),
    )
    op.create_index(
        "ix_phone_verification_challenges_purpose",
        "phone_verification_challenges",
        ["purpose"],
    )
    op.create_index(
        "ix_phone_verification_challenges_phone_hash",
        "phone_verification_challenges",
        ["phone_hash"],
    )
    op.create_index(
        "ix_phone_verification_challenges_user_id",
        "phone_verification_challenges",
        ["user_id"],
    )
    op.create_index(
        "ix_phone_verification_challenges_expires_at",
        "phone_verification_challenges",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_table("phone_verification_challenges")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "auth_version")
    op.drop_column("users", "phone")
