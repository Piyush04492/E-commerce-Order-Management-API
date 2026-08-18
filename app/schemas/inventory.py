from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class InventoryUpdate(BaseModel):
    """Schema for updating product inventory details."""
    quantity: Optional[int] = Field(None, ge=0, examples=[100])
    reserved_quantity: Optional[int] = Field(None, ge=0, examples=[5])
    reorder_level: Optional[int] = Field(None, ge=0, examples=[10])

class InventoryResponse(BaseModel):
    """Schema for returning product inventory details."""
    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_level: int
    updated_at: datetime
    is_low_stock: bool

    model_config = ConfigDict(from_attributes=True)

class LowStockAlert(BaseModel):
    """Schema for low stock alert response."""
    product_id: int
    product_name: str
    sku: str
    quantity: int
    reorder_level: int
