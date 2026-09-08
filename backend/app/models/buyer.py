from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Buyer(Base):
    """SQLAlchemy model representing a verified B2B buyer / wholesale distributor."""

    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    enquiries = relationship(
        "Enquiry",
        back_populates="buyer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
