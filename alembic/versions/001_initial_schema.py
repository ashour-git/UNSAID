"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-06-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("subtitle", sa.String(180), nullable=False),
        sa.Column("concentration", sa.String(80), nullable=False, server_default="Extrait de Parfum"),
        sa.Column("volume", sa.String(20), nullable=False, server_default="30ml"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("olfactory_notes", sa.JSON(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("compare_at_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column("dynamic_slug", sa.String(140), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("meta_title", sa.String(160), nullable=False, server_default=""),
        sa.Column("meta_description", sa.String(320), nullable=False, server_default=""),
        sa.Column("gallery_images", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dynamic_slug"),
        sa.CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )
    op.create_index(op.f("ix_products_dynamic_slug"), "products", ["dynamic_slug"], unique=True)
    op.create_index(op.f("ix_products_id"), "products", ["id"])
    op.create_index(op.f("ix_products_is_active"), "products", ["is_active"])

    op.create_table(
        "product_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("volume", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_options_id"), "product_options", ["id"])
    op.create_index(op.f("ix_product_options_product_id"), "product_options", ["product_id"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_key", sa.String(160), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_key"),
    )
    op.create_index(op.f("ix_knowledge_documents_category"), "knowledge_documents", ["category"])
    op.create_index(op.f("ix_knowledge_documents_document_key"), "knowledge_documents", ["document_key"], unique=True)
    op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(40), nullable=False, server_default="customer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"])
    op.create_index(op.f("ix_users_role"), "users", ["role"])

    op.create_table(
        "customer_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(80), nullable=False, server_default=""),
        sa.Column("city", sa.String(120), nullable=False, server_default=""),
        sa.Column("shipping_address", sa.String(500), nullable=False, server_default=""),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_customer_profiles_id"), "customer_profiles", ["id"])
    op.create_index(op.f("ix_customer_profiles_user_id"), "customer_profiles", ["user_id"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(40), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("customer_name", sa.String(160), nullable=False),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("customer_phone", sa.String(80), nullable=False),
        sa.Column("shipping_address", sa.String(500), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="new"),
        sa.Column("source", sa.String(80), nullable=False, server_default="site"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("whatsapp_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("internal_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index(op.f("ix_orders_city"), "orders", ["city"])
    op.create_index(op.f("ix_orders_created_at"), "orders", ["created_at"])
    op.create_index(op.f("ix_orders_customer_email"), "orders", ["customer_email"])
    op.create_index(op.f("ix_orders_id"), "orders", ["id"])
    op.create_index(op.f("ix_orders_order_number"), "orders", ["order_number"], unique=True)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"])
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"])

    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("source", sa.String(80), nullable=False, server_default="footer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_newsletter_subscribers_email"), "newsletter_subscribers", ["email"], unique=True)
    op.create_index(op.f("ix_newsletter_subscribers_id"), "newsletter_subscribers", ["id"])

    op.create_table(
        "insight_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("summary", sa.String(1200), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("model", sa.String(120), nullable=False, server_default="deterministic"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_insight_snapshots_created_at"), "insight_snapshots", ["created_at"])
    op.create_index(op.f("ix_insight_snapshots_id"), "insight_snapshots", ["id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("product_name_snapshot", sa.String(160), nullable=False),
        sa.Column("product_slug_snapshot", sa.String(160), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_id"), "order_items", ["id"])
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"])
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"])

    op.create_table(
        "order_status_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_status_events_actor_user_id"), "order_status_events", ["actor_user_id"])
    op.create_index(op.f("ix_order_status_events_id"), "order_status_events", ["id"])
    op.create_index(op.f("ix_order_status_events_order_id"), "order_status_events", ["order_id"])

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_name", sa.String(120), nullable=False),
        sa.Column("anonymous_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id")),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_events_anonymous_id"), "analytics_events", ["anonymous_id"])
    op.create_index(op.f("ix_analytics_events_created_at"), "analytics_events", ["created_at"])
    op.create_index(op.f("ix_analytics_events_event_name"), "analytics_events", ["event_name"])
    op.create_index(op.f("ix_analytics_events_id"), "analytics_events", ["id"])
    op.create_index(op.f("ix_analytics_events_order_id"), "analytics_events", ["order_id"])
    op.create_index(op.f("ix_analytics_events_product_id"), "analytics_events", ["product_id"])
    op.create_index(op.f("ix_analytics_events_user_id"), "analytics_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("order_status_events")
    op.drop_table("order_items")
    op.drop_table("insight_snapshots")
    op.drop_table("newsletter_subscribers")
    op.drop_table("orders")
    op.drop_table("customer_profiles")
    op.drop_table("users")
    op.drop_table("knowledge_documents")
    op.drop_table("product_options")
    op.drop_table("products")
