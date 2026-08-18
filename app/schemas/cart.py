from typing import List
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse

class CartItemAdd(BaseModel):
    """Schema for adding a product to the cart."""
    product_id: int = Field(..., examples=[101])
    quantity: int = Field(..., gt=0, examples=[2])

class CartItemUpdate(BaseModel):
    """Schema for updating the quantity of a product in the cart."""
    quantity: int = Field(..., gt=0, examples=[3])

class CartItemResponse(BaseModel):
    """Schema representing an item in the cart."""
    id: int
    product_id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    """Schema representing a shopping cart with all its items."""
    id: int
    user_id: int
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True
