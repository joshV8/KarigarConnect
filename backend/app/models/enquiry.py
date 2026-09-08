from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Enquiry(Base):
    """SQLAlchemy model representing a B2B enquiry / wholesale deal between an artisan and a buyer."""

    __tablename__ = "enquiries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'contacted', 'accepted', 'rejected')",
            name="chk_enquiry_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    buyer_id = Column(
        Integer,
        ForeignKey("buyers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = Column(Text, nullable=False)
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # pending | contacted | accepted | rejected
    artisan_response = Column(Text, nullable=True)
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
    responded_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    buyer = relationship("Buyer", back_populates="enquiries")
    product = relationship("Product", back_populates="enquiries")
