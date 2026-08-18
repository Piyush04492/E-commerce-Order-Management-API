from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    """Schema for validating user registration requests."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Piyush"])
    email: EmailStr = Field(..., examples=["piyush@example.com"])
    password: str = Field(..., min_length=6, max_length=100, examples=["password123"])

class UserLogin(BaseModel):
    """Schema for validating user login requests."""
    email: EmailStr = Field(..., examples=["piyush@example.com"])
    password: str = Field(..., examples=["password123"])

class UserResponse(BaseModel):
    """Schema for returning user details (excludes password hash)."""
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to parse ORM models directly

class Token(BaseModel):
    """Schema for returning OAuth2/JWT access tokens."""
    access_token: str
    token_type: str = "bearer"
