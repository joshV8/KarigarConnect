from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """SQLAlchemy model representing an artisan user authenticated via Firebase."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    language = Column(String(10), default="hi", nullable=False)
    location = Column(String(100), nullable=True)
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

    products = relationship(
        "Product",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    catalogs = relationship(
        "Catalog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
