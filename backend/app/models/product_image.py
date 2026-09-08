from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductImage(Base):
    """SQLAlchemy model for product images uploaded to Cloudinary / storage."""

    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_url = Column(String(1024), nullable=False)
    processed_url = Column(
        String(1024),
        nullable=True,
    )  # Ready for Person 2's AI image processing pipeline
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    product = relationship("Product", back_populates="images")
