from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Inventory(Base):
    """
    SQLAlchemy model representing the 'inventory' table.
    Separates product definitions from physical counts.
    Tracks total quantity, reserved quantities during checkout, and reorder levels for low stock alerts.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships:
    product = relationship("Product", back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        """
        Calculates how many items can actually be sold.
        Formula: quantity - reserved_quantity
        """
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self) -> bool:
        """
        Checks if physical stock count is below reorder level.
        """
        return self.quantity < self.reorder_level
