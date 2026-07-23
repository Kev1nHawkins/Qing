"""initial schema

Revision ID: 20260723_0001
Revises:
Create Date: 2026-07-23
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260723_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def create_index(table: str, *columns: str, unique: bool = False) -> None:
    name = f"ix_{table}_{'_'.join(columns)}"
    op.create_index(name, table, list(columns), unique=unique)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
    )
    create_index("roles", "code", unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(64), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("points_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role_id", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_users_role_id_roles"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    create_index("users", "username", unique=True)
    create_index("users", "email", unique=True)
    create_index("users", "is_active")
    create_index("users", "role_id")

    op.create_table(
        "file_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("public_url", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usage_type", sa.String(50), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_file_assets_owner_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_file_assets"),
        sa.UniqueConstraint("storage_key", name="uq_file_assets_storage_key"),
    )
    create_index("file_assets", "owner_id")

    op.create_table(
        "culture_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("source_title", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_culture_items_created_by_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_culture_items"),
    )
    create_index("culture_items", "title")
    create_index("culture_items", "slug", unique=True)
    create_index("culture_items", "category")
    create_index("culture_items", "status")
    create_index("culture_items", "created_by_id")

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("culture_item_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["culture_item_id"], ["culture_items.id"], name="fk_locations_culture_item_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_locations"),
    )
    create_index("locations", "name")
    create_index("locations", "culture_item_id")

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("distance_km", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_routes_created_by_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_routes"),
    )
    create_index("routes", "title")
    create_index("routes", "slug", unique=True)
    create_index("routes", "status")
    create_index("routes", "created_by_id")

    op.create_table(
        "creation_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("options_schema", sa.JSON(), nullable=True),
        sa.Column("preview_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("culture_item_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["culture_item_id"],
            ["culture_items.id"],
            name="fk_creation_templates_culture_item_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_creation_templates"),
    )
    create_index("creation_templates", "code", unique=True)
    create_index("creation_templates", "status")
    create_index("creation_templates", "culture_item_id")

    op.create_table(
        "route_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("culture_item_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(30), nullable=False, server_default="CHECK_IN"),
        sa.Column("question", sa.String(500), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.String(255), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("qr_code", sa.String(120), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="100"),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["route_id"], ["routes.id"], name="fk_route_tasks_route_id_routes"
        ),
        sa.ForeignKeyConstraint(
            ["culture_item_id"],
            ["culture_items.id"],
            name="fk_route_tasks_culture_item_id",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["locations.id"], name="fk_route_tasks_location_id_locations"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_route_tasks"),
        sa.UniqueConstraint("route_id", "order_no", name="uq_route_task_order"),
        sa.UniqueConstraint("qr_code", name="uq_route_tasks_qr_code"),
    )
    create_index("route_tasks", "route_id")
    create_index("route_tasks", "culture_item_id")
    create_index("route_tasks", "location_id")

    op.create_table(
        "user_task_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("answer", sa.String(500), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("awarded_points", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_task_records_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["route_tasks.id"], name="fk_user_task_records_task_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_task_records"),
        sa.UniqueConstraint("user_id", "task_id", name="uq_user_task_record"),
    )
    create_index("user_task_records", "user_id")
    create_index("user_task_records", "task_id")

    op.create_table(
        "ai_creations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("culture_item_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_creations_user_id_users"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["creation_templates.id"], name="fk_ai_creations_template_id"
        ),
        sa.ForeignKeyConstraint(
            ["culture_item_id"], ["culture_items.id"], name="fk_ai_creations_culture_item_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_creations"),
    )
    create_index("ai_creations", "user_id")
    create_index("ai_creations", "template_id")
    create_index("ai_creations", "culture_item_id")
    create_index("ai_creations", "status")

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("culture_item_id", sa.Integer(), nullable=True),
        sa.Column("creation_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("favorite_count", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_posts_author_id_users"),
        sa.ForeignKeyConstraint(
            ["culture_item_id"], ["culture_items.id"], name="fk_posts_culture_item_id"
        ),
        sa.ForeignKeyConstraint(
            ["creation_id"], ["ai_creations.id"], name="fk_posts_creation_id_ai_creations"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_posts"),
    )
    create_index("posts", "author_id")
    create_index("posts", "culture_item_id")
    create_index("posts", "creation_id")
    create_index("posts", "status")

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.String(1000), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        *timestamps(),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_comments_post_id_posts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_comments_user_id_users"),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["comments.id"], name="fk_comments_parent_id_comments"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
    )
    create_index("comments", "post_id")
    create_index("comments", "user_id")
    create_index("comments", "parent_id")

    op.create_table(
        "post_likes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_post_likes_post_id_posts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_post_likes_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_post_likes"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_user_like"),
    )
    create_index("post_likes", "post_id")
    create_index("post_likes", "user_id")

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_favorites_post_id_posts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_favorites_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_favorites"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_user_favorite"),
    )
    create_index("favorites", "post_id")
    create_index("favorites", "user_id")

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
    )
    create_index("tags", "name", unique=True)
    create_index("tags", "slug", unique=True)

    op.create_table(
        "post_tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_post_tags_post_id_posts"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], name="fk_post_tags_tag_id_tags"),
        sa.PrimaryKeyConstraint("id", name="pk_post_tags"),
        sa.UniqueConstraint("post_id", "tag_id", name="uq_post_tag"),
    )
    create_index("post_tags", "post_id")
    create_index("post_tags", "tag_id")

    op.create_table(
        "point_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason_type", sa.String(40), nullable=False),
        sa.Column("reason_id", sa.Integer(), nullable=True),
        sa.Column("business_key", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_point_records_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_point_records"),
        sa.UniqueConstraint("user_id", "business_key", name="uq_user_point_business"),
    )
    create_index("point_records", "user_id")
    create_index("point_records", "reason_type")
    create_index("point_records", "reason_id")

    op.create_table(
        "badges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("rule_type", sa.String(40), nullable=False, server_default="MANUAL"),
        sa.Column("rule_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_badges"),
    )
    create_index("badges", "code", unique=True)

    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("badge_id", sa.Integer(), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_badges_user_id_users"),
        sa.ForeignKeyConstraint(
            ["badge_id"], ["badges.id"], name="fk_user_badges_badge_id_badges"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_badges"),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    create_index("user_badges", "user_id")
    create_index("user_badges", "badge_id")


def downgrade() -> None:
    for table in [
        "user_badges",
        "badges",
        "point_records",
        "post_tags",
        "tags",
        "favorites",
        "post_likes",
        "comments",
        "posts",
        "ai_creations",
        "user_task_records",
        "route_tasks",
        "creation_templates",
        "routes",
        "locations",
        "culture_items",
        "file_assets",
        "users",
        "roles",
    ]:
        op.drop_table(table)
