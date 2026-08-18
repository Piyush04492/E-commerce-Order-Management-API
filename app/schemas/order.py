from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse

class OrderCheckout(BaseModel):
    """Schema for checkout requests, requiring a shipping address."""
    shipping_address: str = Field(
        ..., 
        min_length=5, 
        max_length=500, 
        examples=["123 Main St, Tech City, 560001"]
    )

class OrderItemResponse(BaseModel):
    """Schema representing an item purchased within an order."""
    id: int
    product_id: Optional[int]
    quantity: int
    unit_price: float
    subtotal: float
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    """Schema representing a complete order, including its items and payment status."""
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    """Schema for updating an order's status (used by admins)."""
    status: str = Field(..., examples=["CONFIRMED"])
