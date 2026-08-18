from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Category(Base):
    """
    SQLAlchemy model representing the 'categories' table.
    Allows organizing products into distinct groups.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships:
    # 1-to-many relationship with Products
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
