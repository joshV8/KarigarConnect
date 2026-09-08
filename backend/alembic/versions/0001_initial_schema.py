"""Initial Database Schema with Constraints and Indexes

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-08 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("firebase_uid", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=10), server_default="hi", nullable=False),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)

    # 2. products table
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_hi", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("material", sa.String(length=100), nullable=True),
        sa.Column("raw_material_cost", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("labour_cost", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("packaging_cost", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="draft", nullable=False),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_keywords", sa.JSON(), nullable=True),
        sa.Column("voice_transcription", sa.Text(), nullable=True),
        sa.Column("translated_voice_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("raw_material_cost >= 0", name="chk_product_raw_material_cost"),
        sa.CheckConstraint("labour_cost >= 0", name="chk_product_labour_cost"),
        sa.CheckConstraint("packaging_cost >= 0", name="chk_product_packaging_cost"),
        sa.CheckConstraint(
            "status IN ('draft', 'uploaded', 'processing', 'processed', 'processing_failed', 'published', 'archived')",
            name="chk_product_status_valid",
        ),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_user_id", "products", ["user_id"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_status", "products", ["status"])

    # 3. product_images table
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_url", sa.String(length=1024), nullable=False),
        sa.Column("processed_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_product_images_id", "product_images", ["id"])
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    # 4. product_audio table
    op.create_table(
        "product_audio",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audio_url", sa.String(length=1024), nullable=False),
        sa.Column("language", sa.String(length=10), server_default="hi", nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_product_audio_id", "product_audio", ["id"])
    op.create_index("ix_product_audio_product_id", "product_audio", ["product_id"])

    # 5. prices table
    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_price", sa.Float(), nullable=False),
        sa.Column("minimum_price", sa.Float(), nullable=False),
        sa.Column("maximum_price", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("recommended_price >= 0", name="chk_price_recommended_positive"),
        sa.CheckConstraint("minimum_price >= 0", name="chk_price_minimum_positive"),
        sa.CheckConstraint("maximum_price >= minimum_price", name="chk_price_maximum_valid"),
    )
    op.create_index("ix_prices_id", "prices", ["id"])
    op.create_index("ix_prices_product_id", "prices", ["product_id"])

    # 6. catalogs table
    op.create_table(
        "catalogs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="chk_catalog_status_valid",
        ),
    )
    op.create_index("ix_catalogs_id", "catalogs", ["id"])
    op.create_index("ix_catalogs_user_id", "catalogs", ["user_id"])
    op.create_index("ix_catalogs_title", "catalogs", ["title"])
    op.create_index("ix_catalogs_status", "catalogs", ["status"])

    # 7. catalog_products association table
    op.create_table(
        "catalog_products",
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("catalogs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("catalog_id", "product_id", name="uq_catalog_product"),
    )

    # 8. buyers table
    op.create_table(
        "buyers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_buyers_id", "buyers", ["id"])
    op.create_index("ix_buyers_company", "buyers", ["company"])
    op.create_index("ix_buyers_location", "buyers", ["location"])
    op.create_index("ix_buyers_category", "buyers", ["category"])

    # 9. enquiries table
    op.create_table(
        "enquiries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("artisan_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'contacted', 'accepted', 'rejected')",
            name="chk_enquiry_status_valid",
        ),
    )
    op.create_index("ix_enquiries_id", "enquiries", ["id"])
    op.create_index("ix_enquiries_buyer_id", "enquiries", ["buyer_id"])
    op.create_index("ix_enquiries_product_id", "enquiries", ["product_id"])
    op.create_index("ix_enquiries_status", "enquiries", ["status"])

    # 10. notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), server_default="new_enquiry", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_enquiry_id", sa.Integer(), sa.ForeignKey("enquiries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("enquiries")
    op.drop_table("buyers")
    op.drop_table("catalog_products")
    op.drop_table("catalogs")
    op.drop_table("prices")
    op.drop_table("product_audio")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("users")
