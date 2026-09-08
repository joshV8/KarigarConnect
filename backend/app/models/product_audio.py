from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductAudio(Base):
    """SQLAlchemy model for voice recordings uploaded to Cloudinary / storage."""

    __tablename__ = "product_audio"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audio_url = Column(String(1024), nullable=False)
    language = Column(String(10), nullable=True, default="hi")  # hi, mr, gu, ta, en, etc.
    duration = Column(Float, nullable=True)  # Duration in seconds
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship back to product
    product = relationship("Product", back_populates="audio_recordings")
