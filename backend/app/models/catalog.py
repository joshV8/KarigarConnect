from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Table,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Association table for Many-to-Many Catalog <-> Product relationship with uniqueness guarantee
catalog_products = Table(
    "catalog_products",
    Base.metadata,
    Column(
        "catalog_id",
        Integer,
        ForeignKey("catalogs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    UniqueConstraint("catalog_id", "product_id", name="uq_catalog_product"),
)


class Catalog(Base):
    """SQLAlchemy model representing an artisan's curated digital catalog."""

    __tablename__ = "catalogs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="chk_catalog_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to owning User
    user = relationship("User", back_populates="catalogs")

    # Many-to-Many relationship with Product
    products = relationship(
        "Product",
        secondary=catalog_products,
        back_populates="catalogs",
        lazy="selectin",
    )
