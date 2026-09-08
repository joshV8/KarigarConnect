from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    """SQLAlchemy model representing an in-app event notification for an artisan."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(
        String(50),
        default="new_enquiry",
        nullable=False,
        index=True,
    )  # new_enquiry | enquiry_status | system
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_enquiry_id = Column(
        Integer,
        ForeignKey("enquiries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="notifications")
    product = relationship("Product")
    enquiry = relationship("Enquiry")
