from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    """Schema for validating product creation requests."""
    name: str = Field(..., min_length=1, max_length=255, examples=["iPhone 16"])
    description: Optional[str] = Field(None, max_length=1000, examples=["Latest Apple smartphone"])
    price: float = Field(..., gt=0, examples=[69999.0])
    category_id: int = Field(..., examples=[1])
    sku: str = Field(..., min_length=1, max_length=100, examples=["IP16-001"])

class ProductUpdate(BaseModel):
    """Schema for validating product update requests. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=100)

class ProductResponse(BaseModel):
    """Schema for returning product details."""
    id: int
    name: str
    description: Optional[str]
    price: float
    category_id: int
    sku: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
