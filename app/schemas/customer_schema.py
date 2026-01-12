"""
Pydantic schemas for customer-related operations.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    """Base customer schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    password: str = Field(..., min_length=8)


class CustomerUpdate(BaseModel):
    """Schema for updating customer information."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerLogin(BaseModel):
    """Schema for customer login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None
    exp: Optional[int] = None
    type: Optional[str] = None
