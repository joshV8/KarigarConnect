from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """SQLAlchemy model representing an artisan's product in the catalog."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("raw_material_cost >= 0", name="chk_product_raw_material_cost"),
        CheckConstraint("labour_cost >= 0", name="chk_product_labour_cost"),
        CheckConstraint("packaging_cost >= 0", name="chk_product_packaging_cost"),
        CheckConstraint(
            "status IN ('draft', 'uploaded', 'processing', 'processed', 'processing_failed', 'published', 'archived')",
            name="chk_product_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description_en = Column(Text, nullable=True)
    description_hi = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    material = Column(String(100), nullable=True)
    raw_material_cost = Column(Float, default=0.0, nullable=False)
    labour_cost = Column(Float, default=0.0, nullable=False)
    packaging_cost = Column(Float, default=0.0, nullable=False)
    # Status lifecycle: draft → uploaded → processing → processed | processing_failed | published | archived
    status = Column(String(50), default="draft", nullable=False, index=True)
    seo_title = Column(String(255), nullable=True)
    seo_keywords = Column(JSON, nullable=True)
    # Voice AI transcription fields (nullable — populated only when audio is processed)
    voice_transcription = Column(Text, nullable=True)    # Raw regional-language STT output
    translated_voice_text = Column(Text, nullable=True)  # English translation of above
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to owning User
    user = relationship("User", back_populates="products")

    # Relationship to product images
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImage.id.asc()",
    )

    # Relationship to voice recordings
    audio_recordings = relationship(
        "ProductAudio",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductAudio.id.asc()",
    )

    # Relationship to pricing history
    prices = relationship(
        "Price",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Price.created_at.desc()",
    )

    # Many-to-Many relationship to Catalogs
    catalogs = relationship(
        "Catalog",
        secondary="catalog_products",
        back_populates="products",
        lazy="selectin",
    )

    # Relationship to B2B Enquiries
    enquiries = relationship(
        "Enquiry",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Enquiry.created_at.desc()",
    )
