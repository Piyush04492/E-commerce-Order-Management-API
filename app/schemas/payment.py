from datetime import datetime
from pydantic import BaseModel, Field

class PaymentSimulationRequest(BaseModel):
    """Schema to trigger a payment simulation for a pending order."""
    payment_method: str = Field(..., examples=["credit_card", "UPI", "net_banking"])
    simulate_success: bool = Field(True, description="Force simulation to succeed (True) or fail (False)")

class PaymentResponse(BaseModel):
    """Schema representing a payment transaction record."""
    id: int
    order_id: int
    amount: float
    payment_method: str
    status: str
    transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True
