from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Payment(Base):
    """
    SQLAlchemy model representing the 'payments' table.
    Tracks simulated transaction statuses (PENDING, SUCCESS, FAILED, REFUNDED).
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, FAILED, REFUNDED
    transaction_id = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships:
    order = relationship("Order", back_populates="payments")
