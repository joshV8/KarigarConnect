from sqlalchemy import Column, Integer, Float, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Price(Base):
    """SQLAlchemy model representing a calculated pricing recommendation for a product."""

    __tablename__ = "prices"
    __table_args__ = (
        CheckConstraint("recommended_price >= 0", name="chk_price_recommended_positive"),
        CheckConstraint("minimum_price >= 0", name="chk_price_minimum_positive"),
        CheckConstraint("maximum_price >= minimum_price", name="chk_price_maximum_valid"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommended_price = Column(Float, nullable=False)
    minimum_price = Column(Float, nullable=False)
    maximum_price = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    product = relationship("Product", back_populates="prices")
