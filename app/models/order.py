from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Order(Base):
    """
    SQLAlchemy model representing the 'orders' table.
    Tracks user, total cost, shipping details, and status.
    Uses status strings matching our state machine: PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="PENDING")
    shipping_address = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships:
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    """
    SQLAlchemy model representing the 'order_items' table.
    Captures specific items bought in an order.
    CRITICAL INTERVIEW DETAIL: unit_price is explicitly stored here to freeze the historical 
    price of the product at checkout. If the product price changes in the future, 
    the historic order total is preserved.
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Frozen price
    subtotal = Column(Float, nullable=False)      # quantity * unit_price (frozen)

    # Relationships:
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
