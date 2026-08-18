from datetime import datetime
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Electronics"])

class CategoryResponse(BaseModel):
    """Schema for returning category details."""
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
