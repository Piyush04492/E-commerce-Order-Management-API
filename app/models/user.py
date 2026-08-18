from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class User(Base):
    """
    SQLAlchemy model representing the 'users' table.
    Stores names, emails (indexed and unique for fast logins), hashed passwords, and roles.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="customer")  # Role can be 'customer' or 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships:
    # uselist=False creates a 1-to-1 relationship with the Cart
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    # 1-to-many relationship with Orders
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
