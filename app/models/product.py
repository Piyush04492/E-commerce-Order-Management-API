from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Product(Base):
    """
    SQLAlchemy model representing the 'products' table.
    Contains product specifications and links to a Category and Inventory.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    price = Column(Float, nullable=False)  # Float representation for simplicity
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships:
    category = relationship("Category", back_populates="products")
    # uselist=False creates a 1-to-1 relationship with the Inventory record
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
